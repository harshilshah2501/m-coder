#!/usr/bin/env bash
# Example: POST plan request to local plan-gate service
# Ensure service is running: python -m runtime.plan_gate_service.app
curl -X POST http://127.0.0.1:8089/v0/plan \
  -H "Content-Type: application/json" \
  -d @runtime/plan_gate_service/examples/curl_plan_request.json
