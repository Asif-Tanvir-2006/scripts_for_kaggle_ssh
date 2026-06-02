import os
import subprocess
import time
import re


def run_shell(cmd, capture=False):
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=capture,
        text=True,
    )

    if capture:
        return result.stdout + result.stderr

    return result.returncode


def install_cloudflared():
    print("[1/4] Installing cloudflared...")

    run_shell(
        "wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/"
        "cloudflared-linux-amd64 -O /usr/local/bin/cloudflared"
    )

    run_shell("chmod +x /usr/local/bin/cloudflared")

    print("      cloudflared installed.")


def install_code_server():
    print("[2/4] Installing code-server...")

    run_shell(
        "curl -fsSL https://code-server.dev/install.sh | sh"
    )

    print("      code-server installed.")


def start_code_server():
    print("[3/4] Starting code-server...")

    os.makedirs("/root/.config/code-server", exist_ok=True)

    proc = subprocess.Popen(
        [
            "code-server",
            "--bind-addr",
            "127.0.0.1:8080",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    config_path = "/root/.config/code-server/config.yaml"

    for _ in range(30):
        if os.path.exists(config_path):
            break
        time.sleep(1)
    else:
        raise RuntimeError(
            "code-server config file was never created"
        )

    with open(config_path) as f:
        config = f.read()

    password_match = re.search(
        r"password:\s*(.+)",
        config
    )

    password = (
        password_match.group(1).strip()
        if password_match
        else "NOT FOUND"
    )

    print("      code-server started.")

    return proc, password


def start_tunnel():
    print("[4/4] Starting Cloudflare tunnel...")

    proc = subprocess.Popen(
        [
            "cloudflared",
            "tunnel",
            "--url",
            "http://localhost:8080",
            "--no-autoupdate",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )

    print("      Waiting for tunnel URL...")

    deadline = time.time() + 60
    output = ""

    while time.time() < deadline:
        try:
            chunk = proc.stderr.read1(4096).decode(
                errors="ignore"
            )
        except Exception:
            chunk = ""

        output += chunk

        match = re.search(
            r"https://[a-z0-9\-]+\.trycloudflare\.com",
            output,
        )

        if match:
            return proc, match.group(0)

        time.sleep(1)

    raise RuntimeError(
        "Could not obtain tunnel URL.\n\n"
        + output[-5000:]
    )


def bash():
    if os.path.exists(".bashrc"):
        run_shell("mv .bashrc ~/.bashrc")
        print("Moved custom .bashrc file")


def main():
    print("\n=== Setting up VS Code Web ===\n")

    bash()

    install_cloudflared()
    install_code_server()

    _, password = start_code_server()
    _, tunnel_url = start_tunnel()

    print("\n" + "=" * 60)
    print("VS CODE WEB READY")
    print("=" * 60)
    print(f"URL      : {tunnel_url}")
    print(f"PASSWORD : {password}")
    print("=" * 60)

    print("\nProcesses are running in the background.")
    print("This notebook cell is now free.")
    print("\nTo verify later:")
    print("  pgrep -af code-server")
    print("  pgrep -af cloudflared")


if __name__ == "__main__":
    main()
