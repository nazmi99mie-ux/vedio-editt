"""Generate AI b-roll stills (SDXL-Turbo on CPU) for the dakwah edit."""
import torch, sys, os
from diffusers import AutoPipelineForText2Image
torch.set_num_threads(4)
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
STYLE = ", cinematic documentary photo, dramatic lighting, film grain, anamorphic, highly detailed, 35mm"
SHOTS = {
 "mosque_golden": "a traditional Malaysian kampung mosque with green dome at golden hour, palm trees, warm light rays",
 "mosque_site": "cleared empty land with wooden survey stakes in a rural Malaysian village edge of rubber tree forest, early morning mist, sun rays",
 "students": "young Malay students wearing white robes and white skullcaps reading Quran sitting on wooden floor of a traditional village madrasah, seen from behind, soft window light",
 "elderly": "elderly Malay man wearing white kopiah praying inside a simple mosque, seen from behind, soft morning light",
 "donate": "close-up of a hand putting banknotes into a wooden donation box inside a mosque, warm light, shallow depth of field",
 "light_sky": "god rays breaking through dramatic clouds over tropical rainforest, heavenly golden light",
 "sujud": "rows of men in white performing prostration prayer inside a mosque, seen from behind, warm lamp light",
 "quran": "open Quran on a wooden rehal stand, warm golden light, dust particles in the air, bokeh",
 "grave": "Malaysian Muslim cemetery with white batu nisan headstones under a frangipani tree at dusk, golden light, gentle mist",
 "village_dawn": "aerial view of a Malaysian village at dawn, mosque among green trees, mist over rainforest hills",
 "interior": "interior of a Malaysian mosque prayer hall with green carpet and arches, morning light through windows",
 "night": "silhouette of a mosque dome and minaret against deep blue night sky with crescent moon and stars",
 "dua": "silhouette of a man raising both hands in prayer at sunset over paddy field",
 "grave2": "traditional Malay Muslim graveyard in a kampung, small white pointed batu nisan stones without inscriptions, frangipani flowers on the ground, soft golden evening light, gentle mist, peaceful",
 "path": "dirt path leading toward a small mosque in a Malaysian village, glowing sunrise, long shadows",
}
p = AutoPipelineForText2Image.from_pretrained("stabilityai/sdxl-turbo", dtype=torch.bfloat16, variant="fp16", low_cpu_mem_usage=True)
names = sys.argv[2:] or list(SHOTS)
for name in names:
    for seed in (11, 23):
        f = f"{OUT}/{name}_{seed}.png"
        if os.path.exists(f): continue
        g = torch.Generator().manual_seed(seed)
        p(prompt=SHOTS[name] + STYLE, num_inference_steps=3, guidance_scale=0.0,
          width=576, height=1024, generator=g).images[0].save(f)
        print("done", f, flush=True)
