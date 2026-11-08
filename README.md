# vedio-editt — Video Dakwah Sinematik

**Hasil:** `output/wakaf_masjid_zawiyah_annur_9x16.mp4` (1:45, 9:16, 1080x1920, 30fps, -14 LUFS)

Sumber: rakaman asal 75 saat, iaitu penceramah di tapak cadangan masjid Pondok Zawiyah An-Nur, Gerik.

## Struktur suntingan
| Masa | Bahagian | Isi |
|---|---|---|
| 0:00 | Hook | "Siapa membina masjid, pahala sangat besar dari sisi Allah SWT… selama itulah mengalir saham-saham kita di dalam kubur" |
| 0:09 | Tajuk | SAHAM — YANG TERUS MENGALIR |
| 0:12 | Konteks | Tanah lapang pondok, rancangan buka masjid untuk pelajar pondok & warga emas |
| 0:28 | Seruan | Siapa ada rezeki lebih, berwakaflah untuk masjid |
| 0:36 | Sebab | Pahala membina masjid; ibadah jemaah = saham dalam kubur |
| 0:52 | Hadis | Sedekah jariah (HR Muslim, no. 1631) |
| 1:01 | Jemputan | Datang ke pondok, infak di jalan Allah |
| 1:11 | Hubungi | Hubungi mudir madrasah, Facebook & TikTok, penutup salam |
| 1:28 | Penutup | Hadis membina masjid (HR Muslim, no. 533) + kad akhir DuitNow QR (AnNurResources) |

## Cara render semula
```
python3 tools/audio_synth.py WORK/sfx 110      # SFX + muzik latar (disintesis)
python3 tools/gen_broll.py WORK/ai              # visual AI (SDXL-Turbo, CPU)
python3 tools/clean_words.py tr.json WORK/words.json
python3 tools/render.py WORK out.mp4            # perlukan WORK/{aroll.mp4,voice.wav,broll/,fonts/,sfx/}
```
`tools/edl.py` mengandungi senarai suntingan (titik potong, b-roll, kad hadis, SFX).

Gambar sebenar pondok (tapak, bahan binaan, kelas warga emas & pelajar) digunakan sebagai b-roll utama; visual AI hanya untuk konsep (kubur, cahaya, sujud) dan dilabel "ILUSTRASI AI".
