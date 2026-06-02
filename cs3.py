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
        return result.stdout + result.stderr

    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")

    return result.returncode


def install_cloudflared():
    print("[1/6] Installing cloudflared...")

    run(
        "wget -q "
        "https://github.com/cloudflare/cloudflared/releases/latest/download/"
        "cloudflared-linux-amd64 "
        "-O /usr/local/bin/cloudflared"
    )

    run("chmod +x /usr/local/bin/cloudflared")

    print("      cloudflared installed.")


def install_code_server():
    print("[2/6] Installing code-server...")

    run("curl -fsSL https://code-server.dev/install.sh | sh")

    print("      code-server installed.")


def create_code_server_service():
    print("[3/6] Creating code-server service...")

    service = """[Unit]
Description=code-server
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/code-server --bind-addr 127.0.0.1:8080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

    with open("/etc/systemd/system/code-server.service", "w") as f:
        f.write(service)

    print("      service created.")


def create_cloudflared_service():
    print("[4/6] Creating cloudflared service...")

    service = """[Unit]
Description=Cloudflare Tunnel for code-server
After=network-online.target code-server.service
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/bin/bash -c 'exec /usr/local/bin/cloudflared tunnel --url http://127.0.0.1:8080 --no-autoupdate'
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

    with open(
        "/etc/systemd/system/cloudflared-code-server.service",
        "w",
    ) as f:
        f.write(service)

    print("      service created.")


def start_services():
    print("[5/6] Starting services...")

    run("systemctl daemon-reload")

    run("systemctl enable code-server.service")
    run("systemctl restart code-server.service")

    run("systemctl enable cloudflared-code-server.service")
    run("systemctl restart cloudflared-code-server.service")

    print("      services started.")


def wait_for_password():
    config_path = "/root/.config/code-server/config.yaml"

    for _ in range(60):
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = f.read()

            match = re.search(
                r"password:\s*(.+)",
                config,
            )

            if match:
                return match.group(1).strip()

        time.sleep(1)

    raise RuntimeError(
        "Could not obtain code-server password"
    )


def wait_for_tunnel_url():
    print("[6/6] Waiting for Cloudflare tunnel URL...")

    pattern = r"https://[a-z0-9\-]+\.trycloudflare\.com"

    for _ in range(60):
        logs = run(
            "journalctl "
            "-u cloudflared-code-server.service "
            "-n 100 "
            "--no-pager",
            capture=True,
        )

        match = re.search(pattern, logs)

        if match:
            return match.group(0)

        time.sleep(2)

    raise RuntimeError(
        "Could not obtain Cloudflare tunnel URL"
    )


def main():
    print("\n=== VS Code Web Setup ===\n")

    install_cloudflared()
    install_code_server()

    create_code_server_service()
    create_cloudflared_service()

    start_services()

    password = wait_for_password()
    tunnel_url = wait_for_tunnel_url()

    print("\n" + "=" * 60)
    print("VS CODE WEB READY")
    print("=" * 60)
    print(f"URL      : {tunnel_url}")
    print(f"PASSWORD : {password}")
    print("=" * 60)

    print("\nUseful commands:")
    print(
        "journalctl -u cloudflared-code-server.service -f"
    )
    print(
        "journalctl -u code-server.service -f"
    )
    print(
        "systemctl status cloudflared-code-server.service"
    )
    print(
        "systemctl status code-server.service"
    )


if __name__ == "__main__":
    main()
