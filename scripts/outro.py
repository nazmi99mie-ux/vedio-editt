import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
F=os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))+'/fonts/'
W,H=1080,1920; img=Image.new('RGBA',(W,H),(4,10,18,215)); d=ImageDraw.Draw(img)
GOLD=(232,196,104,255)
def ct(y,t,f,fill,**kw):
    bb=d.textbbox((0,0),t,font=f,**kw); d.text(((W-(bb[2]-bb[0]))//2-bb[0],y),t,font=f,fill=fill,**kw); return bb[3]-bb[1]
ar1='وَمَن يَبْتَغِ غَيْرَ الْإِسْلَامِ دِينًا'; ar2='فَلَن يُقْبَلَ مِنْهُ'; ar3='وَهُوَ فِي الْآخِرَةِ مِنَ الْخَاسِرِينَ'
af=ImageFont.truetype(F+'Amiri-Arabic-Bold.ttf',84)
y=560
for a in (ar1,ar2,ar3): ct(y,a,af,GOLD,direction='rtl',language='ar'); y+=150
d.line([(300,y+20),(780,y+20)],fill=GOLD,width=3)
tf=ImageFont.truetype(F+'Poppins-Bold.ttf',44)
y+=70
for l in ['"Dan sesiapa yang mencari agama','selain Islam, maka tidak akan','diterima daripadanya, dan dia di','akhirat kelak dari golongan','orang-orang yang rugi."']:
    y+=ct(y,l,tf,(255,255,255,255))+20
cf=ImageFont.truetype(F+'Cinzel-ExtraBold.ttf',50); ct(y+40,"Surah Ali 'Imran : 85",cf,GOLD)
img.save(sys.argv[1])
