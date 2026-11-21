import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key-ganti-di-env")
user = os.getenv("DB_USER", "root")
password = os.getenv("DB_PASSWORD", "")
host = os.getenv("DB_HOST", "localhost")
port = os.getenv("DB_PORT", "3306")
dbname = os.getenv("DB_NAME", "car_sales_db")
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}?charset=utf8mb4"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Sale(db.Model):
    __tablename__ = "sales"
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)
    merek = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    tahun = db.Column(db.Integer, nullable=False)
    harga_jual = db.Column(db.BigInteger, nullable=False)
    kilometer = db.Column(db.Integer, nullable=False)
    transmisi = db.Column(db.String(20), nullable=False)
    bahan_bakar = db.Column(db.String(20), nullable=False)
    kapasitas_mesin = db.Column(db.Integer, nullable=False)
    kota = db.Column(db.String(50), nullable=False)

CATEGORICAL = ["merek", "transmisi", "bahan_bakar"]
NUMERIC = ["tahun", "kilometer", "kapasitas_mesin"]

def rupiah(value):
    return "Rp {:,.0f}".format(value or 0).replace(",", ".")

@app.template_filter("rupiah")
def rupiah_filter(value):
    return rupiah(value)

def sale_form_values(form):
    return {
        "tanggal": datetime.strptime(form["tanggal"], "%Y-%m-%d").date(),
        "merek": form["merek"].strip(),
        "model": form["model"].strip(),
        "tahun": int(form["tahun"]),
        "harga_jual": int(form["harga_jual"]),
        "kilometer": int(form["kilometer"]),
        "transmisi": form["transmisi"],
        "bahan_bakar": form["bahan_bakar"],
        "kapasitas_mesin": int(form["kapasitas_mesin"]),
        "kota": form["kota"].strip()
    }

@app.route("/")
def dashboard():
    total = Sale.query.count()
    revenue = db.session.query(func.coalesce(func.sum(Sale.harga_jual), 0)).scalar()
    avg = db.session.query(func.coalesce(func.avg(Sale.harga_jual), 0)).scalar()
    brands = db.session.query(Sale.merek, func.count(Sale.id)).group_by(Sale.merek).all()
    fuel = db.session.query(Sale.bahan_bakar, func.count(Sale.id)).group_by(Sale.bahan_bakar).all()
    monthly = db.session.query(
        func.date_format(Sale.tanggal, "%Y-%m").label("bulan"),
        func.count(Sale.id).label("jumlah")
    ).group_by("bulan").order_by("bulan").all()
    prices = [x.harga_jual for x in Sale.query.with_entities(Sale.harga_jual).all()]
    return render_template("dashboard.html", total=total, revenue=revenue, avg=avg,
        brand_labels=[x[0] for x in brands], brand_values=[x[1] for x in brands],
        fuel_labels=[x[0] for x in fuel], fuel_values=[x[1] for x in fuel],
        month_labels=[x[0] for x in monthly], month_values=[x[1] for x in monthly],
        prices=prices)

@app.route("/sales")
def sales():
    page = request.args.get("page", 1, type=int)
    pagination = Sale.query.order_by(Sale.tanggal.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("sales.html", pagination=pagination)

@app.route("/sales/add", methods=["GET", "POST"])
def add_sale():
    if request.method == "POST":
        try:
            db.session.add(Sale(**sale_form_values(request.form)))
            db.session.commit()
            flash("Data penjualan berhasil ditambahkan.", "success")
            return redirect(url_for("sales"))
        except Exception as e:
            db.session.rollback()
            flash(f"Gagal menyimpan data. Periksa kembali input. ({e})", "danger")
    return render_template("sale_form.html", sale=None, title="Tambah Penjualan")

@app.route("/sales/edit/<int:sale_id>", methods=["GET", "POST"])
def edit_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    if request.method == "POST":
        try:
            for key, value in sale_form_values(request.form).items():
                setattr(sale, key, value)
            db.session.commit()
            flash("Data penjualan berhasil diperbarui.", "success")
            return redirect(url_for("sales"))
        except Exception as e:
            db.session.rollback()
            flash(f"Gagal memperbarui data. ({e})", "danger")
    return render_template("sale_form.html", sale=sale, title="Edit Penjualan")

@app.route("/sales/delete/<int:sale_id>", methods=["POST"])
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    db.session.delete(sale)
    db.session.commit()
    flash("Data penjualan berhasil dihapus.", "success")
    return redirect(url_for("sales"))

def train_model():
    rows = Sale.query.all()
    if len(rows) < 20:
        return None
    df = pd.DataFrame([{
        "merek": r.merek, "transmisi": r.transmisi, "bahan_bakar": r.bahan_bakar,
        "tahun": r.tahun, "kilometer": r.kilometer,
        "kapasitas_mesin": r.kapasitas_mesin, "harga_jual": r.harga_jual
    } for r in rows])
    X = df[CATEGORICAL + NUMERIC]
    y = df["harga_jual"]
    preprocessor = ColumnTransformer([
        ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ("numeric", "passthrough", NUMERIC)
    ])
    model = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=160, random_state=42, min_samples_leaf=2))
    ])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/car_price_model.joblib")
    return {"mae": mean_absolute_error(y_test, predictions),
            "r2": r2_score(y_test, predictions), "trained": len(df)}

@app.route("/machine-learning", methods=["GET", "POST"])
def machine_learning():
    metrics = None
    prediction = None
    if request.method == "POST" and request.form.get("action") == "train":
        metrics = train_model()
        if metrics:
            flash("Model berhasil dilatih dan disimpan.", "success")
        else:
            flash("Data belum cukup untuk melatih model (minimal 20 transaksi).", "warning")
    elif request.method == "POST" and request.form.get("action") == "predict":
        model_path = "models/car_price_model.joblib"
        if not os.path.exists(model_path):
            flash("Latih model terlebih dahulu.", "warning")
        else:
            try:
                model = joblib.load(model_path)
                sample = pd.DataFrame([{
                    "merek": request.form["merek"],
                    "transmisi": request.form["transmisi"],
                    "bahan_bakar": request.form["bahan_bakar"],
                    "tahun": int(request.form["tahun"]),
                    "kilometer": int(request.form["kilometer"]),
                    "kapasitas_mesin": int(request.form["kapasitas_mesin"])
                }])
                prediction = float(model.predict(sample)[0])
            except Exception as e:
                flash(f"Prediksi gagal: {e}", "danger")
    return render_template("machine_learning.html", metrics=metrics, prediction=prediction,
                           model_exists=os.path.exists("models/car_price_model.joblib"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
