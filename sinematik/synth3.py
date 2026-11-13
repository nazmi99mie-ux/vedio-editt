import numpy as np, wave, sys
SR=44100; rng=np.random.default_rng(11)
def save(name,x,norm=0.89):
    x=np.asarray(x,np.float32)
    if x.ndim==1: x=np.stack([x,x],1)
    x=x/(np.max(np.abs(x))+1e-9)*norm
    w=wave.open(name,"wb");w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
    w.writeframes((x*32767).astype(np.int16).tobytes());w.close()
def t_(d): return np.arange(int(d*SR))/SR
def filt(x,lo=0,hi=None):
    X=np.fft.rfft(x);f=np.fft.rfftfreq(len(x),1/SR)
    if hi: X*=1/(1+(f/hi)**4)
    if lo: X*=1/(1+(lo/np.maximum(f,1))**4)
    return np.fft.irfft(X,len(x))
def place(b,x,t,g=1.0):
    i=int(t*SR); j=min(len(b),i+len(x))
    if i<len(b): b[i:j]+=g*x[:j-i]
def reverb(x,dec=2.5,mix=0.35):
    n=int(dec*SR); ir=rng.standard_normal(n)*np.exp(-np.arange(n)/SR*(6.9/dec))
    ir=filt(ir,200,5000); L=len(x)+n
    y=np.fft.irfft(np.fft.rfft(x,L)*np.fft.rfft(ir,L),L)
    y=y/np.max(np.abs(y)+1e-9)*np.max(np.abs(x)+1e-9)
    out=np.zeros(L); out[:len(x)]=x*(1-mix); return out+y*mix
def piano(f,d=3.0):
    t=t_(d); x=np.zeros_like(t)
    for h,a in [(1,1),(2,0.5),(3,0.25),(4,0.12),(5,0.06)]:
        x+=a*np.sin(2*np.pi*f*h*t*(1+0.0004*h))*np.exp(-t*(1.2+h*0.9))
    att=np.minimum(1,t/0.004); return x*att
def heartbeat():
    t=t_(0.5); f=60*np.exp(-t*8)+38
    k=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*12)
    out=np.zeros(int(0.8*SR)); place(out,k,0,1); place(out,k,0.22,0.7); return out
def strings(freqs,d):
    t=t_(d); x=np.zeros_like(t)
    for f in freqs:
        for det in (-0.25,0,0.25):
            ph=2*np.pi*(f+det)*t+rng.uniform(0,6)+0.003*np.sin(2*np.pi*5*t)*f
            x+=2*(ph/(2*np.pi)%1)-1
    sw=np.sin(np.pi*np.clip(t/d,0,1))**1.5
    return filt(x,150,1800)*sw*0.15
L=float(sys.argv[1]); BPM=70; beat=60/BPM; bar=4*beat
mus=np.zeros(int((L+4)*SR))
A=55.0; nt=lambda s,o=1: A*o*2**(s/12)
# Am - F - C - G  (i-VI-III-VII), dark emotional
prog=[[0,3,7],[-4,0,3],[3,7,10],[-2,2,5]]
HB=heartbeat()
for b in range(int(L/bar)+1):
    t0=b*bar; ch=prog[b%4]
    place(mus,strings([nt(c,4) for c in ch],bar*1.05),t0,1.0 if b>=2 else 0.6)
    t=t_(bar); place(mus,np.sin(2*np.pi*nt(ch[0],1)*t)*np.minimum(1,t/0.2)*np.exp(-t*0.3)*0.5,t0)
    for q in range(4):
        if b>=1 and q in (0,2): place(mus,HB,t0+q*beat,0.9)
    # piano arpeggio
    arp=[ch[0],ch[1],ch[2],ch[1]+12,ch[2],ch[1],ch[0]+12,ch[2]]
    for k,n in enumerate(arp):
        place(mus,piano(nt(n,8)),t0+k*beat/2,0.22 if k else 0.3)
    if b%4==3: place(mus,piano(nt(prog[(b+1)%4][0],16),5),t0+bar-beat/2,0.15)
mus=reverb(mus,3.0,0.3)[:int(L*SR)]
fade=np.ones(len(mus)); n=int(4*SR); fade[-n:]=np.linspace(1,0,n); fade[:int(SR)]=np.linspace(0,1,int(SR))
save("sfx3/music.wav",np.tanh(mus*1.2)*fade)
# SFX
save("sfx3/heartbeat.wav",HB)
t=t_(0.05); save("sfx3/type.wav",filt(rng.standard_normal(len(t)),1500,9000)*np.exp(-t*120)+0.3*np.sin(2*np.pi*900*t)*np.exp(-t*200))
g=np.zeros(int(0.35*SR))
for i in range(7):
    s=int(rng.uniform(0,0.3)*SR); n=int(rng.uniform(0.01,0.05)*SR)
    seg=np.sign(np.sin(2*np.pi*rng.uniform(80,2000)*np.arange(n)/SR))*rng.uniform(0.3,1)
    g[s:s+n]+=seg[:len(g)-s]
g+=filt(rng.standard_normal(len(g)),2000)*0.3*(rng.random(len(g))<0.5)
save("sfx3/glitch.wav",np.round(g*6)/6)
t=t_(0.25); sh=filt(rng.standard_normal(len(t)),2000)*(np.exp(-t*60)+0.6*np.exp(-np.maximum(t-0.08,0)*60)*(t>0.08))
save("sfx3/shutter.wav",sh)
t=t_(0.9); f=220*(1-t/0.9)**2+20
save("sfx3/tapestop.wav",np.tanh(3*np.sin(2*np.pi*np.cumsum(f)/SR))*(1-t/0.9))
t=t_(0.6); f=55*np.exp(-t*3)+30
boom=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*4)+filt(rng.standard_normal(len(t)),0,300)*np.exp(-t*20)
save("sfx3/boom.wav",reverb(boom,2.5,0.4))
clk=np.zeros(int(2*SR))
for i in range(4):
    t=t_(0.03); place(clk,filt(rng.standard_normal(len(t)),3000)*np.exp(-t*200)*(1 if i%2==0 else 0.6),i*0.5)
save("sfx3/tick.wav",clk)
t=t_(1.2); f=4000*np.exp(-t*4)+80
save("sfx3/whip.wav",filt(rng.standard_normal(len(t)),300,8000)*np.sin(np.pi*np.clip(t/0.35,0,1))**2*(t<0.35)+0.0*f[:len(t)])
print("ok")
