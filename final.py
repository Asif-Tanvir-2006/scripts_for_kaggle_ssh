import os
import re
import time
import subprocess


def run(cmd, capture=False):
    result = subprocess.run(
        cmd,
        shell=True,
        text=True,
        capture_output=capture,
    )

    if capture:
        return result.stdout

    if result.returncode != 0:
        print(f"Command failed: {cmd}")
        print("Proceeding to next")

    return ""


def session_exists(name):
    result = subprocess.run(
        f"tmux has-session -t {name}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0
print("Copying .bashrc")
run("cp bashrc ~/.bashrc")
print("Done...")
print("\n=== VS Code Web Setup ===\n")

print("[1/5] Installing dependencies...")

run("apt-get update -qq")
run("apt-get install -y tmux curl wget")

print("[2/5] Installing cloudflared...")

run(
    "wget -q "
    "https://github.com/cloudflare/cloudflared/releases/latest/download/"
    "cloudflared-linux-amd64 "
    "-O /usr/local/bin/cloudflared"
)

run("chmod +x /usr/local/bin/cloudflared")

print("[3/5] Installing code-server...")

run("curl -fsSL https://code-server.dev/install.sh | sh")

SESSION = "vscode"

print("[4/5] Creating tmux session...")

if session_exists(SESSION):
    run(f"tmux kill-session -t {SESSION}")

run(f"tmux new-session -d -s {SESSION}")

# Window 0 = code-server
run(
    f"tmux send-keys -t {SESSION}:0 "
    "'code-server --bind-addr 127.0.0.1:8080' C-m"
)

# Window 1 = cloudflared
run(f"tmux new-window -t {SESSION} -n cloudflared")

run(
    f"tmux send-keys -t {SESSION}:1 "
    "'cloudflared tunnel --url http://127.0.0.1:8080 --no-autoupdate' C-m"
)

print("[5/5] Waiting for services...")

config_path = "/root/.config/code-server/config.yaml"

password = None

for _ in range(60):
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = f.read()

        match = re.search(
            r"password:\s*(.+)",
            config,
        )

        if match:
            password = match.group(1).strip()
            break

    time.sleep(1)

if not password:
    raise RuntimeError(
        "Could not obtain code-server password"
    )

tunnel_url = None

for _ in range(60):
    output = run(
        f"tmux capture-pane -J -t {SESSION}:1 -pS -50000",
        capture=True,
    )

    match = re.search(
        r"https://[a-z0-9\-]+\.trycloudflare\.com",
        output,
    )

    if match:
        tunnel_url = match.group(0)
        break

    time.sleep(1)

if not tunnel_url:
    raise RuntimeError(
        "Could not obtain Cloudflare tunnel URL"
    )

print("\n" + "=" * 60)
print("VS CODE WEB READY")
print("=" * 60)
print(f"URL      : {tunnel_url}")
print(f"PASSWORD : {password}")
print("=" * 60)

print("\nTMUX SESSION:")
print(f"  tmux attach -t {SESSION}")

print("\nUseful commands:")
print(
    f"tmux capture-pane -J -t {SESSION}:1 -pS -50000 | grep trycloudflare"
)

print("\nNotebook cell is now free.")
