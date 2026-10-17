# Super Economy Bekasi

Tugas mata kuliah Smart City. Gagasan Bupati Kabupaten Bekasi periode 2029–2034 di bidang **Smart Economy** untuk UMKM.

Halaman web ini menyajikan:

1. **Fakta resmi & status**: angka dari BPS, Pemkab Bekasi, dan pemerintah pusat, lengkap dengan sumbernya. Tiap angka dibandingkan dengan Jawa Barat dan nasional, lalu diberi status *Kritis*, *Waspada*, atau *Aman*.
2. **Rekomendasi kebijakan**: dua program untuk memperbaiki indikator yang kritis, dengan target per tahun 2030–2034:
   - **Super UMKM Bekasi**: portal profil, legalitas, pelatihan, kredit digital, dan monitoring status UMKM.
   - **Pasar UMKM Bekasi**: marketplace B2B (dengan Peraturan Bupati kemitraan industri–UMKM) dan B2C.

## Struktur

| File | Isi |
|---|---|
| `data/sumber_resmi.csv` | Semua fakta resmi: indikator, wilayah, tahun, nilai, sumber, URL |
| `scripts/interpolasi.py` | Menghitung interpolasi, proyeksi, status, dan kesenjangan |
| `data/hasil.json` | Hasil perhitungan (dibaca oleh halaman web) |
| `index.html`, `assets/` | Halaman presentasi |

## Metode (di skrip)

Perhitungan interpolasi dan proyeksi tetap ada di `scripts/interpolasi.py` sebagai dasar angka target.

**Interpolasi linear** (mengisi tahun di antara dua data resmi):

```
y(t) = y0 + (y1 − y0) × (t − t0) / (t1 − t0)
```

Contoh: kontribusi UMKM terhadap PDRB 11,99% (2016) dan 13,77% (2020), sehingga 2017 = 12,44%, 2018 = 12,88%, 2019 = 13,32%.

**Proyeksi dengan laju tetap** (melanjutkan tren setelah data terakhir):

```
r    = (y_akhir / y_awal) ^ (1 / n) − 1
y(t) = y_akhir × (1 + r) ^ (t − t_akhir)
```

Laju persentase dipakai, bukan garis lurus, supaya angka persen tidak jatuh di bawah nol. Untuk pengangguran, laju dihitung dari 2023–2025 agar tidak terdistorsi pemulihan COVID.

**Status**: *Kritis* jika lebih buruk dari semua pembanding, *Aman* jika lebih baik dari semua pembanding, selain itu *Waspada*.

**Estimasi jumlah UMKM**: jumlah UMKM nasional × proporsi penduduk Bekasi terhadap Indonesia. Ini estimasi kasar, karena angka nasional mencakup usaha mikro yang sangat kecil.

## Menjalankan

```bash
python3 scripts/interpolasi.py          # menghitung ulang data/hasil.json
python3 -m http.server 8000             # buka http://localhost:8000
```

Untuk memperbarui data, ubah atau tambah baris di `data/sumber_resmi.csv`, lalu jalankan skrip lagi.

## Keterbatasan

- Kontribusi UMKM terhadap PDRB hanya punya dua titik data (2016 dan 2020), sehingga proyeksinya paling lemah.
- Beberapa angka diambil dari media atau jurnal yang mengutip BPS, karena tabel aslinya tidak bisa diakses langsung.
- Target per tahun adalah usulan kebijakan, bukan data resmi.
