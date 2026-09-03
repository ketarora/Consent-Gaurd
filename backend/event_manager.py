import asyncio
import json
from typing import AsyncGenerator

class EventManager:
    def __init__(self):
        self.listeners = []

    async def subscribe(self) -> AsyncGenerator[str, None]:
        queue = asyncio.Queue()
        self.listeners.append(queue)
        try:
            while True:
                msg = await queue.get()
                yield f"data: {msg}\n\n"
        finally:
            self.listeners.remove(queue)

    def publish(self, message: dict):
        # We need this to push out updates to all active SSE subscribers
        msg_str = json.dumps(message)
        for queue in self.listeners:
            queue.put_nowait(msg_str)

# Singleton instance exported for routes
sse_manager = EventManager()
