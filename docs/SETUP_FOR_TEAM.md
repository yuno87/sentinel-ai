# Setting up Sentinel on your computer

About 10 minutes. You need Python 3.10 or newer (`python --version` to check) and Git.

## 1. Get the code

```bash
git clone https://github.com/yuno87/sentinel-ai.git
cd sentinel-ai
```

## 2. Create the virtual environment and install

Windows Command Prompt:

```bash
python -m venv .venv
.venv\Scripts\activate.bat
cd code
pip install -r requirements.txt
```

(PowerShell: `.venv\Scripts\Activate.ps1`. macOS/Linux: `source .venv/bin/activate`.)
Your prompt now starts with `(.venv)`. **Every command below runs from the `code` folder.**

## 3. Check it works

No API key is needed for this.

```bash
python -m pytest -q
```

You should see all tests pass (they don't use the API, so they're free). Then start the app:

```bash
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>, click **Try the example bot**, then **Scan my chatbot**. Without an API key the app
runs in **demo mode** (pre-written answers for the example bot). Stop it with `Ctrl + C`.

## 4. API key (only for real runs, later)

The test runner and the prompt experiment need real model answers, so they need an API key. When the team has one:

1. In the `code` folder, copy `.env.example` to a new file named `.env`.
2. Put the key after `ANTHROPIC_API_KEY=`.

**Never commit `.env` and never paste the key into a chat group or a document.** Git already ignores `.env`.
A key visible in the repo gives the whole team 0 for the repository part.

## 5. Saving your work to GitHub

After the team leader adds you as a collaborator (accept the email invite):

```bash
git add <the files you changed>
git commit -m "Short description of what you did"
git push
```

Your commits are the evidence for your part in the contribution table, so commit your own work yourself.
