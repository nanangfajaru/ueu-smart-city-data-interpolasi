"""
Interpolasi & proyeksi data Smart Economy UMKM Kabupaten Bekasi.

Jalankan:  python3 scripts/interpolasi.py
Input   :  data/sumber_resmi.csv   (fakta dari sumber resmi)
Output  :  data/hasil.json          (dibaca oleh index.html)

Metode
------
1. Interpolasi linear  : mengisi tahun yang kosong DI ANTARA dua data resmi.
       y(t) = y0 + (y1 - y0) * (t - t0) / (t1 - t0)
2. Proyeksi (ekstrapolasi) laju tetap : melanjutkan tren SETELAH data resmi terakhir.
       y(t) = y_akhir * (1 + r) ** (t - t_akhir),   r = (y_akhir / y_awal) ** (1 / n) - 1
   Laju persentase dipakai (bukan garis lurus) agar angka persen tidak jatuh di bawah nol.
3. Status   : angka Bekasi dibandingkan dengan Jawa Barat dan Nasional.
4. Gap      : selisih proyeksi "tanpa kebijakan" dengan target kebijakan.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

AWAL_JABATAN, AKHIR_JABATAN = 2029, 2034


def baca_csv():
    rows = list(csv.DictReader(open(DATA / "sumber_resmi.csv", encoding="utf-8")))
    for r in rows:
        r["tahun"] = int(r["tahun"])
        r["nilai"] = float(r["nilai"])
    return rows


def ambil(rows, indikator, wilayah):
    return sorted((r for r in rows if r["indikator"] == indikator and r["wilayah"] == wilayah),
                  key=lambda r: r["tahun"])


def nilai(rows, indikator, wilayah, tahun=None):
    seri = ambil(rows, indikator, wilayah)
    r = seri[-1] if tahun is None else next(x for x in seri if x["tahun"] == tahun)
    return r


def interpolasi_linear(t0, y0, t1, y1, t):
    return y0 + (y1 - y0) * (t - t0) / (t1 - t0)


def laju(y_awal, y_akhir, n_tahun):
    return (y_akhir / y_awal) ** (1 / n_tahun) - 1


def proyeksi(y_akhir, t_akhir, r, sampai):
    return {t: y_akhir * (1 + r) ** (t - t_akhir) for t in range(t_akhir + 1, sampai + 1)}


def status_lebih_kecil_lebih_baik(x, pembanding):
    """Kritis jika lebih buruk dari semua pembanding, Aman jika lebih baik dari semua, selain itu Waspada."""
    if all(x > p for p in pembanding):
        return "kritis"
    if all(x < p for p in pembanding):
        return "aman"
    return "waspada"


def r2(x):
    return round(x, 2)


def idn(x, d=2):
    """Format angka gaya Indonesia: koma desimal."""
    return f"{x:.{d}f}".replace(".", ",")


def main():
    rows = baca_csv()
    hasil = {"metode": __doc__.strip()}

    # ---------- 1. Interpolasi: kontribusi UMKM terhadap PDRB ----------
    a, b = ambil(rows, "kontribusi_umkm_pdrb", "Kabupaten Bekasi")
    kemiringan = (b["nilai"] - a["nilai"]) / (b["tahun"] - a["tahun"])
    seri = []
    for t in range(a["tahun"], AKHIR_JABATAN + 1):
        if t in (a["tahun"], b["tahun"]):
            seri.append({"tahun": t, "nilai": a["nilai"] if t == a["tahun"] else b["nilai"], "jenis": "resmi"})
        elif t < b["tahun"]:
            seri.append({"tahun": t, "nilai": r2(interpolasi_linear(a["tahun"], a["nilai"], b["tahun"], b["nilai"], t)),
                         "jenis": "interpolasi"})
        else:
            seri.append({"tahun": t, "nilai": r2(b["nilai"] + kemiringan * (t - b["tahun"])), "jenis": "proyeksi"})
    hasil["umkm_pdrb"] = {"seri": seri, "kemiringan": round(kemiringan, 3),
                          "titik": [a["tahun"], a["nilai"], b["tahun"], b["nilai"]],
                          "nasional": nilai(rows, "kontribusi_umkm_pdb", "Indonesia")["nilai"]}

    # ---------- 2. Proyeksi pengangguran (TPT) ----------
    def seri_proyeksi(indikator, wilayah, t_awal_laju):
        s = ambil(rows, indikator, wilayah)
        awal = next(x for x in s if x["tahun"] == t_awal_laju)
        akhir = s[-1]
        r = laju(awal["nilai"], akhir["nilai"], akhir["tahun"] - awal["tahun"])
        proj = proyeksi(akhir["nilai"], akhir["tahun"], r, AKHIR_JABATAN)
        return s, r, proj

    bks, r_bks, p_bks = seri_proyeksi("tpt", "Kabupaten Bekasi", 2023)
    nas, r_nas, p_nas = seri_proyeksi("tpt", "Indonesia", 2023)
    y_awal_jabatan = p_bks[AWAL_JABATAN]
    target = {t: y_awal_jabatan * (1 + r_nas) ** (t - AWAL_JABATAN) for t in range(AWAL_JABATAN, AKHIR_JABATAN + 1)}

    ak_2024 = nilai(rows, "angkatan_kerja", "Kabupaten Bekasi")["nilai"]
    tambah_ak = 27000  # kenaikan angkatan kerja Agt 2023 -> Agt 2024 (RLPPD 2024)
    ak_2034 = ak_2024 + tambah_ak * (AKHIR_JABATAN - 2024)
    penganggur_tanpa = ak_2034 * p_bks[AKHIR_JABATAN] / 100
    penganggur_target = ak_2034 * target[AKHIR_JABATAN] / 100

    hasil["tpt"] = {
        "tahun": list(range(2020, AKHIR_JABATAN + 1)),
        "bekasi_resmi": {x["tahun"]: x["nilai"] for x in bks},
        "bekasi_tanpa_kebijakan": {t: r2(v) for t, v in p_bks.items()},
        "bekasi_target": {t: r2(v) for t, v in target.items()},
        "nasional_resmi": {x["tahun"]: x["nilai"] for x in nas},
        "nasional_proyeksi": {t: r2(v) for t, v in p_nas.items()},
        "laju_bekasi": round(r_bks * 100, 2),
        "laju_nasional": round(r_nas * 100, 2),
        "rasio_2025": r2(bks[-1]["nilai"] / nas[-1]["nilai"]),
        "rasio_2034_tanpa": r2(p_bks[AKHIR_JABATAN] / p_nas[AKHIR_JABATAN]),
        "angkatan_kerja_2034": ak_2034,
        "penganggur_2034_tanpa": round(penganggur_tanpa, -2),
        "penganggur_2034_target": round(penganggur_target, -2),
        "gap_orang": round(penganggur_tanpa - penganggur_target, -2),
        "penganggur_2025": nilai(rows, "penganggur", "Kabupaten Bekasi")["nilai"],
    }

    # ---------- 3. Proyeksi kemiskinan ----------
    mb, r_mb, p_mb = seri_proyeksi("miskin", "Kabupaten Bekasi", 2023)
    hasil["miskin"] = {"bekasi_resmi": {x["tahun"]: x["nilai"] for x in mb},
                       "bekasi_proyeksi": {t: r2(v) for t, v in p_mb.items()},
                       "laju": round(r_mb * 100, 2)}

    # ---------- 4. Estimasi cakupan data UMKM (metode proporsi penduduk) ----------
    umkm_nas = nilai(rows, "umkm_total", "Indonesia")["nilai"]
    pop_bks = nilai(rows, "penduduk", "Kabupaten Bekasi")["nilai"]
    pop_nas = nilai(rows, "penduduk", "Indonesia")["nilai"]
    est_umkm = umkm_nas * pop_bks / pop_nas
    tercatat = nilai(rows, "umkm_tercatat", "Kabupaten Bekasi")["nilai"]
    hasil["umkm_cakupan"] = {"estimasi": round(est_umkm, -3), "tercatat": tercatat,
                             "persen_tercatat": r2(tercatat / est_umkm * 100),
                             "proporsi_penduduk": round(pop_bks / pop_nas * 100, 2),
                             "target_2034": 100000,
                             "persen_target_2034": r2(100000 / est_umkm * 100)}

    # ---------- 5. Fakta + status ----------
    def f(ind, wil, tahun=None):
        return nilai(rows, ind, wil, tahun)

    tpt_b, tpt_j, tpt_n = f("tpt", "Kabupaten Bekasi"), f("tpt", "Jawa Barat"), f("tpt", "Indonesia")
    mis_b, mis_j, mis_n = f("miskin", "Kabupaten Bekasi"), f("miskin", "Jawa Barat"), f("miskin", "Indonesia")
    gini_b, gini_n = f("gini", "Kabupaten Bekasi"), f("gini", "Indonesia")
    pe_b, pe_n = f("pertumbuhan_ekonomi", "Kabupaten Bekasi"), f("pertumbuhan_ekonomi", "Indonesia")
    ind23, ind24 = f("pertumbuhan_industri", "Kabupaten Bekasi", 2023), f("pertumbuhan_industri", "Kabupaten Bekasi", 2024)
    kap_b, kap_n = f("pdrb_per_kapita", "Kabupaten Bekasi"), f("pdrb_per_kapita", "Indonesia")
    umkm_b, umkm_n = f("kontribusi_umkm_pdrb", "Kabupaten Bekasi"), f("kontribusi_umkm_pdb", "Indonesia")
    cak = hasil["umkm_cakupan"]

    def src(r):
        return {"nama": r["sumber"], "url": r["url"]}

    fakta = [
        {"id": "tpt", "judul": "Pengangguran terbuka", "nilai": f"{idn(tpt_b['nilai'])}%", "tahun": tpt_b["tahun"],
         "sumber": src(tpt_b),
         "pembanding": [f"Jawa Barat {idn(tpt_j['nilai'])}%", f"Nasional {idn(tpt_n['nilai'])}%"],
         "status": status_lebih_kecil_lebih_baik(tpt_b["nilai"], [tpt_j["nilai"], tpt_n["nilai"]]),
         "kesimpulan": f"Tertinggi di Jawa Barat dan {idn(hasil['tpt']['rasio_2025'], 1)}× angka nasional. Sejak 2023 Bekasi hanya turun "
                       f"{idn(abs(hasil['tpt']['laju_bekasi']), 1)}% per tahun, nasional {idn(abs(hasil['tpt']['laju_nasional']), 1)}% per tahun.",
         "program": ["Program 1", "Program 2"]},
        {"id": "umkm_pdrb", "judul": "Kontribusi UMKM terhadap ekonomi", "nilai": f"{idn(umkm_b['nilai'])}%", "tahun": umkm_b["tahun"],
         "sumber": src(umkm_b), "pembanding": [f"Nasional {int(umkm_n['nilai'])}% dari PDB"],
         "status": "kritis",
         "kesimpulan": "Ekonomi Bekasi dikuasai industri besar; porsi UMKM kurang dari seperempat porsi UMKM nasional.",
         "program": ["Program 2"]},
        {"id": "umkm_data", "judul": "UMKM yang tercatat", "nilai": f"{int(cak['tercatat']):,}".replace(",", "."),
         "tahun": 2023, "sumber": src(f("umkm_tercatat", "Kabupaten Bekasi")),
         "pembanding": [f"Estimasi potensi ±{int(cak['estimasi']):,} usaha".replace(",", ".")],
         "status": "kritis",
         "kesimpulan": f"Hanya sekitar {idn(cak['persen_tercatat'], 1)}% dari potensi UMKM yang tercatat. "
                       "Pemerintah tidak bisa membina usaha yang tidak terdata.",
         "program": ["Program 1"]},
        {"id": "industri", "judul": "Pertumbuhan sektor industri", "nilai": f"{idn(ind24['nilai'])}%", "tahun": ind24["tahun"],
         "sumber": src(ind24), "pembanding": [f"Tahun sebelumnya {idn(ind23['nilai'])}%"],
         "status": "waspada",
         "kesimpulan": "Melambat karena penutupan pabrik besar; pekerja formal turun 38 ribu orang. Warga butuh sumber penghasilan selain pabrik.",
         "program": ["Program 2"]},
        {"id": "gini", "judul": "Ketimpangan (rasio Gini)", "nilai": str(gini_b["nilai"]).replace(".", ","), "tahun": gini_b["tahun"],
         "sumber": src(gini_b), "pembanding": [f"Nasional {str(gini_n['nilai']).replace('.', ',')}"],
         "status": "waspada",
         "kesimpulan": "Sedikit lebih baik dari nasional, tetapi masih kategori ketimpangan sedang (0,3–0,5) menurut BPS.",
         "program": ["Program 1"]},
        {"id": "kapita", "judul": "PDRB per kapita", "nilai": f"Rp{str(kap_b['nilai']).replace('.', ',')} jt", "tahun": kap_b["tahun"],
         "sumber": src(kap_b), "pembanding": [f"Nasional Rp{str(kap_n['nilai']).replace('.', ',')} jt"],
         "status": "aman",
         "kesimpulan": "Tinggi karena output pabrik, bukan pendapatan warga. RLPPD 2024 sendiri mencatat banyak warga berdaya beli rendah.",
         "program": []},
        {"id": "pe", "judul": "Pertumbuhan ekonomi", "nilai": f"{idn(pe_b['nilai'])}%", "tahun": pe_b["tahun"],
         "sumber": src(pe_b), "pembanding": [f"Nasional {idn(pe_n['nilai'])}%"],
         "status": "aman", "kesimpulan": "Sedikit di atas nasional. Masalahnya bukan pertumbuhan, tetapi siapa yang menikmatinya.",
         "program": []},
        {"id": "miskin", "judul": "Penduduk miskin", "nilai": f"{idn(mis_b['nilai'])}%", "tahun": mis_b["tahun"],
         "sumber": src(mis_b), "pembanding": [f"Jawa Barat {idn(mis_j['nilai'])}%", f"Nasional {idn(mis_n['nilai'])}%"],
         "status": status_lebih_kecil_lebih_baik(mis_b["nilai"], [mis_j["nilai"], mis_n["nilai"]]),
         "kesimpulan": "Jauh lebih baik dari Jawa Barat dan nasional. Masalah utama Bekasi adalah pengangguran, bukan kemiskinan.",
         "program": []},
    ]
    hasil["fakta"] = fakta

    # ---------- 6. Perbandingan Bekasi vs Jawa Barat vs Nasional (untuk grafik) ----------
    def bar(w, r):
        return {"wilayah": w, "nilai": r["nilai"], "tahun": r["tahun"]}

    hasil["perbandingan"] = [
        {"judul": "Pengangguran terbuka", "satuan": "%", "arah": "rendah",
         "data": [bar("Kab. Bekasi", tpt_b), bar("Jawa Barat", tpt_j), bar("Nasional", tpt_n)]},
        {"judul": "Penduduk miskin", "satuan": "%", "arah": "rendah",
         "data": [bar("Kab. Bekasi", mis_b), bar("Jawa Barat", mis_j), bar("Nasional", mis_n)]},
        {"judul": "Kontribusi UMKM terhadap ekonomi", "satuan": "%", "arah": "tinggi",
         "data": [bar("Kab. Bekasi", umkm_b), bar("Nasional", umkm_n)]},
        {"judul": "Pertumbuhan ekonomi", "satuan": "%", "arah": "tinggi",
         "data": [bar("Kab. Bekasi", pe_b), bar("Nasional", pe_n)]},
        {"judul": "Rasio Gini (ketimpangan)", "satuan": "", "arah": "rendah", "status": "waspada",
         "catatan": "Sedikit lebih baik dari nasional, tetapi masih ketimpangan sedang (0,3–0,5)",
         "data": [bar("Kab. Bekasi", gini_b), bar("Nasional", gini_n)]},
        {"judul": "PDRB per kapita", "satuan": " jt", "arah": "tinggi",
         "catatan": "Lebih tinggi dari nasional karena output pabrik, bukan pendapatan warga",
         "data": [bar("Kab. Bekasi", kap_b), bar("Nasional", kap_n)]},
    ]
    hasil["jabatan"] = [AWAL_JABATAN, AKHIR_JABATAN]

    (DATA / "hasil.json").write_text(json.dumps(hasil, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TPT 2029 tanpa kebijakan:", r2(y_awal_jabatan), "| 2034 tanpa:", r2(p_bks[AKHIR_JABATAN]),
          "| 2034 target:", r2(target[AKHIR_JABATAN]), "| gap orang:", hasil["tpt"]["gap_orang"])
    print("UMKM tercatat:", cak["persen_tercatat"], "% dari estimasi", cak["estimasi"])
    print("Interpolasi UMKM-PDRB:", [s for s in seri if s["jenis"] == "interpolasi"])


if __name__ == "__main__":
    main()
