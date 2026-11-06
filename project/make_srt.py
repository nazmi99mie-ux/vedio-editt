"""Writes an SRT of the final cut (corrected spelling) from plan.json."""
import json, sys
sys.argv += []
from render import make_groups
plan = json.load(open(sys.argv[1] + "/plan.json"))
def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
groups = make_groups([dict(w, hook=False) for w in plan["words"]])
with open(sys.argv[2], "w") as f:
    for i, g in enumerate(groups, 1):
        f.write(f"{i}\n{ts(max(0,g['s']))} --> {ts(g['end'])}\n{' '.join(w['w'] for w in g['words'])}\n\n")
