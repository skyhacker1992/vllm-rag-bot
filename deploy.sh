#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "Create .env from .env.example and set REPORTS_SECRET_KEY"
  cp -n .env.example .env 2>/dev/null || true
  exit 1
fi

set -a
source .env
set +a

if [[ -z "${REPORTS_SECRET_KEY:-}" || "${REPORTS_SECRET_KEY}" == "your-reports-secret-here" ]]; then
  echo "Set REPORTS_SECRET_KEY in .env (same value as Reports Hub)"
  exit 1
fi

echo "Starting NAOFPA LLM platform..."
docker compose -p naofpa-vllmproj up -d --build
echo ""
echo "Services:"
echo "  Gateway (S.A.R.A UI)  http://127.0.0.1:7862/?token=YOUR_JWT"
echo "  vLLM OpenAI API       http://127.0.0.1:8001/v1"
echo "  Prometheus            http://127.0.0.1:9190"
echo "  Grafana               http://127.0.0.1:3002  (admin/admin)"
echo ""
echo "Benchmark: ./benchmarks/compare_backends.sh"