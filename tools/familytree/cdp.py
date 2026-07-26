"""A minimal Chrome DevTools Protocol client, in nothing but the standard library.

Why this exists at all: some archives cannot be reached with `urllib`. FamilySearch
sits behind Imperva bot protection and MyHeritage behind a commercial equivalent, so a
bare HTTP request from Python is challenged long before it reaches a login form. The
only session those venues will accept is one inside the real browser the human already
uses — which is exactly the Chrome that `.mcp.json` attaches to on port 9222.

CDP speaks WebSocket, and the standard library has no WebSocket client. So there is one
here: about eighty lines of RFC 6455, which is the whole reason this file is longer than
the job it does. That is still the right trade for this project — `pyproject.toml`
declares no dependencies on purpose, and a protocol frozen since 2011 is a far safer
thing to vendor than a package that has to still resolve in ten years.

Deliberately partial. It evaluates JavaScript in a page and navigates one, because that
is all the session helper needs. It is not a browser automation library, and it should
not grow into one — `chrome-devtools-mcp` is already the tool for that, and it is what
the agent drives interactively. This is for the unattended path.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import ssl
import struct
import time
import urllib.request
from urllib.parse import urlparse

DEFAULT_BROWSER_URL = "http://127.0.0.1:9222"


class CDPError(RuntimeError):
    """Chrome could not be reached, or refused what was asked of it."""


class _WebSocket:
    """Just enough RFC 6455 to hold a CDP conversation.

    Client frames must be masked and server frames must not be; both directions can
    fragment, and Chrome does fragment when a page returns a large result — which is
    why `recv` reassembles continuation frames rather than assuming one frame per
    message. Getting that wrong shows up as truncated JSON only on big pages, so it is
    handled here rather than discovered later.
    """

    def __init__(self, url: str, timeout: float = 30.0):
        u = urlparse(url)
        port = u.port or (443 if u.scheme == "wss" else 80)
        self._sock = socket.create_connection((u.hostname, port), timeout=timeout)
        if u.scheme == "wss":
            self._sock = ssl.create_default_context().wrap_socket(self._sock, server_hostname=u.hostname)
        self._buf = b""

        key = base64.b64encode(os.urandom(16)).decode()
        path = u.path + (f"?{u.query}" if u.query else "")
        self._sock.sendall(
            (
                f"GET {path} HTTP/1.1\r\n"
                f"Host: {u.hostname}:{port}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                "Sec-WebSocket-Version: 13\r\n"
                "\r\n"
            ).encode()
        )
        status = self._read_until(b"\r\n\r\n").split(b"\r\n", 1)[0]
        if b"101" not in status:
            raise CDPError(f"WebSocket upgrade refused: {status.decode(errors='replace')}")

    def _read_until(self, marker: bytes) -> bytes:
        while marker not in self._buf:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise CDPError("Chrome closed the connection during the handshake")
            self._buf += chunk
        head, self._buf = self._buf.split(marker, 1)
        return head

    def _exact(self, n: int) -> bytes:
        while len(self._buf) < n:
            chunk = self._sock.recv(max(65536, n - len(self._buf)))
            if not chunk:
                raise CDPError("Chrome closed the connection")
            self._buf += chunk
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def send(self, text: str) -> None:
        payload = text.encode()
        n = len(payload)
        header = bytearray([0x81])  # FIN + text frame
        if n < 126:
            header.append(0x80 | n)
        elif n < 1 << 16:
            header.append(0x80 | 126)
            header += struct.pack("!H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack("!Q", n)
        mask = os.urandom(4)
        header += mask
        self._sock.sendall(bytes(header) + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def recv(self) -> str:
        chunks: list[bytes] = []
        while True:
            b1, b2 = self._exact(2)
            fin, opcode, masked, n = b1 & 0x80, b1 & 0x0F, b2 & 0x80, b2 & 0x7F
            if n == 126:
                n = struct.unpack("!H", self._exact(2))[0]
            elif n == 127:
                n = struct.unpack("!Q", self._exact(8))[0]
            mask = self._exact(4) if masked else b""
            data = self._exact(n)
            if masked:
                data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
            if opcode == 0x8:
                raise CDPError("Chrome closed the WebSocket")
            if opcode == 0x9:  # ping — answer it or Chrome eventually hangs up
                self._sock.sendall(b"\x8a" + bytes([0x80 | len(data)]) + os.urandom(4) + data)
                continue
            if opcode == 0xA:  # pong
                continue
            chunks.append(data)
            if fin:
                return b"".join(chunks).decode(errors="replace")

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass


class Page:
    """One open tab, addressed by its CDP target."""

    def __init__(self, ws_url: str, target_url: str = "", timeout: float = 30.0):
        self.url = target_url
        self._ws = _WebSocket(ws_url, timeout=timeout)
        self._n = 0

    def _call(self, method: str, params: dict | None = None) -> dict:
        self._n += 1
        wanted = self._n
        self._ws.send(json.dumps({"id": wanted, "method": method, "params": params or {}}))
        while True:
            # Chrome interleaves domain events with command replies; ours is the one
            # carrying our id, and everything else on the wire is somebody else's.
            msg = json.loads(self._ws.recv())
            if msg.get("id") != wanted:
                continue
            if "error" in msg:
                raise CDPError(f"{method}: {msg['error'].get('message', msg['error'])}")
            return msg.get("result", {})

    def evaluate(self, expression: str):
        """Run JS in the page and return its value. Promises are awaited."""
        result = self._call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": True,
                "returnByValue": True,
                "userGesture": True,
            },
        )
        if "exceptionDetails" in result:
            detail = result["exceptionDetails"]
            text = (detail.get("exception") or {}).get("description") or detail.get("text", "")
            raise CDPError(f"page threw: {text}")
        return result.get("result", {}).get("value")

    def navigate(self, url: str, settle: float = 25.0) -> None:
        self._call("Page.navigate", {"url": url})
        deadline = time.monotonic() + settle
        while time.monotonic() < deadline:
            time.sleep(0.4)
            try:
                if self.evaluate("document.readyState") == "complete":
                    self.url = self.evaluate("location.href") or url
                    return
            except CDPError:
                continue  # mid-navigation the context is briefly gone
        self.url = url

    def close(self) -> None:
        self._ws.close()


def targets(browser_url: str = DEFAULT_BROWSER_URL, timeout: float = 5.0) -> list[dict]:
    try:
        with urllib.request.urlopen(f"{browser_url}/json/list", timeout=timeout) as r:
            return [t for t in json.loads(r.read()) if t.get("type") == "page"]
    except OSError as e:
        raise CDPError(
            f"No Chrome listening on {browser_url} ({e}). Start it with "
            "--remote-debugging-port=9222 --user-data-dir=$HOME/.chrome-genealogy "
            "(see docs/searching.md)."
        ) from e


def open_page(host_match: str, browser_url: str = DEFAULT_BROWSER_URL) -> Page:
    """Reuse a tab already on that host, or open one.

    Reusing matters: the point of driving the human's own Chrome is to inherit the
    cookies and the device fingerprint it has already established with the venue. A
    fresh tab in the same profile inherits both, so opening one is safe — but reusing
    is cheaper and leaves the browser as it was found.
    """
    found = targets(browser_url)
    for t in found:
        if host_match in (t.get("url") or ""):
            return Page(t["webSocketDebuggerUrl"], t.get("url", ""))
    if not found:
        raise CDPError("Chrome is running but has no open pages")
    page = Page(found[0]["webSocketDebuggerUrl"], found[0].get("url", ""))
    return page
