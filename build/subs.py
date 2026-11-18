"""Writes the .ass file: word-by-word captions with highlight boxes, hook titles,
counter, chips, Arabic accents and the outro card."""
from PIL import ImageFont
import plan

W, H = plan.W, plan.H
SIZE = 78
# libass scales by (winAscent+winDescent); PIL by em. Montserrat: 1562/1000.
PIL_FONT = ImageFont.truetype(f"{plan.S}/fd/montserrat-latin-800-normal.woff", round(SIZE * 1000 / 1562))
SPACE = 26
CAP_Y = 1470
KEY = {"allah", "dermawan", "budiman", "warga", "emas", "30", "pintu", "ibadah", "simen", "bata",
       "besi", "struktur", "sedikit", "banyak", "hargai", "menyumbang", "membantu", "share", "amin",
       "pembinaan", "pondok", "sumbangan", "jasa", "segera"}
GOLD, EMER, WHITE, DARK = "&H42C4F5&", "&H608C12&", "&HFFFFFF&", "&H1A1A1A&"

segs, TOTAL = plan.timeline()
ev = []


def ts(t):
    t = max(t, 0); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def add(t0, t1, text, style="Cap", layer=1):
    if t1 > t0: ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},{style},,0,0,0,,{text}")


def rrect(w, h, r):
    """ASS vector drawing of a rounded rect centered on (0,0)."""
    x0, y0, x1, y1 = 0, 0, w, h
    k = r * 0.55
    return (f"m {x0+r:.0f} {y0:.0f} l {x1-r:.0f} {y0:.0f} b {x1-r+k:.0f} {y0:.0f} {x1:.0f} {y0+r-k:.0f} {x1:.0f} {y0+r:.0f} "
            f"l {x1:.0f} {y1-r:.0f} b {x1:.0f} {y1-r+k:.0f} {x1-r+k:.0f} {y1:.0f} {x1-r:.0f} {y1:.0f} "
            f"l {x0+r:.0f} {y1:.0f} b {x0+r-k:.0f} {y1:.0f} {x0:.0f} {y1-r+k:.0f} {x0:.0f} {y1-r:.0f} "
            f"l {x0:.0f} {y0+r:.0f} b {x0:.0f} {y0+r-k:.0f} {x0+r-k:.0f} {y0:.0f} {x0+r:.0f} {y0:.0f}")


def wwidth(s):
    return PIL_FONT.getlength(s)


def is_key(word):
    return word.strip(".,!?").lower() in KEY


# ------------------------------------------------------------- word-by-word captions
words = plan.words()
chunks, cur = [], []
for w in words:
    disp = w["text"].strip(",.").upper()
    w["disp"] = disp
    glue = cur and cur[-1]["disp"] == "WARGA" and disp == "EMAS"
    if cur and not glue and (len(cur) >= 3 or sum(wwidth(x["disp"]) for x in cur) + wwidth(disp) + SPACE * len(cur) > 900
                or cur[-1]["seg"] != w["seg"] or w["s"] - cur[-1]["e"] > 0.45):
        chunks.append(cur); cur = []
    cur.append(w)
    if w["text"].endswith((".", ",")):
        chunks.append(cur); cur = []
if cur: chunks.append(cur)
# merge one-word orphans back into the previous line when it fits
merged = []
for ch in chunks:
    if (len(ch) == 1 and merged and merged[-1][-1]["seg"] == ch[0]["seg"]
            and ch[0]["s"] - merged[-1][-1]["e"] < 0.45 and len(merged[-1]) <= 3
            and sum(wwidth(x["disp"]) for x in merged[-1] + ch) + SPACE * len(merged[-1]) <= 960):
        merged[-1] = merged[-1] + ch
    else:
        merged.append(ch)
chunks = merged

for ci, ch in enumerate(chunks):
    end = ch[-1]["e"] + 0.35
    if ci + 1 < len(chunks): end = min(end, chunks[ci + 1][0]["s"])
    widths = [wwidth(x["disp"]) for x in ch]
    total = sum(widths) + SPACE * (len(ch) - 1)
    x = W / 2 - total / 2
    for i, w in enumerate(ch):
        cx = x + widths[i] / 2; x += widths[i] + SPACE
        s0 = max(w["s"], plan.COLD + 0.15)
        nxt = ch[i + 1]["s"] if i + 1 < len(ch) else end
        key = is_key(w["disp"])
        # highlight box while the word is spoken
        bw, bh = widths[i] + 28, SIZE + 22
        add(s0, max(nxt, s0 + 0.12),
            f"{{\\an5\\pos({cx:.0f},{CAP_Y:.0f})\\p1\\bord0\\shad0\\1c{GOLD if key else EMER}\\alpha&H10&"
            f"\\fscx80\\fscy80\\t(0,90,\\fscx106\\fscy106)\\t(90,150,\\fscx100\\fscy100)}}{rrect(bw, bh, 18)}",
            "Box", 0)
        # the word itself: pops in when spoken, stays for the rest of the chunk
        col_active = DARK if key else WHITE
        col_after = GOLD if key else WHITE
        add(s0, end,
            f"{{\\an5\\pos({cx:.0f},{CAP_Y:.0f})\\1c{col_active}{'\\bord0\\shad0' if key else ''}\\fscx60\\fscy60\\alpha&HFF&"
            f"\\t(0,80,\\fscx112\\fscy112\\alpha&H00&)\\t(80,150,\\fscx100\\fscy100)"
            f"\\t({int((max(nxt, s0+0.12) - s0)*1000)},{int((max(nxt, s0+0.12) - s0)*1000)+60},\\1c{col_after}{'\\bord5\\shad3' if key else ''})}}{w['disp']}",
            "Cap", 1)

# ------------------------------------------------------------- cold-open hook
add(0.15, 2.35, "{\\an5\\pos(540,760)\\fad(250,150)\\fsp6\\t(0,2200,\\fsp10)}BAYANGKAN HARI TUA", "Hook1")
add(0.75, 2.35, "{\\an5\\pos(540,850)\\fad(250,150)\\fsp6}HANYA UNTUK", "Hook1")
add(1.15, 2.40, "{\\an5\\pos(540,1010)\\fscx150\\fscy150\\alpha&HFF&\\blur8"
    "\\t(0,260,\\fscx100\\fscy100\\alpha&H00&\\blur0)\\t(1000,1250,\\fscx104\\fscy104)\\fad(0,120)}IBADAH", "Hook2")
add(1.15, 2.40, "{\\an5\\pos(540,1010)\\alpha&HB0&\\blur22\\bord14\\3c&H42C4F5&\\1a&HFF&\\fad(260,120)}IBADAH", "Hook2", 0)

# ------------------------------------------------------------- cues rendered as text
for c in plan.cues():
    t = c["t"]
    if c["kind"] == "counter":
        steps = 16
        for j in range(steps):
            n = round(c["n"] * (j + 1) / steps)
            a, b = t + j * 0.045, t + (j + 1) * 0.045
            if j == steps - 1: b = t + c["dur"]
            pop = "\\fscx118\\fscy118\\t(0,180,\\fscx100\\fscy100)" if j == steps - 1 else ""
            fade = "\\fad(0,250)" if j == steps - 1 else ""
            add(a, b, f"{{\\an5\\pos(540,420){pop}{fade}}}{n}", "Big")
        add(t + 0.25, t + c["dur"], "{\\an5\\pos(540,585)\\fad(200,250)\\fsp14\\alpha&HFF&\\t(0,200,\\alpha&H00&)}"
            + c["label"], "Hook1")
    elif c["kind"] == "chip":
        wdt = PIL_FONT.getlength(c["text"]) * 0.58 + 70
        add(t, t + c["dur"], f"{{\\an5\\pos(540,250)\\p1\\bord0\\shad0\\1c{EMER}\\alpha&H20&\\fscx0"
            f"\\t(0,250,\\fscx100)\\fad(0,250)}}{rrect(wdt, 70, 35)}", "Box", 0)
        add(t + 0.15, t + c["dur"], f"{{\\an5\\pos(540,250)\\fad(200,250)\\fsp3}}{c['text']}", "Chip")
        add(t + 0.15, t + c["dur"], "{\\an5\\pos(540,312)\\fad(300,250)\\fsp4\\1c&HFFFFFF&}DI ZAWIYAH", "Chip2")

# ------------------------------------------------------------- doa: Arabic accents
Hs = segs[-1]
for w in plan.words():
    low = w["text"].strip(".,").lower()
    if w["seg"] != "H": continue
    if low == "allah" and w["s"] < Hs["t0"] + 1.5:
        add(w["s"] - 0.3, w["s"] + 2.6, "{\\an5\\pos(540,330)\\fad(500,600)\\blur1\\fscx90\\fscy90"
            "\\t(0,2900,\\fscx104\\fscy104)}يا الله", "Arab")
    if low == "amin":
        add(w["s"] - 0.1, Hs["t1"] + 0.3, "{\\an5\\pos(540,330)\\fad(400,400)\\fscx70\\fscy70"
            "\\t(0,400,\\fscx100\\fscy100)}آمين", "Arab")
add(Hs["t0"] + 0.4, Hs["t0"] + 3.2, "{\\an5\\pos(540,440)\\fad(400,500)\\fsp8}DOA UNTUK SEMUA", "Chip2")

# ------------------------------------------------------------- outro
o = Hs["t1"] + 0.3
end = TOTAL
add(o, end, "{\\an5\\pos(540,700)\\fad(300,0)\\fsp10}JOM", "Hook1")
add(o + 0.15, end, "{\\an5\\pos(540,840)\\fscx140\\fscy140\\alpha&HFF&\\t(0,300,\\fscx100\\fscy100\\alpha&H00&)}BANTU", "Hook2")
add(o + 0.5, end, "{\\an5\\pos(540,990)\\fad(300,0)\\fsp4}PONDOK WARGA EMAS", "Out1")
for i, (txt, col) in enumerate([("SUMBANG", GOLD), ("SHARE", WHITE), ("DOAKAN", GOLD)]):
    add(o + 0.9 + i * 0.22, end, f"{{\\an5\\pos({[250, 540, 830][i]},1130)\\1c{col}\\fscx50\\fscy50\\alpha&HFF&"
        f"\\t(0,220,\\fscx100\\fscy100\\alpha&H00&)}}{txt}", "Out2")
add(o + 1.6, end, "{\\an5\\pos(540,1260)\\fad(400,0)}Hubungi pihak Zawiyah untuk menyumbang", "Out3")
add(o + 1.6, end, f"{{\\an5\\pos(540,1130)\\p1\\1c{EMER}\\alpha&H30&\\bord0\\shad0\\fscx0\\t(0,250,\\fscx100)}}{rrect(900, 90, 45)}", "Box", 0)

head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Montserrat ExtraBold,{SIZE},&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,0,0,0,0,100,100,0,0,1,5,3,5,0,0,0,1
Style: Box,Montserrat ExtraBold,{SIZE},&H00608C12,&H00FFFFFF,&H00000000,&H60000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Hook1,Montserrat ExtraBold,62,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,3,4,5,0,0,0,1
Style: Hook2,Anton,230,&H0042C4F5,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,4,0,1,4,6,5,0,0,0,1
Style: Big,Anton,300,&H0042C4F5,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,6,8,5,0,0,0,1
Style: Chip,Montserrat ExtraBold,40,&H0042C4F5,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Chip2,Montserrat ExtraBold,34,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,5,0,0,0,1
Style: Arab,Amiri,170,&H0042C4F5,&H00FFFFFF,&H00143020,&H90000000,1,0,0,0,100,100,0,0,1,4,5,5,0,0,0,1
Style: Out1,Montserrat ExtraBold,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,3,4,5,0,0,0,1
Style: Out2,Montserrat ExtraBold,52,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Out3,Montserrat ExtraBold,36,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,2,2,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
open(f"{plan.S}/subs.ass", "w").write(head + "\n".join(ev) + "\n")
print(len(chunks), "chunks,", len(ev), "events")
open(plan.S+"/chunks.txt","w").write("\n".join(" ".join(x["disp"] for x in ch) for ch in chunks))
