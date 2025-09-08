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
- **Neovim** - Installation script for Neovim editor
- **Lazygit** - Installation script for terminal-based Git UI

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

### Advanced Options

You can also use dry-run mode to preview what would be executed:
```bash
./setup.sh --dry
./setup.sh mac --dry
```

### Selective Setup
If you want to run only specific components, you can use the modular run system directly:

```bash
# Run only dotfiles setup
./run.sh dotfiles

# Run only Claude setup
./run.sh claude

# Run only Zed setup
./run.sh zed

# Run only macOS AeroSpace setup
./run.sh aerospace

# Run only Neovim installation
./run.sh neovim

# Run only Lazygit installation
./run.sh lazygit

# Dry run to see what would be executed
./run.sh --dry
```

## How the Setup Works

The `setup.sh` script is the main entry point that runs the core setup components:

- **Shell Configuration**: Copies `.zshrc`, `.bashrc`, and `.p10k.zsh` to your home directory
- **Claude Code Setup**: Runs Claude Code setup scripts and copies configuration files  
- **Zed Editor**: Copies Zed configuration to `~/.config/zed`
- **Neovim**: Installs Neovim using the dedicated installation script
- **macOS Only**: Copies AeroSpace configuration to `~/.config/aerospace` (when using `mac` flag)

Under the hood, `setup.sh` uses a modular system with individual scripts in the `runs/` directory:

1. **01-dotfiles**: Shell configuration setup
2. **02-claude**: Claude Code setup  
3. **03-zed**: Zed Editor configuration
4. **04-aerospace-mac**: AeroSpace window manager (macOS only)
5. **05-neovim**: Neovim installation
6. **06-lazygit**: Lazygit installation (available via direct run.sh usage)

The `run.sh` script orchestrates these individual components and can be used directly for selective setup or advanced filtering.

## Manual Configuration

If you prefer to set up components individually, you can run the individual scripts directly:

```bash
# Shell configuration
./runs/01-dotfiles

# Claude Code setup
./runs/02-claude

# Zed Editor setup
./runs/03-zed

# AeroSpace setup (macOS)
./runs/04-aerospace-mac

# Neovim installation
./runs/05-neovim

# Lazygit installation
./runs/06-lazygit
```

Or use the traditional manual approach:

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

### Development Tools
```bash
# Install Neovim
./install-neovim.sh

# Install Lazygit
./install-lazygit.sh
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
