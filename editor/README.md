# Video Dakwah Sinematik: Rayuan Wakaf Pondok Zawiyah An-Nur

Renderer berasaskan Python yang menukar rakaman ceramah asal (720×1280, 3:20)
kepada video menegak sinematik **1080×1920, 30 FPS, 1:49**.

## Isi kandungan

| Fail | Fungsi |
|---|---|
| `plan.py` | Pelan pengarah: hook, julat rakaman yang digunakan, babak, transisi, overlay, no. akaun dan QR |
| `render.py` | Enjin render: latar procedural, parallax, gambar Ken Burns, kinetic typography, muzik dan bunyi |
| `data/words.json` | Transkrip perkataan demi perkataan berserta masa (Whisper large-v3, disemak) |
| `assets/` | Gambar majlis (ketibaan, banner pelancaran, tanam pokok) dan QR DuitNow |
| `fonts/` | Montserrat dan Playfair Display (lesen SIL OFL) |

## Struktur video (v2)

| Masa | Babak | Visual |
|---|---|---|
| 0:00–0:05 | **Hook** | *"sedekah jariah kita yang berkekalan sampai kita di alam kubur nanti"* |
| 0:05–0:24 | Lokasi dan majlis | Gambar ketibaan dengan lower-third lokasi, banner *Majlis Pelancaran*, gambar tanam pokok dengan **1 EKAR** |
| 0:24–0:54 | Isi | Kiraan **30 PINTU**, siluet musolla (Warga Emas, Pondok, Tahfiz), **WAKAF RM50 sekaki** |
| 0:54–1:06 | Cara menyumbang | **QR DuitNow + No. Akaun 558079530303 (An Nur Resources)** (dipapar besar dan tidak bergerak supaya mudah diimbas) |
| 1:06–1:18 | Emotional peak | Close-up penceramah |
| 1:18–1:42 | Rayuan | Penceramah, banner majlis, cahaya bokeh |
| 1:42–1:49 | Kad akhir | WAKAF SEKAKI RM50, QR dan no. akaun |

Mukadimah (salam dan selawat) tidak dimasukkan. Tiga ayat yang berulang juga
dibuang supaya video tidak melebihi 2 minit. Ayat-ayat yang digunakan tetap
dimainkan mengikut susunan asal.

- **Muzik:** piano dan strings yang sedih, digubah dan dijana sendiri (A minor, 68 bpm).
  Muzik direndahkan ketika penceramah bercakap dan dinaikkan pada kad akhir.
- **Kesan bunyi:** whoosh sahaja, iaitu pada transisi, tajuk penting dan
  perkataan yang di-highlight (penanda emas). Tiada bunyi "ting".
- **Wajah:** setiap gambar mempunyai `face_band`. Semua teks diletakkan di luar
  kawasan wajah.

## Amanah kandungan

- Hanya suara asal penceramah yang digunakan. Jeda yang panjang dipendekkan, dan
  ayat yang digunakan tidak disusun semula atau dipotong di tengah.
- Hook ialah petikan sebenar dari minit 2:36. Petikan itu didengar semula dalam
  konteks penuhnya pada babak emosi.
- Sari kata diambil terus daripada transkrip rakaman.
- Wajah dan suara penceramah tidak diubah. Hanya gred warna dan pembingkaian digunakan.
- Visual terdiri daripada gambar sebenar majlis dan grafik procedural. Tiada klip
  pihak ketiga digunakan dan tiada gambaran perkara ghaib atau suci.

## Perlu disemak / diisi

1. **Nama bank** tidak dipaparkan. Yang dipaparkan ialah no. akaun, nama akaun dan QR. Jika perlu,
   tambah nama bank pada `ACCOUNT_NO` dalam `plan.py`.
2. **Nama kampung.** Transkrip mendengar "Padang Stang". Sila sahkan ejaannya
   dalam `data/words.json`.
3. Perkataan *"lima..."* (sebelum "30 pintu") ialah tafsiran transkripsi. Sila
   semak dengan audio.

## Cara render

```bash
pip install opencv-python-headless numpy pillow scipy
# letak rakaman asal di editor/source/src.mov
python3 render.py --stills          # satu gambar setiap babak  -> out/stills/
python3 render.py --preview 30      # pratonton 30 s separuh resolusi
python3 render.py                   # render penuh -> out/final.mp4
```
