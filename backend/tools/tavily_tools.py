import asyncio
import os
import re
from abc import ABC, abstractmethod
from typing import Dict, List
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class BaseSearchTool(ABC):
    @abstractmethod
    async def search(self, query: str, topic: str = "general") -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    async def crawl(self, url: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def extract(self, urls: List[str]) -> List[Dict]:
        raise NotImplementedError


class MockTavily(BaseSearchTool):
    async def search(self, query: str, topic: str = "general") -> List[Dict]:
        await asyncio.sleep(0.2)
        company = _extract_company(query)
        topic_key = topic.lower()

        if topic_key == "finance":
            titles = [
                f"{company} Q4 2024 Revenue Hits Record $25B",
                f"{company} Financial Performance Exceeds Analyst Expectations",
                f"{company} Valuation Analysis: Bull vs Bear Case",
            ]
            contents = [
                f"{company} reported stronger revenue momentum as analysts focused on margin quality, cash generation, and capital allocation. The company's valuation continues to reflect expectations for durable growth and improving operating leverage.",
                f"{company}'s latest financial performance points to resilient demand and tighter cost controls. Investors are watching whether revenue gains can translate into sustainable earnings expansion.",
                f"Market analysts remain split on {company}'s valuation, with bullish views tied to growth optionality and bearish views focused on competitive pressure. Funding access and balance-sheet flexibility remain important diligence points.",
            ]
        elif topic_key == "news":
            titles = [
                f"{company} Announces New Product and Expansion Plans",
                f"{company} Draws Fresh Press Coverage After Strategic Update",
                f"{company} Leadership Comments on 2024 Market Priorities",
            ]
            contents = [
                f"{company} announced a new product initiative aimed at deepening customer engagement and expanding its addressable market. The update generated fresh attention from business and technology media.",
                f"Recent coverage of {company} highlights operational announcements, customer momentum, and management commentary. The news cycle suggests stakeholders are watching execution against stated milestones.",
                f"{company} executives outlined market priorities for 2024, including product delivery, partnerships, and disciplined expansion. Press coverage framed the update as a test of strategic consistency.",
            ]
        else:
            titles = [
                f"{company} Company Overview and Business Model",
                f"{company} Products and Services Gain Market Attention",
                f"{company} Strategy Highlights Competitive Position",
            ]
            contents = [
                f"{company} operates with a business model centered on product execution, customer adoption, and defensible market positioning. Its overview points to a company balancing growth ambitions with operating discipline.",
                f"{company}'s products and services remain central to its revenue streams and customer relationships. The company appears focused on improving market reach while maintaining strategic clarity.",
                f"{company} continues to refine its corporate strategy as competition intensifies. Its market position depends on execution quality, brand strength, and the durability of customer demand.",
            ]

        domains = ["bloomberg.com", "techcrunch.com", "reuters.com"]
        scores = [0.92, 0.78, 0.65]
        return [
            {
                "title": titles[index],
                "url": f"https://{domains[index]}/{company.lower()}-{topic_key}-analysis",
                "content": contents[index],
                "score": scores[index],
            }
            for index in range(3)
        ]

    async def crawl(self, url: str) -> str:
        await asyncio.sleep(0.3)
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        company = _company_from_domain(domain)
        return (
            f"{company} is presented as a focused organization serving customers through a portfolio of products, "
            f"services, and digital experiences. The homepage for {domain} emphasizes practical outcomes, customer "
            f"trust, and a clear value proposition built around performance, reliability, and innovation. Visitors "
            "are guided toward understanding the company's core offerings, leadership priorities, and market focus. "
            "The content highlights product capabilities, support resources, and signals of momentum such as customer "
            "adoption, partnerships, and ongoing investment in better experiences. It also positions the company as "
            "responsive to changing market needs while maintaining a disciplined brand message. From a research "
            "perspective, the homepage provides useful context for business model analysis, product segmentation, "
            "and the themes management wants customers and investors to associate with the company. It also gives "
            "researchers a baseline for comparing public positioning with outside reporting, financial evidence, "
            "customer proof points, hiring signals, and the strategic claims that later pipeline stages should "
            "validate against independent sources."
        )

    async def extract(self, urls: List[str]) -> List[Dict]:
        await asyncio.sleep(0.2)
        article_text = (
            "This article reviews company performance, market positioning, executive priorities, customer demand, "
            "financial signals, competitive pressure, product development, regulatory considerations, investor "
            "sentiment, and operational execution. The coverage combines recent announcements with broader context "
            "about industry trends, growth expectations, management credibility, pricing dynamics, partnership "
            "activity, capital allocation, risk exposure, strategic focus, brand strength, supply conditions, "
            "customer retention, market share, technology adoption, margin outlook, funding flexibility, analyst "
            "commentary, governance quality, geographic expansion, pricing leverage, execution risk, supplier "
            "resilience, customer economics, hiring pace, and practical milestones observers will monitor closely "
            "as the company advances its public plans across priority markets this fiscal year globally."
        )
        return [{"url": url, "content": article_text} for url in urls]


class RealTavily(BaseSearchTool):
    def __init__(self):
        from tavily import TavilyClient

        self.client = TavilyClient(
            api_key=os.getenv("TAVILY_API_KEY")
        )

    async def search(self, query: str, topic: str = "general") -> List[Dict]:
        kwargs = {
            "query": query,
            "max_results": 5,
            "search_depth": "basic",
        }
        if topic in ("finance", "news"):
            kwargs["topic"] = topic
        try:
            raw = await asyncio.to_thread(self.client.search, **kwargs)
            results = raw.get("results", [])
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0.5),
                }
                for r in results
            ]
        except Exception as e:
            print(f"Tavily search failed: {e}")
            return await MockTavily().search(query, topic=topic)

    async def crawl(self, url: str) -> str:
        try:
            raw = await asyncio.to_thread(self.client.crawl, url)
            results = raw.get("results", [])
            return results[0].get("raw_content", "") if results else ""
        except Exception as e:
            print(f"Crawl failed: {e}")
            return await MockTavily().crawl(url)

    async def extract(self, urls: List[str]) -> List[Dict]:
        try:
            raw = await asyncio.to_thread(
                self.client.extract,
                urls=urls,
            )
            return [
                {
                    "url": r.get("url", ""),
                    "content": r.get("raw_content", ""),
                }
                for r in raw.get("results", [])
            ]
        except Exception as e:
            print(f"Extract failed: {e}")
            return await MockTavily().extract(urls)


def get_search_tool() -> BaseSearchTool:
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    use_mocks = os.getenv("USE_MOCKS", "true").lower() == "true"
    if use_mocks or not tavily_key:
        return MockTavily()
    return RealTavily()


def _extract_company(text: str) -> str:
    match = re.search(r"\b[A-Z][A-Za-z0-9&.-]*\b", text)
    return match.group(0) if match else "Company"


def _company_from_domain(domain: str) -> str:
    clean_domain = domain.replace("www.", "").split(":")[0]
    label = clean_domain.split(".")[0] if clean_domain else "company"
    return label.replace("-", " ").title() or "Company"


if __name__ == "__main__":
    import asyncio

    async def test():
        tool = get_search_tool()
        print("Type:", type(tool).__name__)
        results = await tool.search("Tesla financial 2024", topic="finance")
        assert len(results) == 3
        assert all("title" in r for r in results)
        assert all("url" in r for r in results)
        assert all("content" in r for r in results)
        assert all("score" in r for r in results)
        print(f"✅ Search: {len(results)} results")
        for r in results:
            print(f"   [{r['score']}] {r['title']}")
        content = await tool.crawl("https://tesla.com")
        assert len(content) > 50
        print(f"✅ Crawl: {len(content)} chars")
        extracted = await tool.extract(["https://bloomberg.com/tesla"])
        assert len(extracted) == 1
        print(f"✅ Extract: {len(extracted)} pages")

    asyncio.run(test())
