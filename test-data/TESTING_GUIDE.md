# Testing guide (test table, Milestone 2 Section 4)

How the test table is produced. Time needed: about 30 minutes, most of it waiting.

## What's already here

- `inputs/T01.json` to `inputs/T15.json`: 15 test inputs (7 Normal, 5 Edge, 3 Invalid), each with
  the input, its type and the **expected output**.
- `code/tools/run_tests.py`: runs every input through the app's real API and saves what comes back.

## Steps

1. Set up the project first: see `docs/SETUP_FOR_TEAM.md`. **This task needs an API key** (step 4 of that guide), because its results must be real model output. Without one, the script stops with a message saying so.
2. From the `code` folder, run all the tests (about 15 to 25 minutes, roughly 250 API calls):

   ```bash
   python -m tools.run_tests
   ```

   To re-run only some tests: `python -m tools.run_tests T09 T10`.
3. Open `test-data/test_table.md`. The **Actual output** column is filled in automatically.
4. **Your job: decide Pass or Fail for each row by hand.** For each test:
   - Read the expected output.
   - Open `outputs/Txx_report.md` (the full report) and check whether the expected things really happened.
     For example, for T10, check the weak spots list really mentions the "report no weak spots" note.
   - Replace `_fill in_` with **Pass** or **Fail**. If it's a Fail, add a few words saying why.
   - **Be honest.** The guidelines say failed tests are fine but hiding failures is not, and an all-pass
     table with no edge cases gets lower marks. 
5. Take **2 to 3 screenshots of real runs** in the app (browser at <http://127.0.0.1:8000>):
   - Run the same input as T01 (Try the example bot, Scan), and screenshot the **Report** tab. Caption: "Test T01".
   - Open a failed row so the attack and evidence show, and screenshot it. Caption: "Test T01, attack detail".
   - Do T07 in the app (Fix & re-test tab), and screenshot the before/after table. Caption: "Test T07".
   - Save them in `docs/screenshots/` as `T01_report.png`, `T01_detail.png`, `T07_retest.png`.
6. Commit and push the outputs, the filled-in table and the screenshots:

   ```bash
   git add test-data docs/screenshots
   git commit -m "Run Milestone 2 test inputs and record results"
   git push
   ```

