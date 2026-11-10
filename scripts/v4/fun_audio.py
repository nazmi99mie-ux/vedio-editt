import numpy as np, wave, sys
sr=44100; out=sys.argv[1]; rng=np.random.default_rng(3)
def save(n,x):
    x=x/np.max(np.abs(x))*0.95
    if x.ndim==1: x=np.stack([x,x],1)
    w=wave.open(f"{out}/{n}.wav",'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x*32767).astype(np.int16).tobytes()); w.close()
f=lambda m:440*2**((m-69)/12)
dur=95; t=np.arange(int(sr*dur))/sr; bpm=116; b=60/bpm
mus=np.zeros_like(t)
prog=[[60,64,67],[57,60,64],[53,57,60],[55,59,62]]  # C Am F G (happy)
bass=[48,45,41,43]
def note(st,fr,L,amp,kind):
    i0=int(st*sr); n=int(L*sr)
    if i0+n>len(mus): return
    tt=np.arange(n)/sr
    if kind=='pluck': y=(np.sin(2*np.pi*fr*tt)+0.3*np.sin(4*np.pi*fr*tt))*np.exp(-tt*7)
    elif kind=='bass': y=np.sin(2*np.pi*fr*tt)*np.exp(-tt*4)*np.minimum(tt*80,1)
    elif kind=='kick': y=np.sin(2*np.pi*(50+110*np.exp(-tt*40))*tt)*np.exp(-tt*9)
    elif kind=='snap': y=rng.standard_normal(n)*np.exp(-tt*35)
    mus[i0:i0+n]+=amp*y
nbar=int(dur/(4*b))+1
mel=[0,2,4,2,1,2,0,-1]
for bar in range(nbar):
    ch=prog[bar%4]; st=bar*4*b
    for k in range(8):  # eighth-note bouncy arpeggio
        n=ch[[0,1,2,1,0,2,1,2][k]]+12
        note(st+k*b/2,f(n),0.35,0.22,'pluck')
    for k in (0,1.5,2,3.5): note(st+k*b,f(bass[bar%4]),0.4,0.5,'bass')
    for k in range(4): note(st+k*b,0,0.3,0.6 if k%2==0 else 0,'kick') if k%2==0 else None
    for k in (1,3): note(st+k*b,0,0.15,0.18,'snap')
mus*=np.clip((dur-t)/2,0,1)
save('music',mus)
# boing
L=int(0.7*sr); tt=np.arange(L)/sr
fr=180+120*np.sin(2*np.pi*9*tt)*np.exp(-tt*3)+200*np.exp(-tt*6)
save('boing',np.sin(2*np.pi*np.cumsum(fr)/sr)*np.exp(-tt*4.5))
# pop
L=int(0.25*sr); tt=np.arange(L)/sr
save('pop',np.sin(2*np.pi*np.cumsum(400+900*np.exp(-tt*30))/sr)*np.exp(-tt*22))
# ding
L=int(1.5*sr); tt=np.arange(L)/sr
save('ding',(np.sin(2*np.pi*1318*tt)+0.5*np.sin(2*np.pi*2637*tt)+0.25*np.sin(2*np.pi*1975*tt))*np.exp(-tt*3))
