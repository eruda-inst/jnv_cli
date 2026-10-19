from typing import ClassVar

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    olt_acija_hostname: str = Field(default="olt_acija_hostname")
    olt_itaitu_hostname: str = Field(default="olt_itaitu_hostname")
    olt_jac_3_hostname: str = Field(default="olt_jac_3_hostname")
    olt_lajes_hostname: str = Field(default="olt_lajes_hostname")
    olt_newnet_hostname: str = Field(default="olt_newnet_hostname")
    olt_palmeirinha_hostname: str = Field(default="olt_palmeirinha_hostname")
    olt_paraiso_hostname: str = Field(default="olt_paraiso_hostname")

    olt_default_username: str = Field(default="olt_default_username")
    olt_default_password: SecretStr = Field(default=SecretStr("olt_default_password"))

    olt_fiberhome_default_username: str = Field(
        default="olt_fiberhome_default_username"
    )
    olt_fiberhome_default_password: SecretStr = Field(
        default=SecretStr("olt_fiberhome_default_password")
    )


settings = Settings()
