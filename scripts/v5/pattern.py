# Subtle Islamic geometric background: 8-point star (Khatam) tessellation + mosque silhouette
import sys, math
from PIL import Image, ImageDraw, ImageFilter
W,H=1080,1920; out=sys.argv[1]
img=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(img)
GOLD=(214,175,90)
def star(cx,cy,r,col,w):
    pts=[]
    for k in range(16):
        a=math.pi/8*k+math.pi/8
        rr=r if k%2==0 else r*0.72
        pts.append((cx+rr*math.cos(a),cy+rr*math.sin(a)))
    d.line(pts+[pts[0]],fill=col,width=w)
    # inner square pair (khatam)
    for off in (0,math.pi/4):
        sq=[(cx+r*0.55*math.cos(off+math.pi/2*k),cy+r*0.55*math.sin(off+math.pi/2*k)) for k in range(4)]
        d.line(sq+[sq[0]],fill=col,width=max(1,w-1))
S=150
for j in range(-1,H//S+2):
    for i in range(-1,W//S+2):
        cx=i*S+(S//2 if j%2 else 0); cy=j*S
        star(cx,cy,S*0.46,GOLD+(255,),2)
        d.ellipse([cx-4,cy-4,cx+4,cy+4],outline=GOLD+(255,),width=1)
# fade the pattern: strongest at edges, invisible behind the video panel
mask=Image.new('L',(W,H),0); md=ImageDraw.Draw(mask)
for y in range(H):
    if y<560: a=70
    elif y<1400: a=18
    else: a=60
    md.line([(0,y),(W,y)],fill=a)
mask=mask.filter(ImageFilter.GaussianBlur(60))
img.putalpha(Image.eval(img.getchannel('A'),lambda v:v).point(lambda v:v)) 
alpha=Image.composite(mask,Image.new('L',(W,H),0),img.getchannel('A'))
img.putalpha(alpha)
# mosque silhouette near bottom (small, faint)
sil=Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sil)
k=0.55; base=1912; col=GOLD+(34,)
X=lambda x:540+(x-540)*k; Yb=lambda dy:base-dy*k
sd.rectangle([X(140),Yb(120),X(940),base],fill=col)
sd.pieslice([X(340),Yb(420),X(740),Yb(20)],180,360,fill=col)
sd.rectangle([X(340),Yb(220),X(740),Yb(120)],fill=col)
for x in (200,880): sd.pieslice([X(x-110),Yb(260),X(x+110),Yb(40)],180,360,fill=col)
for x in (90,990):
    sd.rectangle([X(x-22),Yb(520),X(x+22),base],fill=col)
    sd.polygon([(X(x-30),Yb(520)),(X(x+30),Yb(520)),(X(x),Yb(620))],fill=col)
sd.polygon([(540,Yb(470)),(544,Yb(430)),(536,Yb(430))],fill=col)
img.alpha_composite(sil)
img.save(out)
