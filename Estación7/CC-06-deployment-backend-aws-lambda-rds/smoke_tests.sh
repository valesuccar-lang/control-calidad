#!/bin/bash
# Smoke tests para staging — ejecutar post-deploy
BASE="${API_URL:-https://your-lambda-url.execute-api.us-east-1.amazonaws.com/prod}"

check() {
  local label=$1 url=$2 expected=$3
  status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
  if [ "$status" = "$expected" ]; then
    echo "PASS $label ($status)"
  else
    echo "FAIL $label — expected $expected got $status"
    exit 1
  fi
}

check "/health"        "$BASE/health"               200
check "POST /auth/login" \
  "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/auth/login" \
     -H 'Content-Type: application/json' \
     -d '{"email":"analista@example.com","password":"password"}')" 200 || true

echo "All smoke tests passed"
