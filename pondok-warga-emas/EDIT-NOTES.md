# Rayuan Pondok Warga Emas — Nota Suntingan

**Sumber:** video rayuan 2:43 (464×848, satu syot kamera statik).
**Hasil:** `renders/pondok-warga-emas.mp4` — 1080×1920, 30 fps, ~86 s.

## Struktur cerita (selepas potong)

| Masa | Babak | Visual |
|---|---|---|
| 0:00 | **HOOK** — "Di belakang saya ni… tanah yang diwakafkan… lebih kurang satu ekar" | Tajuk "Tanah Wakaf untuk Warga Emas" pada frame 0 → drone tanah, garis sempadan lot dilukis, "1 Ekar" + impak bass |
| 0:08 | Salam | Kembali ke penceramah (light leak + whoosh) |
| 0:12 | Lokasi | Drone kawasan pondok + kad lokasi "Madrasah Zawiyah An-Nur · Gerik, Perak" |
| 0:17 | Syukur atas wakaf | Penceramah, punch-in berselang |
| 0:25 | **REVEAL** — "membina pondok untuk warga emas, single dan berkelamin" | Tanah kosong → kilatan cahaya emas → pelan konsep kompleks + cip "Bujang / Berkelamin" |
| 0:30 | "Projek berjalan selepas Hari Raya" | Kad bulan sabit "Projek Bermula · Selepas Hari Raya" |
| 0:34 | Rayuan sumbangan | Punch-in pada perkataan "sumbangan", B-roll asrama & pondok |
| 0:43 | Menuntut ilmu | Jemaah warga emas → majlis ilmu → ustaz |
| 0:53 | "Kebajikan hingga ke akhirat" | Wajah jemaah tersenyum + petikan emas |
| 0:57 | "Tolong sebarkan" | Cip "Sebarkan" |
| 1:00 | Harapan | Pelan konsep (dekat), dua tuan guru |
| 1:10 | Penutup | Penceramah |
| 1:19 | Salam penutup | Kad akhir "Jom Bersama Bina Pondok Warga Emas" |

## Apa yang dibuang
- Bismillah / hamdalah / selawat pembukaan & "Yang saya hormati…" (0:07–0:33 asal) — hook diletak dahulu, salam dikekalkan.
- "yang bersempadan dengan madrasah ini" (sudah jelas dari hook).
- Ayat tidak jelas "Ini … nanti" (1:21 asal).
- Ulangan "lelaki dan perempuan yang single dan juga kelamin" (sudah disebut).
- Mula palsu "dengan penempatan kompleks ini" dan "mendirikan madrasah" (salah sebut, dibetulkan sendiri oleh penceramah).
- "Wallahu a'lam, wabillahi taufiq".
- Semua jeda janggal >0.4 s dipotong ketat; setiap sambungan disahkan dengan transkripsi semula.

## Teknik
- Punch-in berselang (1.00× / 1.12–1.22×) pada setiap potongan untuk sembunyikan jump cut + slow push sinematik.
- Gred warna "Natural Portrait" (skin-soft, highlights diturunkan untuk langit mendung, sedikit hangat, vignette halus) pada penceramah dan semua foto.
- Light leak emas pada 5 peralihan bermotif sahaja — tidak berlebihan.
- Audio suara: high-pass, denoise, compressor, loudness -15 LUFS.
- SFX: whoosh pada potongan B-roll, impak bass pada "1 Ekar" & reveal, pop pada cip, sparkle pada momen emosi.
- Tiada muzik latar (lazim untuk kandungan rayuan madrasah). Boleh ditambah jika mahu (nasyid vokal/ambien).
- Kapsyen BM karaoke (perkataan aktif putih, kata kunci emas), ejaan dibetulkan daripada Whisper.

## Perlu semak / boleh ubah
- **Pelan konsep & poster masjid**: pelan konsep dilabel "GAMBARAN KONSEP". Poster Masjid Muhammad tidak digunakan (projek berlainan).
- **Kad akhir**: teks maklumat sumbangan ialah pembolehubah `maklumat_sumbangan` — masukkan no. akaun / QR / nombor telefon sebenar di panel Variables (Studio) atau dalam `index.html`.
- Nama/jawatan penceramah tidak diketahui — tiada lower-third nama. Beritahu jika mahu ditambah.

## Bina semula
```bash
python3 build/build.py      # jana semula index.html + compositions/ dari build/edl.json
npx hyperframes check
npx hyperframes render -o renders/pondok-warga-emas.mp4 --quality delivery
```
`build/edl.json` = senarai potongan (masa asal → masa suntingan). `assets/talk.mp4` = video asal yang dibesarkan ke 1080×1920 dengan audio dibersihkan.
