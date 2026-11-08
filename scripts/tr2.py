import sys, wave, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[2], device="cpu", compute_type="int8", cpu_threads=4)
w=wave.open(sys.argv[1]); sr=16000
a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
for rng in sys.argv[3:]:
    s,e=map(float,rng.split('-'))
    segs,_=m.transcribe(a[int(s*sr):int(e*sr)],language="ms",beam_size=5,word_timestamps=True,condition_on_previous_text=False)
    print(f"=== {rng}")
    for sg in segs:
        print(f"{s+sg.start:.2f}\t{s+sg.end:.2f}\t{sg.text.strip()}")
        print("  W "+" ".join(f"{s+x.start:.2f}|{x.word.strip()}" for x in sg.words))
    sys.stdout.flush()
