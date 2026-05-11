import asyncio
import os


class BaseLLM:
    async def generate_queries(self, company_name):
        return None

    async def summarize(self, category, documents):
        return None

    async def compile_report(self, state):
        return None


class MockLLM(BaseLLM):
    async def generate_queries(self, company_name):
        return None

    async def summarize(self, category, documents):
        return None

    async def compile_report(self, state):
        return None


async def get_llm():
    return None
