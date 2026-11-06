# vedio-editt

Suntingan dakwah sinematik: **Rayuan Pembinaan Pondok Warga Emas — Madrasah Zawiyah An Nur, Gerik**

## Hasil (`output/`)
| Fail | Keterangan |
|---|---|
| `rayuan_pondok_warga_emas_9x16.mp4` | Versi utama, 1080×1920, 30fps, 2:04, suara asal + muzik latar + SFX |
| `rayuan_pondok_warga_emas_9x16_tanpa_muzik.mp4` | Sama, tanpa muzik latar (suara + SFX sahaja) |
| `sarikata.srt` | Sari kata potongan akhir (ejaan dibetulkan) |
| `pratonton.jpg` | Lembaran pratonton setiap 6 saat |

## Struktur cerita
1. **Hook (0:00)** – "Mudah-mudahan sumbangan tuan-tuan sekalian menjadi kebajikan hingga ke akhirat" (perkataan demi perkataan, besar)
2. **Kad tajuk** – *Sebidang Tanah Wakaf untuk Pondok Warga Emas*
3. Salam → lokasi madrasah → tanah wakaf ±1 hektar → rancangan pondok warga emas → selepas Hari Raya
4. Rayuan sumbangan → tujuan: warga emas menuntut ilmu → kebajikan hingga ke akhirat
5. Sebarkan berita ini → penutup & salam → kad akhir

Mukadimah bahasa Arab dan sapaan panjang dipendekkan; frasa berulang dibuang; jeda senyap panjang dipadatkan. Kata-kata penceramah tidak diubah.

## Pipeline (`project/`)
```
python project/build_audio.py <audio48k.wav> <work>        # potong suara, muzik, SFX, mix
python project/render.py <work> <graded_frames_dir> x 4    # render 1080x1920
python project/make_srt.py <work> sarikata.srt
```
Muzik latar dan kesan bunyi disintesis sendiri (tiada isu hak cipta).

## Versi 2 — High Impact Motion Graphics (`output/v2_*`)
Suara, potongan dan jalan cerita sama seperti versi 1, ditambah:
- Teks 3D timbul (extrude + kilauan) dengan animasi hentak, terbang masuk, membesar dan jatuh-melantun
- Sari kata 3D perkataan demi perkataan, berwarna ikut kategori (emas = ibadah/akhirat, hijau = tanah/projek, jingga = warga emas, biru = seruan)
- Kaligrafi Arab 3D (Assalamualaikum, Bismillah, Alhamdulillah)
- Ikon 3D (Microsoft Fluent Emoji, lesen MIT) mengikut cerita: pin lokasi, rumah, warga emas, buku, bulan Hari Raya, megafon, jam pasir, dll.
- Partikel, percikan, sinar cahaya, kilat, gegaran kamera, transisi whip / zoom / flash
- 80 beat animasi, ~200 kesan bunyi (tiada bunyi tik setiap perkataan): loceng, pop, whoosh, swoosh, riser, sparkle, chime, bass drop, cinematic hit

Pipeline: `build_audio2.py` → `render2.py` (beat ditakrif dalam `beats.py`).
