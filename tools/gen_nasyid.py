import numpy as np, wave, sys
SR=48000; DUR=18.0; N=int(SR*DUR); t=np.arange(N)/SR
rng=np.random.default_rng(7)
out=np.zeros((N,2))
def env(n,a,r):
    e=np.ones(n); a=int(a*SR); r=int(r*SR)
    e[:a]=np.linspace(0,1,a); e[-r:]*=np.linspace(1,0,r); return e
def place(sig,start,pan=0.0,gain=1.0):
    s=int(start*SR); e=min(N,s+len(sig)); sig=sig[:e-s]*gain
    out[s:e,0]+=sig*(1-pan)/1.0*0.7071*np.sqrt(2)*(0.5-pan/2+0.5)/1
    out[s:e,1]+=sig*(0.5+pan/2+0.5)/1*0.7071*np.sqrt(2)*0.5
# D Hijaz: D Eb F# G A Bb C D
base=146.83
semis=[0,1,4,5,7,8,10,12,13,16]
def f(i,oct=0): return base*2**((semis[i]+12*oct)/12)
BPM=76; beat=60/BPM
# Drone pad (D + A), slow swell
for fr,g in [(base/2,0.16),(base*1.5/2,0.08),(base,0.06)]:
    ph=rng.random()*6
    pad=g*(np.sin(2*np.pi*fr*t+ph)+0.3*np.sin(2*np.pi*2*fr*t)+0.12*np.sin(2*np.pi*3*fr*t))
    pad*=0.85+0.15*np.sin(2*np.pi*0.15*t)
    out[:,0]+=pad; out[:,1]+=pad*0.95
# Plucked oud-like melody (Karplus-Strong)
def pluck(freq,dur,bright=0.5):
    n=int(dur*SR); p=int(SR/freq); buf=rng.uniform(-1,1,p)
    y=np.zeros(n)
    for i in range(n):
        y[i]=buf[i%p]
        buf[i%p]=0.5*(buf[i%p]+buf[(i+1)%p])*0.996
    return y*np.exp(-np.arange(n)/SR*1.2)
mel=[(4,1),(5,0.5),(4,0.5),(2,1),(1,1),(2,0.5),(4,0.5),(5,1),(6,1),(5,1),(4,0.5),(2,0.5),(1,1),(0,2),
     (4,1),(5,0.5),(6,0.5),(7,1),(6,1),(5,0.5),(4,0.5),(2,1),(1,1),(0,2)]
tt=2.0
for deg,ln in mel:
    if tt>DUR-2.5: break
    place(pluck(f(deg,0)*1.0, ln*beat+0.8),tt,gain=0.22)
    place(pluck(f(deg,-1),ln*beat+0.6),tt+0.012,gain=0.07)
    tt+=ln*beat
# Daf / frame drum: dum (low) and tak (high)
def dum():
    n=int(0.5*SR); x=np.arange(n)/SR
    fr=90*np.exp(-x*6)+55
    return np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-x*7)
def tak():
    n=int(0.15*SR); x=np.arange(n)/SR
    nz=rng.uniform(-1,1,n); nz=np.convolve(nz,[1,-0.9],'same')
    jingle=sum(np.sin(2*np.pi*fq*x) for fq in (3100,4300,5600))*0.15
    return (nz*0.6+jingle)*np.exp(-x*30)
# pattern per 4-beat bar: D . T . D D T .
pat=[(0,'d'),(1,'t'),(2,'d'),(2.5,'d'),(3,'t'),(3.5,'t')]
b0=2.0
while b0<DUR-2.0:
    for off,k in pat:
        st=b0+off*beat
        if st>DUR-2: break
        if k=='d': place(dum(),st,gain=0.35)
        else: place(tak(),st,gain=0.12)
    b0+=4*beat
# intro: single soft dum + pad only; ending fade
fade=np.ones(N); fi=int(1.5*SR); fo=int(2.5*SR)
fade[:fi]=np.linspace(0,1,fi); fade[-fo:]=np.linspace(1,0,fo)
out*=fade[:,None]
# simple reverb: multi-tap feedback delays
rev=np.zeros_like(out)
for d,g in [(0.031,0.35),(0.047,0.3),(0.071,0.25),(0.113,0.2),(0.173,0.15)]:
    k=int(d*SR); rev[k:]+=out[:-k]*g
out=out+rev*0.6
out/=np.max(np.abs(out))*1.12
w=wave.open(sys.argv[1],'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out*32767).astype('<i2').tobytes()); w.close()
