import os
import subprocess
import time
import re


def run_shell(cmd, capture=False):
    """Run a shell command, optionally capturing output."""
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=capture)
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


def setup_ssh():
    print("[2/4] Setting up OpenSSH server...")
    run_shell("apt-get update -qq")
    run_shell("apt-get install -qq openssh-server -y")
    os.makedirs("/var/run/sshd", exist_ok=True)
    run_shell("/usr/sbin/sshd")
    print("      SSH server started.")


def configure_ssh():
    print("[3/4] Configuring SSH authentication...")
    run_shell("echo 'root:kaggle123' | chpasswd")

    sshd_config = "/etc/ssh/sshd_config"
    with open(sshd_config, "a") as f:
        f.write("\nPasswordAuthentication yes\n")
        f.write("PermitRootLogin yes\n")

    # Validate config and reload
    test = subprocess.run(
        ["/usr/sbin/sshd", "-t"], capture_output=True, text=True
    )
    if test.returncode != 0:
        print("      WARNING: sshd config test failed:", test.stderr)
    else:
        # Try to HUP existing sshd, fall back to starting a new one
        pid_file = "/var/run/sshd.pid"
        if os.path.exists(pid_file):
            with open(pid_file) as f:
                pid = f.read().strip()
            run_shell(f"kill -HUP {pid} 2>/dev/null || /usr/sbin/sshd")
        else:
            run_shell("/usr/sbin/sshd")
    print("      SSH configured.")


def start_tunnel():
    print("[4/4] Starting cloudflared tunnel...")
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "ssh://localhost:22", "--no-autoupdate"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    print("      Waiting for tunnel URL...")
    time.sleep(5)

    output = proc.stderr.read1(4096).decode()
    match = re.search(r"https://[a-z0-9\-]+\.trycloudflare\.com", output)

    if match:
        tunnel_url = match.group(0)
        hostname = tunnel_url.replace("https://", "")
        print(f"\n{'='*50}")
        print(f"  Tunnel URL : {tunnel_url}")
        print(f"\n  Connect via SSH:")
        print(f"    ssh -o ProxyCommand='cloudflared access ssh --hostname %h' root@{hostname}")
        print(f"\n  Password   : kaggle123")
        print(f"{'='*50}\n")
    else:
        print("\n  Could not parse tunnel URL. Raw output:\n")
        print(output)

    return proc


def main():
    print("\n=== Kaggle SSH Tunnel Setup ===\n")
    install_cloudflared()
    setup_ssh()
    configure_ssh()
    proc = start_tunnel()

    try:
        print("Tunnel is running. Press Ctrl+C to stop.")
        proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down tunnel...")
        proc.terminate()
        print("Done.")


if __name__ == "__main__":
    main()
