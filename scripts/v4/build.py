import os, sys, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D=os.path.dirname(os.path.abspath(__file__)); S=os.path.dirname(D); FD=S+'/fonts/'; V=S+'/src/video.mp4'
W,H=1080,1920; PY=570; PW,PH=1080,810          # video panel
INTRO=2.6; OUTRO=4.2
# ------------------------------------------------------------------ segments
# (src_start, src_end, chapter, shot, face_cx)
SEG=[(755.00,759.40,1,'w',340),(761.80,766.60,1,'c',350),(767.20,770.30,1,'w',370),(771.60,780.00,1,'c',380),
     (786.00,791.95,1,'w',350),(792.20,796.45,1,'c',350),
     (1615.70,1620.00,2,'w',300),(1620.70,1625.10,2,'c',300),(1629.80,1634.70,2,'w',300),(1635.70,1637.60,2,'c',300),
     (2005.40,2012.00,3,'w',310),(2014.20,2015.40,3,'c',300),(2017.60,2021.50,3,'w',300),(2028.20,2032.60,3,'w',240),
     (2032.90,2036.90,3,'c',230),(2055.30,2056.90,3,'w',260),(2059.00,2060.40,3,'c',260),(2062.40,2065.20,3,'w',260),(2066.30,2074.30,3,'c',260)]
Y='{\\c&H00E1FF&}'; R='{\\c&H0080FF&}'; N='{\\r}'
SUB=[(755.00,757.80,f"DIA BUKAN CAKAP BISMILLAH — {Y}ASTAGHFIRULLAH PUN BOLEH{N}"),(758.00,759.40,"DIA JUAL PINGGAN MANGKUK"),
 (761.85,764.90,f"SAMPAI ORANG PANGGIL {Y}\"CINA BISMILLAH\"{N}"),(764.90,766.60,f"{Y}\"CINA ASSALAMUALAIKUM\"{N}"),
 (767.20,770.30,f"KITA SAMPAI JE — {R}\"ASSALAMUALAIKUM!\"{N}"),(771.60,775.50,"\"NI BARANG BARU — PINGGAN MANGKUK, PERIUK BARU\""),
 (775.50,777.10,"\"MAHAL KE?\""),(777.10,780.00,f"{R}\"INSYAALLAH TAK MAHAL!\"{N}"),
 (786.00,790.10,f"SEMUA {Y}ASTAGHFIRULLAH...{N}"),(790.10,791.95,f"{R}\"MAKCIK, TAK TIPU YA KITA\"{N}"),
 (792.20,794.10,f"{Y}\"BISMILLAH...\"{N}"),(794.10,796.45,f"{R}\"ASTAGHFIRULLAH, ALHAMDULILLAH, SUBHANALLAH!\"{N}"),
 (1615.70,1617.30,"CONTOHNYA BEGINI..."),(1617.30,1620.00,f"ORANG MARI: \"HAJI, TOLONG {Y}ISLAMKAN{N} SAYA\""),
 (1620.70,1623.90,"\"OH SENANG JE — ESOK MARI YA, PETANG NI ADA HAL\""),(1624.00,1625.10,f"{R}\"NAK TENGOK BAJET!\"{N}"),
 (1629.80,1632.90,"\"NI BAJET... ADA BAJET UNTUK KITA NI\""),(1632.90,1634.70,f"\"PETANG ESOK BAJET BAGI {Y}APA?\"{N}"),
 (1635.70,1637.60,f"{R}FAQAD KAFARA — KAFIR!{N}"),
 (2005.40,2006.60,f"BILA {Y}WAJIB{N} NIKAH?"),(2006.60,2009.80,"CUKUP SYARAT, DUIT PUN ADA"),
 (2009.80,2012.00,f"{R}KEROPOK LEKOR PUN \"POWER\" MOLEK{N}"),(2014.20,2015.40,f"{Y}250 CC!{N}"),
 (2017.60,2020.10,"TENGOK PEREMPUAN PUN TAK TAHAN"),(2020.10,2021.50,f"KETIKA ITU — {Y}WAJIB NIKAH{N}"),
 (2028.20,2030.10,"KAWAN TU DAH NIKAH"),(2030.75,2032.60,"NOMBOR SATU DAH ADA..."),
 (2032.90,2034.70,f"ADA KEMAMPUAN LAGI UNTUK {R}NOMBOR DUA{N}"),(2034.70,2036.90,f"{Y}SUNAT NIKAH!{N}"),
 (2055.30,2056.90,f"BILA {R}HARAM{N} NIKAH?"),(2059.00,2060.40,f"KEROPOK LEKOR {R}TAK ADA API LANGSUNG{N}"),
 (2062.40,2065.20,"\"API...\" — TAK ADA API!"),(2066.30,2067.80,"DUIT PUN TAK ADA"),
 (2067.80,2071.90,"SAJA NAK KAHWIN DENGAN PEREMPUAN TU, NAK RASA"),(2071.90,2074.30,f"NAK MALUKAN ORANG JE — {R}HARAM NIKAH!{N}")]
CH={1:("01","CINA BISMILLAH","Peniaga yang lebih fasih berzikir"),
    2:("02","NAK TENGOK BAJET","Alasan tangguh orang nak masuk Islam"),
    3:("03","KEROPOK LEKOR","Hukum nikah: wajib, sunat & haram")}
PUNCH=[763.6,778.2,795.6,1624.4,1636.4,2010.7,2014.5,2034.4,2073.8]
# timeline
tl=[];t=INTRO
for s,e,c,sh,cx in SEG: tl.append(t); t+=e-s
BODY_END=t; TOTAL=BODY_END+OUTRO
def out_t(src):
    for (s,e,*_),o in zip(SEG,tl):
        if s-0.05<=src<=e+0.05: return o+max(0,min(src,e)-s)
    raise ValueError(src)
chap_start={}
for (s,e,c,*_),o in zip(SEG,tl): chap_start.setdefault(c,o)
print(f"body={BODY_END-INTRO:.2f}s total={TOTAL:.2f}s chapters={chap_start}")
# ------------------------------------------------------------------ static frame
img=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(img)
g=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(g)
for y in range(0,PY): gd.line([(0,y),(W,y)],fill=(6,8,14,int(245*min(1,(PY-y)/120+0.0)) if y>PY-120 else 245))
for y in range(PY+PH,H): gd.line([(0,y),(W,y)],fill=(6,8,14,int(240*min(1,(y-PY-PH)/140))))
img.alpha_composite(g)
GOLD=(255,214,0,255); RED=(255,110,0,255)
def ctext(y,txt,font,fill,x=None):
    bb=d.textbbox((0,0),txt,font=font); w=bb[2]-bb[0]
    xx=(W-w)//2-bb[0] if x is None else x
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).text((xx,y+5),txt,font=font,fill=(0,0,0,220))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7))); d.text((xx,y),txt,font=font,fill=fill); return bb
A=lambda s:ImageFont.truetype(FD+'Anton.ttf',s)
P=lambda s:ImageFont.truetype(FD+'Poppins-ExtraBold.ttf',s)
# label
lab="KULIAH SANTAI"; lf=P(28); bb=d.textbbox((0,0),lab,font=lf); pw=bb[2]-bb[0]+50
d.rounded_rectangle([(W-pw)//2,150,(W+pw)//2,198],radius=24,outline=GOLD,width=3)
ctext(155,lab,lf,GOLD)
ctext(205,"USTAZ BUAT LAWAK",A(112),(255,255,255,255))
# red slanted box with SELAIN ISLAM
t2="TAPI ADA ISI!"; f2=A(104); bb=d.textbbox((0,0),t2,font=f2); tw=bb[2]-bb[0]
x0=(W-tw)//2-40; x1=(W+tw)//2+40
d.polygon([(x0+18,352),(x1+18,352),(x1-18,482),(x0-18,482)],fill=RED)
d.text(((W-tw)//2-bb[0],352-bb[1]+12),t2,font=f2,fill=(255,255,255,255))
# panel borders
d.rectangle([0,PY-6,W,PY-1],fill=GOLD); d.rectangle([0,PY+PH,W,PY+PH+5],fill=GOLD)
# bottom: progress track + footer
d.rounded_rectangle([60,1838,1020,1850],radius=6,fill=(255,255,255,50))
ff=ImageFont.truetype(FD+'Poppins-Bold.ttf',26)
ctext(1866,"Petikan kuliah  •  Kongsikan peringatan ini",ff,(200,200,200,255))
img.save(D+'/frame.png')
# ------------------------------------------------------------------ ASS
def ts(x): return f"{int(x//3600)}:{int(x%3600//60):02d}:{x%60:05.2f}"
ass=f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Anton,100,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,0,0,0,0,100,100,1,0,1,6,4,5,60,60,0,1
Style: Big,Anton,200,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,2,0,1,8,6,5,40,40,0,1
Style: Pop,Poppins ExtraBold,52,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,4,3,5,60,60,0,1
Style: Tab,Poppins ExtraBold,36,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,0,0,5,0,0,0,1
Style: Box,Poppins ExtraBold,10,&H00000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Ar,Amiri,84,&H0000D6FF,&H0000D6FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,3,3,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
E=[]
def ev(a,b,style,text,layer=0): E.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{text}")
def rect(x,y,w,h): return f"m 0 0 l {w} 0 {w} {h} 0 {h}"
# --- HOOK
ev(0,INTRO,'Box',"{\\pos(0,0)\\p1\\c&H0A0806&\\alpha&H50&}"+rect(0,0,W,H)+"{\\p0}",0)
ev(0.10,INTRO,'Big',"{\\pos(540,680)\\fs240\\fscx260\\fscy260\\alpha&HFF&\\t(0,140,\\fscx100\\fscy100\\alpha&H00&)\\fad(0,150)}SENYUM SIKIT",2)
ev(0.55,INTRO,'Box',"{\\pos(60,820)\\p1\\c&H006EFF&\\clip(0,0,0,1920)\\t(0,180,\\clip(0,0,1080,1920))\\fad(0,150)}m 30 0 l 990 0 960 220 0 220{\\p0}",1)
ev(0.55,INTRO,'Big',"{\\pos(540,930)\\fs130\\alpha&HFF&\\t(80,200,\\alpha&H00&)\\fad(0,150)}KULIAH PUN MASUK!",2)
ev(1.10,INTRO,'Pop',"{\\pos(540,1130)\\fs72\\alpha&HFF&\\t(0,200,\\alpha&H00&)\\fad(0,150)}3 MOMEN LAWAK DALAM KULIAH",2)
ev(1.55,INTRO,'Pop',"{\\pos(540,1250)\\c&H00D7FF&\\fs56\\alpha&HFF&\\t(0,200,\\alpha&H00&)\\fad(0,150)}CINA BISMILLAH  •  BAJET  •  KEROPOK LEKOR",2)
# --- tabs (chapter indicator) under header
names=['BISMILLAH','BAJET','KEROPOK']; xs=[230,540,850]
bounds=[chap_start[1],chap_start[2],chap_start[3],BODY_END]
for k in range(3):
    a,b=bounds[k],bounds[k+1]
    for j in range(3):
        if j==k:
            ev(a,b,'Box',f"{{\\pos({xs[j]-150},508)\\p1\\c&H00D6FF&}}m 0 0 l 300 0 300 50 0 50{{\\p0}}",1)
            ev(a,b,'Tab',f"{{\\pos({xs[j]},533)\\c&H0A0A0A&}}{names[j]}",2)
        else:
            ev(a,b,'Tab',f"{{\\pos({xs[j]},533)\\alpha&H70&}}{names[j]}",2)
# --- chapter cards
for c,(num,title,desc) in CH.items():
    a=chap_start[c]; b=a+2.1; cy=PY+PH//2
    ev(a,b,'Box',f"{{\\pos(0,{cy-170})\\p1\\c&H0A0806&\\alpha&H30&\\fad(80,200)}}"+rect(0,0,W,340)+"{\\p0}",3)
    ev(a,b,'Box',f"{{\\pos(0,{cy-170})\\p1\\c&H006EFF&\\fad(80,200)\\clip(0,0,0,1920)\\t(0,220,\\clip(0,0,1080,1920))}}"+rect(0,0,W,10)+"{\\p0}",4)
    ev(a,b,'Box',f"{{\\pos(0,{cy+160})\\p1\\c&H006EFF&\\fad(80,200)\\clip(1080,0,1080,1920)\\t(0,220,\\clip(0,0,1080,1920))}}"+rect(0,0,W,10)+"{\\p0}",4)
    ev(a,b,'Big',f"{{\\an6\\move(-200,{cy-20},330,{cy-20},0,180)\\c&H00D6FF&\\fs230\\fad(0,200)}}{num}",5)
    ev(a+0.08,b,'Big',f"{{\\an4\\move(1200,{cy-50},370,{cy-50},0,200)\\fad(0,200)\\fs{150 if len(title)<=9 else (118 if len(title)<=13 else 104)}}}{title}",5)
    ev(a+0.25,b,'Pop',f"{{\\an4\\pos(375,{cy+70})\\fs40\\alpha&HFF&\\t(0,200,\\alpha&H00&)\\fad(0,200)}}{desc}",5)
# --- subtitles
SUBY=1540
for a,b,txt in SUB:
    oa,ob=out_t(a),out_t(b)
    ev(oa,ob,'Sub',f"{{\\q0\\pos(540,{SUBY})\\fscx70\\fscy70\\t(0,90,\\fscx108\\fscy108)\\t(90,170,\\fscx100\\fscy100)}}{txt}",6)
# --- HAHA stickers
import random; random.seed(5)
for p in PUNCH:
    tp=out_t(p); x=random.choice([210,870]); rot=random.choice([-14,12])
    ev(tp,tp+1.1,'Big',f"{{\\pos({x},{PY+120})\\frz{rot}\\fs110\\c&H00E1FF&\\3c&H000000&\\bord7\\fscx30\\fscy30\\t(0,120,\\fscx115\\fscy115)\\t(120,220,\\fscx100\\fscy100)\\fad(0,250)}}HAHA!",9)
# --- outro
o=BODY_END
ev(o,TOTAL,'Box',"{\\pos(0,0)\\p1\\c&H0A0806&\\alpha&H40&\\fad(250,0)}"+rect(0,0,W,H)+"{\\p0}",7)
ev(o+0.15,TOTAL,'Ar',"{\\pos(540,660)\\fs150\\fad(300,300)\\blur1}تَبَسُّمُكَ فِي وَجْهِ أَخِيكَ",8)
ev(o+0.35,TOTAL,'Ar',"{\\pos(540,840)\\fs170\\fad(300,300)\\blur1}لَكَ صَدَقَةٌ",8)
ev(o+0.7,TOTAL,'Pop',"{\\pos(540,1040)\\fs66\\fad(300,300)}\"Senyumanmu kepada",8)
ev(o+0.7,TOTAL,'Pop',"{\\pos(540,1125)\\fs66\\fad(300,300)}saudaramu adalah",8)
ev(o+0.7,TOTAL,'Pop',"{\\pos(540,1215)\\fs76\\fad(300,300)\\c&H00E1FF&}SEDEKAH.\"",8)
ev(o+1.0,TOTAL,'Tab',"{\\pos(540,1335)\\fs52\\c&H00D6FF&\\fad(300,300)}HADIS RIWAYAT AT-TIRMIZI",8)
ass+="\n".join(E)+"\n"
open(D+'/v4.ass','w').write(ass)
# ------------------------------------------------------------------ ffmpeg
args=['ffmpeg','-v','error','-stats','-y']
for s,e,*_ in SEG: args+=['-ss',f"{s:.3f}",'-t',f"{e-s:.3f}",'-i',V]
n=len(SEG)
args+=['-loop','1','-t',f"{INTRO}",'-i',D+'/intro_bg.png','-loop','1','-t',f"{OUTRO}",'-i',D+'/outro_bg.png',
       '-loop','1','-t',f"{TOTAL:.3f}",'-i',D+'/frame.png',
       '-i',D+'/music.wav','-i',D+'/boing.wav','-i',D+'/whoosh.wav','-i',D+'/ding.wav']
iI,iO,iF,iM,iImp,iW,iR=n,n+1,n+2,n+3,n+4,n+5,n+6
fc=[];cat=''
BG="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30,eq=brightness=-0.30:saturation=0.55"
for i,(s,e,c,sh,cx) in enumerate(SEG):
    dd=e-s
    if sh=='w': cw,chh,cy0=576,432,0
    else: cw,chh,cy0=480,360,0
    x0=max(0,min(768-cw,cx-cw//2))
    z0,z1=(1.0,1.06) if sh=='w' else (1.04,1.12)
    fc.append(f"[{i}:v]fps=30,setpts=PTS-STARTPTS,split[b{i}][f{i}]")
    fc.append(f"[b{i}]{BG}[bg{i}]")
    fc.append(f"[f{i}]crop={cw}:{chh}:{x0}:{cy0},scale=w='trunc(1080*({z0}+{z1-z0}*t/{dd:.3f})/2)*2':h=-2:eval=frame:flags=lanczos,crop=1080:810:(iw-1080)/2:(ih-810)/2,eq=contrast=1.06:saturation=1.12,unsharp=5:5:0.6[fg{i}]")
    fc.append(f"[bg{i}][fg{i}]overlay=0:{PY},setsar=1[v{i}]")
    fc.append(f"[{i}:a]asetpts=PTS-STARTPTS,aresample=44100,afade=in:d=0.03,afade=out:st={dd-0.04:.3f}:d=0.04[a{i}]")
for k,(idx,dur) in enumerate([(iI,INTRO),(iO,OUTRO)]):
    fc.append(f"[{idx}:v]fps=30,{BG},setsar=1[sv{k}]")
    fc.append(f"anullsrc=r=44100:cl=mono,atrim=duration={dur}[sa{k}]")
cat="[sv0][sa0]"+"".join(f"[v{i}][a{i}]" for i in range(n))+"[sv1][sa1]"
fc.append(f"{cat}concat=n={n+2}:v=1:a=1[base][voiceraw]")
flashes=[chap_start[c] for c in (1,2,3)]+[BODY_END]
fl=",".join(f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.85:t=fill:enable='between(t,{x-0.02:.3f},{x+0.07:.3f})'" for x in flashes)
fc.append(f"[{iF}:v]format=rgba[frm]")
fc.append(f"[base][frm]overlay=0:0:enable='between(t,{INTRO},{BODY_END})'[b1]")
fc.append(f"color=c=0xFFD600:s=960x12:r=30,format=rgba[bar]")
fc.append(f"[b1][bar]overlay=x='60-960+960*(t-{INTRO})/{BODY_END-INTRO:.3f}':y=1838:enable='between(t,{INTRO},{BODY_END})':shortest=0[b1b]")
fc.append(f"[b1b]crop=1080:1920:0:0,ass={D}/v4.ass:fontsdir={FD},{fl},fade=in:st=0:d=0.25,fade=out:st={TOTAL-0.5:.3f}:d=0.5,format=yuv420p[vout]")
# audio
fc.append("[voiceraw]highpass=f=80,lowpass=f=12000,acompressor=threshold=-22dB:ratio=3.5:attack=5:release=120:makeup=5,loudnorm=I=-14:TP=-1.5:LRA=8,aresample=44100,asplit[voice][sc]")
fc.append(f"[{iM}:a]atrim=duration={TOTAL:.3f},volume=0.45,aformat=channel_layouts=stereo[mraw]")
fc.append("[sc]aformat=channel_layouts=stereo[sc2]")
fc.append("[mraw][sc2]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400:makeup=1[mduck]")
sfx=[(iImp,0.10,0.8),(iW,0.45,0.6),(iImp,0.60,0.6),(iW,1.05,0.4)]
for c in (1,2,3): sfx+= [(iW,chap_start[c]-0.25,0.7)]
sfx+=[(iR,BODY_END,0.5)]+[(iImp,out_t(p),0.55) for p in PUNCH]
names=[]
for k,(idx,at,vol) in enumerate(sfx):
    fc.append(f"[{idx}:a]volume={vol},adelay={int(at*1000)}|{int(at*1000)}[sx{k}]")
    names.append(f"[sx{k}]")
# split shared inputs: ffmpeg allows reuse of input pads only once -> use asplit
fcs=";".join(fc)
uses={}
for idx,_,_ in sfx: uses[idx]=uses.get(idx,0)+1
for idx,cnt in uses.items():
    labels="".join(f"[in{idx}_{j}]" for j in range(cnt))
    fcs=f"[{idx}:a]asplit={cnt}{labels};"+fcs
    for j in range(cnt): fcs=fcs.replace(f"[{idx}:a]volume",f"[in{idx}_{j}]volume",1)
fcs+=f";[voice]aformat=channel_layouts=stereo[vst];[vst][mduck]{''.join(names)}amix=inputs={2+len(names)}:duration=first:normalize=0,alimiter=limit=0.95,atrim=duration={TOTAL:.3f}[aout]"
args+=['-filter_complex',fcs,'-map','[vout]','-map','[aout]','-c:v','libx264','-preset','medium','-crf','19','-r','30',
       '-c:a','aac','-b:a','192k','-movflags','+faststart','-t',f"{TOTAL:.3f}",D+'/final_v4.mp4']
if '--dry' in sys.argv: print(fcs[:3000]); sys.exit()
subprocess.run(args,check=True)
