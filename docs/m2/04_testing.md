# 4. Demonstration and testing

{{tests_intro}}

## Test table

{{test_table}}

## Screenshots of real runs

Taken on 21 November 2026 by `code/tools/capture_screenshots.py`, which runs the app on Gemini 3.5 Flash-Lite and clicks through it in Chrome like a user. Each is a new real run of the named test's input, so its numbers can differ slightly from that test's row in the table (model answers vary between runs).

{{screenshot:T01_detail|Test T01 input, run in the app: launch call "Block launch" (4 of 8 attacks worked) and one failed attack opened, showing the injected email, the simulated reply and the evidence quote}}

{{screenshot:T01_report|Test T01 input, run in the app: all 8 attacks with result, severity and the judge's reason}}

{{screenshot:T07_retest|Test T07 flow, run in the app: after Suggest fixes, the re-test shows 4 fixed, 0 still failing, 0 new problems}}

## Known limitations and what we will try next

{{limitations}}
