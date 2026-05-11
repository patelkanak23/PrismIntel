class BaseSearchTool:
    async def search(self, query):
        return None

    async def search_many(self, queries):
        return None

    async def crawl(self, url):
        return None


class MockTavily(BaseSearchTool):
    async def search(self, query):
        return None

    async def search_many(self, queries):
        return None

    async def crawl(self, url):
        return None


async def get_search_tool():
    return None
