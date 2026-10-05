"""Use Vercel's overwritten client-IP header only inside its trusted runtime."""
import os
from ipaddress import ip_address

from fastapi import Request


def client_ip(request: Request) -> str:
    if os.getenv("VERCEL") == "1":
        value = request.headers.get("x-forwarded-for", "").strip()
        try:
            return str(ip_address(value))
        except ValueError:
            pass
    # Direct/local deployments must not trust caller-supplied forwarding headers.
    return request.client.host if request.client else "unknown"
