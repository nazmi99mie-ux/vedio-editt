# Video Dakwah Sinematik — Madrasah Zawiyah An Nur

A 9:16, 1080×1920, 30 fps edit of the infak appeal recording
(`VID_20261106_100640_100.mp4`, 1:53), made into a documentary-style piece of about **2:13**, with an inserted, stabilised walkthrough of the infaqpay.my sign-up.

## Struktur cerita

| Masa | Bahagian | Isi |
|---|---|---|
| 0:00–0:03 | **HOOK** | *"Kita mungkin tak mampu jadi orang yang mengajar ilmu agama, kan?"* (ayat penutup penceramah, dijadikan soalan pembuka) |
| 0:03–0:05 | Tajuk | Logo Madrasah Zawiyah An Nur · *Tarbiyah · Ilmu · Amal* |
| 0:05–0:28 | Kisah | Pondok, anak muda dan warga emas belajar dan beribadah |
| 0:28–0:44 | Realiti | Yuran **RM150** sebulan, kos makan minum, elektrik, air, penyelenggaraan, allowance guru |
| 0:44–0:56 | Impak | **3 pelajar** menyambung pengajian di **Yaman**; kelas Fardu Ain, majlis ilmu, program dakwah |
| 0:56–1:34 | Seruan | Jadi **penginfak tetap bulanan**, ikhlas dan istiqamah, pahala yang berterusan |
| 1:34–1:42 | Cara | 3 langkah: tekan pautan → pilih sumbangan melalui InfakPay → daftar |
| 1:42–1:54 | **Demo** | Rakaman sebenar pendaftaran di infaqpay.my, skrin distabilkan dalam bingkai telefon, dengan cip langkah 1–2–3 yang sama |
| 1:54–2:08 | Penutup | *"…kita mampu jadi orang yang membantu ilmu itu untuk terus disampaikan, terus diajarkan."* |
| 2:08–2:13 | Kad akhir | Logo + seruan tindakan |

The speaker's voice is kept exactly as recorded. The only things cut are the throwaway lines
*"Semua dalam tu."* and *"Tak gitu."*. The hook reuses a line the speaker says later, word for word,
so the meaning is unchanged.

Subtitle spelling fixes, where the speech recogniser misheard dialect pronunciation:
`ayak→air`, `menyambut→menyambung`, `mengajak→mengajar`, `Fardun→Fardu`,
`kuraikan. Murniakan daripada→kurniakan kepada`, `infak pay→InfakPay`.

## Fail

- `edit_plan.py`: the edit decision list, the visual plan (which photo goes with which sentence), labels and kinetic keywords
- `track_screen.py`: tracks the four screen edges of the hand-held demo recording on every frame (output in `assets/demo_corners.npy`). The renderer uses it to rectify the screen into a perfectly still, upright rectangle.
- `assets/demo_infaqpay.mp4` + `transcript_demo.json`: the sign-up demo clip and its voice-over transcript
- `render.py`: the frame renderer (speaker zoom, Ken Burns on the photos, cards, word-by-word subtitles, light leaks, gold particles, colour grade, grain)
- `audio.py`: voice clean-up and loudness, a synthesized ambient score with automatic ducking, and synthesized SFX (impact, whoosh, riser, shimmer, tick)
- `assets/img/`: the madrasah's own photos. The account number on the electricity meter is blurred automatically.
- `transcript_raw.json`: the word-level transcription (Whisper large-v3)

## Bina semula

```bash
pip install -r requirements.txt
./build.sh /path/to/VID_20261106_100640_100.mp4 out
```

This produces `dakwah_zawiyah_an_nur_9x16.mp4` and `dakwah_zawiyah_an_nur_9x16_tanpa_muzik.mp4`
(voice and SFX only, with no music).
