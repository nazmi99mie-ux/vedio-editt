import os, sys, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D=os.path.dirname(os.path.abspath(__file__)); S=os.path.dirname(D); FD=S+'/fonts/'; V=S+'/src/video.mp4'
W,H=1080,1920; PY=570; PW,PH=1080,810          # video panel
INTRO=2.6; OUTRO=4.2
# ------------------------------------------------------------------ segments
# (src_start, src_end, chapter, shot, face_cx)
SEG=[(1136.60,1148.95,1,'w',340),(1150.50,1154.10,1,'c',340),(1156.05,1160.75,1,'w',340),
     (1198.60,1209.25,1,'w',340),(1209.25,1212.90,1,'c',340),
     (2288.45,2292.60,2,'w',420),(2294.15,2296.85,2,'w',420),(2296.85,2300.95,2,'c',420),
     (2331.95,2333.95,2,'c',420),(2454.55,2455.95,2,'w',420),(2456.75,2461.15,2,'c',420),
     (2472.75,2474.90,3,'w',440),(2475.95,2480.50,3,'w',440),(2480.50,2486.20,3,'c',440),
     (2506.60,2512.35,3,'c',440),(2512.35,2516.95,3,'w',440),(2533.85,2537.15,3,'w',440),(2537.15,2542.30,3,'c',440)]
Y='{\\c&H00D7FF&}'; R='{\\c&H3C3CFF&}'; N='{\\r}'
SUB=[(1136.70,1138.80,"TIDAK BOLEH MENUMPAHKAN DARAH"),(1138.85,1140.80,f"SESAMA {Y}AHLI KIBLAT{N}"),
 (1140.85,1142.10,"YANG TUMPAH DARAH"),(1142.10,1144.10,"KITA TENGOK DALAM TV, TIKTOK"),
 (1144.10,1146.40,"KADANG-KADANG DI LUAR NEGARA"),(1146.40,1148.10,"BUKAN PEGANGAN AHLI SUNNAH WAL JAMAAH"),
 (1148.10,1148.95,f"ITU {R}KHAWARIJ{N}"),(1150.60,1152.70,f"SATU PUAK YANG {R}MENGHALALKAN{N}"),
 (1152.70,1154.10,f"{R}DARAH{N} SESAMA ISLAM"),(1156.10,1158.00,f"BUAT DOSA BESAR — {R}KAFIR{N}"),
 (1158.60,1160.00,f"MINUM ARAK — {R}KAFIR{N}"),(1160.00,1160.75,f"HUKUMNYA {R}BUNUH{N}"),
 (1198.70,1200.75,"JANGAN HAIRAN — PAKAI SERBAN, JUBAH, JANGGUT"),(1200.75,1203.95,"KATA PERANG FISABILILLAH DI LUAR NEGARA"),
 (1204.10,1206.60,f"{R}SEMBELIH{N} TENGKUK SESAMA ISLAM"),(1206.70,1209.25,"BUDAK-BUDAK, PEREMPUAN — TAK KIRA"),
 (1209.30,1211.55,f"DIPUJI {Y}\"FISABILILLAH\"{N}"),(1211.55,1212.90,f"PADAHAL DIA {R}KHAWARIJ{N}"),
 (2288.50,2292.60,f"KALAU UNDANG-UNDANG BERTUKAR {Y}MACAM INDONESIA{N}"),(2294.20,2296.80,"SEORANG KAFIR, SEORANG ISLAM — KAHWIN"),
 (2296.90,2298.00,f"{Y}SAH TAK?{N}"),(2298.00,2299.30,f"JAWAPANNYA: {R}TAK SAH{N}"),
 (2299.35,2300.95,"TAK PAYAH TANYA MUFTI!"),(2332.00,2333.00,"KALAU DUA-DUA LELAKI"),
 (2333.00,2333.95,f"{R}TAK BOLEH NIKAH{N}"),(2454.60,2455.95,f"JANGAN ADA HUKUM KATA {R}BOLEH{N}"),
 (2456.80,2458.90,"BILA BERTEMBUNG HUKUM DENGAN AL-QURAN"),(2459.90,2461.15,f"KENA {Y}IKUT AL-QURAN{N}"),
 (2472.80,2474.90,f"CONTOHNYA {Y}AZERBAIJAN{N}"),(2476.00,2478.70,f"ISLAM SEMUA — {Y}97 PERATUS{N}"),
 (2478.70,2480.50,"LEBIH RAMAI DARI MALAYSIA"),(2480.50,2483.05,"TAPI ISLAM ZAHIR SAHAJA"),
 (2483.05,2485.10,f"AKIDAH DIA {R}SEKULAR{N}"),(2485.10,2486.20,"TAK BOLEH KATA APA"),
 (2506.65,2508.45,f"PENTING KITA {Y}PEGANG KUASA{N}"),(2508.45,2512.35,"SUPAYA BOLEH LAKSANA APA YANG ALLAH TETAPKAN DALAM AL-QURAN"),(2512.40,2514.15,"KALAU KITA TAK PEGANG"),(2514.15,2515.50,f"ORANG {R}SEKULAR{N} AKAN PEGANG"),
 (2515.50,2516.95,"JADI MACAM AZERBAIJAN"),(2533.90,2536.10,f"KALAU TAK ADA {Y}KUASA{N} — JADI MACAM AZERBAIJAN"),
 (2536.10,2537.20,"KUASA DI TANGAN ORANG LAIN"),(2537.20,2538.85,"PARLIMEN DI TANGAN ORANG LAIN"),
 (2538.85,2541.00,"KEMENTERIAN DI TANGAN ORANG LAIN"),(2541.00,2542.30,f"ISLAM KITA {R}TERPAKSA IKUT{N}")]
CH={1:("01","KHAWARIJ","Ekstremis yang halalkan darah sesama Muslim"),
    2:("02","LIBERAL","Menghalalkan apa yang Allah haramkan"),
    3:("03","SEKULAR","Memisahkan agama daripada kuasa")}
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
GOLD=(255,200,60,255); RED=(205,30,40,255)
def ctext(y,txt,font,fill,x=None):
    bb=d.textbbox((0,0),txt,font=font); w=bb[2]-bb[0]
    xx=(W-w)//2-bb[0] if x is None else x
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).text((xx,y+5),txt,font=font,fill=(0,0,0,220))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7))); d.text((xx,y),txt,font=font,fill=fill); return bb
A=lambda s:ImageFont.truetype(FD+'Anton.ttf',s)
P=lambda s:ImageFont.truetype(FD+'Poppins-ExtraBold.ttf',s)
# label
lab="PERINGATAN KERAS"; lf=P(28); bb=d.textbbox((0,0),lab,font=lf); pw=bb[2]-bb[0]+50
d.rounded_rectangle([(W-pw)//2,150,(W+pw)//2,198],radius=24,outline=GOLD,width=3)
ctext(155,lab,lf,GOLD)
ctext(205,"BAHAYA FAHAMAN",A(118),(255,255,255,255))
# red slanted box with SELAIN ISLAM
t2="SELAIN ISLAM"; f2=A(104); bb=d.textbbox((0,0),t2,font=f2); tw=bb[2]-bb[0]
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
Style: Ar,Amiri,84,&H0060C8FF,&H0060C8FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,3,3,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
E=[]
def ev(a,b,style,text,layer=0): E.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{text}")
def rect(x,y,w,h): return f"m 0 0 l {w} 0 {w} {h} 0 {h}"
# --- HOOK
ev(0,INTRO,'Box',"{\\pos(0,0)\\p1\\c&H0A0806&\\alpha&H50&}"+rect(0,0,W,H)+"{\\p0}",0)
ev(0.10,INTRO,'Big',"{\\pos(540,680)\\fs240\\fscx260\\fscy260\\alpha&HFF&\\t(0,140,\\fscx100\\fscy100\\alpha&H00&)\\fad(0,150)}3 FAHAMAN",2)
ev(0.55,INTRO,'Box',"{\\pos(150,820)\\p1\\c&H281ECD&\\clip(0,0,0,1920)\\t(0,180,\\clip(0,0,1080,1920))\\fad(0,150)}m 30 0 l 810 0 780 220 0 220{\\p0}",1)
ev(0.55,INTRO,'Big',"{\\pos(540,930)\\fs175\\alpha&HFF&\\t(80,200,\\alpha&H00&)\\fad(0,150)}PALING BAHAYA",2)
ev(1.10,INTRO,'Pop',"{\\pos(540,1130)\\fs72\\alpha&HFF&\\t(0,200,\\alpha&H00&)\\fad(0,150)}UNTUK UMAT ISLAM HARI INI",2)
ev(1.55,INTRO,'Pop',"{\\pos(540,1250)\\c&H00D7FF&\\fs56\\alpha&HFF&\\t(0,200,\\alpha&H00&)\\fad(0,150)}KHAWARIJ  •  LIBERAL  •  SEKULAR",2)
# --- tabs (chapter indicator) under header
names=[CH[i][1] for i in (1,2,3)]; xs=[230,540,850]
bounds=[chap_start[1],chap_start[2],chap_start[3],BODY_END]
for k in range(3):
    a,b=bounds[k],bounds[k+1]
    for j in range(3):
        if j==k:
            ev(a,b,'Box',f"{{\\pos({xs[j]-130},508)\\p1\\c&H3CC8FF&}}m 0 0 l 260 0 260 50 0 50{{\\p0}}",1)
            ev(a,b,'Tab',f"{{\\pos({xs[j]},533)\\c&H0A0A0A&}}{names[j]}",2)
        else:
            ev(a,b,'Tab',f"{{\\pos({xs[j]},533)\\alpha&H70&}}{names[j]}",2)
# --- chapter cards
for c,(num,title,desc) in CH.items():
    a=chap_start[c]; b=a+2.1; cy=PY+PH//2
    ev(a,b,'Box',f"{{\\pos(0,{cy-170})\\p1\\c&H0A0806&\\alpha&H30&\\fad(80,200)}}"+rect(0,0,W,340)+"{\\p0}",3)
    ev(a,b,'Box',f"{{\\pos(0,{cy-170})\\p1\\c&H281ECD&\\fad(80,200)\\clip(0,0,0,1920)\\t(0,220,\\clip(0,0,1080,1920))}}"+rect(0,0,W,10)+"{\\p0}",4)
    ev(a,b,'Box',f"{{\\pos(0,{cy+160})\\p1\\c&H281ECD&\\fad(80,200)\\clip(1080,0,1080,1920)\\t(0,220,\\clip(0,0,1080,1920))}}"+rect(0,0,W,10)+"{\\p0}",4)
    ev(a,b,'Big',f"{{\\an6\\move(-200,{cy-20},330,{cy-20},0,180)\\c&H3CC8FF&\\fs230\\fad(0,200)}}{num}",5)
    ev(a+0.08,b,'Big',f"{{\\an4\\move(1200,{cy-50},370,{cy-50},0,200)\\fs150\\fad(0,200)}}{title}",5)
    ev(a+0.25,b,'Pop',f"{{\\an4\\pos(375,{cy+70})\\fs40\\alpha&HFF&\\t(0,200,\\alpha&H00&)\\fad(0,200)}}{desc}",5)
# --- subtitles
SUBY=1540
for a,b,txt in SUB:
    oa,ob=out_t(a),out_t(b)
    ev(oa,ob,'Sub',f"{{\\q0\\pos(540,{SUBY})\\fscx70\\fscy70\\t(0,90,\\fscx108\\fscy108)\\t(90,170,\\fscx100\\fscy100)}}{txt}",6)
# --- outro
o=BODY_END
ev(o,TOTAL,'Box',"{\\pos(0,0)\\p1\\c&H0A0806&\\alpha&H40&\\fad(250,0)}"+rect(0,0,W,H)+"{\\p0}",7)
ev(o+0.15,TOTAL,'Ar',"{\\pos(540,600)\\fs200\\fad(300,300)\\blur1}يَا أَيُّهَا الَّذِينَ آمَنُوا",8)
ev(o+0.35,TOTAL,'Ar',"{\\pos(540,820)\\fs215\\fad(300,300)\\blur1}ادْخُلُوا فِي السِّلْمِ كَافَّةً",8)
ev(o+0.7,TOTAL,'Pop',"{\\pos(540,1060)\\fs70\\fad(300,300)}\"Wahai orang-orang yang beriman,",8)
ev(o+0.7,TOTAL,'Pop',"{\\pos(540,1150)\\fs70\\fad(300,300)}masuklah ke dalam Islam",8)
ev(o+0.7,TOTAL,'Pop',"{\\pos(540,1240)\\fs70\\fad(300,300)\\c&H00D7FF&}secara keseluruhan.\"",8)
ev(o+1.0,TOTAL,'Tab',"{\\pos(540,1370)\\fs56\\c&H3CC8FF&\\fad(300,300)}SURAH AL-BAQARAH : 208",8)
ass+="\n".join(E)+"\n"
open(D+'/v2.ass','w').write(ass)
# ------------------------------------------------------------------ ffmpeg
args=['ffmpeg','-v','error','-stats','-y']
for s,e,*_ in SEG: args+=['-ss',f"{s:.3f}",'-t',f"{e-s:.3f}",'-i',V]
n=len(SEG)
args+=['-loop','1','-t',f"{INTRO}",'-i',D+'/f1140.png','-loop','1','-t',f"{OUTRO}",'-i',D+'/f2480.png',
       '-loop','1','-t',f"{TOTAL:.3f}",'-i',D+'/frame.png',
       '-i',D+'/music.wav','-i',D+'/impact.wav','-i',D+'/whoosh.wav','-i',D+'/riser.wav']
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
fc.append(f"color=c=0xFFC83C:s=960x12:r=30,format=rgba[bar]")
fc.append(f"[b1][bar]overlay=x='60-960+960*(t-{INTRO})/{BODY_END-INTRO:.3f}':y=1838:enable='between(t,{INTRO},{BODY_END})':shortest=0[b1b]")
fc.append(f"[b1b]crop=1080:1920:0:0,ass={D}/v2.ass:fontsdir={FD},{fl},fade=in:st=0:d=0.25,fade=out:st={TOTAL-0.5:.3f}:d=0.5,format=yuv420p[vout]")
# audio
fc.append("[voiceraw]highpass=f=80,lowpass=f=12000,acompressor=threshold=-22dB:ratio=3.5:attack=5:release=120:makeup=5,loudnorm=I=-14:TP=-1.5:LRA=8,aresample=44100,asplit[voice][sc]")
fc.append(f"[{iM}:a]atrim=duration={TOTAL:.3f},volume=0.55,aformat=channel_layouts=stereo[mraw]")
fc.append("[sc]aformat=channel_layouts=stereo[sc2]")
fc.append("[mraw][sc2]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400:makeup=1[mduck]")
sfx=[(iImp,0.10,1.0),(iW,0.45,0.6),(iImp,0.55,0.8),(iW,1.05,0.4)]
for c in (1,2,3): sfx+= [(iW,chap_start[c]-0.25,0.7),(iImp,chap_start[c],0.9)]
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
       '-c:a','aac','-b:a','192k','-movflags','+faststart','-t',f"{TOTAL:.3f}",D+'/final_v2.mp4']
if '--dry' in sys.argv: print(fcs[:3000]); sys.exit()
subprocess.run(args,check=True)
