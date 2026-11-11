import numpy as np, wave, sys
SR=44100
def save(name,x):
    x=np.asarray(x,np.float32)
    if x.ndim==1: x=np.stack([x,x],1)
    x=x/ (np.max(np.abs(x))+1e-9)*0.89
    w=wave.open(name,"wb");w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
    w.writeframes((x*32767).astype(np.int16).tobytes());w.close()
def t_(d): return np.arange(int(d*SR))/SR
def env(n,a,r):
    e=np.ones(n);ai=int(a*SR);ri=int(r*SR)
    if ai: e[:ai]=np.linspace(0,1,ai)
    if ri: e[-ri:]*=np.linspace(1,0,ri)**2
    return e
def lp(x,a):  # one-pole lowpass, a in (0,1)
    y=np.empty_like(x);s=0.0
    for i in range(len(x)): s+=a*(x[i]-s); y[i]=s
    return y
def lpf(x,cut):  # vectorised-ish via fft brickwall smooth
    X=np.fft.rfft(x);f=np.fft.rfftfreq(len(x),1/SR)
    X*=1/(1+(f/cut)**4);return np.fft.irfft(X,len(x))
def hpf(x,cut):
    X=np.fft.rfft(x);f=np.fft.rfftfreq(len(x),1/SR)
    X*=1/(1+(cut/np.maximum(f,1))**4);return np.fft.irfft(X,len(x))
rng=np.random.default_rng(7)
def kick(d=0.6,f0=110,f1=38,dec=7):
    t=t_(d);f=f1+(f0-f1)*np.exp(-t*25);ph=2*np.pi*np.cumsum(f)/SR
    return np.sin(ph)*np.exp(-t*dec)+0.3*np.tanh(3*np.sin(ph))*np.exp(-t*dec*1.5)
def taiko(d=1.2):
    t=t_(d);k=kick(d,140,55,4.5)
    n=lpf(rng.standard_normal(len(t)),900)*np.exp(-t*18)*0.6
    return k+n
def hat(d=0.06):
    t=t_(d);return hpf(rng.standard_normal(len(t)),7000)*np.exp(-t*70)
def snare(d=0.3):
    t=t_(d);n=hpf(lpf(rng.standard_normal(len(t)),6000),1200)*np.exp(-t*16)
    return n+0.5*np.sin(2*np.pi*190*t)*np.exp(-t*22)
def pluck(f,d=0.7):
    # karplus-strong oud-ish
    N=int(SR/f);buf=rng.uniform(-1,1,N);out=np.zeros(int(d*SR))
    for i in range(len(out)):
        out[i]=buf[i%N]; buf[i%N]=0.996*0.5*(buf[i%N]+buf[(i+1)%N])
    return out*env(len(out),0.002,0.1)
def pad(freqs,d):
    t=t_(d);x=np.zeros_like(t)
    for f in freqs:
        for det in (-0.12,0,0.12):
            x+=np.sign(np.sin(2*np.pi*(f+det)*t+rng.uniform(0,6)))*0.15+np.sin(2*np.pi*(f+det)*t)*0.3
    return lpf(x,900)*env(len(t),1.0,1.0)
def place(buf,x,t,g=1.0):
    i=int(t*SR);j=min(len(buf),i+len(x));buf[i:j]+=g*x[:j-i]
# ---------- MUSIC ----------
L=float(sys.argv[1]) if len(sys.argv)>1 else 100
BPM=96;beat=60/BPM;bar=4*beat
mus=np.zeros(int((L+2)*SR))
D=73.42
# Hijaz on D: D Eb F# G A Bb C D
scale=[0,1,4,5,7,8,10,12]
hz=lambda st,o=2: D*o*2**(st/12)
chords=[[0,7,12],[1,8,13],[0,7,12],[-2,5,10]]   # D, Eb, D, C
TK=taiko();KK=kick();HH=hat();SN=snare()
nb=int(L/bar)+1
melody=[7,8,7,5,4,5,4,1, 0,1,4,5,7,5,4,1]
for b in range(nb):
    t0=b*bar
    ch=chords[b%4]
    place(mus,pad([hz(c,1) for c in ch],bar+1.0),t0,0.16)
    place(mus,np.sin(2*np.pi*hz(ch[0],0.5)*t_(bar))*env(int(bar*SR),0.05,0.3),t0,0.3)  # sub bass
    intro = b<2
    for q in range(4):
        tb=t0+q*beat
        if not intro:
            if q in (0,2): place(mus,KK,tb,0.9)
            if q==2 and b%2==1: place(mus,TK,tb+beat*0.5,0.6)
            if q in (1,3): place(mus,SN,tb,0.35)
            for e in (0,0.5): place(mus,HH,tb+e*beat,0.18 if e else 0.12)
        if q==0 and b%4==0: place(mus,TK,tb,1.0)
    if b>=2:
        for k in range(8):
            n=melody[(b*8+k)%16]
            if (k%2==0) or rng.random()<0.5:
                place(mus,pluck(hz(scale[n%8] if n<8 else n,4)),t0+k*beat/2,0.28)
mus=mus[:int(L*SR)]
mus=np.tanh(mus*0.9)
save("sfx/music.wav",mus*env(len(mus),0.5,3.0))
# ---------- SFX ----------
t=t_(2.0);f=200+np.exp(t*2.5)*60;ns=rng.standard_normal(len(t))
riser=hpf(ns,800)*(t/2)**2*0.6+np.sin(2*np.pi*np.cumsum(f)/SR)*(t/2)**2*0.4
save("sfx/riser.wav",riser)
t=t_(1.5);f=90*np.exp(-t*2.2)+28
save("sfx/subdrop.wav",np.sin(2*np.pi*np.cumsum(f)/SR)*env(len(t),0.005,1.0))
t=t_(2.5);b=np.zeros_like(t)
for fq in (36.7,73.4,110.1,146.8,77.8):
    b+=np.sign(np.sin(2*np.pi*fq*t))*0.3+np.sin(2*np.pi*fq*1.003*t)
braam=lpf(np.tanh(b*1.5),1500)*env(len(t),0.02,1.8)+kick(2.5,90,30,1.5)
save("sfx/braam.wav",braam)
t=t_(0.45);ns=rng.standard_normal(len(t));sw=np.zeros_like(t)
for i,c in enumerate(np.linspace(300,6000,9)):
    seg=slice(int(i*len(t)/9),int((i+1)*len(t)/9));sw[seg]=hpf(lpf(ns,c+800),c*0.5)[seg]
save("sfx/swoosh.wav",sw*np.sin(np.pi*t/0.45)**2)
save("sfx/hit.wav",np.concatenate([taiko()*1.0])+0)
t=t_(0.12);save("sfx/click.wav",hpf(rng.standard_normal(len(t)),3000)*np.exp(-t*60)+np.sin(2*np.pi*2000*t)*np.exp(-t*80))
t=t_(1.6);save("sfx/revcym.wav",(hpf(rng.standard_normal(len(t)),4000)*(t/1.6)**3))
print("ok")
