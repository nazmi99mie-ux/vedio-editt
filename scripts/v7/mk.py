s=open('../v2/build.py').read()
s=s.replace("S=os.path.dirname(D); FD=S+'/fonts/'; V=S+'/src/video.mp4'","S=os.path.dirname(D); FD=S+'/fonts/'; V=S+'/vid2/src/video.mp4'")
a=s.index('SEG=['); b=s.index('# timeline')
s=s[:a]+open('data.py').read()+s[b:]
rep=[('lab="PERINGATAN KERAS"','lab="PENYAKIT HATI"'),
('ctext(205,"BAHAYA FAHAMAN",A(118)','ctext(205,"MENGUMPAT:",A(118)'),
('t2="SELAIN ISLAM"','t2="DOSA PALING SEDAP?"'),
('GOLD=(255,200,60,255); RED=(205,30,40,255)','GOLD=(222,184,92,255); RED=(0,110,72,255)'),
("'/f1140.png'","'/intro_bg.png'"),("'/f2480.png'","'/outro_bg.png'"),
("}3 FAHAMAN\",2)","}MENGUMPAT...\",2)"),
("}PALING BAHAYA\",2)","}DOSA PALING SEDAP!\",2)"),
("}UNTUK UMAT ISLAM HARI INI\",2)","}TAPI SOLAT TUHAN TAK TERIMA\",2)"),
("}KHAWARIJ  •  LIBERAL  •  SEKULAR\",2)","}MAKNA  •  SEDAP  •  AKIBAT  •  BILA BOLEH\",2)"),
("final_v2.mp4","final_v7.mp4"),("/v2.ass","/v7.ass"),("color=c=0xFFC83C","color=c=0xDEB85C")]
for x,y in rep:
    assert x in s, x
    s=s.replace(x,y)
def R(x,y):
    global s
    assert x in s, x
    s=s.replace(x,y)
R('\\\\fs240\\\\fscx260','\\\\fs170\\\\fscx260')
R('m 30 0 l 810 0 780 220 0 220','m 30 0 l 990 0 960 220 0 220'); R('\\\\pos(150,820)\\\\p1','\\\\pos(60,820)\\\\p1')
R('{\\\\pos(540,930)\\\\fs175','{\\\\pos(540,930)\\\\fs118')
s=s.replace("\\\\c&H281ECD&","\\\\c&H486E00&").replace("\\\\c&H3CC8FF&","\\\\c&H5CB8DE&")
R("names=[CH[i][1] for i in (1,2,3)]; xs=[230,540,850]","CK=sorted(CH); names=['MAKNA','SEDAP','AKIBAT','BILA BOLEH']; xs=[150,410,670,930]")
R("bounds=[chap_start[1],chap_start[2],chap_start[3],BODY_END]\nfor k in range(3):","bounds=[chap_start[c] for c in CK]+[BODY_END]\nfor k in range(len(CK)):")
R("    for j in range(3):","    for j in range(len(CK)):")
R("m 0 0 l 260 0 260 50 0 50","m 0 0 l 240 0 240 50 0 50"); R("{xs[j]-130},508","{xs[j]-120},508")
R("Style: Tab,Poppins ExtraBold,36,","Style: Tab,Poppins ExtraBold,30,")
R("flashes=[chap_start[c] for c in (1,2,3)]","flashes=[chap_start[c] for c in sorted(CH)]")
R("for c in (1,2,3): sfx+=","for c in sorted(CH): sfx+=")
R("Style: Sub,Anton,100,","Style: Sub,Anton,96,")
R("img.alpha_composite(g)\n","""img.alpha_composite(g)
img.alpha_composite(Image.open(D+'/islamic_bg.png').convert('RGBA'))
import math
def star8(cx,cy,r,fill):
    pts=[(cx+(r if k%2==0 else r*0.45)*math.cos(math.pi/8*k),cy+(r if k%2==0 else r*0.45)*math.sin(math.pi/8*k)) for k in range(16)]
    d.polygon(pts,fill=fill)
""")
R("d.rectangle([0,PY-6,W,PY-1],fill=GOLD); d.rectangle([0,PY+PH,W,PY+PH+5],fill=GOLD)",
 "d.rectangle([0,PY-6,W,PY-1],fill=GOLD); d.rectangle([0,PY+PH,W,PY+PH+5],fill=GOLD)\nstar8(540,PY-3,22,GOLD); star8(540,PY+PH+3,22,GOLD)\nfor cx in (60,1020):\n    star8(cx,PY-3,13,GOLD); star8(cx,PY+PH+3,13,GOLD)")
a=s.index("ev(o+0.15,TOTAL,'Ar'"); b=s.index("ass+=")
s=s[:a]+open('outro.py').read()+s[b:]
s=s.replace("&H0060C8FF,&H0060C8FF","&H005CB8DE,&H005CB8DE")
R("'-i',D+'/music.wav'","'-loop','1','-t',f\"{TOTAL:.3f}\",'-i',D+'/islamic_bg.png','-i',D+'/music.wav'")
R("iI,iO,iF,iM,iImp,iW,iR=n,n+1,n+2,n+3,n+4,n+5,n+6","iI,iO,iF,iP,iM,iImp,iW,iR=n,n+1,n+2,n+3,n+4,n+5,n+6,n+7")
R('fc.append(f"[{iF}:v]format=rgba[frm]")','fc.append(f"[{iF}:v]format=rgba[frm]"); fc.append(f"[{iP}:v]format=rgba[pat]")')
R("fc.append(f\"[base][frm]overlay=0:0:enable='between(t,{INTRO},{BODY_END})'[b1]\")",
 "fc.append(f\"[base][pat]overlay=0:0:enable='not(between(t,{INTRO},{BODY_END}))'[b0p]\"); fc.append(f\"[b0p][frm]overlay=0:0:enable='between(t,{INTRO},{BODY_END})'[b1]\")")
R("volume=0.55,aformat","volume=0.6,aformat")
s=s.replace('\\\\fs150\\\\fad(0,200)}}{title}','\\\\fs{150 if len(title)<=9 else (112 if len(title)<=13 else 92)}\\\\fad(0,200)}}{title}')
assert 'fc.append(f"[{i}:a]asetpts=PTS-STARTPTS,aresample=44100,afade=in:d=0.03,afade=out:st={dd-0.04:.3f}:d=0.04[a{i}]")' in s
s=s.replace('fc.append(f"[{i}:a]asetpts=PTS-STARTPTS,aresample=44100,afade=in:d=0.03,afade=out:st={dd-0.04:.3f}:d=0.04[a{i}]")','fi=0.06 if i==0 or abs(SEG[i-1][1]-s)>0.01 else 0.0\n    fo=0.06 if i==len(SEG)-1 or abs(SEG[i+1][0]-e)>0.01 else 0.0\n    af=",".join(x for x in ([f"afade=in:d={fi}"] if fi else [])+([f"afade=out:st={dd-fo:.3f}:d={fo}"] if fo else []))\n    fc.append(f"[{i}:a]asetpts=PTS-STARTPTS,aresample=44100"+(","+af if af else "")+f"[a{i}]")')
open('build.py','w').write(s)
