# Stage 1: Build stage
FROM python:3.9-slim as builder

WORKDIR /app

# Copy only the requirements file first to leverage Docker caching
COPY requirements.txt .

# Install dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.9-slim

WORKDIR /app

# Copy only the virtual environment and necessary files
COPY --from=builder /opt/venv /opt/venv
COPY . .

# Set the environment variables
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port
EXPOSE 6969

# Run the application
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "6969"]
