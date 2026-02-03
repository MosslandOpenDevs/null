#!/bin/bash
# 9-hour simulation monitor — logs every 30 minutes
WORLD_ID="b578faf4-3846-4094-8023-6ca093fa2d6c"
API="http://localhost:3301/api"
LOG="/Users/wooramson/Documents/GitHub/null/simulation_monitor.log"
DURATION=$((9 * 60 * 60))  # 9 hours in seconds
INTERVAL=1800               # 30 minutes

echo "=== Simulation Monitor Started: $(date) ===" > "$LOG"
echo "World: $WORLD_ID" >> "$LOG"
echo "Duration: 9 hours | Interval: 30 min" >> "$LOG"
echo "========================================" >> "$LOG"

START=$(date +%s)

while true; do
  NOW=$(date +%s)
  ELAPSED=$(( NOW - START ))
  if [ $ELAPSED -ge $DURATION ]; then
    echo "" >> "$LOG"
    echo "=== MONITOR COMPLETE: $(date) ===" >> "$LOG"
    break
  fi

  HOURS=$(( ELAPSED / 3600 ))
  MINS=$(( (ELAPSED % 3600) / 60 ))

  echo "" >> "$LOG"
  echo "--- [+${HOURS}h${MINS}m] $(date '+%Y-%m-%d %H:%M:%S') ---" >> "$LOG"

  # World status
  curl -s "$API/worlds/$WORLD_ID" 2>/dev/null | python3 -c "
import sys,json
try:
  w=json.load(sys.stdin)
  print(f'Status: {w[\"status\"]}  Epoch: {w[\"current_epoch\"]}  Tick: {w[\"current_tick\"]}')
except: print('ERROR: Could not fetch world')
" >> "$LOG" 2>&1

  # Wiki pages
  curl -s "$API/worlds/$WORLD_ID/wiki" 2>/dev/null | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin); print(f'Wiki pages: {len(d)}')
except: print('Wiki: error')
" >> "$LOG" 2>&1

  # Strata
  curl -s "$API/worlds/$WORLD_ID/strata" 2>/dev/null | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin); print(f'Strata: {len(d)}')
except: print('Strata: error')
" >> "$LOG" 2>&1

  # Entity graph
  curl -s "$API/worlds/$WORLD_ID/entity-graph" 2>/dev/null | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  print(f'Entity nodes: {len(d.get(\"nodes\",[]))}  Edges: {len(d.get(\"edges\",[]))}')
except: print('Entity graph: error')
" >> "$LOG" 2>&1

  # Recent messages count
  curl -s "$API/worlds/$WORLD_ID/recent-messages?limit=50" 2>/dev/null | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin); print(f'Recent messages: {len(d)}')
except: print('Messages: error')
" >> "$LOG" 2>&1

  # Factions agent counts
  curl -s "$API/worlds/$WORLD_ID/factions" 2>/dev/null | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  total=sum(f.get('agent_count',0) for f in d)
  print(f'Factions: {len(d)}  Total agents: {total}')
except: print('Factions: error')
" >> "$LOG" 2>&1

  # Check if Ollama is alive
  curl -s --max-time 5 http://localhost:11434/api/tags >/dev/null 2>&1
  if [ $? -eq 0 ]; then
    echo "Ollama: alive" >> "$LOG"
  else
    echo "Ollama: DOWN — attempting restart notification" >> "$LOG"
  fi

  sleep $INTERVAL
done
