# Container for the Sentinel AI prototype, for running it anywhere Docker runs.
# The AI key is NOT in this image: it is set as a secret in the Space settings
# (GEMINI_API_KEY or ANTHROPIC_API_KEY). With no secret, the app runs in demo mode.
FROM python:3.12-slim

WORKDIR /app
COPY code/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY code/ .

# The app listens on port 7860 inside the container.
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
