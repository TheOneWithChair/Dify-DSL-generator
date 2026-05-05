"""Network diagnostics utility (stub — extend as needed)"""

import socket
import requests
from typing import Dict


def diagnose_network_connectivity(
    hosts: list = None,
) -> Dict:
    """Run basic network connectivity checks."""
    if hosts is None:
        hosts = [
            ("generativelanguage.googleapis.com", 443),
            ("api.dify.ai", 443),
        ]

    results = {}
    for host, port in hosts:
        try:
            socket.setdefaulttimeout(5)
            with socket.create_connection((host, port)):
                results[host] = {"reachable": True, "port": port}
        except OSError as e:
            results[host] = {"reachable": False, "port": port, "error": str(e)}

    return results


def print_diagnostics_report(diagnostics: Dict) -> str:
    """Format diagnostics as a human-readable report."""
    lines = ["=== Network Diagnostics Report ==="]
    for host, info in diagnostics.items():
        status = "✅ REACHABLE" if info["reachable"] else "❌ UNREACHABLE"
        line = f"{status}  {host}:{info['port']}"
        if not info["reachable"]:
            line += f"  — {info.get('error', 'unknown error')}"
        lines.append(line)
    return "\n".join(lines)
