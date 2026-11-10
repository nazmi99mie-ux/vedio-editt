import os, sys, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D=os.path.dirname(os.path.abspath(__file__)); S=os.path.dirname(D); FD=S+'/fonts/'; V=S+'/vid2/src/video.mp4'
W,H=1080,1920; PY=570; PW,PH=1080,810          # video panel
INTRO=2.6; OUTRO=4.2
# ------------------------------------------------------------------ segments
# (src_start, src_end, chapter, shot, face_cx)
SEG=[(2393.79,2400.42,1,'w',375),(2400.42,2407.30,1,'c',432),
     (2407.30,2413.40,2,'w',444),(2413.40,2420.10,2,'c',411),(2420.10,2426.75,2,'w',513),(2426.75,2428.65,2,'c',510),
     (2428.65,2438.90,3,'w',432),(2438.90,2443.65,3,'c',384),(2443.65,2449.85,3,'w',486),(2449.85,2452.25,3,'c',438),
     (2453.59,2459.05,4,'c',420),(2466.32,2473.19,4,'w',411),(2511.37,2516.15,4,'w',579),(2527.93,2531.50,4,'c',282)]
Y='{\\c&H00D7FF&}'; R='{\\c&H4646FF&}'; N='{\\r}'
SUB=[(2394.42,2397.65,"KHUSYUK HATI KEPADA ALLAH DALAM SOLAT ITU,"),(2397.65,2400.40,f"BARU ALLAH {Y}TERIMA{N}."),
 (2400.48,2403.50,f"APA MAKNA KHUSYUK? {Y}TETAP.{N}"),(2403.60,2407.25,f"HATI SENTIASA SEDAR — {Y}AKU SEDANG SOLAT.{N}"),
 (2407.40,2410.40,"BAWA SEEKOR LEMBU LALU ATAS BATAS BENDANG."),(2410.50,2413.40,"SEBELAH SINI ADA PADI, SEBELAH SANA ADA PADI."),
 (2413.40,2416.80,"BILA KITA HERET LEMBU ATAS BATAS TU,"),(2416.80,2420.10,f"PERANGAI LEMBU — {R}KEPALA DIA NAK CAPAI JUGA.{N}"),
 (2420.10,2422.20,"KITA TARIK NAIK ATAS BATAS."),(2422.20,2425.20,"JALAN SIKIT, DIA CAPAI LAGI — TARIK DIA ATAS BATAS."),
 (2425.20,2426.75,"SAMPAI KE HUJUNG JALAN."),(2426.75,2428.65,f"{Y}MACAM ITULAH SOLAT KITA.{N}"),
 (2428.70,2433.40,"BILA KITA TAKBIR, MULA-MULA KITA INGAT LAGI."),(2433.40,2436.40,"BACAAN KITA TAHU, APA KITA BUAT KITA TAHU —"),
 (2436.40,2438.90,f"ITU DIPANGGIL {Y}KHUSYUK.{N}"),(2438.96,2443.60,"\"AKU SEDANG BERDIRI SOLAT, DALAM RUKUN YANG PERTAMA.\""),
 (2443.70,2447.70,"\"AKU SEDANG MEMBACA AL-FATIHAH, DAN FAHAM MAKNANYA.\""),(2447.70,2449.85,"\"PERBUATAN AKU INI RUKUN.\""),
 (2449.90,2452.25,f"INI DIPANGGIL KITA DALAM {Y}KHUSYUK.{N}"),
 (2454.10,2457.30,"DALAM BACA-BACA TU, TIBA-TIBA DATANG..."),(2457.30,2459.00,f"{R}\"PRN MELAKA!\"{N}"),
 (2466.45,2468.00,"\"INGAT NI — PRN MELAKA...\""),(2468.00,2471.60,f"\"SIAPA YANG BERTANDING?\" — {R}PULA DAH, DIA DATANG!{N}"),
 (2471.60,2473.10,f"{Y}TAK PAYAHLAH TU!{N}"),
 (2511.40,2513.60,"SAMPAI BERI SALAM, HABIS SOLAT —"),(2513.60,2516.20,f"YANG MANA INGAT TU, {Y}DIA KIRA PAHALA.{N}"),
 (2527.93,2531.50,f"MAKA KETIKA ITU, {Y}BARU SOLAT KITA DITERIMA ALLAH.{N}")]
CH={1:("01","MAKNA KHUSYUK","Hati sentiasa sedar: aku sedang solat"),
    2:("02","IBARAT LEMBU","Tarik lembu di atas batas bendang"),
    3:("03","SEDAR SETIAP RUKUN","Tahu apa yang dibaca & dibuat"),
    4:("04","BILA HATI LARI","Tarik balik — hingga beri salam")}
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
img.alpha_composite(Image.open(D+'/islamic_bg.png').convert('RGBA'))
import math
def star8(cx,cy,r,fill):
    pts=[(cx+(r if k%2==0 else r*0.45)*math.cos(math.pi/8*k),cy+(r if k%2==0 else r*0.45)*math.sin(math.pi/8*k)) for k in range(16)]
    d.polygon(pts,fill=fill)
GOLD=(222,184,92,255); RED=(0,110,72,255)
def ctext(y,txt,font,fill,x=None):
    bb=d.textbbox((0,0),txt,font=font); w=bb[2]-bb[0]
    xx=(W-w)//2-bb[0] if x is None else x
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).text((xx,y+5),txt,font=font,fill=(0,0,0,220))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7))); d.text((xx,y),txt,font=font,fill=fill); return bb
A=lambda s:ImageFont.truetype(FD+'Anton.ttf',s)
P=lambda s:ImageFont.truetype(FD+'Poppins-ExtraBold.ttf',s)
# label
lab="SOLAT KHUSYUK"; lf=P(28); bb=d.textbbox((0,0),lab,font=lf); pw=bb[2]-bb[0]+50
d.rounded_rectangle([(W-pw)//2,150,(W+pw)//2,198],radius=24,outline=GOLD,width=3)
ctext(155,lab,lf,GOLD)
ctext(205,"KHUSYUK DALAM SOLAT",A(108),(255,255,255,255))
# red slanted box with SELAIN ISLAM
t2="IBARAT TARIK LEMBU?"; f2=A(104); bb=d.textbbox((0,0),t2,font=f2); tw=bb[2]-bb[0]
x0=(W-tw)//2-40; x1=(W+tw)//2+40
d.polygon([(x0+18,352),(x1+18,352),(x1-18,482),(x0-18,482)],fill=RED)
d.text(((W-tw)//2-bb[0],352-bb[1]+12),t2,font=f2,fill=(255,255,255,255))
# panel borders
d.rectangle([0,PY-6,W,PY-1],fill=GOLD); d.rectangle([0,PY+PH,W,PY+PH+5],fill=GOLD)
star8(540,PY-3,22,GOLD); star8(540,PY+PH+3,22,GOLD)
for cx in (60,1020):
    star8(cx,PY-3,13,GOLD); star8(cx,PY+PH+3,13,GOLD)
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
Style: Sub,Anton,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,0,0,0,0,100,100,1,0,1,6,4,5,60,60,0,1
Style: Big,Anton,200,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,2,0,1,8,6,5,40,40,0,1
Style: Pop,Poppins ExtraBold,52,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,4,3,5,60,60,0,1
Style: Tab,Poppins ExtraBold,30,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,0,0,5,0,0,0,1
Style: Box,Poppins ExtraBold,10,&H00000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Ar,Amiri,84,&H005CB8DE,&H005CB8DE,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,3,3,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
E=[]
def ev(a,b,style,text,layer=0): E.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{text}")
def rect(x,y,w,h): return f"m 0 0 l {w} 0 {w} {h} 0 {h}"
# --- HOOK
ev(0,INTRO,'Box',"{\\pos(0,0)\\p1\\c&H0A0806&\\alpha&H50&}"+rect(0,0,W,H)+"{\\p0}",0)
ev(0.10,INTRO,'Big',"{\\pos(540,680)\\fs170\\fscx260\\fscy260\\alpha&HFF&\\t(0,140,\\fscx100\\fscy100\\alpha&H00&)\\fad(0,150)}SOLAT KITA...",2)
ev(0.55,INTRO,'Box',"{\\pos(60,820)\\p1\\c&H486E00&\\clip(0,0,0,1920)\\t(0,180,\\clip(0,0,1080,1920))\\fad(0,150)}m 30 0 l 990 0 960 220 0 220{\\p0}",1)
ev(0.55,INTRO,'Big',"{\\pos(540,930)\\fs118\\alpha&HFF&\\t(80,200,\\alpha&H00&)\\fad(0,150)}KHUSYUK ATAU TIDAK?",2)
ev(1.10,INTRO,'Pop',"{\\pos(540,1130)\\fs72\\alpha&HFF&\\t(0,200,\\alpha&H00&)\\fad(0,150)}IBARAT TARIK LEMBU ATAS BATAS",2)
ev(1.55,INTRO,'Pop',"{\\pos(540,1250)\\c&H00D7FF&\\fs56\\alpha&HFF&\\t(0,200,\\alpha&H00&)\\fad(0,150)}MAKNA  •  LEMBU  •  RUKUN  •  HATI LARI",2)
# --- tabs (chapter indicator) under header
CK=sorted(CH); names=['MAKNA','LEMBU','RUKUN','HATI LARI']; xs=[150,410,670,930]
bounds=[chap_start[c] for c in CK]+[BODY_END]
for k in range(len(CK)):
    a,b=bounds[k],bounds[k+1]
    for j in range(len(CK)):
        if j==k:
            ev(a,b,'Box',f"{{\\pos({xs[j]-120},508)\\p1\\c&H5CB8DE&}}m 0 0 l 240 0 240 50 0 50{{\\p0}}",1)
            ev(a,b,'Tab',f"{{\\pos({xs[j]},533)\\c&H0A0A0A&}}{names[j]}",2)
        else:
            ev(a,b,'Tab',f"{{\\pos({xs[j]},533)\\alpha&H70&}}{names[j]}",2)
# --- chapter cards
for c,(num,title,desc) in CH.items():
    a=chap_start[c]; b=a+2.1; cy=PY+PH//2
    ev(a,b,'Box',f"{{\\pos(0,{cy-170})\\p1\\c&H0A0806&\\alpha&H30&\\fad(80,200)}}"+rect(0,0,W,340)+"{\\p0}",3)
    ev(a,b,'Box',f"{{\\pos(0,{cy-170})\\p1\\c&H486E00&\\fad(80,200)\\clip(0,0,0,1920)\\t(0,220,\\clip(0,0,1080,1920))}}"+rect(0,0,W,10)+"{\\p0}",4)
    ev(a,b,'Box',f"{{\\pos(0,{cy+160})\\p1\\c&H486E00&\\fad(80,200)\\clip(1080,0,1080,1920)\\t(0,220,\\clip(0,0,1080,1920))}}"+rect(0,0,W,10)+"{\\p0}",4)
    ev(a,b,'Big',f"{{\\an6\\move(-200,{cy-20},330,{cy-20},0,180)\\c&H5CB8DE&\\fs230\\fad(0,200)}}{num}",5)
    ev(a+0.08,b,'Big',f"{{\\an4\\move(1200,{cy-50},370,{cy-50},0,200)\\fs{150 if len(title)<=9 else (112 if len(title)<=13 else 92)}\\fad(0,200)}}{title}",5)
    ev(a+0.25,b,'Pop',f"{{\\an4\\pos(375,{cy+70})\\fs40\\alpha&HFF&\\t(0,200,\\alpha&H00&)\\fad(0,200)}}{desc}",5)
# --- subtitles
SUBY=1540
for a,b,txt in SUB:
    oa,ob=out_t(a),out_t(b)
    ev(oa,ob,'Sub',f"{{\\q0\\pos(540,{SUBY})\\fscx70\\fscy70\\t(0,90,\\fscx108\\fscy108)\\t(90,170,\\fscx100\\fscy100)}}{txt}",6)
# --- outro
o=BODY_END
ev(o,TOTAL,'Box',"{\\pos(0,0)\\p1\\c&H0A0806&\\alpha&H40&\\fad(250,0)}"+rect(0,0,W,H)+"{\\p0}",7)
ev(o+0.15,TOTAL,'Ar',"{\\pos(540,600)\\fs230\\fad(300,300)\\blur1}قَدْ أَفْلَحَ الْمُؤْمِنُونَ",8)
ev(o+0.35,TOTAL,'Ar',"{\\pos(540,810)\\fs175\\fad(300,300)\\blur1}الَّذِينَ هُمْ فِي صَلَاتِهِمْ خَاشِعُونَ",8)
ev(o+0.7,TOTAL,'Pop',"{\\pos(540,1030)\\fs62\\fad(300,300)}\"Sesungguhnya berjayalah orang beriman,",8)
ev(o+0.7,TOTAL,'Pop',"{\\pos(540,1115)\\fs62\\fad(300,300)}iaitu mereka yang",8)
ev(o+0.7,TOTAL,'Pop',"{\\pos(540,1205)\\fs72\\fad(300,300)\\c&H5CB8DE&}KHUSYUK DALAM SOLATNYA.\"",8)
ev(o+1.0,TOTAL,'Tab',"{\\pos(540,1325)\\fs50\\c&H5CB8DE&\\fad(300,300)}SURAH AL-MU'MINUN : 1-2",8)
ass+="\n".join(E)+"\n"
open(D+'/v6.ass','w').write(ass)
# ------------------------------------------------------------------ ffmpeg
args=['ffmpeg','-v','error','-stats','-y']
for s,e,*_ in SEG: args+=['-ss',f"{s:.3f}",'-t',f"{e-s:.3f}",'-i',V]
n=len(SEG)
args+=['-loop','1','-t',f"{INTRO}",'-i',D+'/intro_bg.png','-loop','1','-t',f"{OUTRO}",'-i',D+'/outro_bg.png',
       '-loop','1','-t',f"{TOTAL:.3f}",'-i',D+'/frame.png',
       '-loop','1','-t',f"{TOTAL:.3f}",'-i',D+'/islamic_bg.png','-i',D+'/music.wav','-i',D+'/impact.wav','-i',D+'/whoosh.wav','-i',D+'/riser.wav']
iI,iO,iF,iP,iM,iImp,iW,iR=n,n+1,n+2,n+3,n+4,n+5,n+6,n+7
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
    fi=0.06 if i==0 or abs(SEG[i-1][1]-s)>0.01 else 0.0
    fo=0.06 if i==len(SEG)-1 or abs(SEG[i+1][0]-e)>0.01 else 0.0
    af=",".join(x for x in ([f"afade=in:d={fi}"] if fi else [])+([f"afade=out:st={dd-fo:.3f}:d={fo}"] if fo else []))
    fc.append(f"[{i}:a]asetpts=PTS-STARTPTS,aresample=44100"+(","+af if af else "")+f"[a{i}]")
for k,(idx,dur) in enumerate([(iI,INTRO),(iO,OUTRO)]):
    fc.append(f"[{idx}:v]fps=30,{BG},setsar=1[sv{k}]")
    fc.append(f"anullsrc=r=44100:cl=mono,atrim=duration={dur}[sa{k}]")
cat="[sv0][sa0]"+"".join(f"[v{i}][a{i}]" for i in range(n))+"[sv1][sa1]"
fc.append(f"{cat}concat=n={n+2}:v=1:a=1[base][voiceraw]")
flashes=[chap_start[c] for c in sorted(CH)]+[BODY_END]
fl=",".join(f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.85:t=fill:enable='between(t,{x-0.02:.3f},{x+0.07:.3f})'" for x in flashes)
fc.append(f"[{iF}:v]format=rgba[frm]"); fc.append(f"[{iP}:v]format=rgba[pat]")
fc.append(f"[base][pat]overlay=0:0:enable='not(between(t,{INTRO},{BODY_END}))'[b0p]"); fc.append(f"[b0p][frm]overlay=0:0:enable='between(t,{INTRO},{BODY_END})'[b1]")
fc.append(f"color=c=0xDEB85C:s=960x12:r=30,format=rgba[bar]")
fc.append(f"[b1][bar]overlay=x='60-960+960*(t-{INTRO})/{BODY_END-INTRO:.3f}':y=1838:enable='between(t,{INTRO},{BODY_END})':shortest=0[b1b]")
fc.append(f"[b1b]crop=1080:1920:0:0,ass={D}/v6.ass:fontsdir={FD},{fl},fade=in:st=0:d=0.25,fade=out:st={TOTAL-0.5:.3f}:d=0.5,format=yuv420p[vout]")
# audio
fc.append("[voiceraw]highpass=f=80,lowpass=f=12000,acompressor=threshold=-22dB:ratio=3.5:attack=5:release=120:makeup=5,loudnorm=I=-14:TP=-1.5:LRA=8,aresample=44100,asplit[voice][sc]")
fc.append(f"[{iM}:a]atrim=duration={TOTAL:.3f},volume=0.6,aformat=channel_layouts=stereo[mraw]")
fc.append("[sc]aformat=channel_layouts=stereo[sc2]")
fc.append("[mraw][sc2]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400:makeup=1[mduck]")
sfx=[(iImp,0.10,1.0),(iW,0.45,0.6),(iImp,0.55,0.8),(iW,1.05,0.4)]
for c in sorted(CH): sfx+= [(iW,chap_start[c]-0.25,0.7),(iImp,chap_start[c],0.9)]
sfx+=[(iR,BODY_END-1.5,0.5),(iImp,BODY_END,0.8)]
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
       '-c:a','aac','-b:a','192k','-movflags','+faststart','-t',f"{TOTAL:.3f}",D+'/final_v6.mp4']
if '--dry' in sys.argv: print(fcs[:3000]); sys.exit()
subprocess.run(args,check=True)
