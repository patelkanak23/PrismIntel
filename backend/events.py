import asyncio
import json
from typing import Dict, AsyncIterator


class EventManager:
    """Manages one SSE event queue per research job."""

    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}

    def create_queue(self, job_id: str) -> None:
        self.queues[job_id] = asyncio.Queue()

    async def publish(self, job_id: str,
                      event_type: str, data: dict) -> None:
        if job_id not in self.queues:
            return
        event = {"type": event_type, "data": data}
        await self.queues[job_id].put(event)

    async def stream(self, job_id: str) -> AsyncIterator[str]:
        if job_id not in self.queues:
            yield 'data: {"type":"error","data":{"message":"Job not found"}}\n\n'
            return
        while True:
            try:
                event = await asyncio.wait_for(
                    self.queues[job_id].get(), timeout=0.5
                )
                yield f"data: {json.dumps(event)}\n\n"
                if event["type"] in ("complete", "error"):
                    break
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"  # keep connection alive

    def cleanup(self, job_id: str) -> None:
        self.queues.pop(job_id, None)


# Global singleton used by both main.py and graph.py
event_manager = EventManager()


if __name__ == "__main__":
    import asyncio

    async def test():
        em = EventManager()
        em.create_queue("job_test")

        async def producer():
            await em.publish("job_test", "progress",
                             {"message": "Starting..."})
            await asyncio.sleep(0.1)
            await em.publish("job_test", "briefing_complete",
                             {"category": "company"})
            await asyncio.sleep(0.1)
            await em.publish("job_test", "complete",
                             {"report": "Final report"})

        async def consumer():
            count = 0
            async for line in em.stream("job_test"):
                if line.startswith(": heartbeat"):
                    continue
                print(f"Event: {line.strip()}")
                count += 1
            print(f"[PASS] Received {count} events")

        await asyncio.gather(producer(), consumer())

    asyncio.run(test())
