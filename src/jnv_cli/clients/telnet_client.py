import select
import socket
import threading
import time

from jnv_cli.config import settings

IAC: bytes = bytes([255])
DONT: bytes = bytes([254])
DO: bytes = bytes([253])
WONT: bytes = bytes([252])
WILL: bytes = bytes([251])

_RETRYABLE_ERRORS: tuple[type[BaseException], ...] = (
    BrokenPipeError,
    ConnectionResetError,
    ConnectionAbortedError,
)


class TelnetClient:
    def __init__(
        self,
        hostname: str,
        port: int = 23,
        username: str = settings.olt_fiberhome_username,
        password: str = settings.olt_fiberhome_password.get_secret_value(),
        timeout: float = 30,
    ) -> None:
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout

        self._keepalive_interval: float = 60.0

        self._socket: socket.socket | None = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._keepalive_thread: threading.Thread | None = None

        self.connect()

        self._write(data="/\r\n")
        self._read_until(match=["#", ">"])
        self._write(data="cd service\r\n")
        self._read_until(match=["#", ">"])
        self._write(data="terminal length 0\r\n")
        self._read_until(match=["#", ">"])

        self._start_keepalive_locked()

    def close(self) -> None:
        self._stop.set()

        sock = self._socket
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        with self._lock:
            self._mark_dead_locked()

        if self._keepalive_thread is not None:
            self._keepalive_thread.join(timeout=5)

    def send_command(self, command: str) -> str:
        with self._lock:
            if self._stop.is_set():
                raise ConnectionResetError("TelnetClient foi fechado")

            if self._socket is None:
                self._reconnect_locked()

            try:
                return self._send_locked(command)
            except _RETRYABLE_ERRORS:
                self._mark_dead_locked()
                self._reconnect_locked()
                return self._send_locked(command)

    def _send_locked(self, command: str) -> str:
        self._write(data=f"{command.strip()}\r\n")
        return self._read_until(match=["#", ">"])

    def _start_keepalive_locked(self) -> None:
        self._stop.clear()
        self._keepalive_thread = threading.Thread(
            target=self._keepalive_loop, daemon=True
        )
        self._keepalive_thread.start()

    def _reconnect_locked(self) -> None:
        self._mark_dead_locked()
        self.connect()
        self._write(data="/\r\n")
        self._read_until(match=["#", ">"])
        self._write(data="cd service\r\n")
        self._read_until(match=["#", ">"])
        self._write(data="terminal length 0\r\n")
        self._read_until(match=["#", ">"])

        if self._keepalive_thread is None or not self._keepalive_thread.is_alive():
            self._start_keepalive_locked()

    def _mark_dead_locked(self) -> None:
        sock = self._socket
        self._socket = None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

    def _keepalive_loop(self) -> None:
        while not self._stop.wait(timeout=self._keepalive_interval):
            with self._lock:
                if self._socket is None:
                    return
                try:
                    self._write(data="help\r\n")
                    self._read_until(match=["#", ">"], timeout=5)
                except _RETRYABLE_ERRORS:
                    self._mark_dead_locked()
                    return

    def connect(self) -> None:
        sock = socket.create_connection(
            address=(self.hostname, self.port), timeout=self.timeout
        )
        self._socket = sock
        try:
            self._read_until(match=["Login:", "login:"])
            self._write(data=f"{self.username}\r\n")
            self._read_until(match=["Password:", "password:"])
            self._write(data=f"{self.password}\r\n")
            self._read_until(match=["User>", ">"])
            self._write(data="EN\r\n")
            self._read_until(match=["Password:", "password:"])
            self._write(data=f"{self.password}\r\n")
            self._read_until(match=["Admin#", "#"])
        except Exception:
            self._mark_dead_locked()
            raise

    def _write(self, data: str) -> None:
        if self._socket is None:
            raise ConnectionResetError("Sessão Telnet está fechada")
        self._socket.sendall(data.encode("utf-8"))

    def _write_raw(self, raw_bytes: bytes) -> None:
        if self._socket is not None:
            try:
                self._socket.sendall(raw_bytes)
            except OSError:
                pass

    def _read_until(self, match: str | list[str], timeout: float | None = None) -> str:
        targets = [match] if isinstance(match, str) else match
        read_timeout = timeout if timeout is not None else self.timeout
        deadline = time.time() + read_timeout
        buffer = bytearray()

        while time.time() <= deadline:
            sock = self._socket
            if sock is None:
                raise ConnectionResetError("Sessão Telnet está fechada")

            rlist, _, _ = select.select([sock], [], [], 0.1)
            if not rlist:
                continue

            chunk = sock.recv(4096)
            if not chunk:
                raise ConnectionResetError("Sessão Telnet fechada")

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
