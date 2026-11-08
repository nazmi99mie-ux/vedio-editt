# Usage: overlay.py out.png "TITLE" "subtitle" "arabic" "arabic ref"
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os; F=os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))+'/fonts/'
W,H=1080,1920
out,title,sub,arab,ref=sys.argv[1:6]
img=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(img)
GOLD=(232,196,104,255); WHITE=(255,255,255,255)
def ctext(y,txt,font,fill,shadow=True,**kw):
    bb=d.textbbox((0,0),txt,font=font,**kw); x=(W-(bb[2]-bb[0]))//2-bb[0]
    if shadow:
        sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).text((x,y+4),txt,font=font,fill=(0,0,0,200),**kw)
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d.text((x,y),txt,font=font,fill=fill,**kw)
    return bb[3]-bb[1]
# top gradient panel
grad=Image.new('RGBA',(W,H),(0,0,0,0)); g=ImageDraw.Draw(grad)
for y in range(0,560): g.line([(0,y),(W,y)],fill=(5,12,20,int(235*(1-max(0,y-380)/180)) if y>380 else 235))
img.alpha_composite(grad)
# small label pill
lab="PERINGATAN"; lf=ImageFont.truetype(F+'Poppins-Bold.ttf',30)
bb=d.textbbox((0,0),lab,font=lf); pw=bb[2]-bb[0]+56
d.rounded_rectangle([(W-pw)//2,150,(W+pw)//2,205],radius=28,fill=(170,30,30,255))
ctext(155,lab,lf,WHITE,shadow=False)
# title (auto-size, 1-2 lines)
lines=title.split('|'); y=235
for ln in lines:
    size=104
    while True:
        tf=ImageFont.truetype(F+'Cinzel-ExtraBold.ttf',size)
        if d.textlength(ln,font=tf)<W-100: break
        size-=4
    y+=ctext(y,ln,tf,GOLD)+18
sf=ImageFont.truetype(F+'Poppins-Bold.ttf',40)
ctext(y+14,sub,sf,WHITE)
# ornament line
oy=y+90
d.line([(240,oy),(500,oy)],fill=GOLD,width=3); d.line([(580,oy),(840,oy)],fill=GOLD,width=3)
d.polygon([(540,oy-14),(554,oy),(540,oy+14),(526,oy)],fill=GOLD)
# frame around the video (video placed at y=600..1208)
d.rounded_rectangle([22,594,1058,1182],radius=14,outline=GOLD,width=5)
# bottom verse panel
if arab:
    pan=Image.new('RGBA',(W,H),(0,0,0,0)); pd=ImageDraw.Draw(pan)
    for y in range(1540,H): pd.line([(0,y),(W,y)],fill=(5,12,20,int(min(1,(y-1540)/90)*225)))
    img.alpha_composite(pan)
    size=58
    while True:
        af=ImageFont.truetype(F+'Amiri-Arabic-Bold.ttf',size)
        if d.textlength(arab,font=af,direction='rtl',language='ar')<W-90: break
        size-=2
    ctext(1620,arab,af,GOLD,direction='rtl',language='ar')
    tf2=ImageFont.truetype(F+'Poppins-Bold.ttf',29)
    y=1730
    for ln in ref.split('|'):
        y+=ctext(y,ln,tf2,(235,235,235,255))+12
img.save(out)
