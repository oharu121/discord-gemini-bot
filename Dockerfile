FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency files and README (needed for build)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/

# Expose port for HF Spaces
EXPOSE 7860

# Run the app (Gradio + Discord bot)
CMD ["uv", "run", "python", "-m", "src.main"]
