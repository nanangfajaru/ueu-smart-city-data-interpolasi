const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const id = (x) => document.getElementById(x);
const fmt = (n, d = 2) => Number(n).toLocaleString("id-ID", { minimumFractionDigits: d, maximumFractionDigits: d });
const ribu = (n) => Number(n).toLocaleString("id-ID", { maximumFractionDigits: 0 });
const ICON = { kritis: "!", waspada: "~", aman: "✓" };
const LABEL = { kritis: "Kritis", waspada: "Waspada", aman: "Aman" };
const badge = (s) => `<span class="badge ${s}"><i aria-hidden="true">${ICON[s]}</i>${LABEL[s]}</span>`;

function parseCSV(text) {
  const [head, ...lines] = text.trim().split("\n");
  const keys = head.split(",");
  return lines.map((l) => {
    const p = l.split(",");
    const url = p.pop();
    const o = {};
    keys.slice(0, -1).forEach((k, i) => (o[k] = i === keys.length - 2 ? p.slice(i).join(",") : p[i]));
    o.url = url;
    return o;
  });
}

function table(head, rows) {
  return `<table><thead><tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows
    .map((r) => (r.group ? `<tr class="group"><td colspan="${head.length}">${r.group}</td></tr>` : `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`))
    .join("")}</tbody></table>`;
}

function baseOptions(yTitle) {
  const ink2 = css("--ink-2"), line = css("--line"), muted = css("--muted");
  return {
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: css("--surface"), titleColor: css("--ink"), bodyColor: ink2,
        borderColor: line, borderWidth: 1, padding: 10, usePointStyle: true,
        filter: (i) => i.raw !== null && i.raw !== undefined,
        callbacks: { label: (c) => ` ${c.dataset.label}: ${fmt(c.raw)}%` },
      },
    },
    scales: {
      x: { grid: { display: false }, ticks: { color: muted }, border: { color: css("--line") } },
      y: { title: { display: true, text: yTitle, color: muted }, grid: { color: line }, ticks: { color: muted }, border: { display: false } },
    },
  };
}

async function main() {
  const [h, csv] = await Promise.all([
    fetch("data/hasil.json").then((r) => r.json()),
    fetch("data/sumber_resmi.csv").then((r) => r.text()),
  ]);

  // ---------- 1-2. Fakta & status ----------
  const count = { kritis: 0, waspada: 0, aman: 0 };
  h.fakta.forEach((f) => count[f.status]++);
  id("tally").innerHTML = ["kritis", "waspada", "aman"].map((s) => `${badge(s)} <span class="muted small">${count[s]} indikator</span>`).join("&nbsp;&nbsp;");
  id("kartu").innerHTML = h.fakta.map((f) => `
    <article class="card ${f.status}">
      <div>${badge(f.status)}</div>
      <h3>${f.judul}</h3>
      <div class="val">${f.nilai}<small>${f.tahun}</small></div>
      <div class="cmp">vs ${f.pembanding.join(" · ")}</div>
      <p class="concl">${f.kesimpulan}</p>
      ${f.program.length ? `<div class="prg">${f.program.map((p) => `<span>→ ${p}</span>`).join("")}</div>` : ""}
      <div class="src">Sumber: <a href="${f.sumber.url}" target="_blank" rel="noopener">${f.sumber.nama}</a></div>
    </article>`).join("");

  const t = h.tpt;
  const c = h.umkm_cakupan;

  // ---------- 5. Target ----------
  const yr = [2030, 2031, 2032, 2033, 2034];
  const pct = (a, b) => { const v = (a / b) * 100; return v < 10 ? fmt(v, 1) + "%" : Math.round(v) + "%"; };
  const cell = (v, p) => `${v}<span class="p">${p}</span>`;
  const reg = [25000, 45000, 65000, 85000, 100000], leg = [8000, 20000, 35000, 50000, 65000];
  const qris = [0.3, 0.4, 0.5, 0.6, 0.7], kur = [1000, 2500, 4500, 7000, 10000];
  const mitra = [100, 300, 600, 900, 1200], b2b = [50, 150, 350, 600, 1000], b2c = [10, 30, 60, 100, 150];
  const desa = [5, 12, 22, 35, 50], kerja = [5000, 15000, 30000, 45000, 60000];
  const rp = (m) => (m >= 1000 ? "Rp1 T" : `Rp${m} M`);
  const rows = [
    { group: "Program 1 · Super UMKM" },
    ["UMKM terdaftar", "% dari potensi ±761 rb usaha", ...reg.map((x) => cell(ribu(x), pct(x, c.estimasi)))],
    ["Legalitas (NIB/izin)", "% dari UMKM terdaftar", ...leg.map((x, i) => cell(ribu(x), pct(x, reg[i])))],
    ["Pengguna QRIS", "% dari UMKM terdaftar", ...qris.map((q, i) => cell(ribu(reg[i] * q), Math.round(q * 100) + "%"))],
    ["Penerima KUR", "% dari UMKM terdaftar", ...kur.map((x, i) => cell(ribu(x), pct(x, reg[i])))],
    { group: "Program 2 · Pasar UMKM" },
    ["Perusahaan mitra B2B", "% dari ±2.553 perusahaan kawasan", ...mitra.map((x) => cell(ribu(x), pct(x, 2553)))],
    ["Pendapatan B2B / tahun", "% dari target 2034", ...b2b.map((x) => cell(rp(x), pct(x, 1000)))],
    ["Pendapatan B2C / tahun", "% dari target 2034", ...b2c.map((x) => cell(rp(x), pct(x, 150)))],
    ["Desa UMKM Digital", "% dari 187 desa/kelurahan", ...desa.map((x) => cell(x, pct(x, 187)))],
    { group: "Dampak" },
    ["Lapangan kerja baru", `% dari ${ribu(t.penganggur_2025)} penganggur (2025)`, ...kerja.map((x) => cell(ribu(x), pct(x, t.penganggur_2025)))],
    ["Pengangguran terbuka", "tanpa kebijakan →", ...yr.map((y) => cell(fmt(t.bekasi_target[y]) + "%", fmt(t.bekasi_tanpa_kebijakan[y]) + "%"))],
  ];
  id("tabTarget").innerHTML = table(["Indikator", "Dasar persentase", ...yr], rows);

  // ---------- Sumber ----------
  const seen = new Map();
  parseCSV(csv).forEach((r) => {
    const k = r.sumber + "|" + r.url;
    if (!seen.has(k)) seen.set(k, { nama: r.sumber, url: r.url, ind: new Set() });
    seen.get(k).ind.add(r.indikator.replaceAll("_", " "));
  });
  const host = (u) => new URL(u).hostname.replace(/^www\./, "");
  id("sources").innerHTML = [...seen.values()].map((s) => `<li><a href="${s.url}" target="_blank" rel="noopener">${s.nama}</a> <span class="muted small">— ${host(s.url)} · ${[...s.ind].join(", ")}</span></li>`).join("");
}

main().catch((e) => { console.error(e); document.body.insertAdjacentHTML("afterbegin", `<p style="padding:16px;color:#d03b3b">Gagal memuat data: ${e.message}</p>`); });
