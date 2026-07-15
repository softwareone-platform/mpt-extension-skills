# Test runner image for the skill-script pytest suite.
# Dependencies are managed with uv (pyproject.toml + uv.lock).
FROM python:3.12-slim

# uv binary from the official distroless image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Keep the environment outside /work so the runtime bind-mount does not shadow it.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /work

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --only-group dev

CMD ["/opt/venv/bin/python", "-m", "pytest"]
