#!/bin/bash

# Create ~/.claude directory if it doesn't exist
mkdir -p ~/.claude

# Copy settings.json to ~/.claude
cp settings.json ~/.claude/settings.json

# Run claudekit setup
./setup-claudekit.sh

# Add mcp servers
./setup-mcp.sh

