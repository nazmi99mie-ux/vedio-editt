import sys, cv2, numpy as np, render as R
R.QC["on"] = True
ctx = R.Ctx(sys.argv[1]); out = sys.argv[2]
tiles = []
for s in sys.argv[3].split(","):
    t = float(s); img = R.compose(ctx, t, int(t * 30)).copy()
    for (x0, y0, x1, y1) in R.QC["boxes"]:
        cv2.rectangle(img, (int(x0), int(y0)), (int(x1), int(y1)), (0, 255, 255), 4)
    cv2.putText(img, s, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 0, 0), 6)
    tiles.append(cv2.resize(img, (270, 480)))
cv2.imwrite(out, cv2.cvtColor(np.hstack(tiles), cv2.COLOR_RGB2BGR))
