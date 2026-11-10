"""Small stdlib-only client for the local OS-Ken host-blocking API."""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ControllerAPIError(RuntimeError):
    """Raised when the SDN controller rejects or cannot process a request."""


class ControllerClient:
    def __init__(self, base_url="http://127.0.0.1:8080", timeout=3.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = float(timeout)

    def health(self):
        return self._request("GET", "/health")

    def block(self, ip, block_seconds=300):
        return self._request("POST", "/v1/blocks", {
            "ip": ip, "block_seconds": block_seconds,
        })

    def unblock(self, ip):
        return self._request("DELETE", "/v1/blocks/" + ip)

    def _request(self, method, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            detail = getattr(exc, "read", lambda: b"")()
            if detail:
                detail = detail.decode("utf-8", errors="replace")
            raise ControllerAPIError(f"Controller API {method} {path} failed: {exc} {detail}") from exc
