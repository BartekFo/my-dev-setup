#!/bin/bash
set -u

sleep 0.2

focused_window="$(aerospace list-windows --focused --format '%{window-id}|%{workspace}|%{app-bundle-id}' 2>/dev/null || true)"
[ -n "$focused_window" ] || exit 0

IFS='|' read -r window_id workspace app_id <<< "$focused_window"
[ "$app_id" = 'com.mitchellh.ghostty' ] || exit 0

ghostty_count="$(aerospace list-windows --workspace "$workspace" --app-bundle-id com.mitchellh.ghostty --count 2>/dev/null || printf '0')"
case "$ghostty_count" in
  ''|*[!0-9]*)
    exit 0
    ;;
esac

if [ "$ghostty_count" -ge 3 ]; then
  aerospace join-with --window-id "$window_id" left >/dev/null 2>&1 || true
fi
