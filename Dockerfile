# Container for the Sentinel AI prototype (used by Hugging Face Spaces).
# The AI key is NOT in this image: it is set as a secret in the Space settings
# (GEMINI_API_KEY or ANTHROPIC_API_KEY). With no secret, the app runs in demo mode.
FROM python:3.12-slim

WORKDIR /app
COPY code/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY code/ .

# Hugging Face Spaces sends web traffic to port 7860.
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
