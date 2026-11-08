import numpy as np, wave, sys
sr=44100; dur=96
t=np.arange(int(sr*dur))/sr
# Minor, solemn progression (Am - F - C - G | Am - Dm - E - Am), 6s each
chords=[[57,60,64],[53,57,60],[48,55,64],[55,59,62],[57,60,64],[50,53,57],[52,56,59],[57,60,64]]
f=lambda m:440*2**((m-69)/12)
out=np.zeros_like(t); seg=6.0
for i in range(int(dur/seg)+1):
    c=chords[i%len(chords)]; st=i*seg
    m=(t>=st-1)&(t<st+seg+1.5); tt=t[m]-st
    env=np.clip((tt+1)/2,0,1)*np.clip((seg+1.5-tt)/2.5,0,1)
    for n in c+[c[0]-12]:
        fr=f(n)
        for det,a in [(1,1),(1.003,.5),(0.997,.5),(2,.15)]:
            out[m]+=a*env*np.sin(2*np.pi*fr*det*tt+i)
# soft high bell melody notes
mel=[76,74,72,71,72,69,68,69]
for i in range(int(dur/3)):
    st=i*3+1.5; n=mel[(i//2)%len(mel)] if i%2==0 else mel[(i//2)%len(mel)]-5
    m=(t>=st)&(t<st+4); tt=t[m]-st
    out[m]+=0.35*np.exp(-tt*1.2)*np.sin(2*np.pi*f(n)*tt)*np.minimum(tt*50,1)
# simple reverb via comb delays
r=out.copy()
for d,g in [(0.137,.5),(0.211,.4),(0.311,.3),(0.457,.25)]:
    k=int(d*sr); r[k:]+=g*out[:-k]
r/=np.abs(r).max(); r*=0.8
fade=np.minimum(np.minimum(t/3,(dur-t)/4),1); r*=fade
s=(np.stack([r,np.roll(r,int(.012*sr))],1)*32767).astype(np.int16)
w=wave.open(sys.argv[1],'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(s.tobytes()); w.close()
