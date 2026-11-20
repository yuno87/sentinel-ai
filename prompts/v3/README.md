# v3

v3 is the 5-step pipeline (P1 Analyse, P2 Attacks, P3 Predict, P4 Judge, P5 Harden).
Only P3 changed between v3 and v4, so only v3's P3 is saved here:
`P3v3_predict.md`. The other four v3 prompts are identical to `prompts/final/`.

Changes from v2:
- Added an analysis step (P1) first, so attacks target the bot's actual rules (R1, R2...) and protected assets.
- Structured output: each step's JSON schema is sent with the request and the answer is validated with Pydantic.
- Safety rules in the attack prompt (no genuinely harmful content, made-up names, example.com only), plus a code check.
- Predicting the reply and judging it are separate calls (P3 and P4), so the judge doesn't grade its own prediction.
- The judge must quote exact evidence from the reply, and code checks that the quote is really there.
- Untrusted text (the prompt under test, attacks, replies) is wrapped in XML tags.
- Attack IDs (INJ-01...) and the launch call are assigned by code, not the model.

v4 (the final version, `prompts/final/`) rewrote P3 only: see `prompts/ITERATION_LOG.md`.
