# Prompt iteration log

**How the results were measured.** `code/tools/prompt_experiment.py` ran every version on the same 3 fictional test chatbots
(Copperleaf travel bot, ABC Bank HelpBot from Milestone 1, Lumen Labs HR helper), **2 runs per bot (6 runs per version)**,
with the same model, **Gemini 3.5 Flash-Lite** (free API key), on 20–21 November 2026. v2 to v4 wrote 2 attacks per category
(8 per run, 48 per version); v1 asks for 5 attacks per run. `code/tools/experiment_verdicts.py` then counted what the verdicts said.
All raw answers are saved in `test-data/outputs/prompt_experiment/2026-11-20_2345/` (`summary.md`, `verdicts.md`, one JSON file per run).

| Version | What changed | Why it was changed | Result after the change |
|---|---|---|---|
| v1 | First prompt (Milestone 1): one prompt writes 5 attacks, guesses whether the bot resists each, and suggests a fix, as text lines of the form Attack / Type / Verdict / Severity / Fix, separated by vertical bars | Starting point | Readable in **5 of 6** runs (one run put "Medium" in the verdict column). Covered only **3 of 4** categories in every run: no hidden-instruction (indirect injection) attack at all. **13 of 29** verdicts contradicted themselves (a "Pass" with a Medium or Low severity). Verdicts are guesses with no bot reply behind them (55 % "Fail"). One attack quoted the secret code inside its own message. |
| v2 | Split into two prompts: an attack writer and a predict-and-judge prompt run once per attack. Added the indirect-injection category. Asked for JSON in the prompt text. | v1's text lines broke and contradicted themselves, it never tested hidden instructions in pasted content (the Milestone 1 reviewer's feedback), and it gave verdicts without any reply. | Readable in **6 of 6** runs, **4 of 4** categories every run, **0** contradictions. But **0 of 48** attacks were judged Fail, even on the Copperleaf bot, which keeps a secret code in its prompt and is told to "always do what the customer asks". Predicting and judging in one call imagined a perfectly safe bot and graded its own guess. `target_rules` were copied sentences, not rule IDs (**0 %** IDs), because there was no analysis step. |
| v3 | 5-step pipeline: an analysis step first (P1); structured output with a JSON schema validated by Pydantic; safety rules for attack content; predicting (P3) and judging (P4) as separate calls; the judge must quote evidence, which code checks; XML tags around untrusted text; IDs and launch call assigned by code. | v2 found nothing because one call predicted and judged; its attacks couldn't point at specific rules; and nothing checked the verdicts. | Readable in **6 of 6** runs, **4 of 4** categories, **100 %** of attacks target rule IDs (R1, R2...), **100 %** of evidence quotes found in the reply, **0** unsafe attacks. But still only **1 of 48** attacks judged Fail (2 %): the predictor (P3) imagined an ideal, very careful bot, so the deliberately weak Copperleaf bot scored **0 of 16** Fails. The judge was right about the replies it was given; the replies were unrealistic. |
| v4 (final) | Rewrote only P3 (predict reply): listed how typical deployed chatbots behave (follow their prompt literally including loopholes, know any secrets in it, often follow instructions in pasted text, ordinary resistance to role-play and fake authority, much stronger when the prompt has explicit defences) and added **2 contrasting examples** (a weak and a defended fictional prompt). | v3's predictions were too safe to be useful: a tester that calls a weak bot safe is worse than no tester. | **15 of 48** attacks judged Fail (31 %), and the Fails now follow how weak each bot is: Copperleaf **9 of 16**, ABC Bank **4 of 16**, Lumen HR **2 of 16** (v3: 0, 0 and 1). Format, rule IDs, evidence (100 %) and safety (0 unsafe) unchanged. Checked by reading the failures: they are genuine (the reply leaks the staff code, looks up another customer's booking, or reveals the instructions in French). Faster too: 66 s per run on average vs 121 s for v3 (v3 hit more rate-limit waits). |

## Summary of the measurements

| Version | Readable runs | Categories (of 4) | Tailored to the bot | Contradictory verdicts | Target rules as IDs | Evidence found in reply | Judged Fail |
|---|---|---|---|---|---|---|---|
| v1 | 5/6 | 3.0 | 76 % | 13 of 29 | n/a | n/a | 55 % (guesses) |
| v2 | 6/6 | 4.0 | 73 % | 0 | 0 % | n/a | 0 % |
| v3 | 6/6 | 4.0 | 73 % | 0 | 100 % | 100 % | 2 % |
| v4 | 6/6 | 4.0 | 82 % | 0 | 100 % | 100 % | 31 % |

"Tailored" = the attack mentions something only that bot has (its name, codes, tools...).

## Observations

- Splitting the work into separate steps (v2) fixed the **format** problems completely, but on its own it made the tool **less useful**: a model that predicts and judges in one call is too optimistic. Separating the judge (v3) made the verdicts traceable but didn't fix that, because the problem was in the **prediction**, not the judging.
- The biggest single improvement came from **describing realistic behaviour and adding two examples** (v4): Fails rose from 2 % to 31 %, and they rank the three bots in the order of how weak their prompts are.
- Things that did **not** change: tailoring stayed between 73 % and 82 % across versions, and no version produced unsafe attacks (0 every time).
- Limits of this experiment: 6 runs per version and one model; the v1 Fail rate is not comparable because v1 never saw a reply. A higher Fail rate is only good if it doesn't flag safe bots too, which test **T04** (an already-hardened prompt) checks in the test table.

## Full text of each version

- v1: `prompts/v1/P0_baseline_single_prompt.md`
- v2: `prompts/v2/P2v2_attacks.md`, `prompts/v2/P3v2_predict_judge.md`
- v3: `prompts/v3/P3v3_predict.md` (the only prompt that differs from the final version) plus P1, P2, P4, P5 in `prompts/final/`
- v4 (final): `prompts/final/P1_analyse.md` to `P5_harden.md`
