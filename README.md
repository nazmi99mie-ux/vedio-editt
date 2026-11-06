# vedio-editt — Madrasah Zawiyah An Nur cinematic documentary

Turns the original madrasah talk video (narration) plus the madrasah photos
into a vertical 9:16 cinematic documentary edit at **2160×3840 (4K UHD
vertical), 24 fps**.

## What the edit does

| Element | How |
|---|---|
| Intro / outro | Logo card with a slow push-in and fades to and from black |
| Narration | Original audio kept intact, with a fade at the end |
| Speaker footage | Light denoising, upscaling to 4K, a very slow push-in, and the same grade as the b-roll |
| B-roll (16 photos) | Smooth sub-pixel camera moves: push-ins, left-to-right tracking, elevated zoom-outs, gentle rotation |
| Transitions | 0.5 s soft dissolves |
| Light | Warm golden-hour glow drifting slowly from the top, with faint light rays (screen blend) |
| Grade | Warm highlights, gentle contrast, lifted blacks, vignette, sharpening and fine film grain |

Nothing is generated or invented. Every face, building and object comes from
the original footage and photos; the script only adds camera motion, light and
colour. Two utility-meter photos were left out on purpose.

## Shot order (times in the narration)

0–11.5 s campus road → hostel block · 20 s lecture under the canopy ·
31 s classroom → talaqqi · 48 s students seated → student with the Quran ·
64 s night prayer → maulid night → elders at the banner · 84 s audience →
women in doa → gathering · 101 s podium → food serving → elder walking → logo.
Between these shots the speaker is on screen.

Edit `SHOTS` in `scripts/make_documentary.py` to change timing or motion.

## Render

```bash
pip install opencv-python-headless numpy
# original video: VID_20261106_100640_100.mp4 (Google Drive)
python3 scripts/make_documentary.py original.mp4 out_4k.mp4            # full 4K
python3 scripts/make_documentary.py original.mp4 preview.mp4 --preview # 540x960 quick check
```

Requires `ffmpeg` and `ffprobe` on PATH.

## Limits

The sources are 720–1080 px wide phone images and video, so 4K output is an
upscale with denoising and sharpening, not new detail. The "drone" and
parallax feel comes from 2D camera moves on still photos. The script does not
generate real 3D parallax or new viewpoints.
