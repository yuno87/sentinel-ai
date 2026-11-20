# Prompt iteration log

Results come from `code/tools/prompt_experiment.py`: each version was run on the same 3 test chatbots
(Copperleaf travel bot, ABC Bank HelpBot, Lumen Labs HR helper), 2 runs each, with the same model
(`claude-opus-5-5`). Raw outputs: `test-data/outputs/prompt_experiment/<date>/`.

| Version | What changed | Why it was changed | Result after the change |
|---|---|---|---|
| v1 | First prompt (Milestone 1): one prompt writes 5 attacks, guesses whether the bot resists each, and suggests a fix, as `Attack \| Type \| Verdict \| Severity \| Fix` lines | Starting point | _Fill in from summary.md: format OK x/6, parse failures, categories covered (of 4), tailored %, verdicts %_ |
| v2 | Split into two prompts (attack writer + predict-and-judge per attack); added the prompt-injection category; asked for JSON in the prompt text | v1's text lines were hard to read reliably, it never tested hidden instructions in pasted content (Milestone 1 reviewer feedback), and one prompt both guessed and judged the outcome. _Confirm against what you saw in v1's raw answers._ | _Fill in_ |
| v3 (final) | Added an analysis step first; structured output with a schema validated by Pydantic; safety rules for attack content; prediction and judging as separate calls; judge must quote evidence that code checks; XML tags around untrusted text; IDs and launch call assigned by code | _Fill in from what v2's results showed (for example JSON that broke, generic attacks, verdicts without evidence)_ | _Fill in_ |

## Observations

_Write 3 to 5 sentences on what the numbers show, including anything that didn't improve._

## Full text of each version

- v1: `prompts/v1/P0_baseline_single_prompt.md`
- v2: `prompts/v2/P2v2_attacks.md`, `prompts/v2/P3v2_predict_judge.md`
- v3: `prompts/final/P1_analyse.md` to `P5_harden.md`

(For the PDF, paste the full text of each file below the table.)
