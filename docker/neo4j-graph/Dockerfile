FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY tools/ast_indexer/requirements.txt /tmp/ast-indexer-requirements.txt
RUN pip install --no-cache-dir -r /tmp/ast-indexer-requirements.txt

CMD ["bash"]