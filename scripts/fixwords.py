import json
segs=json.load(open("words2.json"))
words=[]
fix={"resiko":"rezeki","mudi":"mudir","subhanallah.":"subhanallah."}
for s in segs:
    if "Terima kasih" in s["text"]: continue
    if "balik hidayah" in s["text"]:
        toks="Wabillahi taufiq wal hidayah.".split(); a,b=s["start"],s["end"]
        for i,t in enumerate(toks): words.append({"w":t,"s":a+(b-a)*i/len(toks),"e":a+(b-a)*(i+1)/len(toks),"seg":len(words) and words[-1]["seg"]+1})
        continue
    sid=(words[-1]["seg"]+1) if words else 0
    for w in s["words"]:
        t=w["w"].strip(); core=t.rstrip(".,?!").lower()
        if core in fix: t=fix[core]+t[len(core):]
        if core=="ni" and t.endswith(".") and "subhanallah" in s["text"]: t="ni,"
        words.append({"w":t,"s":w["s"],"e":w["e"],"seg":sid})
for w in words:
    if w["w"].lower().startswith("swt"): w["w"]="SWT."
json.dump(words,open("words_final.json","w"),ensure_ascii=False,indent=0)
print(" ".join(w["w"] for w in words))
m=[]
for w in words:
    if w["w"].startswith("-") and m: m[-1]["w"]+=w["w"]; m[-1]["e"]=w["e"]
    else: m.append(dict(w))
for i,w in enumerate(m):
    if w["w"]=="ni" and i+1<len(m) and m[i+1]["w"].lower().startswith("subhanallah"): w["w"]="ni,"; m[i+1]["w"]="subhanallah."
json.dump(m,open("words_final.json","w"),ensure_ascii=False,indent=0)
print(len(m)); print(" ".join(w["w"] for w in m))
