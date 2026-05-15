import asyncio
import os
import re
from abc import ABC, abstractmethod
from typing import List

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class BaseLLM(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def generate_queries(self, company_name: str) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    async def generate_briefing(self, category: str, company: str, docs: list) -> str:
        raise NotImplementedError


class MockLLM(BaseLLM):
    async def generate(self, prompt: str) -> str:
        await asyncio.sleep(0.3)
        match = re.search(r"\b[A-Z][A-Za-z0-9&.-]*\b", prompt)
        company = match.group(0) if match else "Company"
        return (
            f"{company} appears to operate with a focused commercial strategy and a clear market narrative. "
            f"Recent signals suggest {company} is balancing product execution, operating discipline, and competitive positioning. "
            "The business should be assessed across growth durability, leadership quality, and exposure to market shifts."
        )

    async def generate_queries(self, company_name: str) -> List[str]:
        await asyncio.sleep(0.2)
        return [
            f"{company_name} company overview business model 2024",
            f"{company_name} leadership team executives founders",
            f"{company_name} products services revenue streams",
            f"{company_name} corporate strategy market position",
        ]

    async def generate_briefing(self, category: str, company: str, docs: list) -> str:
        await asyncio.sleep(0.5)
        category_key = category.lower()
        doc_context = f"{len(docs)} source documents" if docs else "available public signals"

        if category_key == "company":
            paragraphs = [
                f"{company} presents as a company with a defined operating model, visible product focus, and a leadership structure that should be evaluated for execution consistency. The company overview should emphasize how its products, services, and customer segments connect to revenue generation.",
                f"The business model analysis should examine core offerings, pricing power, distribution channels, and how leadership decisions translate into market performance. Based on {doc_context}, the strongest indicators are product breadth, strategic clarity, and the durability of customer demand.",
                f"Key diligence areas include leadership continuity, product roadmap maturity, and whether the company can defend its market position while expanding into adjacent opportunities.",
            ]
        elif category_key == "financial":
            paragraphs = [
                f"{company} has demonstrated financial momentum that should be reviewed through revenue quality, funding capacity, valuation expectations, and growth efficiency. The financial profile is most useful when revenue expansion is compared with margin resilience and capital needs.",
                f"Investors and operators should assess whether growth is supported by recurring demand, disciplined spending, and credible long-term unit economics. Based on {doc_context}, the main financial questions involve valuation support, cash generation, and sensitivity to market cycles.",
                f"The next layer of analysis should compare {company}'s reported performance against analyst expectations, peer multiples, and any funding or balance-sheet signals that could affect strategic flexibility.",
            ]
        elif category_key == "industry":
            paragraphs = [
                f"{company} operates within an industry shaped by market size, customer adoption trends, regulatory pressure, and competitive intensity. Industry analysis should frame whether the company is riding durable demand or depending on shorter-term market enthusiasm.",
                f"The most important external factors are sector growth rates, regulation, technology shifts, and the pace at which competitors can copy or undercut the company's offerings. Based on {doc_context}, market position should be judged relative to both incumbents and emerging challengers.",
                f"A strong industry view should connect macro trends to practical execution risks, including pricing pressure, supply constraints, compliance obligations, and changes in customer buying behavior.",
            ]
        elif category_key == "news":
            paragraphs = [
                f"Recent coverage of {company} should be read for concrete events: product launches, executive commentary, regulatory developments, partnerships, and operational announcements. News flow can reveal whether strategy is converting into visible market action.",
                f"The most relevant press signals are those that affect customer confidence, investor expectations, or competitive perception. Based on {doc_context}, announcements should be separated from durable operating evidence.",
                f"Follow-up monitoring should focus on whether recent events change the company's risk profile, growth outlook, or credibility with customers, regulators, and capital markets.",
            ]
        else:
            paragraphs = [
                f"{company} should be assessed through the lens of {category_key} signals, with attention to how this area affects operating performance and market confidence.",
                f"Based on {doc_context}, the analysis should separate durable evidence from promotional or low-confidence claims.",
                f"The most useful next step is to compare these findings against peer behavior, historical performance, and near-term execution risks.",
            ]

        return f"## {category.title()} Analysis\n\n" + "\n\n".join(paragraphs)


class GroqLLM(BaseLLM):
    def __init__(self):
        from langchain_groq import ChatGroq

        self.client = ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.1,
            max_tokens=2048,
        )

    async def generate(self, prompt: str) -> str:
        try:
            response = await asyncio.to_thread(self.client.invoke, prompt)
            return response.content
        except Exception as e:
            print(f"Groq generation failed: {e}")
            return await MockLLM().generate(prompt)

    async def generate_queries(self, company_name: str) -> List[str]:
        prompt = (
            f"Generate exactly 4 specific web search queries to "
            f"research {company_name}. Return only the 4 queries, "
            f"one per line. No numbering, no bullets, no explanation."
        )
        text = await self.generate(prompt)
        queries = [q.strip() for q in text.strip().split("\n") if q.strip()]
        if len(queries) < 4:
            return await MockLLM().generate_queries(company_name)
        return queries[:4]

    async def generate_briefing(self, category: str, company: str, docs: list) -> str:
        context = "\n\n".join(
            d.get("content", "")[:3000] for d in docs[:5]
        )
        prompt = (
            f"Write a structured markdown briefing about {company}'s "
            f"{category} profile. Use ## headers and bullet points. "
            f"Be specific and factual. Base it on this context:\n\n"
            f"{context}"
        )
        briefing = await self.generate(prompt)
        if not briefing.strip().startswith("##"):
            return await MockLLM().generate_briefing(category, company, docs)
        return briefing


def get_llm() -> BaseLLM:
    groq_key = os.getenv("GROQ_API_KEY", "")
    use_mocks = os.getenv("USE_MOCKS", "true").lower() == "true"
    if use_mocks or not groq_key:
        return MockLLM()
    return GroqLLM()


if __name__ == "__main__":
    import asyncio

    async def test():
        llm = get_llm()
        print("Type:", type(llm).__name__)
        queries = await llm.generate_queries("Tesla")
        assert len(queries) == 4
        print(f"✅ Queries: {len(queries)}")
        for q in queries:
            print(f"   - {q}")
        briefing = await llm.generate_briefing("financial", "Tesla", [])
        assert "##" in briefing
        print(f"✅ Briefing: {len(briefing)} chars")
        print(briefing[:200])

    asyncio.run(test())
