# Reel script (Milestone 2)

Target length: **about 120 seconds** (must be 90 to 150). Screen recording with a voice-over.
The demo must be a **real run** on the deployed app with an API key. Demo mode doesn't count:
its answers are pre-written, and mock-up screens get 0 for the demo part.

## Before recording

- Open the deployed prototype link in a normal browser window, zoomed to about 110 % so text is readable.
- Have these ready in tabs:
  1. `prompts/v1/P0_baseline_single_prompt.md` on GitHub
  2. Karan's saved v1 output: `test-data/outputs/prompt_experiment/<date>/v1_copperleaf_run1.json`
  3. `prompts/final/P4_judge.md` on GitHub
  4. A v3 output from the same experiment: `v3_copperleaf_run1.json`
- Run one scan beforehand to check the app works, then refresh so the recording starts clean.
- Record with **Windows Game Bar** (press `Win + Alt + R` to start and stop) or **Clipchamp** (built into Windows).
  Record the voice live, or add it afterwards in Clipchamp.

## Timeline and voice-over

| Time | On screen | Voice-over (read naturally) |
|---|---|---|
| 0:00–0:10 | App home page (Setup tab) | "Companies launch chatbots without testing them against attacks like prompt injection. Sentinel AI is a red-team kit that finds those weaknesses before launch." |
| 0:10–0:25 | v1 prompt file, then its saved output | "In Milestone 1 we used one prompt that did everything. Its output was free-text lines: some couldn't be parsed, it never tested hidden instructions, and it judged its own guesses." (Say the real numbers from the iteration log, e.g. "it was readable in X of 6 runs".) |
| 0:25–0:45 | `P4_judge.md`, then the v3 output with `evidence` and `evidence_verified` highlighted | "Now it's five separate prompts. The judge is a separate call that must quote evidence from the reply, and our code checks the quote. Structured output made every answer readable." (Use the real v3 numbers.) |
| 0:45–0:55 | Click **Try the example bot**, then **Scan my chatbot** | "Here's a real run. I load a fictional travel-agency bot and click Scan." |
| 0:55–1:10 | Progress checklist, then the **Report** tab | "Sentinel reads the prompt, writes attacks for this bot, tests each one and judges the replies. The verdict is in plain words." |
| 1:10–1:25 | Click a **Failed** row to open it | "This attack hid an instruction inside a pasted email, and the bot leaked its staff discount code. The evidence is quoted straight from the reply." |
| 1:25–1:40 | **Fix & re-test** tab → **Suggest fixes** → **What changed** | "Sentinel suggests fixes, both prompt changes and app changes, and rewrites the prompt." |
| 1:40–1:50 | **Re-test with the fixed prompt** → the before/after table | "Re-testing shows which problems are fixed and if anything new broke." |
| 1:50–2:05 | GitHub repo page, then back to the app | "Done so far: the full pipeline, live mode for real chatbots, and exports. For Milestone 3 we'll add multi-turn attacks and compare several models." |

## After recording

1. Trim the start and end. Check the length is **between 90 and 150 seconds** and note the **exact number of seconds** (form Q14).
2. Upload to Google Drive (or YouTube as **Unlisted**).
3. Drive: Share → General access → **Anyone with the link** → Viewer. Copy the link.
4. Open the link in an **incognito window** to check it plays without signing in.
5. Send the link and the exact length to the team leader.
