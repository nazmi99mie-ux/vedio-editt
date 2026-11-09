# Video Dakwah Sinematik: Rayuan Wakaf Pondok Zawiyah An-Nur

Renderer berasaskan Python yang menukar rakaman ceramah asal (720×1280, 3:20)
kepada video menegak sinematik **1080×1920, 30 FPS, ±2:47**.

## Isi kandungan

| Fail | Fungsi |
|---|---|
| `plan.py` | Pelan pengarah: hook, babak, mod komposisi, transisi, overlay, maklumat wakaf |
| `render.py` | Enjin render: latar procedural, parallax, kinetic typography, gred warna, reka bunyi |
| `data/words.json` | Transkrip perkataan demi perkataan berserta masa (Whisper large-v3, disemak) |
| `fonts/` | Montserrat dan Playfair Display (lesen SIL OFL) |

## Struktur video

| Masa | Babak | Visual |
|---|---|---|
| 0:00–0:05 | **Hook** | Petikan sebenar *"sedekah jariah kita yang berkekalan sampai kita di alam kubur nanti"*, kad penceramah dengan punch-in, langit senja, impact dan teks besar |
| 0:05–0:31 | Connection | Salam dan pembuka, judul *Pondok Warga Emas & Musolla*, lower-third lokasi |
| 0:31–1:33 | Deep message | Blueprint pembinaan, grid perspektif **1 EKAR**, kampung parallax, kiraan **30 PINTU**, siluet musolla dengan cip *Warga Emas / Pondok / Tahfiz*, jubin **RM50 sekaki** |
| 1:33–1:55 | Maklumat dan doa | Panel maklumat wakaf, sinar cahaya, *ALLAH* dengan penegasan lembut |
| 1:55–2:08 | **Emotional peak** | Close-up penceramah, gerakan push-in perlahan, vignette, muzik direndahkan |
| 2:08–2:47 | Final impact | Rayuan, cahaya bokeh (membaca al-Quran dan mengaji), penutup salam, kad akhir |

Setiap latar belakang sentiasa bergerak melalui beberapa lapisan: langit, cahaya
matahari dan sinar, awan dua lapisan, bukit jauh, lapisan tengah (rumah kampung,
pokok kelapa atau masjid) dan latar depan. Setiap lapisan bergerak pada kelajuan
parallax yang berbeza. Sesetengah babak menggunakan gerakan kamera menegak, dan
ada yang menggunakan gelongsor mendatar. Kesemuanya dilengkapi partikel debu,
grain dan vignette.

## Amanah kandungan

- Hanya suara asal penceramah yang digunakan. Jeda yang panjang dipendekkan,
  tetapi tiada perkataan dibuang atau disusun semula.
- Hook ialah petikan sebenar dari minit 2:36. Petikan itu didengar semula dalam
  konteks penuhnya pada babak emosi.
- Sari kata diambil terus daripada transkrip rakaman. Lafaz Arab pembuka dan penutup
  ditulis mengikut ejaan rumi yang lazim.
- Wajah dan suara penceramah tidak diubah. Hanya gred warna dan pembingkaian digunakan.
- Semua visual dijana secara procedural. Tiada klip pihak ketiga digunakan dan tiada
  gambaran perkara ghaib atau suci.
- Muzik latar ialah pad ambien lembut tanpa rentak, dan direndahkan setiap kali
  penceramah bercakap.

## Perlu disemak / diisi

1. **Nombor akaun.** Penceramah menyebut *"melalui skrin yang tertera, nombor akaun..."*.
   Maklumat ini tiada dalam rakaman. Isikan `INFO["account"]`, `account_name`, dan
   `contact` dalam `plan.py`, kemudian render semula.
2. **Nama kampung.** Transkrip mendengar "Padang Stang". Sila sahkan ejaannya
   dalam `data/words.json`.
3. Perkataan *"menginfak"* (sekitar 1:20) dan *"lima..."* (sebelum "30 pintu") ialah
   tafsiran transkripsi. Sila semak dengan audio.

## Cara render

```bash
pip install opencv-python-headless numpy pillow scipy
# letak rakaman asal di editor/source/src.mov
python3 render.py --stills          # satu gambar setiap babak  -> out/stills/
python3 render.py --preview 30      # pratonton 30 s separuh resolusi
python3 render.py                   # render penuh -> out/final.mp4
```
