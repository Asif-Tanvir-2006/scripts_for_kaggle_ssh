# ~/.bashrc

# If not running interactively, don't do anything
[ -z "$PS1" ] && return

# ─── History ────────────────────────────────────────────────────────────────
shopt -s histappend
HISTFILE=/var/log/.bash_history
HISTSIZE=10000
HISTFILESIZE=20000
PROMPT_COMMAND="history -a;$PROMPT_COMMAND"

# ─── Shell Options ───────────────────────────────────────────────────────────
shopt -s checkwinsize

# ─── Prompt ──────────────────────────────────────────────────────────────────
PS1='\[\033[01;32m\]kaggle-gpu\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

# ─── Colors ──────────────────────────────────────────────────────────────────
if [ -x /usr/bin/dircolors ]; then
    eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# ─── Aliases ─────────────────────────────────────────────────────────────────
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'
alias cls='clear'
alias ports='ss -tulanp'
alias gpu='nvidia-smi'
alias py='python'

# ─── Kaggle Environment ──────────────────────────────────────────────────────
# Load full environment from the Kaggle kernel process (handles all special chars safely)
while IFS= read -r -d '' var; do
    export "$var"
done < /proc/1/environ

# ─── PATH ────────────────────────────────────────────────────────────────────
export PATH=/opt/bin:/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/tools/node/bin:/tools/google-cloud-sdk/bin

# ─── CUDA ────────────────────────────────────────────────────────────────────
export CUDA_HOME=/usr/local/cuda
export LD_LIBRARY_PATH=/usr/local/nvidia/lib64:/usr/local/cuda/lib64
export LIBRARY_PATH=/usr/local/cuda/lib64/stubs

# ─── Python ──────────────────────────────────────────────────────────────────
export PYTHONPATH=/kaggle/lib/kagglegym:/kaggle/lib
export PYTHONUSERBASE=/root/.local
