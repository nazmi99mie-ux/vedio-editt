"""QC: find frames where any on-screen text overlaps a detected face."""
import sys, cv2, numpy as np
sys.argv = sys.argv[:1] + sys.argv[1:]
import render as R, timeline as TL
src, step = sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 1 / 3
R.QC["on"] = True
ctx = R.Ctx(src)
ff = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
pf = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
t, bad = 0.0, []
while t < TL.TOTAL:
    R.compose(ctx, t, int(t * 30))
    g = cv2.cvtColor(cv2.resize(R.QC["base"], (540, 960)), cv2.COLOR_RGB2GRAY)
    faces = [tuple(int(v * 2) for v in f) for f in ff.detectMultiScale(g, 1.1, 6, minSize=(22, 22))]
    for fl in (False, True):
        gg = cv2.flip(g, 1) if fl else g
        for (x, y, w, h) in pf.detectMultiScale(gg, 1.1, 6, minSize=(22, 22)):
            if fl: x = 540 - x - w
            faces.append((x * 2, y * 2, w * 2, h * 2))
    for (fx, fy, fw, fh) in faces:
        for (x0, y0, x1, y1) in R.QC["boxes"]:
            ix = min(x1, fx + fw) - max(x0, fx); iy = min(y1, fy + fh) - max(y0, fy)
            if ix > 0 and iy > 0 and ix * iy > 0.15 * fw * fh:
                bad.append((round(t, 2), (fx, fy, fw, fh), (x0, y0, x1, y1)))
    t += step
for b in bad: print(*b)
print("overlaps:", len(bad))
