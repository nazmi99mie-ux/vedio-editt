"""Track the four edges of a hand-held phone screen in a recording, so the
screen can be rectified into a perfectly still, upright rectangle.

usage: python3 track_screen.py CLIP.mp4 OUT_corners.npy [debug_dir]

Each edge is followed frame-to-frame: points are sampled along the previous
edge, the dark-bezel -> bright-screen transition is searched along the normal,
and a line is fitted robustly (fingers crossing the edge are rejected as
outliers). Corners are the intersections of adjacent edges; the trajectories
are lightly smoothed afterwards.
"""
import sys, os, subprocess
import numpy as np, cv2


def read_frames(path):
    info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=width,height", "-of", "csv=p=0", path], capture_output=True, text=True)
    w, h = map(int, info.stdout.strip().split(","))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(w * h)
        if len(b) < w * h:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w)


def initial_quad(g):
    """Largest bright region enclosed by the dark bezel -> 4 corners (TL, TR, BR, BL)."""
    dark = (cv2.GaussianBlur(g, (5, 5), 0) < 28).astype(np.uint8)
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, stats, cent = cv2.connectedComponentsWithStats(1 - dark, 4)
    H, W = g.shape
    best, ba = None, 0
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if x > 5 and y > 5 and x + w < W - 5 and y + h < H - 5 and a > ba:
            best, ba = i, a
    m = (lab == best).astype(np.uint8)
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hull = cv2.convexHull(max(cnts, key=cv2.contourArea))
    pts = hull[:, 0, :].astype(np.float32)
    s, d = pts.sum(1), pts[:, 0] - pts[:, 1]
    tl, br = pts[np.argmin(s)], pts[np.argmax(s)]
    tr, bl = pts[np.argmax(d)], pts[np.argmin(d)]
    return np.array([tl, tr, br, bl], np.float32)


def line_from_pts(a, b):
    p = np.array(a, np.float64)
    d = np.array(b, np.float64) - p
    return p, d / np.linalg.norm(d)


def intersect(l1, l2):
    (p1, d1), (p2, d2) = l1, l2
    A = np.array([d1, -d2]).T
    t = np.linalg.solve(A, p2 - p1)
    return p1 + t[0] * d1


def fit_line(pts):
    """Robust total-least-squares line fit with iterative outlier rejection."""
    pts = np.asarray(pts, np.float64)
    keep = np.ones(len(pts), bool)
    for _ in range(4):
        q = pts[keep]
        c = q.mean(0)
        u, s, vt = np.linalg.svd(q - c)
        d = vt[0]
        nrm = np.array([-d[1], d[0]])
        r = np.abs((pts - c) @ nrm)
        thr = max(1.5, 2.5 * np.median(r[keep]))
        nk = r < thr
        if nk.sum() < 8:
            break
        keep = nk
    q = pts[keep]
    c = q.mean(0)
    d = np.linalg.svd(q - c)[2][0]
    return (c, d), keep.sum()


def track_edge(gf, a, b, inward, R=34, n=48):
    """Search the bezel->screen transition near segment a-b."""
    H, W = gf.shape
    ts = np.linspace(0.12, 0.88, n)
    base = a[None] + ts[:, None] * (b - a)[None]
    offs = np.arange(-R, R + 1, dtype=np.float32)
    xs = base[:, 0:1] + offs[None] * inward[0]
    ys = base[:, 1:2] + offs[None] * inward[1]
    prof = cv2.remap(gf, xs.astype(np.float32), ys.astype(np.float32), cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_REPLICATE)
    good = []
    for i in range(n):
        p = prof[i]
        dp = np.convolve(p, [1, 1, 0, -1, -1], "same") * -1  # derivative along inward normal
        dp[:3] = dp[-3:] = 0
        j = int(np.argmax(dp))
        out_v = p[max(j - 6, 0)]
        in_v = p[min(j + 6, len(p) - 1)]
        if dp[j] > 40 and out_v < 32 and in_v > 34:
            good.append(base[i] + offs[j] * inward)
    return good


def main():
    clip, out = sys.argv[1], sys.argv[2]
    dbg = sys.argv[3] if len(sys.argv) > 3 else None
    quads = []
    q = None
    for fi, g in enumerate(read_frames(clip)):
        gf = cv2.GaussianBlur(g, (3, 3), 0).astype(np.float32)
        if q is None:
            q = initial_quad(g)
        centre = q.mean(0)
        lines = []
        for k in range(4):
            a, b = q[k], q[(k + 1) % 4]
            d = (b - a) / np.linalg.norm(b - a)
            nrm = np.array([-d[1], d[0]], np.float32)
            if np.dot(centre - (a + b) / 2, nrm) < 0:
                nrm = -nrm
            pts = track_edge(gf, a, b, nrm)
            if len(pts) >= 10:
                ln, used = fit_line(pts)
            else:
                ln = line_from_pts(a, b)
            lines.append(ln)
        nq = np.array([intersect(lines[(k - 1) % 4], lines[k]) for k in range(4)], np.float32)
        # guard against blow-ups
        if np.max(np.abs(nq - q)) < 60:
            q = nq
        quads.append(q.copy())
        if dbg and fi % 15 == 0:
            c = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
            cv2.polylines(c, [q.astype(np.int32)], True, (0, 255, 255), 3)
            cv2.imwrite(os.path.join(dbg, f"trk_{fi:04d}.jpg"), cv2.resize(c, (270, 480)))
    Q = np.array(quads)
    # light temporal smoothing (keeps registration, removes sub-pixel jitter)
    k = cv2.getGaussianKernel(7, 1.4)[:, 0]
    Qs = Q.copy()
    for c in range(8):
        v = Q.reshape(len(Q), 8)[:, c]
        vp = np.pad(v, 3, mode="edge")
        Qs.reshape(len(Q), 8)[:, c] = np.convolve(vp, k, "valid")
    np.save(out, Qs)
    side = np.linalg.norm(Qs[:, 1] - Qs[:, 0], axis=1).mean(), np.linalg.norm(Qs[:, 3] - Qs[:, 0], axis=1).mean()
    print("frames", len(Q), "mean screen size w,h", side)


if __name__ == "__main__":
    main()
