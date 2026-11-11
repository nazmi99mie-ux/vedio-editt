import subprocess, sys
SRC="dl/v.mp4"  # video asal (tidak disimpan dalam repo)
# (start,end, point_index or None, captions[(s,e,text)])  text uses {..} for highlight
CL=[
 (450.0,455.7,1,[(450.0,452.6,"Maka agama ni"),(452.6,455.7,"tidak boleh {dipisah} dengan kehidupan")]),
 (487.0,506.4,None,[(487.0,491.6,"Maka tak boleh pisah kehidupan kita dengan {agama}"),
   (491.6,494.6,"Siapa kata agama asing, kehidupan asing..."),
   (494.6,499.8,"{Kafir}, keluar dari Islam!"),
   (499.8,504.5,"Kalau kata agama hanya waktu {ibadat} sahaja..."),
   (504.5,506.4,"orang tu {SEKULAR}")]),
 (546.6,567.2,2,[(546.6,550.6,"Tapi oleh kerana ada orang {berkepentingan}"),
   (550.6,553.0,"untuk mendapatkan {dunia}"),
   (553.0,557.6,"maka dia buatlah ajaran macam ni, untunglah dia"),
   (557.6,560.2,"sebab benda ni {mudah}"),
   (560.2,563.1,"\"Kita nak agama ni di {masjid} sahaja\""),
   (563.1,567.2,"\"Keluar sini, jangan kira agama\"... senang lah!")]),
 (735.0,754.0,3,[(735.0,737.9,"Bukan kerana apa..."),
   (737.9,740.0,"kerana {jahilnya} kita orang Islam"),
   (740.0,743.3,"kita tak faham agama kita {sendiri}"),
   (743.3,744.6,"Sebab tu jangan hairan"),
   (744.6,747.5,"orang nama Islam, {IC Islam}"),
   (747.5,750.0,"dia paling kuat {menentang Islam}"),
   (750.0,751.9,"Jangan hairan. Kenapa?"),
   (751.9,754.0,"Dia tak faham agama dia {sendiri}")]),
 (818.9,846.1,4,[(818.9,823.0,"Ni yang jadi {jahil} kita, tak selesai-selesai"),
   (823.0,824.1,"Islam jadi {lemah}"),
   (824.1,828.4,"sebab kita faham agama secara {sempit}"),
   (828.4,831.2,"Bila faham macam tu..."),
   (831.2,836.6,"dia {lawan} sesama orang Islam, sama-sama kita"),
   (836.6,840.3,"Bukan orang {kafir}, orang kafir memang kafir dah"),
   (840.3,843.2,"Yang ada nama Islam, ada IC Islam"),
   (843.2,846.1,"{dia yang kuat lawan!}")]),
]
POINTS={1:("AGAMA TAK BOLEH","DIPISAH DARI KEHIDUPAN"),2:("ADA YANG","BERKEPENTINGAN DUNIA"),
        3:("JAHIL AGAMA","SENDIRI"),4:("FAHAM AGAMA SEMPIT,","UMAT JADI LEMAH")}
def ts(t):
  h=int(t//3600);m=int(t%3600//60);s=t%60
  return f"{h}:{m:02d}:{s:05.2f}"
YEL=r"{\c&H00D7FF&}"; WHT=r"{\c&HFFFFFF&}"
ass=["[Script Info]","ScriptType: v4.00+","PlayResX: 1080","PlayResY: 1920","WrapStyle: 0","",
"[V4+ Styles]","Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
"Style: Hook,Anton,118,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,2,0,1,9,6,5,60,60,0,1",
"Style: PNum,Anton,62,&H00000000,&H00000000,&H0000D7FF,&H00000000,0,0,0,0,100,100,4,0,3,14,0,8,0,0,0,1",
"Style: PTitle,Anton,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,7,5,8,40,40,0,1",
"Style: Sub,Poppins ExtraBold,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,1,7,4,8,70,70,0,1",
"Style: Tag,Poppins ExtraBold,34,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,3,0,3,10,0,2,0,0,0,1",
"","[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
def ev(s,e,style,txt,layer=0): ass.append(f"Dialogue: {layer},{ts(s)},{ts(e)},{style},,0,0,0,,{txt}")
sfx=[]  # (time, file, vol)
t=0.0; vparts=[]; 
for i,(a,b,p,caps) in enumerate(CL):
  off=t-a
  if i>0: sfx.append((t-0.25,"whoosh",0.55))
  if p:
    pe=t+(b-a)
    # continue point 1 through clip 2
    if p==1: pe=t+(b-a)+(CL[1][1]-CL[1][0])
    st=t+(3.6 if p==1 else 0.15)
    l1,l2=POINTS[p]
    ev(st,pe,"PNum",r"{\pos(540,150)\fad(150,150)\t(0,180,\fscx115\fscy115)\t(180,320,\fscx100\fscy100)}  POINT "+str(p)+"  ",1)
    ev(st+0.15,pe,"PTitle",r"{\fad(0,150)\move(-500,280,540,280,0,280)}"+YEL+l1,1)
    ev(st+0.35,pe,"PTitle",r"{\fad(0,150)\move(1600,400,540,400,0,280)}"+l2,1)
    sfx.append((st,"impact" if p==1 else "ding",0.7 if p==1 else 0.45))
    sfx.append((st+0.15,"whoosh",0.35))
  for (s,e,txt) in caps:
    s2=max(s,a)+off; e2=min(e,b)+off
    txt=txt.replace("{","\x01").replace("}","\x02").replace("\x01",YEL+r"{\fscx112\fscy112}").replace("\x02",WHT+r"{\fscx100\fscy100}")
    ev(s2,e2,"Sub",r"{\pos(540,1320)\fad(60,0)\frz-3\t(0,140,\frz0)}"+txt)
  vparts.append((a,b)); t+=b-a
T=t
# hook
ev(0,3.5,"Hook",r"{\pos(540,330)\fscx40\fscy40\t(0,180,\fscx110\fscy110)\t(180,300,\fscx100\fscy100)\fad(0,200)}KENAPA"+r"\N"+YEL+r"ORANG ISLAM"+WHT+r"\NLAWAN ISLAM?",2)
sfx.append((0.0,"impact",0.8))
# outro CTA
ev(T-4.5,T,"Hook",r"{\pos(540,1640)\fscx40\fscy40\t(0,180,\fscx105\fscy105)\t(180,300,\fscx100\fscy100)\fs80}"+r"FAHAMI AGAMA"+r"\N"+YEL+"SEBAGAI CARA HIDUP",2)
sfx.append((T-4.5,"impact",0.6))
ev(0,T,"Tag",r"{\pos(540,1880)\alpha&H40&}  KULIAH KITAB  ",0)
open("subs.ass","w").write("\n".join(ass)+"\n")
# ffmpeg graph
f=[]; n=len(vparts)
for k,(a,b) in enumerate(vparts):
  f.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=30[v{k}]")
  f.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.05,afade=t=out:st={b-a-0.06:.2f}:d=0.06[a{k}]")
f.append("".join(f"[v{k}][a{k}]" for k in range(n))+f"concat=n={n}:v=1:a=1[cv][ca]")
f.append("[cv]split[c1][c2]")
f.append("[c1]scale=-2:1920,crop=1080:1920,boxblur=25:2,eq=brightness=-0.18:saturation=1.2[bg]")
f.append("[c2]scale=1080:608,setsar=1[fg]")
f.append("[bg][fg]overlay=0:656,drawbox=x=0:y=652:w=1080:h=4:color=0xFFD700@1:t=fill,drawbox=x=0:y=1264:w=1080:h=4:color=0xFFD700@1:t=fill,subtitles=subs.ass:fontsdir=fonts,format=yuv420p[vout]")
f.append("[ca]highpass=f=70,acompressor=threshold=-20dB:ratio=3:makeup=4,loudnorm=I=-15:TP=-1.5[sp]")
inputs=["-i",SRC]; mix=["[sp]"]
for j,(tt,name,vol) in enumerate(sfx):
  inputs+=["-i",f"sfx/{name}.wav"]; d=int(max(tt,0)*1000)
  f.append(f"[{j+1}:a]volume={vol},adelay={d}|{d}[s{j}]"); mix.append(f"[s{j}]")
f.append("".join(mix)+f"amix=inputs={len(mix)}:normalize=0:duration=first,alimiter=limit=0.95[aout]")
cmd=["ffmpeg","-v","error","-y"]+inputs+["-filter_complex",";".join(f),"-map","[vout]","-map","[aout]",
 "-c:v","libx264","-preset","medium","-crf","20","-c:a","aac","-b:a","192k","-movflags","+faststart","point_lawan_islam.mp4"]
print("duration",T)
subprocess.run(cmd,check=True)
