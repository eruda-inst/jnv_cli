import paramiko

from ..config import settings


class SSHClient:
    def __init__(
        self,
        hostname: str,
        username: str = settings.olt_default_username,
        password: str = settings.olt_default_password.get_secret_value(),
    ) -> None:
        self.hostname = hostname
        self.username = username
        self.password = password

        self.stdout = None
        self.exit_status = None

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(policy=paramiko.AutoAddPolicy())

        self.client.connect(
            hostname=self.hostname,
            username=self.username,
            password=self.password,
            auth_timeout=30,
            timeout=30,
            banner_timeout=30,
            look_for_keys=False,
            allow_agent=False,
        )

    def close(self) -> None:
        self.client.close()

    def execute_command(self, command: str, timeout: float = 30.0) -> None:
        _, self.stdout, _ = self.client.exec_command(command=command)
        self.stdout.channel.settimeout(timeout=timeout)
        self.exit_status = self.stdout.channel.recv_exit_status()
        if self.exit_status != 0:
            raise RuntimeError(f"comando falhou (exit={self.exit_status}): {command}")

    def get_stdout(self) -> str:
        if self.stdout is None:
            return ""
        return self.stdout.read().decode(errors="replace")
