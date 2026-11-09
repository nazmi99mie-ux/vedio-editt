import numpy as np, wave, sys
sr=44100; out=sys.argv[1]
rng=np.random.default_rng(7)
def save(name,x):
    x=np.atleast_2d(x.T).T if x.ndim==1 else x
    if x.ndim==1 or x.shape[1]==1: x=np.stack([x.ravel(),x.ravel()],1)
    x=x/np.max(np.abs(x))*0.95
    w=wave.open(f"{out}/{name}.wav",'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((x*32767).astype(np.int16).tobytes()); w.close()
f=lambda m:440*2**((m-69)/12)
def lp(x,a):  # one-pole lowpass, a in (0,1)
    y=np.empty_like(x); s=0.
    for i in range(len(x)): s+=a*(x[i]-s); y[i]=s
    return y
# ---- music: 92s, 100bpm, D minor dark pulse
dur=92; t=np.arange(int(sr*dur))/sr; bpm=100; beat=60/bpm
mus=np.zeros_like(t)
prog=[50,46,43,45]  # D Bb G A (bass midi)
bar=beat*4
for i in range(int(dur/bar)+1):
    st=i*bar; root=prog[i%4]
    m=(t>=st)&(t<st+bar+1.0); tt=t[m]-st
    env=np.clip(tt/0.6,0,1)*np.clip((bar+1.0-tt)/1.0,0,1)
    chord=[root+12,root+15 if root in(50,43) else root+16,root+19]
    if root==45: chord=[57,61,64]
    for n in chord:
        for det in (1,1.004,0.996):
            mus[m]+=0.18*env*np.sin(2*np.pi*f(n)*det*tt+det)
    # sub drone
    mus[m]+=0.35*env*np.sin(2*np.pi*f(root-12)*tt)
nb=int(dur/beat)
for k in range(nb):
    st=k*beat; i0=int(st*sr); L=int(0.5*sr); tt=np.arange(L)/sr
    if i0+L>len(mus): break
    # kick-like pulse on every beat (stronger on 1 and 3)
    amp=1.0 if k%2==0 else 0.55
    kick=amp*np.sin(2*np.pi*(45+90*np.exp(-tt*35))*tt)*np.exp(-tt*7)
    mus[i0:i0+L]+=0.9*kick
    # ticking hat on off-beats
    j0=int((st+beat/2)*sr); H=int(0.05*sr)
    if j0+H<len(mus): mus[j0:j0+H]+=0.08*rng.standard_normal(H)*np.exp(-np.arange(H)/sr*90)
# intro/outro shaping: start strong, fade end
mus*=np.minimum(1,(dur-t)/2.5).clip(0,1)
save('music',mus)
# ---- impact/boom 2.5s
L=int(2.5*sr); tt=np.arange(L)/sr
boom=np.sin(2*np.pi*(38+120*np.exp(-tt*12))*tt)*np.exp(-tt*2.2)
noise=lp(rng.standard_normal(L),0.08)*np.exp(-tt*9)*2.5
crack=rng.standard_normal(L)*np.exp(-tt*60)*0.6
save('impact',boom+noise+crack)
# ---- whoosh 0.8s (rising-falling filtered noise)
L=int(0.8*sr); tt=np.arange(L)/sr
n=rng.standard_normal(L); env=np.sin(np.pi*tt/0.8)**2
a=0.02+0.25*np.sin(np.pi*tt/0.8)
y=np.empty(L); s=0.
for i in range(L): s+=a[i]*(n[i]-s); y[i]=s
save('whoosh',y*env)
# ---- riser 1.5s
L=int(1.5*sr); tt=np.arange(L)/sr
r=np.sin(2*np.pi*np.cumsum(200+1400*(tt/1.5)**2)/sr)*0.3*(tt/1.5)**2
r+=lp(rng.standard_normal(L),0.3)*(tt/1.5)**3
save('riser',r)
