#!/bin/bash
set -euo pipefail

config="${AEROSPACE_CONFIG:-$HOME/.config/aerospace/aerospace.toml}"
monitor='PL4594DQ'
center_gap=720
full_gap=10
mode="${1:-toggle}"

current_gap="$(/usr/bin/perl -ne 'if (/outer\.left = \[\{ monitor\."PL4594DQ" = ([0-9]+) \}, 10\]/) { print $1; exit }' "$config")"

case "$mode" in
  center)
    next_gap="$center_gap"
    ;;
  full)
    next_gap="$full_gap"
    ;;
  toggle)
    if [ "$current_gap" = "$center_gap" ]; then
      next_gap="$full_gap"
    else
      next_gap="$center_gap"
    fi
    ;;
  *)
    exit 2
    ;;
esac

/usr/bin/perl -0pi -e "s/outer\\.left = \\[\\{ monitor\\.\"$monitor\" = [0-9]+ \\}, 10\\]/outer.left = [{ monitor.\"$monitor\" = $next_gap }, 10]/g; s/outer\\.right = \\[\\{ monitor\\.\"$monitor\" = [0-9]+ \\}, 10\\]/outer.right = [{ monitor.\"$monitor\" = $next_gap }, 10]/g" "$config"

aerospace reload-config --dry-run --no-gui
aerospace reload-config --no-gui
