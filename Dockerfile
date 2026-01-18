FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency files and README (needed for build)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code and app
COPY src/ ./src/
COPY app.py ./

# Expose Gradio port (HF Spaces expects 7860)
EXPOSE 7860

# Run the Gradio app
CMD ["uv", "run", "python", "app.py"]
