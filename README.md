# Video Dakwah Sinematik — Masjid Warga Emas, Pondok Zawiyah An-Nur

A cinematic 9:16 (1080×1920, 30 fps) edit of a talk recorded at the site of the planned
masjid for warga emas at Pondok Zawiyah An-Nur, Kg. Kerunai, Gerik, Perak.
The whole edit is generated from code, so it can be changed and rendered again.

## Struktur

| Path | Isi |
|---|---|
| `scripts/timeline.py` | Senarai keputusan suntingan (EDL): syot, transisi, kata kunci, lower-third, kad teks, cahaya |
| `scripts/render.py` | Enjin render: wajah penceramah dijejak, B-roll berlapis (parallax), sari kata kinetik, gred warna, grain |
| `scripts/audio.py` | Reka bunyi: suara asal dibersihkan, impak/whoosh/riser, ambien, pad lembut + ducking |
| `scripts/face.py` | Penjejakan wajah (OpenCV) → `data/face.json` |
| `scripts/fixwords.py` | Pembetulan transkrip Whisper large-v3 → `data/words_final.json` |
| `assets/photos/` | Foto majlis pelancaran, pecah tanah, tapak, lori Kg. Kerunai |
| `data/transcript.txt` | Transkrip akhir yang dipaparkan sebagai sari kata |

## Struktur cerita (masa output)

| Masa | Babak | Isi |
|---|---|---|
| 0:00–0:04 | Hook | Petikan asal: "Siapa membina masjid, pahala sangat besar dari sisi Allah SWT" — punch-in, impak bass, perubahan cahaya |
| 0:04–0:05 | Tajuk | "MEMBINA MASJID — untuk warga emas & pelajar pondok" |
| 0:05–0:27 | Connection | Salam, tanah lapang, Kg. Kerunai (lori), banner pelancaran, warga emas |
| 0:27–0:43 | Deep message | Wakaf, split-screen tapak tiang, "masjid ni, subhanallah", pecah tanah (pan menegak) |
| 0:43–0:53 | Emotional peak | "Selama itulah mengalir saham-saham kita di dalam kubur": close-up, gred lebih sunyi, muzik diperlahankan |
| 0:53–1:20 | Final impact | Infaq, fi sabilillah, berkat dunia akhirat, Facebook/TikTok, salam penutup |
| 1:20–1:32 | Outro | Montaj foto + kad penutup: petikan "Sama-sama kita infaq harta kita pada jalan Allah" |

Ucapan dimainkan **tanpa diubah dan mengikut susunan asal**. Satu-satunya pengulangan ialah
petikan hook (diambil daripada saat 33.5–37.6 rakaman asal).

## Render semula

```bash
pip install faster-whisper "opencv-python-headless<5" scipy pillow numpy
python3 scripts/render.py SRC.mp4 out/ --workers 4        # video
python3 scripts/audio.py  SRC.mp4 out/                    # mix_music.wav & mix_nomusic.wav
ffmpeg -i out/video.mp4 -i out/mix_music.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest final.mp4
```

Pratonton bingkai: `python3 scripts/render.py SRC.mp4 stills/ --stills 1,10,40`.
