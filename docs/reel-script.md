# Reel script (Milestone 2): about 95 seconds, 4 speakers

Target: **90–100 seconds** (the form accepts 90–150). Screen recording with voice-over; faces optional.
The demo must be a **real run** on https://sentinel-ai-chi-two.vercel.app with the Gemini key working
(check `/api/info` says `gemini-3.5-flash-lite`, not `demo`). Demo mode doesn't count: mock-up screens get 0.

Word counts assume a relaxed pace of about 2.4 words per second. Each speaker's block fits their time.

## Before recording

- Have these open in browser tabs, zoomed to about 110 %:
  1. The app: https://sentinel-ai-chi-two.vercel.app
  2. `prompts/ITERATION_LOG.md` on GitHub, scrolled to the **Summary of the measurements** table
  3. A v1 output: `test-data/outputs/prompt_experiment/2026-11-20_2345/v1_copperleaf_run2.json` on GitHub
  4. A v4 output: `test-data/outputs/prompt_experiment/2026-11-20_2345/v4_copperleaf_run1.json` on GitHub
  5. The repository page: https://github.com/yuno87/sentinel-ai
- Do one scan before recording to wake the app up, then refresh so the recording starts clean.
- A scan takes 1–3 minutes on the free key: **record the scan in one take, then cut the waiting** in the editor
  (keep a second or two of the progress checklist).
- Record with **Clipchamp** (built into Windows) or **Win + Alt + R** (Game Bar). Easiest: record the screen
  first, then have each person record their lines over it in Clipchamp.

## Script

| Time | Speaker | On screen | Voice-over |
|---|---|---|---|
| 0:00–0:13 (13 s) | **Person 1** | App home page (Setup tab) | "Companies launch chatbots without testing them against attacks like prompt injection, the top risk in OWASP's list for AI apps. Sentinel AI is a red-team kit that finds those weaknesses before launch." |
| 0:13–0:26 (13 s) | **Person 2** | v1 output file | "In Milestone 1 we used one prompt that did everything. It broke format in one of six runs, never tried hidden-instruction attacks, and contradicted itself in 13 of 29 verdicts." |
| 0:26–0:41 (15 s) | **Person 2** | Iteration log summary table, then the v4 output with `evidence_verified: true` | "So we split it into five prompts with checked JSON. Our first split judged zero attacks as failures. Rewriting the predictor with two examples raised that to 31 percent, matching how weak each bot really is." |
| 0:41–0:51 (10 s) | **Person 3** | Click **Try the example bot**, then **Scan my chatbot**; progress checklist | "Here's a real run. I load a fictional travel-agency bot and click Scan. Sentinel analyses the prompt and writes attacks just for this bot." |
| 0:51–1:05 (14 s) | **Person 3** | **Report** tab: Block launch banner, then click a **Failed** row | "The verdict is in plain words: block launch. Opening a failed attack shows the hidden instruction, the bot's reply, and the exact evidence, which our code checks really appears in the reply." |
| 1:05–1:18 (13 s) | **Person 4** | **Fix & re-test** tab → **Suggest fixes** → **What changed** → **Re-test** | "Sentinel then suggests fixes, both prompt changes and app changes, rewrites the prompt, and re-tests it. Here every attack that worked before is now blocked." |
| 1:18–1:35 (17 s) | **Person 4** | Repository page | "So far: the full five-prompt pipeline, live testing of real chatbots, and fifteen tests, twelve passing. For Milestone 3 we'll fix the three failures we found, add multi-turn attacks, and compare Gemini with Claude." |

Total: about **95 seconds**. If it runs long, trim pauses rather than words; if it runs under 90 seconds,
hold the final repository shot or the re-test table for a few seconds more.

## Lines only (to send to each speaker)

**Person 1** (0:00–0:13)
> Companies launch chatbots without testing them against attacks like prompt injection, the top risk in OWASP's list for AI apps. Sentinel AI is a red-team kit that finds those weaknesses before launch.

**Person 2** (0:13–0:41)
> In Milestone 1 we used one prompt that did everything. It broke format in one of six runs, never tried hidden-instruction attacks, and contradicted itself in 13 of 29 verdicts.
> So we split it into five prompts with checked JSON. Our first split judged zero attacks as failures. Rewriting the predictor with two examples raised that to 31 percent, matching how weak each bot really is.

**Person 3** (0:41–1:05)
> Here's a real run. I load a fictional travel-agency bot and click Scan. Sentinel analyses the prompt and writes attacks just for this bot.
> The verdict is in plain words: block launch. Opening a failed attack shows the hidden instruction, the bot's reply, and the exact evidence, which our code checks really appears in the reply.

**Person 4** (1:05–1:35)
> Sentinel then suggests fixes, both prompt changes and app changes, rewrites the prompt, and re-tests it. Here every attack that worked before is now blocked.
> So far: the full five-prompt pipeline, live testing of real chatbots, and fifteen tests, twelve passing. For Milestone 3 we'll fix the three failures we found, add multi-turn attacks, and compare Gemini with Claude.

## Notes

- The re-test line ("every attack that worked before is now blocked") matches what our real run showed (4 fixed, 0 still failing).
  If your recorded run shows something different, say what it shows, e.g. "most of the attacks that worked before are now blocked".
- Likewise, if the scan you record finds a different number of failures, the "block launch" line still works as long as
  the banner says Block launch; if it says something else, read the banner's words instead.

## After recording

1. Trim the start and end. Check the length is **90–100 seconds** and note the **exact number of seconds** (form Q14).
2. Upload to Google Drive (or YouTube as **Unlisted**).
3. Drive: Share → General access → **Anyone with the link** → Viewer. Copy the link.
4. Open the link in an **incognito window** to check it plays without signing in.
5. Put the link and exact length in the form (Q13, Q14) and in `docs/m2/links.json` (or send them to Claude to rebuild the PDF).
