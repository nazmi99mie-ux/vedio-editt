# Video 3: gaya sinematik (berbeza daripada video 1 & 2)

`video3_jangan_tangguh.mp4`: "Tak solat terus kafir? Jangan tangguh orang masuk Islam" (1:29)

| Point | Isi | Masa asal |
|---|---|---|
| 1 | Tak solat tetap Islam (fasik); kata solat tak wajib baru kafir | 30:01, 30:23–30:47 |
| 2 | Kisah orang India masuk masjid, nak masuk Islam: jangan tangguh | 32:09, 32:44, 33:23–33:41 |
| 3 | "Nanti dulu, mandi dulu", dia mati dalam kafir | 34:15–34:29 |

Gaya: skrin penuh dengan penjejakan ustaz automatik (`track.py`), gred warna sinematik + vignet + butiran filem,
sari kata perkataan demi perkataan (Bebas Neue, karaoke kuning), kad hitam bertaip (Cinzel + Oswald emas),
glitch RGB, hitam-putih + zoom punch pada ayat kuat, muzik piano + strings + degupan jantung (`synth3.py`).

Bina semula: `python3 synth3.py 95 && mkdir -p out w3 && python3 fx3.py spec3.py` (video asal di `dl/v.mp4`, perlu opencv-python-headless).
