# Prompt iteration experiment guide (iteration log, Milestone 2 Section 3)

Owner: **Karan Singh Saggu**. Time needed: about 1 hour, most of it waiting.

## What the three versions are

| Version | Files | In short |
|---|---|---|
| v1 | `prompts/v1/P0_baseline_single_prompt.md` | Milestone 1: one prompt writes 5 attacks, guesses each verdict and suggests a fix, as text lines |
| v2 | `prompts/v2/P2v2_attacks.md`, `prompts/v2/P3v2_predict_judge.md` | Split into an attack writer and a predict-and-judge prompt; 4 categories; JSON asked for in the text |
| v3 | `prompts/final/` (see `prompts/v3/README.md`) | Final: analysis step, structured output, safety rules, separate judge with checked evidence |

`code/tools/prompt_experiment.py` runs each version on the same 3 test chatbots, twice each, and
measures the same things for every version, so you can compare them with numbers.

## Steps

1. Set up the project first: see `docs/SETUP_FOR_TEAM.md`. **This task needs an API key** (step 4 of that guide), because its results must be real model output. Without one, the script stops with a message saying so.
2. From the `code` folder, run v1 on its own first and **look at the raw answers**:

   ```bash
   python -m tools.prompt_experiment --versions v1
   ```

   Open a few files in `test-data/outputs/prompt_experiment/<date>/` (e.g. `v1_copperleaf_run1.json`, the `raw` part).
   Write down what you notice: are lines missing or in the wrong format? Are attacks generic, or about this bot?
   Is any category missing? This is your evidence for **why** v2 was needed.
3. Run all three versions together, so the final comparison comes from one run (about 15 to 20 minutes, roughly 170 API calls):

   ```bash
   python -m tools.prompt_experiment
   ```

4. Open `summary.md` in the new results folder. It has one row per version:

   | Column | Meaning |
   |---|---|
   | Format OK | runs where every answer could be read by the program |
   | Parse failures | single answers that couldn't be read |
   | Categories (of 4) | how many attack types were covered |
   | Tailored % | attacks that mention something specific to that bot |
   | Unsafe | attacks with real-looking web domains or harmful topics |
   | Verdicts % | attacks that got a usable verdict and severity |
   | Evidence found % | judge's quotes really found in the reply (v3 only) |

5. Fill in `prompts/ITERATION_LOG.md`: the **Result** column, using the real numbers, and check the
   "Why" column matches what you saw in step 2. If something surprised you (for example v2 did better on
   something than v3), write it down honestly; that's worth marks.
6. Commit and push the results folder and the filled-in log:

   ```bash
   git add test-data/outputs/prompt_experiment prompts/ITERATION_LOG.md
   git commit -m "Run prompt iteration experiment v1-v3 and record results"
   git push
   ```

## What to send the team leader

- The number of prompt versions in the log (form Q18): 3.
- One clear before/after example for the reel: a v1 output and a v3 output for the same bot
  (for example `v1_copperleaf_run1.json` and `v3_copperleaf_run1.json`).
