# --- STAGE 1: BUILDER ---
FROM python:3.14-slim AS builder

WORKDIR /app

# Copy only the requirements list first (optimizes Docker caching)
COPY requirements.txt .

# Install dependencies into a separate prefix folder (/install)
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- STAGE 2: RUNNER ---
FROM python:3.14-slim AS runner

WORKDIR /app

# Copy the pre-compiled packages from Stage 1 into our global python path
COPY --from=builder /install /usr/local

# Copy the rest of our application code
COPY . .

# Security: Create a system user 'appuser' with a home directory
# and make them the owner of the application folder
RUN useradd -m -r appuser && chown -R appuser:appuser /app

# Switch security context to our non-root user
USER appuser

# Inform Docker that the container will listen on port 8000 at runtime
EXPOSE 8000

# Start the web server (listening on 0.0.0.0 to accept external requests)
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
