#!/usr/bin/env bash

LOKI_URL="http://localhost:3100/loki/api/v1/push"

send_log() {
  local app="$1"
  local env="$2"
  local level="$3"
  local status="$4"
  local method="$5"
  local path="$6"
  local status_code="$7"
  local duration_ms="$8"
  local trace_id="$9"
  local message="${10}"
  local db_queries_count="${11:-0}" # Default 0 se vazio
  local db_failed_count="${12:-0}"  # Default 0 se vazio

  local timestamp_ns
  timestamp_ns=$(date +%s%N)
  local iso_ts
  iso_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  local json_log
  json_log=$(jq -nc --arg ts "$iso_ts" \
                    --arg lvl "$level" \
                    --arg app "$app" \
                    --arg ver "1.0.0" \
                    --arg trace "$trace_id" \
                    --arg st "$status" \
                    --arg msg "$message" \
                    --arg mtd "$method" \
                    --arg pth "$path" \
                    --arg ip "192.168.1.10" \
                    --argjson sc "${status_code:-200}" \
                    --argjson dur "${duration_ms:-0}" \
                    --argjson dbq "$db_queries_count" \
                    --argjson dbf "$db_failed_count" \
                    '{
                        timestamp: $ts,
                        level: $lvl,
                        app: $app,
                        version: $ver,
                        trace_id: $trace,
                        status: $st,
                        message: $msg,
                        method: $mtd,
                        path: $pth,
                        status_code: $sc,
                        duration_ms: $dur,
                        client_ip: $ip,
                        db_queries_count: $dbq,
                        db_failed_count: $dbf
                      }')

  curl -s -H "Content-Type: application/json" -XPOST "$LOKI_URL" -d "{
    \"streams\": [{
      \"stream\": { \"source\": \"api\", \"app\": \"$app\", \"env\": \"$env\" },
      \"values\": [[ \"$timestamp_ns\", \"${json_log//\"/\\\"}\" ]]
    }]
  }" > /dev/null
}

echo "Enviando logs para Loki em $LOKI_URL..."

COUNT=20

# ============================================================
# HERMES – rápido (~50–150 ms), ~3% erro
# ============================================================
echo ">> HERMES (~3% erro, rápido)"
for i in $(seq 1 $COUNT); do
  dur=$((50 + (RANDOM % 100)))
  send_log "hermes" "production" "INFO" "SUCCESS" "POST" "/send" 200 "$dur" "trace-hermes-$i" "Message sent" 2 0
done
send_log "hermes" "production" "WARNING" "FAILED" "POST" "/send" 400 120 "trace-hermes-err-1" "Invalid payload" 1 0

# ============================================================
# PILAR – médio (~250–900 ms), ~20% erro
# ============================================================
echo ">> PILAR (~20% erro, médio)"
for i in $(seq 1 $COUNT); do
  dur=$((250 + (RANDOM % 300)))
  send_log "pilar" "production" "INFO" "SUCCESS" "GET" "/data" 200 "$dur" "trace-pilar-$i" "Data fetched" 3 0
done
for i in $(seq 1 5); do
  dur=$((700 + (RANDOM % 300)))
  send_log "pilar" "production" "ERROR" "FAILED" "GET" "/data" 500 "$dur" "trace-pilar-err-$i" "DB Error" 4 2
done

# ============================================================
# REPORTS – muito lento (~3000–6000 ms), 0% erro
# ============================================================
echo ">> REPORTS (0% erro, muito lento)"
for i in $(seq 1 $COUNT); do
  dur_fast=$((3000 + (RANDOM % 1000)))
  dur_slow=$((4500 + (RANDOM % 1500)))
  send_log "reports" "production" "INFO" "SUCCESS" "GET" "/export" 200 "$dur_fast" "trace-rep-$i" "Report OK" 10 0
  send_log "reports" "production" "WARNING" "SUCCESS" "GET" "/export" 200 "$dur_slow" "trace-rep-slow-$i" "Slow Report" 12 0
done

# ============================================================
# CONTROLLER – médio-rápido (~250–800 ms), ~11% erro
# ============================================================
echo ">> CONTROLLER (~11% erro, médio-rápido)"
for i in $(seq 1 $COUNT); do
  dur=$((250 + (RANDOM % 250)))
  send_log "controller" "production" "INFO" "SUCCESS" "POST" "/run" 201 "$dur" "trace-ctrl-$i" "Triggered" 2 0
done
for i in $(seq 1 2); do
  dur=$((600 + (RANDOM % 200)))
  send_log "controller" "production" "ERROR" "FAILED" "POST" "/run" 500 "$dur" "trace-ctrl-err-$i" "Failed" 3 1
done

# ============================================================
# ZAP_ZAP – bem rápido (~30–120 ms), ~9% erro
# ============================================================
echo ">> ZAP_ZAP (~9% erro, bem rápido)"
for i in $(seq 1 $COUNT); do
  dur=$((30 + (RANDOM % 70)))
  send_log "zap_zap" "production" "INFO" "SUCCESS" "POST" "/message" 200 "$dur" "trace-zap-$i" "Sent" 1 0
done
for i in $(seq 1 2); do
  dur=$((40 + (RANDOM % 40)))
  send_log "zap_zap" "production" "WARNING" "FAILED" "POST" "/message" 400 "$dur" "trace-zap-err-$i" "Invalid Num" 1 0
done

# ============================================================
# DIQUE – médio (~80–400 ms), ~30% erro
# ============================================================
echo ">> DIQUE (~30% erro, médio)"
for i in $(seq 1 $COUNT); do
  dur=$((80 + (RANDOM % 120)))
  send_log "dique" "production" "INFO" "SUCCESS" "POST" "/filter" 200 "$dur" "trace-dique-$i" "Filtered" 1 0
done
for i in $(seq 1 8); do
  dur=$((250 + (RANDOM % 200)))
  send_log "dique" "production" "ERROR" "FAILED" "POST" "/filter" 500 "$dur" "trace-dique-err-$i" "Rule Error" 2 1
done

echo "Concluído sem erros de JQ!"