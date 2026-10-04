"""User concurrency and access control management."""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, AsyncIterator
from bot.config import Config

class ConcurrencyManager:
    """Manages active tasks per user and enforces concurrency limits."""

    def __init__(self) -> None:
        self._user_locks: Dict[int, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    def is_user_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to use the bot."""
        if not Config.ALLOWED_USERS:
            return True
        return user_id in Config.ALLOWED_USERS

    async def is_user_busy(self, user_id: int) -> bool:
        """Check if user already has an active lock acquired."""
        async with self._global_lock:
            if user_id not in self._user_locks:
                return False
            return self._user_locks[user_id].locked()

    @asynccontextmanager
    async def user_session(self, user_id: int) -> AsyncIterator[bool]:
        """
        Context manager to acquire user's processing lock.
        Yields True if lock acquired, False if already busy.
        """
        async with self._global_lock:
            if user_id not in self._user_locks:
                self._user_locks[user_id] = asyncio.Lock()
            lock = self._user_locks[user_id]

        if lock.locked():
            yield False
            return

        await lock.acquire()
        try:
            yield True
        finally:
            lock.release()

concurrency_manager = ConcurrencyManager()
