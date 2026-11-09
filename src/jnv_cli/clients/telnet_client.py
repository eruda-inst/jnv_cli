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

# Errors that mean "the socket is no longer usable" and justify a reconnect.
# These are all subclasses of ConnectionError; we list them explicitly so that
# unrelated OSErrors (e.g. from select) are not misinterpreted as dead sockets.
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
        username: str = settings.olt_fiberhome_default_username,
        password: str = settings.olt_fiberhome_default_password.get_secret_value(),
        timeout: float = 30,
    ) -> None:
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout

        # Keepalive interval. Must be comfortably below the OLT's actual
        # idle-timeout. Fiberhome often defaults to 300 s, but a shorter
        # value (60 s) is safer if the OLT is configured with a tighter
        # value or if the exec-timeout/idle-timeout command silently failed.
        self._keepalive_interval: float = 60.0

        self._socket: socket.socket | None = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._keepalive_thread: threading.Thread | None = None

        self.connect()

        # Session setup must run before the keepalive thread starts so the
        # two never interleave on the wire.
        self._write(data="/\r\n")
        self._read_until(match=["#", ">"])
        self._write(data="cd service\r\n")
        self._read_until(match=["#", ">"])
        self._write(data="terminal length 0\r\n")
        self._read_until(match=["#", ">"])

        self._start_keepalive_locked()

    def close(self) -> None:
        # Signal keepalive to stop before touching the socket so it can
        # exit cleanly on its next wait() wakeup.
        self._stop.set()

        # Force any pending recv() to return (EOF), which unblocks any
        # _read_until() currently waiting inside select().
        sock = self._socket
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        # Now acquire the lock so no command is mid-flight, then actually
        # close the socket and clear the reference.
        with self._lock:
            self._mark_dead_locked()

        if self._keepalive_thread is not None:
            self._keepalive_thread.join(timeout=5)

    def send_command(self, command: str) -> str:
        with self._lock:
            if self._stop.is_set():
                raise ConnectionResetError("TelnetClient foi fechado")

            if self._socket is None:
                # Socket was marked dead by the keepalive or a previous
                # failed command. Transparently reconnect before sending.
                self._reconnect_locked()

            try:
                return self._send_locked(command)
            except _RETRYABLE_ERRORS:
                # The connection died mid-operation (typical when the OLT
                # killed the session for idleness). Try exactly once to
                # re-establish it and retry the command.
                self._mark_dead_locked()
                self._reconnect_locked()
                return self._send_locked(command)

    def _send_locked(self, command: str) -> str:
        self._write(data=f"{command.strip()}\r\n")
        return self._read_until(match=["#", ">"])

    def _start_keepalive_locked(self) -> None:
        # In the normal flow _stop is False here. We clear it defensively so
        # the thread cannot exit immediately due to a stale event state.
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

        # The previous keepalive thread may have exited on error; restart
        # it so the new session is also protected.
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
        # Sends a harmless command periodically so the OLT never considers
        # the session idle. Runs in a dedicated thread because the whole
        # point is: "no commands were sent for a while" is exactly the
        # condition this loop exists to prevent.
        while not self._stop.wait(timeout=self._keepalive_interval):
            with self._lock:
                if self._socket is None:
                    # Another path already marked it dead; send_command
                    # will reconnect on the next user action.
                    return
                try:
                    self._write(data="show hostname\r\n")
                    self._read_until(match=["#", ">"], timeout=5)
                except _RETRYABLE_ERRORS:
                    # Mark the socket dead so the next send_command knows
                    # it must reconnect instead of writing to a dead fd.
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
            # Never leave a half-initialized socket behind.
            self._mark_dead_locked()
            raise

    def _write(self, data: str) -> None:
        if self._socket is None:
            raise ConnectionResetError("Sessão Telnet está fechada")
        self._socket.sendall(data.encode("utf-8"))

    def _write_raw(self, raw_bytes: bytes) -> None:
        # Best-effort write used for IAC negotiation. Silently drops bytes
        # if the socket is already gone: reacting to negotiation on a
        # half-closed connection is not actionable.
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
                # Peer sent EOF: the session is dead.
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
