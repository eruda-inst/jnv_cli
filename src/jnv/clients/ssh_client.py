import paramiko

from ..config import settings


class SSHClient:
    def __init__(
        self,
        hostname: str,
        username: str = settings.olt_default_username,
        password: str = settings.olt_default_password.get_secret_value(),
        port: int = 22,
        auth_timeout: int = 30,
        timeout: int = 30,
        banner_timeout: int = 30,
        channel_timeout: int = 30,
        look_for_keys: bool = False,
        allow_agent: bool = False,
    ) -> None:
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port

        self.auth_timeout = auth_timeout
        self.timeout = timeout
        self.banner_timeout = banner_timeout
        self.channel_timeout = channel_timeout

        self.look_for_keys = look_for_keys
        self.allow_agent = allow_agent

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(policy=paramiko.AutoAddPolicy())

        self.client.connect(
            hostname=self.hostname,
            username=self.username,
            password=self.password,
            port=self.port,
            auth_timeout=self.auth_timeout,
            timeout=self.timeout,
            banner_timeout=self.banner_timeout,
            look_for_keys=self.look_for_keys,
            allow_agent=self.allow_agent,
        )

    def close(self) -> None:
        self.client.close()

    def execute_command(self, command: str, timeout: float = 30.0) -> None:
        self.stdin, self.stdout, self.stderr = self.client.exec_command(command=command)
        self.stdout.channel.settimeout(timeout=timeout)

    def get_stdout(self) -> str:
        if self.stdout is None:
            return ""
        return self.stdout.read().decode(errors="replace")

    def get_stderr(self) -> str:
        if self.stderr is None:
            return ""
        return self.stderr.read().decode(errors="replace")

    def get_stdin(self) -> str | None:
        if self.stdin is None:
            return ""
        return self.stdin.read().decode(errors="replace")
