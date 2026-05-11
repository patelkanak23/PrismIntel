class EventManager:
    async def create_queue(self, job_id):
        return None

    async def publish(self, job_id, event):
        return None

    async def stream(self, job_id):
        return None

    async def cleanup(self, job_id):
        return None
