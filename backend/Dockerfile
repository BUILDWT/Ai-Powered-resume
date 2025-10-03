# --- Stage 1: Build Stage ---
# Use a Python image with build tools
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 2: Final Stage ---
# Use a slim Python image for the final application
FROM python:3.10-slim

WORKDIR /app

# Set non-root user for security
RUN useradd --create-home appuser
USER appuser

# Copy installed packages from the builder stage
COPY --from=builder /home/appuser/.local /home/appuser/.local

# Copy application code
COPY . .

# Ensure the path to installed packages is in PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Expose the port the app runs on
EXPOSE 8080

# Healthcheck to ensure the application is running
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Command to run the application using Uvicorn
# Gunicorn is often used in production, but Uvicorn is sufficient for Cloud Run
# The port is determined by the PORT environment variable, which Cloud Run sets automatically.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
