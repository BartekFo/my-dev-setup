#!/bin/bash

# Script to copy dotfiles to home directory
# Usage: ./setup.sh [mac]

script_dir=$(dirname "$(readlink -f "$0")")
is_mac=false

# Check if 'mac' argument is passed
if [[ "$1" == "mac" ]]; then
    is_mac=true
fi

# Function to execute commands with logging
execute() {
    echo "Executing: $*"
    "$@"
}

# Function to copy directories
copy_dir() {
    local from_dir="$1"
    local to_dir="$2"
    
    if [[ -d "$from_dir" ]]; then
        echo "Copying $from_dir to $to_dir"
        execute rm -rf "$to_dir"
        execute cp -r "$from_dir" "$to_dir"
    else
        echo "Warning: $from_dir does not exist"
    fi
}

# Function to copy files
copy_file() {
    local from_file="$1"
    local to_file="$2"
    
    if [[ -f "$from_file" ]]; then
        echo "Copying $from_file to $to_file"
        execute cp "$from_file" "$to_file"
    else
        echo "Warning: $from_file does not exist"
    fi
}

cd "$script_dir"

echo "Starting dotfiles setup..."

# 1. Copy .zshrc, .bashrc, and .p10k.zsh to $HOME/
copy_file ".zshrc" "$HOME/.zshrc"
copy_file ".bashrc" "$HOME/.bashrc"
copy_file ".p10k.zsh" "$HOME/.p10k.zsh"

# 2. Run .claude setup and copy non-bash files to $HOME/
if [[ -f ".claude/setup.sh" ]]; then
    echo "Running .claude setup script..."
    pushd ".claude"
    execute ./setup.sh
    popd
fi

# Copy .claude files (excluding bash scripts) to $HOME/
echo "Copying .claude files to $HOME/.claude"
execute mkdir -p "$HOME/.claude"
for file in .claude/*; do
    if [[ -f "$file" && ! "$file" =~ \.sh$ ]]; then
        filename=$(basename "$file")
        execute cp "$file" "$HOME/.claude/$filename"
    fi
done

# 3. Copy zed folder to $HOME/.config/
copy_dir "zed" "$HOME/.config/zed"

# 4. Copy aerospace if mac argument is passed
if [[ "$is_mac" == true ]]; then
    echo "Mac setup detected, copying aerospace config..."
    copy_dir "macbook/aerospace" "$HOME/.config/aerospace"
else
    echo "Skipping aerospace config (not mac setup)"
fi

echo "Dotfiles setup complete!"