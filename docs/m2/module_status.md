| Module | What it does | Status | Notes |
|---|---|---|---|
| Prompt analysis (P1) | Reads the system prompt and lists purpose, rules R1..Rn, protected assets, capabilities and weak spots | Working | Found the planted secret in every test that had one, including the Hindi prompt (T09); not fooled by a prompt that told it to report no weak spots (T10) |
| Attack generation (P2) | Writes attacks tailored to the bot in 4 categories; code assigns IDs (INJ-01...) and screens out unsafe content | Working | 4 of 4 categories in every run; 0 unsafe attacks in 48 experiment attacks |
| Simulated replies (P3) | Predicts how a typical chatbot with this prompt would reply; always labelled as a prediction | Working | v4 finds far more real weaknesses than v3 (31 % vs 2 % of attacks), but can still be too optimistic for bots with explicit "never" rules (T03) |
| Live chatbot testing | Sends each attack to a real chatbot's web address and records the real reply; "Test connection" button | Working | Tested against the included practice chatbot (T06) and an address that doesn't exist (T15); not yet tested on a third-party chatbot |
| Judging with evidence (P4) | Separate call: Pass/Fail, severity, one-line reason, exact quote; code checks the quote is in the reply | Working | 100 % of evidence quotes found in the replies; severity can be too high when the leaked text isn't sensitive (T05) |
| Launch call and report | Plain-code launch call (Block / Hold / Fix before launch / No failures found / Not tested) and the filterable results table | Working | "Not tested" added after building test T15 |
| Fixes and hardened prompt (P5) | Suggests prompt and app fixes linked to failed attacks, rewrites the prompt, shows what changed | Working | First run of T07 failed on a schema bug (a field named "title" was dropped); fixed and re-run |
| Re-test comparison | Runs the same attacks on the hardened prompt; shows fixed / still failing / new failures | Working | Tested in T07 |
| Markdown and CSV export | Downloads the full report and the results table | Working | Every test saved a Markdown report (`test-data/outputs/Txx_report.md`) |
| Demo mode | Runs the full flow with no API key, using pre-written answers for the example bot, clearly labelled | Working | Only works with the built-in example prompt |
