#!/usr/bin/env bash

set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
show_diff=0
verbose=0
max_reports=200
report_count=0
suppressed_count=0

usage() {
  cat <<'EOF'
Usage: ./validate.sh [--diff] [--verbose] [--all] [--max-reports N]

Validates that tracked config files in this repository match the files currently
installed on this machine:

  .zshrc              -> ~/.zshrc
  .bashrc             -> ~/.bashrc
  .gitconfig          -> ~/.gitconfig
  starship.toml       -> ~/.config/starship.toml
  .agents/            -> ~/.agents/
  .claude/            -> ~/.claude/
  zed/                -> ~/.config/zed/
  ghostty/            -> ~/.config/ghostty/
  macbook/aerospace/  -> ~/.config/aerospace/   (on macOS or when target exists)

Only git-tracked files are checked inside directories, so local caches/history in
~/.claude or ~/.config are ignored. Symlinks are validated semantically: a repo
symlink to a repo-local path may point to the corresponding $HOME path.

Options:
  --diff           Show unified diffs for changed regular files
  --verbose        Print matching files too
  --all            Print all mismatches instead of capping output
  --max-reports N  Max mismatch lines to print (default: 200; 0 = all)
  -h, --help       Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --diff)
      show_diff=1
      ;;
    --verbose)
      verbose=1
      ;;
    --all)
      max_reports=0
      ;;
    --max-reports)
      shift
      if [[ $# -eq 0 || ! "$1" =~ ^[0-9]+$ ]]; then
        echo "--max-reports requires a non-negative integer" >&2
        exit 2
      fi
      max_reports="$1"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if ! git -C "$repo_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: $repo_dir is not inside a git repository" >&2
  exit 2
fi

ok_count=0
changed_count=0
missing_count=0
type_count=0

canonicalize() {
  local path="$1"
  if command -v realpath >/dev/null 2>&1; then
    realpath "$path"
  else
    python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$path"
  fi
}

relative_to_repo() {
  local path="$1"
  case "$path" in
    "$repo_dir"/*) printf '%s' "${path#"$repo_dir"/}" ;;
    *) printf '%s' "$path" ;;
  esac
}

should_skip_tracked_path() {
  local path="$1"
  case "$path" in
    .claude/plugins/cache/*|.claude/plugins/install-counts-cache.json)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

record_ok() {
  ok_count=$((ok_count + 1))
  if [[ "$verbose" == "1" ]]; then
    echo "OK      $1"
  fi
}

report_mismatch() {
  local line="$1"

  if [[ "$max_reports" == "0" || "$report_count" -lt "$max_reports" ]]; then
    echo "$line"
    report_count=$((report_count + 1))
  else
    suppressed_count=$((suppressed_count + 1))
  fi
}

record_changed() {
  changed_count=$((changed_count + 1))
  report_mismatch "CHANGED $1"
}

record_missing() {
  missing_count=$((missing_count + 1))
  report_mismatch "MISSING $1"
}

record_type() {
  type_count=$((type_count + 1))
  report_mismatch "TYPE    $1"
}

show_file_diff() {
  local src="$1"
  local dst="$2"

  if [[ "$show_diff" != "1" ]]; then
    return
  fi

  if [[ -f "$src" && -f "$dst" && ! -L "$src" && ! -L "$dst" ]]; then
    diff -u --label "repo:$(relative_to_repo "$src")" --label "machine:${dst#"$HOME"/}" "$src" "$dst" || true
  fi
}

compare_symlink() {
  local src="$1"
  local dst="$2"
  local label="$3"

  if [[ ! -L "$dst" ]]; then
    record_type "$label (repo is symlink, machine is not)"
    return
  fi

  local src_real dst_real expected_dst_real
  src_real="$(canonicalize "$src")"
  dst_real="$(canonicalize "$dst")"

  expected_dst_real="$src_real"
  if [[ "$src_real" == "$repo_dir/"* ]]; then
    expected_dst_real="$HOME/${src_real#"$repo_dir"/}"
  fi

  if [[ "$dst_real" == "$src_real" || "$dst_real" == "$expected_dst_real" ]]; then
    record_ok "$label"
  else
    record_changed "$label (symlink target repo=$src_real machine=$dst_real expected=$expected_dst_real)"
  fi
}

compare_one() {
  local src="$1"
  local dst="$2"
  local label="$3"

  if [[ ! -e "$src" && ! -L "$src" ]]; then
    record_missing "$label (repo source missing: $src)"
    return
  fi

  if [[ ! -e "$dst" && ! -L "$dst" ]]; then
    record_missing "$label -> $dst"
    return
  fi

  if [[ -L "$src" ]]; then
    compare_symlink "$src" "$dst" "$label"
    return
  fi

  if [[ -d "$src" ]]; then
    if [[ -d "$dst" ]]; then
      record_ok "$label"
    else
      record_type "$label (repo is directory, machine is not)"
    fi
    return
  fi

  if [[ -f "$src" ]]; then
    if [[ ! -f "$dst" ]]; then
      record_type "$label (repo is file, machine is not)"
      return
    fi

    if cmp -s "$src" "$dst"; then
      record_ok "$label"
    else
      record_changed "$label"
      show_file_diff "$src" "$dst"
    fi
    return
  fi

  record_type "$label (unsupported file type)"
}

check_file() {
  local src_rel="$1"
  local dst="$2"

  compare_one "$repo_dir/$src_rel" "$dst" "$src_rel"
}

check_tracked_tree() {
  local src_rel="$1"
  local dst_root="$2"
  local tracked any=0 rel dst

  if [[ ! -e "$dst_root" && ! -L "$dst_root" ]]; then
    record_missing "$src_rel/ -> $dst_root"
    return
  fi

  while IFS= read -r -d '' tracked; do
    if should_skip_tracked_path "$tracked"; then
      continue
    fi

    any=1
    if [[ "$tracked" == "$src_rel" ]]; then
      rel=""
    else
      rel="${tracked#"$src_rel"/}"
    fi

    if [[ -n "$rel" ]]; then
      dst="$dst_root/$rel"
    else
      dst="$dst_root"
    fi

    compare_one "$repo_dir/$tracked" "$dst" "$tracked"
  done < <(git -C "$repo_dir" ls-files -z -- "$src_rel")

  if [[ "$any" == "0" ]]; then
    record_missing "$src_rel (no tracked files)"
  fi
}

cd "$repo_dir"

echo "Validating repository configs against installed machine files..."
echo "Repo:    $repo_dir"
echo "Machine: $HOME"
echo

check_file ".zshrc" "$HOME/.zshrc"
check_file ".bashrc" "$HOME/.bashrc"
check_file ".gitconfig" "$HOME/.gitconfig"
check_file "starship.toml" "$HOME/.config/starship.toml"

check_tracked_tree ".agents" "$HOME/.agents"
check_tracked_tree ".claude" "$HOME/.claude"
check_tracked_tree "zed" "$HOME/.config/zed"
check_tracked_tree "ghostty" "$HOME/.config/ghostty"

if [[ "$(uname -s)" == "Darwin" || -e "$HOME/.config/aerospace" || -L "$HOME/.config/aerospace" ]]; then
  check_tracked_tree "macbook/aerospace" "$HOME/.config/aerospace"
fi

echo
if [[ "$suppressed_count" -gt 0 ]]; then
  echo "... suppressed $suppressed_count additional mismatch line(s); rerun with --all to print everything."
  echo
fi
printf 'Summary: %d ok, %d changed, %d missing, %d type mismatch\n' \
  "$ok_count" "$changed_count" "$missing_count" "$type_count"

if [[ "$changed_count" -gt 0 || "$missing_count" -gt 0 || "$type_count" -gt 0 ]]; then
  exit 1
fi
