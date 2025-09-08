# My Dev Setup 🚀

A comprehensive development environment setup for fast configuration across machines with all my personal preferences and tools.

## Overview

This repository contains my complete dotfiles and configuration setup that allows me to quickly configure any new development machine with my preferred tools and settings. It includes configurations for shell environments, code editors, window managers, and development tools.

**Note**: I currently use [omarchy.org](https://omarchy.org/) which has adopted many configurations from this repository as it ships with these setups by default. However, this repository remains useful for custom setups and machines where omarchy is not available.

## What's Included

### Shell Configuration
- `.zshrc` - Zsh shell configuration
- `.bashrc` - Bash shell configuration
- `.p10k.zsh` - Powerlevel10k theme configuration

### Editor Setup
- **Zed Editor** (`zed/`)
  - Custom settings and preferences
  - Code snippets for TypeScript, JavaScript, and React
  - Custom keymaps
  - Theme configurations

### macOS Tools
- **AeroSpace** (`macbook/aerospace/`) - Tiling window manager configuration

### Development Tools
- **Claude Code** (`.claude/`) - AI-powered development assistant configuration
  - Custom settings and preferences
  - Setup scripts for MCP and ClaudeKit

## Quick Setup

### Basic Setup (Linux/WSL)
```bash
git clone <your-repo-url>
cd my-dev-setup
chmod +x setup.sh
./setup.sh
```

### macOS Setup
```bash
git clone <your-repo-url>
cd my-dev-setup
chmod +x setup.sh
./setup.sh mac
```

The `mac` flag will additionally install AeroSpace window manager configuration.

## What the Setup Script Does

1. **Shell Configuration**: Copies `.zshrc`, `.bashrc`, and `.p10k.zsh` to your home directory
2. **Claude Code Setup**: Runs Claude Code setup scripts and copies configuration files
3. **Zed Editor**: Copies Zed configuration to `~/.config/zed`
4. **macOS Only**: Copies AeroSpace configuration to `~/.config/aerospace` (when using `mac` flag)

## Manual Configuration

If you prefer to set up components individually:

### Zed Editor
```bash
cp -r zed ~/.config/zed
```

### AeroSpace (macOS)
```bash
cp -r macbook/aerospace ~/.config/aerospace
```

### Claude Code
```bash
cd .claude && ./setup.sh
cp -r .claude ~/.claude
```

## Customization

Feel free to fork this repository and customize it for your own needs:

1. Modify the configuration files in their respective directories
2. Update the `setup.sh` script if you add new tools or configurations
3. Add your own dotfiles and configurations

## Contributing

While this is my personal setup, contributions and improvements are welcome! Feel free to:

- Submit bug fixes
- Suggest improvements to the setup process
- Share useful configurations that others might benefit from

## Related Projects

- [omarchy.org](https://omarchy.org/) - Ships with many of these configurations by default
