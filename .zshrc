ENABLE_CORRECTION="true"

plugins=(git)

alias zshconfig="nvim ~/.zshrc"
alias lg="lazygit"
alias ldoc="lazydocker"
alias ls="eza -lh --group-directories-first --icons=auto"
alias lsa="ls -a"
alias gcof="git cof"
alias cd="zd"
alias cx='claude --allow-dangerously-skip-permissions'
alias c="opencode"
zd() {
  if [[ $# -eq 0 ]]; then
    builtin cd ~ && return
  elif [[ -d "$1" ]]; then
    builtin cd "$1"
  else
    z "$1" && printf "\U000F17A9" && pwd || echo "Error: Directory not found"
  fi
}
n() { if [[ "$#" -eq 0 ]]; then nvim .; else nvim "$1"; fi; }
alias ..="cd .."
alias t3="bunx t3"
alias diff="hunk diff"
# alias ohmyzsh="mate ~/.oh-my-zsh"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

export PATH="/Users/bartosz.f/Library/Python/3.9/bin:$PATH"
source /opt/homebrew/share/zsh-autosuggestions/zsh-autosuggestions.zsh
source /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
eval "$(zoxide init zsh)"

eval "$(starship init zsh)"

export PATH="$PATH:/Users/bartosz.f/.lmstudio/bin"

export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
export PATH="/opt/homebrew/bin/:$PATH"

export PATH="$HOME/.local/bin:$PATH"

# bun global
export PATH="/Users/bartosz.f/.bun/bin:$PATH"

export PATH="$HOME/.cargo/bin:$PATH"

export EDITOR='cursor --wait'


# bun completions
[ -s "/Users/bartosz.f/.bun/_bun" ] && source "/Users/bartosz.f/.bun/_bun"
export GPG_TTY=$(tty)
export GPG_TTY=$(tty)

# pnpm
export PNPM_HOME="/Users/bartosz.f/Library/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
# pnpm end
export PATH=$PATH:$HOME/go/bin
