from aiogram.filters import BaseFilter
from aiogram.types import Message
import re



class YouTubeLinkFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        youtube_pattern = re.compile(
            r"(https?://)?(www\.)?"
            r"(youtube\.com|youtu\.be)/"
            r"([a-zA-Z0-9_-]{11}|watch\?v=[a-zA-Z0-9_-]{11})"
        )
        return bool(youtube_pattern.search(message.text.strip()))