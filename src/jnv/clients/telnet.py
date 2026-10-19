import select
import socket
import time
from typing import ClassVar

from .. import config

IAC: bytes = bytes([255])
DONT: bytes = bytes([254])
DO: bytes = bytes([253])
WONT: bytes = bytes([252])
WILL: bytes = bytes([251])


class TelnetClient:
    DEFAULT_TIMEOUT: ClassVar[float] = 10.0

    def __init__(
        self,
        hostname: str,
        port: int = 23,
        username: str = config.settings.olt_fiberhome_default_username,
        password: str = config.settings.olt_fiberhome_default_password.get_secret_value(),
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.hostname: str = hostname
        self.port: int = port
        self.username: str = username
        self.password: str = password
        self.timeout: float = timeout
        self._socket: socket.socket | None = None
        self.is_connected: bool = False

    def connect(self) -> None:
        self._socket = socket.create_connection(
            (self.hostname, self.port), timeout=self.timeout
        )
        self.is_connected = True

        self._read_until(["Login:", "login:"])
        self._write(f"{self.username}\r\n")

        self._read_until(["Password:", "password:"])
        self._write(f"{self.password}\r\n")

        self._read_until(["User>", ">"])
        self._write("EN\r\n")

        self._read_until(["Password:", "password:"])
        self._write(f"{self.password}\r\n")

        self._read_until(["Admin#", "#"])

    def close(self) -> None:
        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            finally:
                self._socket.close()
                self._socket = None
        self.is_connected = False

    def send_command(
        self, command: str, expected_prompts: list[str] | None = None
    ) -> str:
        if not self.is_connected or self._socket is None:
            raise RuntimeError("Cliente Telnet não está conectado.")

        prompts = expected_prompts or ["#", ">"]
        self._write(f"{command.strip()}\r\n")
        return self._read_until(prompts)

    def _write(self, data: str) -> None:
        if self._socket is None:
            return
        self._socket.sendall(data.encode("utf-8"))

    def _read_until(self, match: str | list[str], timeout: float | None = None) -> str:
        if self._socket is None:
            return ""

        targets = [match] if isinstance(match, str) else match
        read_timeout = timeout if timeout is not None else self.timeout
        start_time = time.time()
        buffer = bytearray()

        while True:
            if time.time() - start_time > read_timeout:
                break

            rlist, _, _ = select.select([self._socket], [], [], 0.1)
            if not rlist:
                continue

            chunk = self._socket.recv(4096)
            if not chunk:
                break

            buffer.extend(self._clean_iac_bytes(chunk))
            text_decoded = buffer.decode("utf-8", errors="replace")

            lines = text_decoded.strip().splitlines()
            last_line = lines[-1] if lines else ""
            if "Press any key to continue" in last_line:
                self._write(" ")
                start_time = time.time()

            if any(target in text_decoded for target in targets):
                return text_decoded

        return buffer.decode("utf-8", errors="replace")

    def _clean_iac_bytes(self, data: bytes) -> bytes:
        clean_bytes = bytearray()
        i = 0
        n = len(data)

        while i < n:
            byte = bytes([data[i]])
            if byte == IAC and i + 1 < n:
                cmd = bytes([data[i + 1]])
                if cmd in (DO, DONT, WILL, WONT) and i + 2 < n:
                    opt = bytes([data[i + 2]])
                    if cmd == DO:
                        self._write_raw(IAC + WONT + opt)
                    elif cmd == WILL:
                        self._write_raw(IAC + DONT + opt)
                    i += 3
                    continue
                i += 2
                continue

            clean_bytes.append(data[i])
            i += 1

        return bytes(clean_bytes)

    def _write_raw(self, raw_bytes: bytes) -> None:
        if self._socket:
            try:
                self._socket.sendall(raw_bytes)
            except OSError:
                pass
