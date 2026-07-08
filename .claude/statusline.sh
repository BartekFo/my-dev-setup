#!/bin/bash
# Read JSON input from stdin
input=$(cat)

# ── Colors ────────────────────────────────────────────────────────────────────
GREEN=$(printf '\033[38;5;71m')
BRIGHT_GREEN=$(printf '\033[38;5;82m')
RED=$(printf '\033[38;5;196m')
YELLOW=$(printf '\033[38;5;220m')
GRAY=$(printf '\033[38;5;244m')
DARK_GRAY=$(printf '\033[38;5;238m')
RESET=$(printf '\033[0m')
BOLD=$(printf '\033[1m')

# ── Extract core values ───────────────────────────────────────────────────────
MODEL_DISPLAY=$(echo "$input" | jq -r '.model.display_name // "Unknown"')
CONTEXT_SIZE=$(echo "$input" | jq -r '.context_window.context_window_size // 0')
USED_PCT=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
TOTAL_INPUT_TOKENS=$(echo "$input" | jq -r '.context_window.total_input_tokens // empty')
FIVE_H_PCT=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
FIVE_H_RESET=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
SEVEN_D_PCT=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

# ── Context progress bar (line 1) ─────────────────────────────────────────────
BAR=""
if [ -n "$USED_PCT" ]; then
  USED_INT=$(printf '%.0f' "$USED_PCT")
  BAR_WIDTH=24
  FILLED=$(( USED_INT * BAR_WIDTH / 100 ))
  [ "$FILLED" -gt "$BAR_WIDTH" ] && FILLED=$BAR_WIDTH

  # Choose bar color based on usage
  if [ "$USED_INT" -ge 80 ]; then
    BAR_COLOR="$RED"
  elif [ "$USED_INT" -ge 50 ]; then
    BAR_COLOR="$YELLOW"
  else
    BAR_COLOR="$GREEN"
  fi

  BAR="${BAR_COLOR}"
  i=0
  while [ "$i" -lt "$FILLED" ]; do
    BAR="${BAR}█"
    i=$(( i + 1 ))
  done
  # Dotted remainder in dark gray
  BAR="${BAR}${DARK_GRAY}"
  while [ "$i" -lt "$BAR_WIDTH" ]; do
    BAR="${BAR}·"
    i=$(( i + 1 ))
  done
  TOKEN_LABEL=""
  if [ -n "$TOTAL_INPUT_TOKENS" ]; then
    if [ "$TOTAL_INPUT_TOKENS" -ge 1000 ] 2>/dev/null; then
      TOKEN_LABEL=" ${GRAY}($(( TOTAL_INPUT_TOKENS / 1000 ))k tokens)${RESET}"
    else
      TOKEN_LABEL=" ${GRAY}(${TOTAL_INPUT_TOKENS} tokens)${RESET}"
    fi
  fi
  BAR="${BAR}${RESET} ${BAR_COLOR}${USED_INT}%${RESET}${TOKEN_LABEL}"
else
  BAR="${DARK_GRAY}$(printf '%.0s·' {1..24})${RESET} ${GRAY}--%${RESET}"
fi

# ── Reasoning effort (line 1) ────────────────────────────────────────────────
EFFORT_PART=""
EFFORT_LEVEL=$(echo "$input" | jq -r '.effort.level // empty')
if [ -n "$EFFORT_LEVEL" ]; then
  EFFORT_UPPER=$(echo "$EFFORT_LEVEL" | tr '[:lower:]' '[:upper:]')
  PURPLE=$(printf '\033[38;5;141m')
  EFFORT_PART="  ${PURPLE}⚡${EFFORT_UPPER}${RESET}"
fi

# ── Repo + Git branch (line 1) ───────────────────────────────────────────────
BRANCH_PART=""
REPO_NAME=$(echo "$input" | jq -r '.workspace.repo.name // empty')
if [ -z "$REPO_NAME" ]; then
  PROJECT_DIR=$(echo "$input" | jq -r '.workspace.project_dir // empty')
  [ -n "$PROJECT_DIR" ] && REPO_NAME=$(basename "$PROJECT_DIR")
fi
BRANCH=$(git -C "${CWD:-$HOME}" branch --show-current 2>/dev/null)
if [ -z "$BRANCH" ]; then
  BRANCH=$(git branch --show-current 2>/dev/null)
fi
if [ -n "$REPO_NAME" ] && [ -n "$BRANCH" ]; then
  BRANCH_PART="  ${GREEN}🌿${RESET} ${BOLD}${REPO_NAME}${RESET}:${BRANCH}"
elif [ -n "$REPO_NAME" ]; then
  BRANCH_PART="  ${GREEN}🌿${RESET} ${BOLD}${REPO_NAME}${RESET}"
elif [ -n "$BRANCH" ]; then
  BRANCH_PART="  ${GREEN}🌿${RESET} ${BRANCH}"
fi

# ── Caveman badge (line 1) ────────────────────────────────────────────────────
CAVEMAN_PART=""
CAVEMAN_FLAG="$HOME/.claude/.caveman-active"
if [ -f "$CAVEMAN_FLAG" ]; then
  CAVEMAN_MODE=$(cat "$CAVEMAN_FLAG" 2>/dev/null)
  ORANGE=$(printf '\033[38;5;172m')
  if [ "$CAVEMAN_MODE" = "full" ] || [ -z "$CAVEMAN_MODE" ]; then
    CAVEMAN_PART="  ${ORANGE}[CAVEMAN]${RESET}"
  else
    CAVEMAN_SUFFIX=$(echo "$CAVEMAN_MODE" | tr '[:lower:]' '[:upper:]')
    CAVEMAN_PART="  ${ORANGE}[CAVEMAN:${CAVEMAN_SUFFIX}]${RESET}"
  fi
fi

# ── 5-hour rate limit (line 2) ────────────────────────────────────────────────
FIVE_H_PART=""
if [ -n "$FIVE_H_PCT" ]; then
  FIVE_H_INT=$(printf '%.0f' "$FIVE_H_PCT")
  TIME_REMAINING=""
  if [ -n "$FIVE_H_RESET" ] && [ "$FIVE_H_RESET" != "null" ]; then
    NOW=$(date +%s)
    DIFF=$(( FIVE_H_RESET - NOW ))
    if [ "$DIFF" -gt 0 ]; then
      HH=$(( DIFF / 3600 ))
      MM=$(( (DIFF % 3600) / 60 ))
      TIME_REMAINING=" ${GRAY}t=${HH}h${MM}m${RESET}"
    fi
  fi
  FIVE_H_PART="${GRAY}5h:${RESET} ${FIVE_H_INT}%${TIME_REMAINING}"
fi

# ── 7-day rate limit with delta vs 1/7th budget expectation (line 2) ──────────
SEVEN_D_PART=""
if [ -n "$SEVEN_D_PCT" ]; then
  SEVEN_D_INT=$(printf '%.0f' "$SEVEN_D_PCT")
  # Expected usage = today's fraction of the week (day 1 of 7 = ~14.3%, day 2 = ~28.6%, etc.)
  DOW=$(date +%u)  # 1=Mon … 7=Sun
  BUDGET_PCT=$(echo "$DOW" | awk '{printf "%.1f", $1 * 100 / 7}')
  DELTA=$(echo "$SEVEN_D_PCT $BUDGET_PCT" | awk '{printf "%.1f", $1 - $2}')
  DELTA_SIGN=$(echo "$DELTA" | cut -c1)
  if [ "$DELTA_SIGN" = "-" ]; then
    DELTA_COLOR="$GREEN"
  else
    DELTA_COLOR="$RED"
    DELTA="+${DELTA}"
  fi
  SEVEN_D_PART="${GRAY}7d:${RESET} ${SEVEN_D_INT}% ${DELTA_COLOR}(${DELTA}% vs budget)${RESET}"
fi

# ── Git diff stats (line 2) ───────────────────────────────────────────────────
GIT_DIFF_PART=""
GIT_STAT=$(git diff --shortstat HEAD 2>/dev/null)
if [ -z "$GIT_STAT" ]; then
  GIT_STAT=$(git diff --shortstat 2>/dev/null)
fi
if [ -n "$GIT_STAT" ]; then
  INSERTIONS=$(echo "$GIT_STAT" | grep -oE '[0-9]+ insertion' | grep -oE '[0-9]+' || echo "0")
  DELETIONS=$(echo "$GIT_STAT" | grep -oE '[0-9]+ deletion' | grep -oE '[0-9]+' || echo "0")
  [ -z "$INSERTIONS" ] && INSERTIONS=0
  [ -z "$DELETIONS" ] && DELETIONS=0
  GIT_DIFF_PART="${BRIGHT_GREEN}+${INSERTIONS}${RESET}/${RED}-${DELETIONS}${RESET}"
fi

# ── Model + context window size (line 2) ──────────────────────────────────────
if [ "$CONTEXT_SIZE" -ge 1000000 ] 2>/dev/null; then
  CTX_LABEL="$(( CONTEXT_SIZE / 1000000 ))M context"
elif [ "$CONTEXT_SIZE" -ge 1000 ] 2>/dev/null; then
  CTX_LABEL="$(( CONTEXT_SIZE / 1000 ))k context"
else
  CTX_LABEL="${CONTEXT_SIZE} context"
fi
MODEL_PART="${GRAY}${MODEL_DISPLAY} (${CTX_LABEL})${RESET}"

# ── Assemble lines ────────────────────────────────────────────────────────────
LINE1="${BAR}${EFFORT_PART}${BRANCH_PART}${CAVEMAN_PART}"

LINE2_PARTS=()
[ -n "$FIVE_H_PART" ]  && LINE2_PARTS+=("$FIVE_H_PART")
[ -n "$SEVEN_D_PART" ] && LINE2_PARTS+=("$SEVEN_D_PART")
[ -n "$GIT_DIFF_PART" ] && LINE2_PARTS+=("$GIT_DIFF_PART")
LINE2_PARTS+=("$MODEL_PART")

LINE2=""
for part in "${LINE2_PARTS[@]}"; do
  if [ -z "$LINE2" ]; then
    LINE2="$part"
  else
    LINE2="${LINE2}  ${part}"
  fi
done

printf "%s\n%s\n" "$LINE1" "$LINE2"
