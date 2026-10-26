# Video engine trials (26 Oct 2026)

Scratch scripts from the Veo-retirement investigation. They call the engines' APIs DIRECTLY with hand-written prompts; they
do NOT go through the studio's own prompt builder (so camera notes / dialogue fix are not exercised). Read keys from
`api/.env` (FAL_KEY, GOOGLE_API_KEY). They spend real credit. Paths are hard-coded to the 26 Oct machine
(`C:\Users\punie\Downloads\engine-trial` for media, a scratchpad folder for the page) -- adapt before reuse.

- `engine_trial.py` reference-to-video (Seedance 2.0, Kling O1) with the real pack photo + cast/location frames
- `i2v_trial.py` scene A image-to-video on Veo(fal) / Kling 3.0 / Seedance 2.0 / Gemini Omni
- `i2v_trial2.py` round 2: MiniMax H3 Max, Wan 3.0, Kling 4.0
- `i2v_trial3.py` scene B (harder frame), all seven engines, prompt rewriting OFF
- `omni_draft_test.py` measures Omni's billed tokens at a given resolution (360p = 1/3 of 720p)
- `analyze_i2v.py` pouch colour/size fidelity metrics + web copies; `build_compare_page.py` + `compare_template.html`
  generate the published comparison page
