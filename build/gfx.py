"""Draws the info-card PNGs (icon + title + subtitle) used as motion graphics."""
import math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import plan

FD = f"{plan.S}/fd"
OUT = f"{plan.S}/gfx"
os.makedirs(OUT, exist_ok=True)
K = 2  # supersample
GOLD = (245, 196, 66)
EMER = (18, 140, 96)


def font(name, size):
    return ImageFont.truetype(f"{FD}/{name}", size * K)


def icon(kind, s=170):
    S = s * K
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = S / 100
    if kind == "cement":
        d.polygon([(22*u, 18*u), (78*u, 18*u), (84*u, 88*u), (16*u, 88*u)], fill=(214, 210, 200))
        d.rectangle([20*u, 14*u, 80*u, 22*u], fill=(190, 186, 176))
        d.rectangle([18*u, 40*u, 82*u, 64*u], fill=EMER)
        f = font("montserrat-latin-800-normal.woff", int(11 * s / 100))
        d.text((50*u, 52*u), "SIMEN", font=f, fill="white", anchor="mm")
        d.line([(30*u, 76*u), (70*u, 76*u)], fill=(170, 165, 155), width=int(2*u))
    elif kind == "brick":
        c1, c2 = (196, 92, 58), (160, 70, 44)
        for r in range(3):
            y = 30*u + r * 20*u
            off = 0 if r % 2 == 0 else -14*u
            for c in range(3):
                x = 10*u + off + c * 30*u
                if x + 28*u < 6*u or x > 94*u: continue
                d.rounded_rectangle([max(x, 8*u), y, min(x + 28*u, 92*u), y + 17*u], radius=2*u,
                                    fill=c1, outline=c2, width=int(1.5*u))
    elif kind == "rebar":
        for i in range(5):
            x0 = 14*u + i * 15*u
            d.line([(x0, 88*u), (x0 + 22*u, 12*u)], fill=(120, 128, 138), width=int(7*u))
            for j in range(9):
                tt = (j + 0.5) / 9
                cx, cy = x0 + 22*u*tt, 88*u - 76*u*tt
                d.line([(cx - 4*u, cy - 1*u), (cx + 4*u, cy + 1*u)], fill=(80, 86, 96), width=int(2*u))
        d.line([(10*u, 60*u), (90*u, 60*u)], fill=GOLD, width=int(3*u))
    elif kind == "heart":
        pts = []
        for i in range(200):
            a = i / 200 * 2 * math.pi
            x = 16 * math.sin(a) ** 3
            y = 13 * math.cos(a) - 5 * math.cos(2*a) - 2 * math.cos(3*a) - math.cos(4*a)
            pts.append((50*u + x * 2.6*u, 48*u - y * 2.6*u))
        d.polygon(pts, fill=(232, 72, 85))
        d.ellipse([30*u, 30*u, 42*u, 40*u], fill=(255, 150, 160))
    elif kind == "phone":
        d.rounded_rectangle([30*u, 10*u, 70*u, 90*u], radius=8*u, fill=(240, 240, 240))
        d.rounded_rectangle([34*u, 18*u, 66*u, 78*u], radius=3*u, fill=EMER)
        d.ellipse([46*u, 81*u, 54*u, 87*u], fill=(150, 150, 150))
        for r in (12, 20):
            d.arc([74*u - r*u, 22*u - r*u, 74*u + r*u, 22*u + r*u], 270, 360, fill=GOLD, width=int(4*u))
    elif kind == "key":   # little house with a door - "30 pintu"
        d.polygon([(50*u, 10*u), (92*u, 46*u), (8*u, 46*u)], fill=(205, 70, 50))
        d.rectangle([18*u, 44*u, 82*u, 90*u], fill=(225, 220, 205))
        d.rounded_rectangle([42*u, 58*u, 58*u, 90*u], radius=2*u, fill=EMER)
        d.ellipse([53*u, 73*u, 56*u, 76*u], fill=GOLD)
        d.rectangle([24*u, 54*u, 36*u, 66*u], fill=(120, 170, 200))
        d.rectangle([64*u, 54*u, 76*u, 66*u], fill=(120, 170, 200))
    elif kind == "share":
        pts = [(72*u, 22*u), (28*u, 50*u), (72*u, 78*u)]
        d.line([pts[0], pts[1], pts[2]], fill="white", width=int(6*u))
        for x, y in pts:
            d.ellipse([x - 13*u, y - 13*u, x + 13*u, y + 13*u], fill=GOLD)
    elif kind == "pray":  # crescent & star
        d.ellipse([12*u, 12*u, 84*u, 84*u], fill=GOLD)
        d.ellipse([28*u, 6*u, 96*u, 74*u], fill=(0, 0, 0, 0))
        pts = []
        for i in range(10):
            r = 15*u if i % 2 == 0 else 6*u
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((70*u + r * math.cos(a), 58*u + r * math.sin(a)))
        d.polygon(pts, fill="white")
    return im


def card(icon_kind, title, sub):
    w, h = 860, 236
    im = Image.new("RGBA", (w*K, h*K), (0, 0, 0, 0))
    # soft drop shadow
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([16*K, 22*K, (w-16)*K, (h-6)*K], radius=40*K, fill=(0, 0, 0, 150))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14*K)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([10*K, 10*K, (w-10)*K, (h-14)*K], radius=36*K, fill=(8, 28, 22, 215),
                        outline=(255, 255, 255, 60), width=2*K)
    d.rounded_rectangle([10*K, 10*K, 30*K, (h-14)*K], radius=10*K, fill=GOLD + (255,))
    # icon in a circle
    d.ellipse([46*K, 22*K, 236*K, 212*K], fill=(255, 255, 255, 28))
    ic = icon(icon_kind, 150)
    im.alpha_composite(ic, (int(66*K), int(42*K)))
    ft = font("montserrat-latin-800-normal.woff", 66 if len(title) < 14 else 54)
    fs = font("montserrat-latin-800-normal.woff", 32)
    d.text((262*K, 96*K), title, font=ft, fill="white", anchor="ls")
    d.text((264*K, 158*K), sub.upper(), font=fs, fill=GOLD, anchor="ls")
    return im.resize((w, h), Image.LANCZOS)


def particles():
    """A soft bokeh dot sprite used for floating dust in the doa/outro."""
    s = 64
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([16, 16, 48, 48], fill=(255, 236, 190, 255))
    return im.filter(ImageFilter.GaussianBlur(7))


if __name__ == "__main__":
    for c in plan.cues():
        if c["kind"] in ("card", "card2"):
            card(c["icon"], c["title"], c["sub"]).save(f"{OUT}/{c['icon']}.png")
    particles().save(f"{OUT}/dot.png")
    # contact preview
    files = sorted(f for f in os.listdir(OUT) if f.endswith(".png") and f != "dot.png" and f != "preview.png")
    pv = Image.new("RGBA", (880, 250 * len(files)), (60, 90, 70, 255))
    for i, f in enumerate(files):
        pv.alpha_composite(Image.open(f"{OUT}/{f}"), (10, i * 250))
    pv.convert("RGB").save(f"{OUT}/preview.png")
    print(files)
