FROM python:3.11-slim

# Create non-root user required by Hugging Face Spaces & enterprise K8s
RUN useradd -m -u 1000 fdeuser
WORKDIR /app

COPY --chown=fdeuser:fdeuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=fdeuser:fdeuser ui/app.py ./ui/app.py

USER fdeuser
EXPOSE 7860

CMD ["streamlit", "run", "ui/app.py", "--server.port=7860", "--server.address=0.0.0.0"]