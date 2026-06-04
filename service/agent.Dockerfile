FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

COPY app/ ./app/
COPY runtime_entry.py ./

CMD ["uv", "run", "python", "runtime_entry.py"]
