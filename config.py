"""Validate dashboard configuration before starting command sessions."""

from string import Formatter

from pydantic import BaseModel, Field, field_validator

from .fetcher.base_model import DEFAULT_FORMAT


class Settings(BaseModel):
    default_source: str = "Aimhaven"
    torrent_send_format: str = DEFAULT_FORMAT
    magnet_to_qrcode: bool = False
    request_timeout: int = Field(default=30, ge=5, le=120)
    session_timeout: int = Field(default=60, ge=10, le=300)
    max_results: int = Field(default=10, ge=1, le=30)
    proxy: str = ""

    @field_validator("torrent_send_format")
    @classmethod
    def validate_template(cls, value: str) -> str:
        allowed = {"game_name", "size", "last_update", "magnet", "torrent_path", "is_hacked"}
        for _, field, spec, conversion in Formatter().parse(value):
            if field is not None and (field not in allowed or spec or conversion):
                raise ValueError("发送格式仅支持 README 所列的简单占位符")
        if not value.strip():
            raise ValueError("发送格式不能为空")
        return value
