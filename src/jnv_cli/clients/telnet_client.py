import select
import socket
import time

from jnv_cli.config import settings

IAC: bytes = bytes([255])
DONT: bytes = bytes([254])
DO: bytes = bytes([253])
WONT: bytes = bytes([252])
WILL: bytes = bytes([251])


class TelnetClient:
    def __init__(
        self,
        hostname: str,
        port: int = 23,
        username: str = settings.olt_fiberhome_default_username,
        password: str = settings.olt_fiberhome_default_password.get_secret_value(),
        timeout: float = 30,
    ) -> None:
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout

        self.connect()

        self.send_command(command="/")
        self.send_command(command="cd service")
        self.send_command(command="idle-timeout 35791")  # Max: 35791
        self.send_command(command="terminal length 0")  # 0 or auto

    def connect(self) -> None:
        self._socket = socket.create_connection(
            address=(self.hostname, self.port), timeout=self.timeout
        )

        self._read_until(match=["Login:", "login:"])
        self._write(data=f"{self.username}\r\n")
        self._read_until(match=["Password:", "password:"])
        self._write(data=f"{self.password}\r\n")
        self._read_until(match=["User>", ">"])
        self._write(data="EN\r\n")
        self._read_until(match=["Password:", "password:"])
        self._write(data=f"{self.password}\r\n")
        self._read_until(match=["Admin#", "#"])

    def close(self) -> None:
        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            finally:
                self._socket.close()
                self._socket = None

    def send_command(self, command: str) -> str:
        self._write(data=f"{command.strip()}\r\n")
        return self._read_until(match=["#", ">"])

    def _write(self, data: str) -> None:
        if self._socket is None:
            return
        self._socket.sendall(data.encode("utf-8"))

    def _read_until(self, match: str | list[str], timeout: float | None = None) -> str:
        targets = [match] if isinstance(match, str) else match
        read_timeout = timeout if timeout is not None else self.timeout
        deadline = time.time() + read_timeout
        buffer = bytearray()

        while time.time() <= deadline:
            rlist, _, _ = select.select([self._socket], [], [], 0.1)
            if not rlist:
                continue

            chunk = self._socket.recv(4096)
            if not chunk:
                break

            buffer.extend(self._clean_iac_bytes(chunk))
            text_decoded = buffer.decode(encoding="utf-8", errors="replace")

            if any(target in text_decoded for target in targets):
                return text_decoded

        return buffer.decode(encoding="utf-8", errors="replace")

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
