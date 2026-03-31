from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TempMailProviderBase(ABC):
    @abstractmethod
    def get_options(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def create_mailbox(self, *, prefix: str | None = None, domain: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def generate_mailbox(self, *, prefix: str | None = None, domain: str | None = None) -> dict[str, Any]:
        return self.create_mailbox(prefix=prefix, domain=domain)

    @abstractmethod
    def delete_mailbox(self, mailbox: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_messages(self, mailbox: dict[str, Any]) -> list[dict[str, Any]] | None:
        raise NotImplementedError

    @abstractmethod
    def get_message_detail(self, mailbox: dict[str, Any], message_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def delete_message(self, mailbox: dict[str, Any], message_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def clear_messages(self, mailbox: dict[str, Any]) -> bool:
        raise NotImplementedError
