import numpy as np, wave, sys
sr=44100; out=sys.argv[1]; rng=np.random.default_rng(11)
def save(n,x):
    x=x/np.max(np.abs(x))*0.95
    if x.ndim==1: x=np.stack([x,x],1)
    w=wave.open(f"{out}/{n}.wav",'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x*32767).astype(np.int16).tobytes()); w.close()
f=lambda m:440*2**((m-69)/12)
dur=96; t=np.arange(int(sr*dur))/sr
mus=np.zeros_like(t)
# D Hijaz scale: D Eb F# G A Bb C
hij=[62,63,66,67,69,70,72,74]
def add(st,y):
    i0=int(st*sr); n=min(len(y),len(mus)-i0)
    if n>0: mus[i0:i0+n]+=y[:n]
def pluck(fr,L=1.6,amp=1.0):  # oud/qanun-ish: Karplus-Strong
    N=int(sr/fr); buf=rng.uniform(-1,1,N); n=int(L*sr); y=np.empty(n)
    for i in range(n):
        y[i]=buf[i%N]; buf[i%N]=0.996*0.5*(buf[i%N]+buf[(i+1)%N])
    return amp*y
# drone pad D + A
for fr,a in ((f(38),0.30),(f(45),0.18),(f(50),0.15)):
    mus+=a*np.sin(2*np.pi*fr*t)*(0.8+0.2*np.sin(2*np.pi*0.07*t))
bpm=84; b=60/bpm
phr=[0,1,2,3,4,3,2,1, 2,3,4,5,4,3,2,0, 4,5,6,7,6,5,4,3, 2,1,2,3,2,1,0,0]
cache={}
for k in range(int(dur/(b/2))):
    st=k*b/2
    if k%16 in (6,7,14,15): continue           # breathing space
    n=hij[phr[k%len(phr)]]
    if n not in cache: cache[n]=pluck(f(n),1.4)
    add(st,0.32*cache[n])
# frame drum (daf): dum on 1, tek on 2.5, 3, 4
L=int(0.4*sr); tt=np.arange(L)/sr
dum=np.sin(2*np.pi*(70+60*np.exp(-tt*25))*tt)*np.exp(-tt*8)
tek=rng.standard_normal(L)*np.exp(-tt*40)*0.25
for bar in range(int(dur/(4*b))):
    st=bar*4*b
    add(st,0.55*dum); add(st+1.5*b,0.35*dum); add(st+2*b,tek); add(st+3*b,tek); add(st+3.5*b,0.6*tek)
# simple reverb
r=mus.copy()
for dly,g in ((0.11,.35),(0.19,.28),(0.31,.2),(0.47,.14)):
    k=int(dly*sr); r[k:]+=g*mus[:-k]
r*=np.clip(t/1.5,0,1)*np.clip((dur-t)/3,0,1)
save('music',r)
