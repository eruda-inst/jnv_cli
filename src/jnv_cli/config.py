from typing import ClassVar

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    olt_acija_hostname: str = Field(default="olt_acija_hostname")
    olt_itaitu_hostname: str = Field(default="olt_itaitu_hostname")
    olt_jacobina_iii_hostname: str = Field(default="olt_jacobina_iii_hostname")
    olt_lages_do_batata_hostname: str = Field(default="olt_lages_do_batata_hostname")
    olt_newnet_hostname: str = Field(default="olt_newnet_hostname")
    olt_palmeirinha_hostname: str = Field(default="olt_palmeirinha_hostname")
    olt_paraiso_hostname: str = Field(default="olt_paraiso_hostname")

    olt_datacom_username: str = Field(default="olt_datacom_username")
    olt_datacom_password: SecretStr = Field(default=SecretStr("olt_datacom_password"))

    olt_fiberhome_username: str = Field(default="olt_fiberhome_username")
    olt_fiberhome_password: SecretStr = Field(
        default=SecretStr("olt_fiberhome_password")
    )


settings = Settings()
