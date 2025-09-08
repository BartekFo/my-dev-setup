#!/bin/bash

# Script to run all setup scripts using the script runner
# Usage: ./setup.sh [mac] [--dry]

script_dir=$(dirname "$(readlink -f "$0")")
is_mac=false
dry_run=""

# Parse arguments
while [[ $# > 0 ]]; do
    case "$1" in
        "mac")
            is_mac=true
            ;;
        "--dry")
            dry_run="--dry"
            ;;
    esac
    shift
done

cd "$script_dir"

echo "Starting dotfiles setup using script runner..."

# Run core setup scripts
./run.sh $dry_run "01-dotfiles"
./run.sh $dry_run "02-claude" 
./run.sh $dry_run "03-zed"
./run.sh $dry_run "05-neovim"

# Run mac-specific setup if requested
if [[ "$is_mac" == true ]]; then
    echo "Mac setup detected, running aerospace setup..."
    ./run.sh $dry_run "04-aerospace-mac"
else
    echo "Skipping aerospace config (not mac setup)"
fi

echo "Dotfiles setup complete!"