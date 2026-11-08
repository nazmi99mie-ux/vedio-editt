import sys, subprocess
B=sys.argv[1]; S=B.rsplit('/',1)[0]; V=S+'/src/video.mp4'
clips=[(803.0,838.6),(848.3,857.05),(1599.6,1614.4),(1635.6,1661.0)]
G=r"{\c&H68C4E8&}"; R=r"{\r}"
subs={0:[(803.0,804.6,"Tapi apa hukum dia?"),(804.7,806.45,f"Hukum dia {G}KAFIR JUGA{R}"),(806.45,810.4,"Sebab dia tak mengucap dua kalimah syahadah"),
 (811.8,814.9,"Orang panggil dia \"Cina Assalamualaikum\""),(815.2,818.2,"Sebab bila sampai, dia sebut \"Assalamualaikum\""),
 (818.5,820.25,"Assalamualaikum — boleh jawab?"),(820.3,822.3,f"Boleh jawab tak? {G}TAK BOLEH JAWAB{R}"),
 (823.6,828.2,"Sebab \"Assalamualaikum\" bukan sama dengan ucapan biasa"),(829.3,831.4,"Bukan sama dengan \"selamat pagi\""),
 (832.2,835.0,"Assalamualaikum — salam sejahtera"),(835.8,838.6,f"Sejahtera daripada siapa? Daripada {G}ALLAH{R}")],
 1:[(848.35,851.4,f"Orang {G}kafir{R} dapat selamat sejahtera?"),(852.2,854.5,f"Di hari akhirat? {G}TAK DAPAT{R}"),(854.6,857.05,"Macam mana boleh jawab \"salam sejahtera\" kepada dia?")],
 2:[(1599.7,1602.3,"Kalau orang nak masuk Islam, ajar dia mengucap dulu"),(1602.3,1604.4,f"Jangan kita {G}beri tangguh{R}"),
 (1604.5,1608.6,f"Saja-saja beri tangguh — faqad kafara — {G}KAFIR{R}"),(1608.7,1614.35,f"Orang yang minta tangguh kepada orang yang nak mengucap masuk Islam, maka {G}KAFIR{R}")],
 3:[(1635.7,1637.6,f"Faqad kafara — {G}KAFIR{R}"),(1637.6,1641.4,f"Sebab {G}meredhai{R} seseorang itu berada dalam {G}KUFUR{R}"),
 (1642.1,1645.7,"Selesaikan dia masuk Islam — ajar dia mengucap betul-betul"),(1645.7,1647.6,"Esok baru urus perkara lain"),
 (1647.6,1650.2,f"{G}Man radhiya bil kufri kafara{R}"),(1650.2,1653.2,f"Siapa redha dengan kufur, {G}KUFUR JUGA{R}"),
 (1653.5,1657.0,"Dia keluar rumah, tiba-tiba dilanggar kereta — mati"),(1657.0,1658.95,f"Kerana kita {G}beri tangguh{R}"),
 (1659.0,1661.0,f"Sebab itu saya kata: {G}JANGAN BERI TANGGUH{R}")]}
TOTAL=90.0
offs=[];o=0
for a,b in clips: offs.append(o); o+=b-a
MAIN=o; OUT=TOTAL-MAIN
def ts(t): return f"0:{int(t//60):02d}:{t%60:05.2f}"
hdr=open(B+'/subs.ass').read().split('[Events]')[0]+"[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
ev=[]
for i,lst in subs.items():
    for a,b,t in lst:
        s=a-clips[i][0]+offs[i]; e=b-clips[i][0]+offs[i]
        ev.append(f"Dialogue: 0,{ts(s)},{ts(e)},Sub,,0,0,0,,{{\\pos(540,1360)\\fad(120,80)\\t(0,150,\\fscx104\\fscy104)\\t(150,300,\\fscx100\\fscy100)}}{t}")
open(B+'/subs.ass','w').write(hdr+"\n".join(ev)+"\n")
args=['ffmpeg','-v','error','-y']
for a,b in clips: args+=['-ss',str(a),'-t',f"{b-a:.3f}",'-i',V]
n=len(clips)
args+=['-loop','1','-t',f"{MAIN:.3f}",'-i',B+'/ov.png','-loop','1','-t',f"{OUT:.3f}",'-i',B+'/outro.png','-i',B+'/music.wav']
f=[];cat=''
for i,(a,b) in enumerate(clips):
    d=b-a
    f.append(f"[{i}:v]fps=30,setpts=PTS-STARTPTS,fade=in:0:5,fade=out:st={d-0.2:.3f}:d=0.2[v{i}]")
    f.append(f"[{i}:a]asetpts=PTS-STARTPTS,afade=in:d=0.12,afade=out:st={d-0.15:.3f}:d=0.15[a{i}]")
    cat+=f"[v{i}][a{i}]"
f+=[f"{cat}concat=n={n}:v=1:a=1[cv][ca]","[cv]split[c1][c2]",
"[c1]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.28:saturation=0.6[bg]",
"[c2]scale=1032:581[fg]","[bg][fg]overlay=24:598[comp]",
f"[{n}:v]format=rgba,fade=in:st=0:d=0.8:alpha=1[ov]",
f"[comp][ov]overlay=0:0:shortest=1,ass={B}/subs.ass:fontsdir={S}/fonts,setsar=1,split[main][mc]",
f"[mc]trim=start={MAIN-0.1:.3f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=8,trim=duration={OUT:.3f},gblur=sigma=25,setpts=PTS-STARTPTS[endbg]",
f"[{n+1}:v]format=rgba,fade=in:st=0:d=0.7:alpha=1[oc]",
f"[endbg][oc]overlay=0:0,fade=out:st={OUT-0.6:.3f}:d=0.6[outro]",
"[main][outro]concat=n=2:v=1:a=0,format=yuv420p[vout]",
f"[ca]highpass=f=80,acompressor=threshold=-20dB:ratio=3:makeup=4,loudnorm=I=-15:TP=-1.5:LRA=9,aresample=44100,apad=pad_dur={OUT+1:.3f}[voice]",
f"[{n+2}:a]volume=0.13,volume='if(gt(t,{MAIN:.3f}),5.5,1)':eval=frame,afade=out:st={TOTAL-1.4}:d=1.4[mus]",
f"[voice][mus]amix=inputs=2:duration=longest:normalize=0,atrim=duration={TOTAL},aformat=channel_layouts=stereo[aout]"]
args+=['-filter_complex',";".join(f),'-map','[vout]','-map','[aout]','-c:v','libx264','-preset','medium','-crf','20','-r','30','-c:a','aac','-b:a','192k','-movflags','+faststart','-t',str(TOTAL),B+'/final.mp4']
print(f"main={MAIN:.2f} outro={OUT:.2f}",flush=True)
subprocess.run(args,check=True)
