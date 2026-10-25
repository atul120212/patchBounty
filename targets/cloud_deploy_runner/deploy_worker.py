"""
Real vulnerable microservice module #2: Cloud Release Artifact Runner.
Contains genuine CWE-78 OS Command Injection via `subprocess.run(..., shell=True)`.
"""
import subprocess


def format_release_banner(release_tag: str) -> str:
    # VULNERABLE SINK (CWE-78): Untrusted release_tag interpolated into shell command string
    completed = subprocess.run(
        f"printf 'RELEASE_READY:%s' {release_tag}",
        shell=True,
        capture_output=True,
        text=True,
        timeout=3,
    )
    return completed.stdout.strip()
