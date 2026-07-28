ENABLE_CORRECTION="true"

plugins=(git)

alias zshconfig="nvim ~/.zshrc"
alias lg="lazygit"
alias ldoc="lazydocker"
alias ls="eza -lh --group-directories-first --icons=auto"
alias lsa="ls -a"
alias gcof="git cof"
alias cd="zd"
alias cc='claude'
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
# alias ohmyzsh="mate ~/.oh-my-zsh"

# fnm
eval "$(fnm env --use-on-cd --shell zsh)"

# FZF: fuzzy file and directory navigation with previews
if (( $+commands[fzf] )); then
  source <(fzf --zsh)
  export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'
  export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
  export FZF_ALT_C_COMMAND='fd --type d --hidden --follow --exclude .git'
  export FZF_CTRL_T_OPTS="--preview 'bat --color=always --style=numbers --line-range=:500 {}'"
  export FZF_ALT_C_OPTS="--preview 'eza --tree --level=1 --icons --color=always {}'"
fi

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
