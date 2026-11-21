# Car Sales Analytics — Flask + MySQL

Aplikasi pembelajaran studi kasus penjualan mobil: CRUD, dashboard grafik (bar, pie, line, histogram), 1.000 transaksi simulasi, dan prediksi harga dengan Random Forest Regression.

## A. Persiapan
1. Python 3.13.2 dapat dicoba terlebih dahulu (sesuai lingkungan yang sudah digunakan); jika instalasi library gagal, gunakan Python 3.11 atau 3.12.
2. Install XAMPP atau MySQL Server, lalu jalankan MySQL.
3. Install VS Code (opsional).
4. Ekstrak ZIP ke folder, misalnya `C:\car_sales_flask`.

## B. Buat database
Buka phpMyAdmin (`http://localhost/phpmyadmin`) atau MySQL Workbench.
Jalankan isi `schema.sql`, atau jalankan perintah:
```sql
CREATE DATABASE car_sales_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## C. Siapkan Python
Buka CMD pada folder proyek:
```bat
cd C:\car_sales_flask
py -3.13 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```
Jika perintah `py -3.13` tidak tersedia atau instalasi scikit-learn bermasalah, gunakan Python 3.11/3.12 dan ganti perintah pembuatan virtual environment sesuai versinya.

## D. Konfigurasi koneksi
Salin `.env.example` menjadi `.env`. Buka `.env`, sesuaikan:
- `DB_USER`: biasanya `root` untuk XAMPP.
- `DB_PASSWORD`: kosong jika MySQL XAMPP tidak memakai password.
- `DB_HOST`, `DB_PORT`, `DB_NAME`: umumnya localhost, 3306, car_sales_db.

Pastikan database `car_sales_db` sudah dibuat.

## E. Buat 1.000 data simulasi
```bat
python generate_data.py
```
Jika sukses akan muncul pesan `Berhasil menambahkan 1.000 data simulasi.` Script tidak menambahkan data lagi jika sudah ada minimal 1.000 baris.

## F. Jalankan aplikasi
```bat
python app.py
```
Buka browser: `http://127.0.0.1:5000`

## G. Cara menggunakan
1. Dashboard: lihat total transaksi, nilai penjualan, rata-rata harga, dan empat grafik.
2. Data Penjualan: tambah, lihat, edit, dan hapus transaksi.
3. Machine Learning: klik **Latih Model Sekarang**. Setelah model tersimpan, isi atribut mobil dan klik **Prediksi Harga**.

## H. Penjelasan grafik
- Bar: membandingkan jumlah transaksi antar-merek.
- Pie: memperlihatkan proporsi bahan bakar.
- Line: memperlihatkan jumlah transaksi per bulan.
- Histogram: memperlihatkan distribusi rentang harga jual.

## I. Penjelasan Machine Learning
Fitur target (y) adalah `harga_jual`. Fitur input (X) terdiri dari merek, transmisi, bahan bakar, tahun, kilometer, dan kapasitas mesin. OneHotEncoder mengubah kategori menjadi representasi numerik. RandomForestRegressor mempelajari hubungan fitur dan harga. Evaluasi menggunakan MAE dan R² pada data uji 20%.

**Catatan:** seluruh 1.000 data dibuat secara acak dengan pola harga buatan untuk demonstrasi. Akurasi pada data simulasi tidak menggambarkan performa pada transaksi riil. Untuk penggunaan nyata, latih ulang dengan data penjualan yang valid dan perhatikan kualitas serta cakupan datanya.

## J. Troubleshooting singkat
- `Access denied for user`: periksa DB_USER dan DB_PASSWORD di `.env`.
- `Unknown database`: buat database `car_sales_db` terlebih dahulu.
- `Can't connect to MySQL`: pastikan MySQL di XAMPP/Services sudah aktif dan port benar.
- `ModuleNotFoundError`: aktifkan venv lalu jalankan `pip install -r requirements.txt`.
- Port 5000 digunakan: ubah `app.run(debug=True, port=5001)` lalu buka port 5001.
