FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.11 /uv /uvx /bin/
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
COPY backend/pyproject.toml backend/pyproject.toml
COPY frontend/pyproject.toml frontend/pyproject.toml
RUN uv sync --locked --no-dev --package frontend
COPY frontend frontend
RUN useradd --create-home app
USER app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8501
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
