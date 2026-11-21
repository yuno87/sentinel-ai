# Reel script (Milestone 2)

Target length: **about 120 seconds** (must be 90 to 150). Screen recording with a voice-over.
The demo must be a **real run** on the deployed app (https://sentinel-ai-chi-two.vercel.app) with the Gemini key set, or on your own computer with the key in `code/.env`. Demo mode doesn't count:
its answers are pre-written, and mock-up screens get 0 for the demo part.

## Before recording

- Open the deployed prototype link in a normal browser window, zoomed to about 110 % so text is readable.
- Have these ready in tabs:
  1. `prompts/v1/P0_baseline_single_prompt.md` on GitHub
  2. A saved v1 output: `test-data/outputs/prompt_experiment/2026-11-20_2345/v1_copperleaf_run2.json` (the run that broke format)
  3. `prompts/final/P4_judge.md` on GitHub
  4. A v4 output from the same experiment: `test-data/outputs/prompt_experiment/2026-11-20_2345/v4_copperleaf_run1.json`
- Run one scan beforehand to check the app works, then refresh so the recording starts clean.
- Record with **Windows Game Bar** (press `Win + Alt + R` to start and stop) or **Clipchamp** (built into Windows).
  Record the voice live, or add it afterwards in Clipchamp.

## Timeline and voice-over

| Time | On screen | Voice-over (read naturally) |
|---|---|---|
| 0:00–0:10 | App home page (Setup tab) | "Companies launch chatbots without testing them against attacks like prompt injection. Sentinel AI is a red-team kit that finds those weaknesses before launch." |
| 0:10–0:25 | v1 prompt file, then its saved output | "In Milestone 1 we used one prompt that did everything. In our tests it broke format in 1 of 6 runs, never tried hidden-instruction attacks, and 13 of its 29 verdicts contradicted themselves." |
| 0:25–0:45 | `prompts/ITERATION_LOG.md` summary table, then the v4 output with `evidence` and `evidence_verified` highlighted | "Now it's five separate prompts with checked JSON. Our first split version judged 0 of 48 attacks as failures, because it imagined a perfectly safe bot. Rewriting the predictor with two examples raised that to 31 percent, matching how weak each bot really is, and every evidence quote is checked against the reply." |
| 0:45–0:55 | Click **Try the example bot**, then **Scan my chatbot** | "Here's a real run. I load a fictional travel-agency bot and click Scan." |
| 0:55–1:10 | Progress checklist, then the **Report** tab | "Sentinel reads the prompt, writes attacks for this bot, tests each one and judges the replies. The verdict is in plain words." |
| 1:10–1:25 | Click a **Failed** row to open it | "This attack hid an instruction inside a pasted email, and the bot leaked its staff discount code. The evidence is quoted straight from the reply." |
| 1:25–1:40 | **Fix & re-test** tab → **Suggest fixes** → **What changed** | "Sentinel suggests fixes, both prompt changes and app changes, and rewrites the prompt." |
| 1:40–1:50 | **Re-test with the fixed prompt** → the before/after table | "Re-testing shows which problems are fixed and if anything new broke." |
| 1:50–2:05 | GitHub repo page, then back to the app | "Done so far: the full five-prompt pipeline, live mode for real chatbots, exports, and 15 tests with 12 passing. For Milestone 3 we'll add multi-turn attacks, fix the three failures we found, and compare Gemini with Claude." |

## After recording

1. Trim the start and end. Check the length is **between 90 and 150 seconds** and note the **exact number of seconds** (form Q14).
2. Upload to Google Drive (or YouTube as **Unlisted**).
3. Drive: Share → General access → **Anyone with the link** → Viewer. Copy the link.
4. Open the link in an **incognito window** to check it plays without signing in.
5. Note the link and the exact length for the form (Q13, Q14) and the PDF cover (`docs/m2/links.json`).
