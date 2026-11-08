set -e
cd /tmp/claude-0/-home-user-vedio-editt/8f3ef6ea-2971-5968-9f80-6878b839992b/scratchpad/build
ffmpeg -v error -stats -y  -ss 31.3 -t 21.15 -i /tmp/claude-0/-home-user-vedio-editt/8f3ef6ea-2971-5968-9f80-6878b839992b/scratchpad/src/video.mp4  -ss 832.1 -t 24.95 -i /tmp/claude-0/-home-user-vedio-editt/8f3ef6ea-2971-5968-9f80-6878b839992b/scratchpad/src/video.mp4  -ss 1599.6 -t 14.8 -i /tmp/claude-0/-home-user-vedio-editt/8f3ef6ea-2971-5968-9f80-6878b839992b/scratchpad/src/video.mp4  -ss 1635.6 -t 24.4 -i /tmp/claude-0/-home-user-vedio-editt/8f3ef6ea-2971-5968-9f80-6878b839992b/scratchpad/src/video.mp4  -loop 1 -t 85.35 -i ov.png  -loop 1 -t 4.65 -i outro.png  -i music.wav  -filter_complex "
 [0:v]fps=30,setpts=PTS-STARTPTS,fade=in:0:6,fade=out:st=20.9:d=0.25[v0];
 [1:v]fps=30,setpts=PTS-STARTPTS,fade=in:0:6,fade=out:st=24.7:d=0.25[v1];
 [2:v]fps=30,setpts=PTS-STARTPTS,fade=in:0:6,fade=out:st=14.55:d=0.25[v2];
 [3:v]fps=30,setpts=PTS-STARTPTS,fade=in:0:6,fade=out:st=24.15:d=0.25[v3];
 [0:a]asetpts=PTS-STARTPTS,afade=in:d=0.15,afade=out:st=20.95:d=0.2[a0];
 [1:a]asetpts=PTS-STARTPTS,afade=in:d=0.15,afade=out:st=24.75:d=0.2[a1];
 [2:a]asetpts=PTS-STARTPTS,afade=in:d=0.15,afade=out:st=14.6:d=0.2[a2];
 [3:a]asetpts=PTS-STARTPTS,afade=in:d=0.15,afade=out:st=24.2:d=0.2[a3];
 [v0][a0][v1][a1][v2][a2][v3][a3]concat=n=4:v=1:a=1[cv][ca];
 [cv]split[c1][c2];
 [c1]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.28:saturation=0.6[bg];
 [c2]scale=1032:581[fg];
 [bg][fg]overlay=24:598[comp];
 [4:v]format=rgba,fade=in:st=0:d=0.8:alpha=1[ov];
 [comp][ov]overlay=0:0:shortest=1,ass=subs.ass:fontsdir=/tmp/claude-0/-home-user-vedio-editt/8f3ef6ea-2971-5968-9f80-6878b839992b/scratchpad/fonts,setsar=1,split[main][mcopy];
 [mcopy]trim=start=85.2,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=5,trim=duration=4.65,gblur=sigma=25,setpts=PTS-STARTPTS[endbg];
 [5:v]format=rgba,fade=in:st=0:d=0.7:alpha=1[oc];
 [endbg][oc]overlay=0:0,fade=out:st=4.0:d=0.65[outro];
 [main][outro]concat=n=2:v=1:a=0,format=yuv420p[vout];
 [ca]highpass=f=80,acompressor=threshold=-20dB:ratio=3:makeup=4,loudnorm=I=-15:TP=-1.5:LRA=9,aresample=44100,apad=pad_dur=4.65[voice];
 [6:a]volume=0.13,volume='if(gt(t,85.35),5.5,1)':eval=frame,afade=out:st=88.6:d=1.4[mus];
 [voice][mus]amix=inputs=2:duration=longest:normalize=0,atrim=duration=90,aformat=channel_layouts=stereo[aout]
 " -map "[vout]" -map "[aout]" -c:v libx264 -preset medium -crf 20 -r 30 -c:a aac -b:a 192k -movflags +faststart -t 90 final.mp4
