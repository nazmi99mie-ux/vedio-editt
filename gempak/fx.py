# Generic "gempak" short-video builder. Usage: python3 fx.py spec.py
import subprocess, sys, os, math
spec={}; exec(open(sys.argv[1]).read(), spec)
SRC=spec["SRC"]; CL=spec["CL"]; POINTS=spec["POINTS"]; HOOK=spec["HOOK"]; OUTRO=spec["OUTRO"]; OUT=spec["OUT"]
TAG=spec.get("TAG","KULIAH KITAB")
XF=0.45; FPS=30
TRANS=["slideleft","zoomin","circleopen","slideup","fadewhite","smoothright","radial"]
os.makedirs("work",exist_ok=True)
def run(c): subprocess.run(c,check=True)
# ---------- 1. render each clip vertical with zoom effects ----------
lens=[]
for k,c in enumerate(CL):
    a,b=c["s"],c["e"]; d=b-a; lens.append(d)
    punches=c.get("punch",[])  # absolute src times
    zp="+".join([f"0.16*exp(-(it-{p-a:.2f})*5)*gte(it,{p-a:.2f})" for p in punches]) or "0"
    sh="+".join([f"18*sin(it*70)*exp(-(it-{p-a:.2f})*7)*gte(it,{p-a:.2f})" for p in punches]) or "0"
    # zoom: entry zoom-out 1.25->1 over .6s, slow kenburns, punches
    z=f"(1+0.25*exp(-it*7)+0.05*it/{d:.2f}+{zp})".replace("it","(on/{0})".format(FPS))
    shx=sh.replace("it","(on/{0})".format(FPS))
    fg=(f"scale=2160:1216,zoompan=z='{z}':x='iw/2-iw/zoom/2+({shx})':y='ih/2-ih/zoom/2':d=1:s=1080x608:fps={FPS}")
    bgz=f"(1+0.06*on/({d*FPS:.0f}))"
    vf=(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,fps={FPS},split[x][y];"
        f"[x]scale=-2:1920,crop=1080:1920,boxblur=28:2,eq=brightness=-0.22:saturation=1.3[bg];"
        f"[y]{fg},setsar=1[fg];"
        f"[bg][fg]overlay=0:656,format=yuv420p[v];"
        f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.04,afade=t=out:st={d-0.05:.2f}:d=0.05[a]")
    run(["ffmpeg","-v","error","-y","-i",SRC,"-filter_complex",vf,"-map","[v]","-map","[a]",
         "-c:v","libx264","-preset","veryfast","-crf","16","-c:a","pcm_s16le",f"work/c{k}.mkv"])
# ---------- 2. join with transitions ----------
starts=[0.0]
for k in range(1,len(CL)): starts.append(starts[-1]+lens[k-1]-XF)
T=starts[-1]+lens[-1]
inp=[];fc=[]
for k in range(len(CL)): inp+=["-i",f"work/c{k}.mkv"]
pv="[0:v]";pa="[0:a]"
for k in range(1,len(CL)):
    tr=TRANS[(k-1)%len(TRANS)]
    fc.append(f"{pv}[{k}:v]xfade=transition={tr}:duration={XF}:offset={starts[k]:.3f}[v{k}]")
    fc.append(f"{pa}[{k}:a]acrossfade=d={XF}[a{k}]")
    pv=f"[v{k}]";pa=f"[a{k}]"
# ---------- 3. captions (ASS) ----------
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
YEL=r"{\c&H00D7FF&}"; WHT=r"{\c&HFFFFFF&}"; RED=r"{\c&H3C3CFF&}"
A=["[Script Info]","ScriptType: v4.00+","PlayResX: 1080","PlayResY: 1920","WrapStyle: 0","",
"[V4+ Styles]","Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
"Style: Hook,Anton,124,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,2,0,1,10,7,5,50,50,0,1",
"Style: PNum,Anton,60,&H00FFFFFF,&H00FFFFFF,&H003C3CE6,&H00000000,0,0,0,0,100,100,5,0,3,16,0,8,0,0,0,1",
"Style: PTitle,Anton,98,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,8,6,8,40,40,0,1",
"Style: Sub,Poppins ExtraBold,82,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,1,8,5,8,60,60,0,1",
"Style: Tag,Poppins ExtraBold,34,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,3,0,3,10,0,2,0,0,0,1",
"","[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
def hl(x): return x.replace("{","\x01").replace("}","\x02").replace("\x01",YEL).replace("\x02",WHT)
def ev(s,e,st,tx,l=0): A.append(f"Dialogue: {l},{ts(max(0,s))},{ts(e)},{st},,0,0,0,,{tx}")
SFX=[]
def sfx(t,n,v): SFX.append((max(0,t),n,v))
# hook
hs=HOOK["lines"]
ev(0,HOOK["dur"],"Hook",r"{\pos(540,330)\fscx30\fscy30\t(0,160,\fscx115\fscy115)\t(160,300,\fscx100\fscy100)\fad(0,200)}"+hl(r"\N".join(hs)),3)
sfx(0,"braam",0.9); sfx(0,"subdrop",0.8)
point_end={}
for k,c in enumerate(CL):
    st0=starts[k]; a=c["s"]; off=st0-a
    if k>0:
        sfx(st0-0.3,"swoosh",0.7); sfx(st0-1.6,"riser",0.35) if c.get("point") else None
    p=c.get("point")
    if p:
        # point lasts until next point starts
        nxt=[starts[j] for j in range(k+1,len(CL)) if CL[j].get("point")]
        pe=(nxt[0] if nxt else T)
        ps=st0+(HOOK["dur"]+0.1 if k==0 else 0.2)
        l1,l2=POINTS[p]
        ev(ps,pe,"PNum",r"{\pos(540,140)\fad(120,120)\fscx0\t(0,200,\fscx100)}  POINT "+str(p)+"  ",2)
        ev(ps+0.12,pe,"PTitle",r"{\fad(0,120)\frz8\move(-500,265,540,265,0,260)\t(0,260,\frz0)}"+YEL+l1,2)
        ev(ps+0.30,pe,"PTitle",r"{\fad(0,120)\frz-8\move(1600,390,540,390,0,260)\t(0,260,\frz0)}"+l2,2)
        sfx(ps,"hit",0.8); sfx(ps,"impact",0.5); sfx(ps+0.12,"whoosh",0.4); sfx(ps+0.3,"whoosh",0.35)
    for (s,e,tx) in c["caps"]:
        s2=max(s,a)+off; e2=min(e,c["e"])+off
        if k+1<len(CL): e2=min(e2,starts[k+1]+0.05)
        if e2<=s2: continue
        tx=tx.replace("{","\x01").replace("}","\x02").replace("[","\x03").replace("]","\x04")
        tx=(tx.replace("\x01",YEL+r"{\fscx115\fscy115}").replace("\x02",WHT+r"{\fscx100\fscy100}")
              .replace("\x03",RED+r"{\fscx120\fscy120}").replace("\x04",WHT+r"{\fscx100\fscy100}"))
        ev(s2,e2,"Sub",r"{\pos(540,1310)\fscx85\fscy85\t(0,90,\fscx106\fscy106)\t(90,170,\fscx100\fscy100)}"+tx)
    for p_ in c.get("punch",[]):
        sfx(p_+off,"hit",0.55); sfx(p_+off,"click",0.4)
# outro
ev(T-OUTRO["dur"],T,"Hook",r"{\pos(540,1650)\fs84\fscx30\fscy30\t(0,160,\fscx110\fscy110)\t(160,280,\fscx100\fscy100)}"+hl(r"\N".join(OUTRO["lines"])),3)
sfx(T-OUTRO["dur"]-1.6,"riser",0.4); sfx(T-OUTRO["dur"],"braam",0.8); sfx(T-OUTRO["dur"],"revcym",0.0)
ev(0,T,"Tag",r"{\pos(540,1885)\alpha&H40&}  "+TAG+"  ",0)
open("work/subs.ass","w").write("\n".join(A)+"\n")
# ---------- 4. final: overlays, progress bar, flash, audio mix ----------
flashes=[s for s in starts[1:]]
fl="+".join([f"between(t,{s-0.05:.2f},{s+0.12:.2f})" for s in flashes]) or "0"
fc.append(f"{pv}drawbox=x=0:y=652:w=1080:h=4:color=0xFFD700@1:t=fill,drawbox=x=0:y=1264:w=1080:h=4:color=0xFFD700@1:t=fill,"
          f"drawbox=x=0:y=1906:w='1080*t/{T:.2f}':h=14:color=0xFFD700@1:t=fill,"
          f"subtitles=work/subs.ass:fontsdir=fonts,format=yuv420p[vout]")
fc.append(f"{pa}highpass=f=70,acompressor=threshold=-20dB:ratio=3:makeup=4,loudnorm=I=-14:TP=-1.5,asplit[sp][key]")
n=len(CL)
inp+=["-stream_loop","-1","-i","sfx/music.wav"]; mi=n
fc.append(f"[{mi}:a]atrim=0:{T:.2f},volume=0.55,afade=t=out:st={T-2:.2f}:d=2[mraw]")
fc.append("[mraw][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[mduck]")
mix=["[sp]","[mduck]"]
SFX=[x for x in SFX if x[2]>0]
for j,(t,nm,v) in enumerate(SFX):
    inp+=["-i",f"sfx/{nm}.wav"]; d=int(t*1000)
    fc.append(f"[{mi+1+j}:a]volume={v},adelay={d}|{d}[s{j}]"); mix.append(f"[s{j}]")
fc.append("".join(mix)+f"amix=inputs={len(mix)}:normalize=0:duration=first,alimiter=limit=0.89[aout]")
run(["ffmpeg","-v","error","-y"]+inp+["-filter_complex",";".join(fc),"-map","[vout]","-map","[aout]",
     "-c:v","libx264","-preset","medium","-crf","20","-c:a","aac","-b:a","192k","-movflags","+faststart",OUT])
print("duration",T)
