import paramiko

from .. import config


class SSHClient:
    def __init__(
        self,
        hostname: str,
        username: str = config.settings.olt_default_username,
        password: str = config.settings.olt_default_password.get_secret_value(),
    ) -> None:
        self.hostname = hostname
        self.username = username
        self.password = password

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.client.connect(
                hostname=self.hostname,
                username=self.username,
                password=self.password,
                look_for_keys=False,
                allow_agent=False,
            )
        except paramiko.SSHException:
            raise paramiko.SSHException()

    def close(self) -> None:
        self.client.close()

    def execute_command(self, command: str, timeout: float = 30.0) -> None:
        self.stdin, self.stdout, self.stderr = self.client.exec_command(command)
        self.stdout.channel.settimeout(timeout)

    def get_stdout(self) -> str:
        if self.stdout is None:
            return ""
        return self.stdout.read().decode(errors="replace")

    def get_stderr(self) -> str:
        if self.stderr is None:
            return ""
        return self.stderr.read().decode(errors="replace")

    def get_stdin(self) -> str | None:
        if self.stdin is not None:
            return self.stdin.read().decode()
