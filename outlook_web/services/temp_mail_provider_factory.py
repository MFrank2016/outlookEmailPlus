from __future__ import annotations

from typing import Any

from outlook_web.repositories import settings as settings_repo
from outlook_web.services.temp_mail_provider_base import TempMailProviderBase
from outlook_web.services.temp_mail_provider_cf import CloudflareTempMailProvider
from outlook_web.services.temp_mail_provider_custom import CustomTempMailProvider


class TempMailProviderFactoryError(Exception):
    def __init__(self, code: str, message: str, *, status: int = 503, data: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.data = data


def get_temp_mail_provider(provider_name: str | None = None) -> TempMailProviderBase:
    resolved_provider_name = settings_repo.get_temp_mail_runtime_provider_name(
        provider_name
    )
    if not resolved_provider_name:
        raise TempMailProviderFactoryError(
            "TEMP_MAIL_PROVIDER_NOT_CONFIGURED",
            "未配置临时邮箱 Provider",
        )

    # Cloudflare Workers 专用路由（在通用检查之前，避免被 CustomTempMailProvider 截获）
    if resolved_provider_name == settings_repo.CLOUDFLARE_TEMP_MAIL_PROVIDER:
        return CloudflareTempMailProvider(provider_name=resolved_provider_name)

    if resolved_provider_name in settings_repo.get_supported_temp_mail_provider_names():
        return CustomTempMailProvider(provider_name=resolved_provider_name)

    raise TempMailProviderFactoryError(
        "TEMP_MAIL_PROVIDER_INVALID",
        "临时邮箱 Provider 配置无效",
        status=500,
        data={"provider_name": resolved_provider_name},
    )
