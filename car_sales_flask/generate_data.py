"""Membuat tepat 1.000 transaksi simulasi dan memasukkannya ke MySQL."""
import os, random
from datetime import date, timedelta
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

load_dotenv()
app = Flask(__name__)
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

BRANDS = {
    "Toyota": ["Avanza", "Innova", "Fortuner", "Yaris", "Agya"],
    "Honda": ["Brio", "Jazz", "HR-V", "CR-V", "Mobilio"],
    "Mitsubishi": ["Xpander", "Pajero Sport", "L300", "Outlander"],
    "Suzuki": ["Ertiga", "XL7", "Carry", "Baleno"],
    "Daihatsu": ["Xenia", "Terios", "Sigra", "Ayla"],
    "Hyundai": ["Creta", "Stargazer", "Ioniq"],
    "Nissan": ["Livina", "Serena", "X-Trail"]
}
CITIES = ["Jakarta", "Bandung", "Surabaya", "Cirebon", "Semarang",
          "Yogyakarta", "Bekasi", "Bogor", "Malang", "Denpasar"]

def estimate_price(brand, year, km, cc):
    brand_factor = {"Toyota":1.12, "Honda":1.10, "Mitsubishi":1.05,
                    "Suzuki":0.94, "Daihatsu":0.90, "Hyundai":1.02,
                    "Nissan":0.96}[brand]
    age = max(0, 2026-year)
    return max(65000000, (115000000 + cc*35000) * brand_factor
               * (0.91 ** age) * max(0.52, 1-km/320000))

with app.app_context():
    db.create_all()
    existing = Sale.query.count()
    if existing >= 1000:
        print(f"Data sudah tersedia: {existing} baris. Tidak menambahkan duplikat.")
    else:
        random.seed(42)
        rows = []
        start = date(2024, 1, 1)
        for i in range(1000 - existing):
            brand = random.choice(list(BRANDS))
            model = random.choice(BRANDS[brand])
            year = random.randint(2014, 2026)
            km = random.randint(1000, 180000)
            cc = random.choice([1000, 1200, 1300, 1500, 1800, 2000, 2400, 2500])
            transmission = random.choice(["Manual", "Automatic"])
            fuel = random.choice(["Bensin", "Diesel", "Hybrid"])
            base = estimate_price(brand, year, km, cc)
            price = int(base * random.uniform(0.88, 1.13) / 1000000) * 1000000
            rows.append(Sale(
                tanggal=start + timedelta(days=random.randint(0, 1050)),
                merek=brand, model=model, tahun=year, harga_jual=price,
                kilometer=km, transmisi=transmission, bahan_bakar=fuel,
                kapasitas_mesin=cc, kota=random.choice(CITIES)
            ))
        db.session.add_all(rows)
        db.session.commit()
        print("Berhasil menambahkan 1.000 data simulasi.")
