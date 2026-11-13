# Cinematic full-bleed style builder.  python3 fx3.py spec.py
import subprocess, sys, os, re
from track import track
spec={}; exec(open(sys.argv[1]).read(), spec)
SRC=spec["SRC"]; SEQ=spec["SEQ"]; OUT=spec["OUT"]; MUSIC=spec.get("MUSIC","sfx3/music.wav")
FPS=30; W,H=1080,1920
os.makedirs("w3",exist_ok=True)
def run(c): subprocess.run(c,check=True)
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
YEL="&H0000E1FF&"; RED="&H3333FF&"; GOLD="&H5AC8F0&"
HDR=["[Script Info]","ScriptType: v4.00+",f"PlayResX: {W}",f"PlayResY: {H}","WrapStyle: 2","",
"[V4+ Styles]","Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
f"Style: Cap,Bebas Neue,150,{YEL},&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,3,0,1,7,6,5,40,40,0,1",
f"Style: Pill,Oswald,50,&H00FFFFFF,&H00FFFFFF,&HB4000000,&H00000000,1,0,0,0,100,100,4,0,3,18,0,8,0,0,0,1",
f"Style: Num,Oswald,58,{GOLD},{GOLD},&H00000000,&H00000000,1,0,0,0,100,100,22,0,1,0,0,5,0,0,0,1",
f"Style: Title,Cinzel,128,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,4,0,1,0,0,5,60,60,0,1",
f"Style: Small,Oswald,40,&H00B4B4B4,&H00B4B4B4,&H00000000,&H00000000,0,0,0,0,100,100,10,0,1,0,0,5,0,0,0,1",
"","[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
def typed(text,t0,cps=22):
    out=[];i=0
    for ch in text:
        if ch=="\\": out.append(ch); continue
        a=int(t0*1000+i*1000/cps); out.append(r"{\alpha&HFF&\t(%d,%d,\alpha&H00&)}"%(a,a+1)+ch); i+=1
    return "".join(out), i/cps
def lerp_expr(kf):
    if len(kf)==1: return str(kf[0][1])
    e=str(kf[-1][1])
    for (t0,x0),(t1,x1) in reversed(list(zip(kf[:-1],kf[1:]))):
        e=f"if(lt(t,{t1}),{x0}+({x1}-{x0})*(t-{t0})/{max(t1-t0,0.01)},{e})"
    return f"if(lt(t,{kf[0][0]}),{kf[0][1]},{e})"
segs=[]; T=0.0; SFX=[]; EV=[]; speech_windows=[]
def sfx(t,n,v): SFX.append((max(0,t),n,v))
for k,it in enumerate(SEQ):
    fn=f"w3/s{k}.mkv"; ass=[]
    if it["type"]=="card":
        d=it["dur"]
        y0=it.get("y",960)
        if it.get("num"):
            ass.append(f"Dialogue: 1,{ts(0)},{ts(d)},Num,,0,0,0,,"+r"{\pos(540,%d)\fad(150,200)\fscx60\t(0,300,\fscx100)}"%(y0-170)+it["num"])
            ass.append(f"Dialogue: 1,{ts(0.1)},{ts(d)},Num,,0,0,0,,"+r"{\pos(540,%d)\fad(0,200)\p1\fscx0\t(0,400,\fscx100)}m 0 0 l 520 0 l 520 5 l 0 5"%(y0-110))
        txt=it["title"]; col=it.get("color","&HFFFFFF&")
        body,tdur=typed(txt,0.25,it.get("cps",30))
        ass.append(f"Dialogue: 1,{ts(0)},{ts(d)},Title,,0,0,0,,"+r"{\pos(540,%d)\c%s\fad(0,200)}"%(y0+30,col)+body)
        if it.get("sub"):
            ass.append(f"Dialogue: 1,{ts(0.25+tdur)},{ts(d)},Small,,0,0,0,,"+r"{\pos(540,%d)\fad(250,200)}"%(y0+260)+it["sub"])
        if it.get("sub2"):
            b2,_=typed(it["sub2"],0.25+tdur+0.3,it.get("cps",30))
            ass.append(f"Dialogue: 1,{ts(0)},{ts(d)},Title,,0,0,0,,"+r"{\pos(540,%d)\c%s\fad(0,200)}"%(y0+170,it.get("color2",RED))+b2)
        open(f"w3/s{k}.ass","w").write("\n".join(HDR+ass)+"\n")
        run(["ffmpeg","-v","error","-y","-f","lavfi","-i",f"color=c=0x07080b:s={W}x{H}:r={FPS}:d={d}",
             "-f","lavfi","-i",f"anullsrc=r=48000:cl=stereo","-t",str(d),
             "-filter_complex",f"[0:v]noise=alls=14:allf=t,vignette=PI/3.2,subtitles=w3/s{k}.ass:fontsdir=fonts,format=yuv420p[v]",
             "-map","[v]","-map","1:a","-c:v","libx264","-preset","veryfast","-crf","16","-c:a","pcm_s16le","-ar","48000",fn])
        sfx(T,it.get("sfx","boom"),0.8)
        nchar=len(txt)+len(it.get("sub2",""))
        for i in range(0,nchar,2): sfx(T+0.25+i/it.get("cps",30),"type",0.35)
        sfx(T,"glitch",0.5)
    else:
        a,b=it["s"],it["e"]; d=b-a
        kf=track(SRC,a,b); xe=lerp_expr(kf)
        P=[p-a for p in it.get("punch",[])]
        zp="+".join([f"0.13*exp(-(T-{p:.2f})*4)*gte(T,{p:.2f})" for p in P]) or "0"
        shk="+".join([f"22*sin(T*75)*exp(-(T-{p:.2f})*7)*gte(T,{p:.2f})" for p in P]) or "0"
        z=f"(1.0+0.06*T/{d:.2f}+{zp})"
        z=z.replace("T",f"(on/{FPS})"); shk=shk.replace("T",f"(on/{FPS})")
        bw="+".join([f"between(t,{p:.2f},{p+0.9:.2f})" for p in P]) or "0"
        gl="between(t,0,0.18)"+"".join([f"+between(t,{p:.2f},{p+0.12:.2f})" for p in P])
        vf=(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,fps={FPS},crop=243:432:x='{xe}':y=0,"
            f"scale={W}:{H}:flags=lanczos,unsharp=5:5:1.0,"
            f"zoompan=z='{z}':x='iw/2-iw/zoom/2+({shk})':y='ih/2-ih/zoom/2-500*(zoom-1)':d=1:s={W}x{H}:fps={FPS},"
            f"eq=contrast=1.12:saturation=1.05:brightness=-0.02,"
            f"colorbalance=rs=-0.06:gs=0.0:bs=0.07:rh=0.07:gh=0.02:bh=-0.07,"
            f"hue=s='if({bw},0,1)',vignette=PI/4.2,noise=alls=9:allf=t,"
            f"rgbashift=rh=-14:bh=14:enable='{gl}',"
            f"format=yuv420p[v];"
            f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,aresample=48000,afade=t=in:d=0.03,afade=t=out:st={d-0.05:.2f}:d=0.05[a]")
        # captions: word-by-word chunks
        ass.append(f"Dialogue: 2,{ts(0)},{ts(d)},Pill,,0,0,0,,"+r"{\pos(540,150)\fad(200,0)}  "+it["pill"]+"  ")
        for (s,e,tx) in it["caps"]:
            s=max(s,a)-a; e=min(e,b)-a
            if e<=s: continue
            words=[]
            for m in re.finditer(r"\[[^\]]+\]|\{[^}]+\}|\S+",tx):
                w=m.group(0)
                if w[0] in "[{": 
                    for j,ww in enumerate(w[1:-1].split()): words.append((ww,w[0]))
                else: words.append((w,""))
            L=sum(len(w)+2 for w,_ in words); t=s; timed=[]
            for w,kind in words:
                dd=(e-s)*(len(w)+2)/L; timed.append((t,t+dd,w,kind)); t+=dd
            # chunk into <=3 words, break after punctuation
            chunks=[];cur=[]
            for x in timed:
                cur.append(x)
                if len(cur)==3 or x[2][-1] in ",.?!" or len(" ".join(c[2] for c in cur))>14:
                    chunks.append(cur);cur=[]
            if cur: chunks.append(cur)
            for ch in chunks:
                cs,ce=ch[0][0],ch[-1][1]
                parts=[]
                for (ws,we,w,kind) in ch:
                    kc=int((we-ws)*100)
                    if kind=="[": parts.append(r"{\k%d\1c%s\3c&HFFFFFF&\bord0\fscx118\fscy118\1c%s}"%(kc,RED,RED)+w.upper()+r"{\fscx100\fscy100\bord7\3c&H000000&\1c%s}"%YEL)
                    elif kind=="{": parts.append(r"{\k%d\2c&H0000E1FF&}"%kc+w.upper()+r"{\2c&H00FFFFFF&}")
                    else: parts.append(r"{\k%d}"%kc+w.upper())
                ass.append(f"Dialogue: 3,{ts(cs)},{ts(ce)},Cap,,0,0,0,,"+r"{\pos(540,1430)\fscx80\fscy80\t(0,80,\fscx104\fscy104)\t(80,150,\fscx100\fscy100)}"+" ".join(parts))
        open(f"w3/s{k}.ass","w").write("\n".join(HDR+ass)+"\n")
        vf=vf.replace("format=yuv420p[v]",f"subtitles=w3/s{k}.ass:fontsdir=fonts,format=yuv420p[v]")
        if not (os.environ.get("REUSE") and os.path.exists(fn)): run(["ffmpeg","-v","error","-y","-i",SRC,"-filter_complex",vf,"-map","[v]","-map","[a]",
             "-c:v","libx264","-preset","veryfast","-crf","16","-c:a","pcm_s16le",fn])
        sfx(T,"glitch",0.45); sfx(T,"whip",0.5)
        for p in P: sfx(T+p,"boom",0.6); sfx(T+p,"shutter",0.5)
        speech_windows.append((T,T+d))
    segs.append(fn); T+=it["dur"] if it["type"]=="card" else it["e"]-it["s"]
# concat
open("w3/list.txt","w").write("".join(f"file '{os.path.basename(f)}'\n" for f in segs))
run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i","w3/list.txt","-c","copy","w3/joined.mkv"])
# final audio mix
inp=["-i","w3/joined.mkv","-stream_loop","-1","-i",MUSIC]; fc=[]
fc.append("[0:a]highpass=f=70,acompressor=threshold=-20dB:ratio=3:makeup=4,loudnorm=I=-14:TP=-1.5,asplit[sp][key]")
fc.append(f"[1:a]atrim=0:{T:.2f},aresample=48000,volume=0.6,afade=t=out:st={T-2.5:.2f}:d=2.5[m]")
fc.append("[m][key]sidechaincompress=threshold=0.025:ratio=10:attack=15:release=500[md]")
mix=["[sp]","[md]"]
for j,(t,nm,v) in enumerate(SFX):
    inp+=["-i",f"sfx3/{nm}.wav"]; d=int(t*1000)
    fc.append(f"[{j+2}:a]aresample=48000,volume={v},adelay={d}|{d}[s{j}]"); mix.append(f"[s{j}]")
fc.append("".join(mix)+f"amix=inputs={len(mix)}:normalize=0:duration=first,alimiter=limit=0.84[aout]")
run(["ffmpeg","-v","error","-y"]+inp+["-filter_complex",";".join(fc),"-map","0:v","-map","[aout]",
     "-c:v","libx264","-preset","medium","-crf","21","-maxrate","6M","-bufsize","12M","-c:a","aac","-b:a","192k","-movflags","+faststart",OUT])
print("duration",T)
