import sys
from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
import wave, numpy as np
w=wave.open(sys.argv[1]); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
segs, info = m.transcribe(a, language="ms", vad_filter=True, beam_size=1)
with open(sys.argv[2], "w") as f:
    for s in segs:
        f.write(f"{s.start:.1f}\t{s.end:.1f}\t{s.text.strip()}\n"); f.flush()
