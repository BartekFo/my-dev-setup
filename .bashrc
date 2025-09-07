# All the default Omarchy aliases and functions
# (don't mess with these directly, just overwrite them here!)
source ~/.local/share/omarchy/default/bash/rc

# Add your own exports, aliases, and functions here.
#
# Make an alias for invoking commands you use constantly
# alias p='python'
#
# Use VSCode instead of neovim as your default editor
# export EDITOR="code"
#
# Set a custom prompt with the directory revealed (alternatively use https://starship.rs)
# PS1="\W \[\e]0;\w\a\]$PS1"

export NVM_DIR="$HOME/.config/nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"                   # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion" # This loads nvm bash_completion

export PATH="$HOME/.cache/.bun/bin:$PATH"

if [ -z "$SSH_AUTH_SOCK" ]; then
  eval $(ssh-agent -s)
fi
eval $(keychain --eval /home/bartek/.ssh/id_ed25519)
eval $(keychain --eval --gpg2 98E19E5F65BFE8AD)

. "$HOME/.local/share/../bin/env"

alias lg="lazygit"

setup_serena() {
  uvx --from git+https://github.com/oraios/serena serena project index
  claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant --project $(pwd)
}
