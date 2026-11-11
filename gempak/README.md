# Versi "gempak": muzik, zoom, slide

| Fail | Tajuk | Tempoh |
|---|---|---|
| `video1_gempak.mp4` | Kenapa Orang Islam Lawan Islam? (4 point) | 1:30 |
| `video2_agama_24_jam.mp4` | Siapa Kata Agama Tak Ada Kena Mengena Dengan Hidup? (5 point) | 1:30 |

Kesan: zoom out pada awal setiap klip, zoom perlahan (Ken Burns), zoom punch dan goncangan skrin pada perkataan kuat,
transisi slide/zoom/circle/flash, bar kemajuan, muzik sinematik skala Hijaz (dijana sendiri, bebas hak cipta)
yang diperlahankan automatik bila ustaz bercakap, dan SFX braam/riser/sub-drop/swoosh/hit.

Bina semula (video asal di `dl/v.mp4`):
```
python3 synth.py 100      # hasilkan sfx/music.wav (muzik tidak disimpan dalam repo kerana besar)
mkdir -p out && python3 fx.py spec2.py
```
