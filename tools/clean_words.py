"""Flatten whisper word timestamps and apply verified spelling fixes (no change of meaning)."""
import json, sys
segs = json.load(open(sys.argv[1]))
FIX = {"resiko": "rezeki", "Anur": "An-Nur", "Grik": "Gerik", "mudi": "mudir",
       "Fisabillillah": "fi sabilillah", "SWT": "SWT", "sembahyang,": "sembahyang,"}
out = []
for s in segs:
    if abs(s["end"] - s["start"]) < 0.4: continue          # drop hallucinated 56.88-57.20 repeat
    for w in s["words"]:
        txt = w["w"].strip()
        if txt.startswith("-"):                               # join "saham" "-saham"
            out[-1]["w"] += txt; out[-1]["e"] = w["e"]; continue
        core = txt.rstrip(",.")
        txt = FIX.get(core, core) + txt[len(core):]
        out.append({"w": txt, "s": w["s"], "e": w["e"]})
# closing formula: whisper heard "Bila kita berhidaya" -> "Billahi taufiq wal hidayah"
i = next(k for k, w in enumerate(out) if w["w"] == "Bila" and w["s"] > 71)
s0, e0 = out[i]["s"], out[i + 2]["e"]; d = (e0 - s0) / 4
out[i:i + 3] = [{"w": "Billahi", "s": s0, "e": s0 + d}, {"w": "taufiq", "s": s0 + d, "e": s0 + 2 * d},
                {"w": "wal", "s": s0 + 2 * d, "e": s0 + 2.6 * d}, {"w": "hidayah,", "s": s0 + 2.6 * d, "e": e0}]
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=0)
print(" ".join(w["w"] for w in out))
