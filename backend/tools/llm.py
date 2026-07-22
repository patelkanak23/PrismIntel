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
            max_tokens=3072,
        )

    async def generate(self, prompt: str) -> str:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(self.client.invoke, prompt)
                return response.content
            except Exception as e:
                err_str = str(e).lower()
                if "rate_limit" in err_str or "429" in err_str or "too many" in err_str:
                    wait = 8 * (attempt + 1)  # 8s, 16s, 24s
                    print(f"Groq rate limited (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                print(f"Groq generation failed: {e}")
                raise RuntimeError(f"Groq API call failed: {e}") from e
        raise RuntimeError("Groq API rate limit exceeded after 3 retries. Try again in a minute.")

    async def generate_queries(self, company_name: str) -> List[str]:
        prompt = (
            f"Generate exactly 4 specific web search queries to "
            f"research {company_name}. Return only the 4 queries, "
            f"one per line. No numbering, no bullets, no explanation."
        )
        text = await self.generate(prompt)
        queries = [q.strip() for q in text.strip().split("\n") if q.strip()]
        if not queries:
            # Groq returned empty - use basic fallback queries
            queries = [
                f"{company_name} company overview business model",
                f"{company_name} revenue financials latest",
                f"{company_name} products services market",
                f"{company_name} news recent developments",
            ]
        if len(queries) < 4:
            fallback = [
                f"{company_name} company overview business model",
                f"{company_name} revenue financials latest",
                f"{company_name} products services market",
                f"{company_name} news recent developments",
            ]
            queries.extend(fallback[len(queries):])
        return queries[:4]

    async def generate_briefing(self, category: str, company: str, docs: list) -> str:
        context = "\n\n".join(
            d.get("content", "")[:3000] for d in docs[:5]
        )
        category_prompts = {
            "company": (
                f"You are a senior equity research analyst. Write a professional Company Overview "
                f"section for an intelligence report on {company}.\n\n"
                f"Structure your response with these exact subsections using ### headers:\n\n"
                f"### Corporate Profile\n"
                f"A paragraph describing what the company does, where it is headquartered, "
                f"when it was founded, and its global footprint.\n\n"
                f"### Product Portfolio\n"
                f"Detailed description of major product lines and brands. Name specific brands "
                f"and products. Group by category (beverages, snacks, etc).\n\n"
                f"### Leadership\n"
                f"Current CEO and key executives. Include names and roles.\n\n"
                f"### Business Model\n"
                f"How the company generates revenue: pricing strategy, distribution channels, "
                f"partnerships, and go-to-market approach.\n\n"
                f"### Target Markets\n"
                f"Who the company sells to: consumer segments, geographic markets, B2B vs B2C.\n\n"
                f"RULES:\n"
                f"- Start with '## Company Overview' as the main header\n"
                f"- Write in professional prose paragraphs, not bullet lists\n"
                f"- Include specific brand names, executive names, locations, dates\n"
                f"- Do NOT cover financials, revenue numbers, stock price, or industry trends\n"
                f"- Do NOT mention competitors in detail (that goes in a separate section)"
            ),
            "financial": (
                f"You are a senior equity research analyst. Write a professional Financial Overview "
                f"section for an intelligence report on {company}.\n\n"
                f"Structure your response with these exact subsections using ### headers:\n\n"
                f"### Revenue and Profitability\n"
                f"Latest annual and quarterly revenue, net income, gross/operating margins, "
                f"and year-over-year growth rates. Include specific dollar amounts and dates.\n\n"
                f"### Key Financial Metrics\n"
                f"EPS, P/E ratio, market capitalization, debt-to-equity ratio, "
                f"free cash flow, and EBITDA. Include actual numbers.\n\n"
                f"### Dividend and Shareholder Returns\n"
                f"Dividend per share, dividend yield, buyback programs, "
                f"and consecutive years of dividend increases.\n\n"
                f"### Financial Outlook\n"
                f"Forward guidance, analyst consensus estimates, and growth projections.\n\n"
                f"RULES:\n"
                f"- Start with '## Financial Overview' as the main header\n"
                f"- Write in professional prose with specific numbers, not vague statements\n"
                f"- Every claim should include a dollar amount, percentage, or date\n"
                f"- Do NOT describe what the company does or its products\n"
                f"- Do NOT discuss industry trends or competitor financials"
            ),
            "industry": (
                f"You are a senior equity research analyst. Write a professional Industry Overview "
                f"section for an intelligence report on {company}'s market.\n\n"
                f"Structure your response with these exact subsections using ### headers:\n\n"
                f"### Market Landscape\n"
                f"Total addressable market size, growth rate (CAGR), and key market segments. "
                f"Where does {company} rank in market share?\n\n"
                f"### Competitive Environment\n"
                f"Name the top 5-8 direct competitors with their market positions. "
                f"Compare market shares where data is available.\n\n"
                f"### Industry Trends\n"
                f"Major trends shaping the industry: consumer behavior shifts, technology, "
                f"regulatory changes, sustainability, health trends.\n\n"
                f"### Market Challenges\n"
                f"Key risks and headwinds facing the industry and {company}'s position.\n\n"
                f"RULES:\n"
                f"- Start with '## Industry Overview' as the main header\n"
                f"- Write in professional prose paragraphs\n"
                f"- Include market size figures, growth rates, and competitor names\n"
                f"- Do NOT repeat {company}'s financial data or internal metrics\n"
                f"- Do NOT discuss company-specific news events"
            ),
            "news": (
                f"You are a senior equity research analyst. Write a professional Recent Developments "
                f"section for an intelligence report on {company}.\n\n"
                f"Structure your response as:\n\n"
                f"### Recent Developments\n"
                f"List each news item as a separate paragraph with the date in bold at the start. "
                f"Cover the most recent and significant developments first.\n\n"
                f"MATERIALITY TEST — For each item from the context, ask yourself:\n"
                f"'Would this appear in a Wall Street equity research note? Could it move the "
                f"stock price, change revenue outlook, or affect the company's strategic position?'\n"
                f"If YES → include it. If NO → skip it.\n\n"
                f"Examples of MATERIAL items (include):\n"
                f"- Earnings results, guidance changes, revenue surprises\n"
                f"- Acquisitions, mergers, divestitures, major partnerships\n"
                f"- CEO/CFO appointments, board restructuring\n"
                f"- Major product launches, market expansion into new regions\n"
                f"- Regulatory actions, lawsuits, compliance changes\n"
                f"- Billion-dollar sponsorship or licensing deals\n"
                f"- Sustainability targets with financial implications\n"
                f"- Supply chain restructuring, factory investments\n\n"
                f"Examples of NON-MATERIAL items (skip):\n"
                f"- High school or college athlete awards\n"
                f"- Routine social media campaigns or marketing posts\n"
                f"- Minor community events or small charitable donations\n"
                f"- Routine dividend payment date reminders (unless it's a policy change)\n\n"
                f"RULES:\n"
                f"- Start with '## Recent Developments' as the main header\n"
                f"- Write each item as: '**Date** — Description of the event in 1-2 sentences.'\n"
                f"- Order chronologically, most recent first\n"
                f"- Include specific dates, dollar amounts, and names\n"
                f"- If fewer than 3 material items exist, include only what qualifies — do NOT pad with filler\n"
                f"- Do NOT include general company background or industry overview\n"
                f"- Do NOT repeat financial metrics already covered in financials section"
            ),
        }
        prompt = category_prompts.get(category, (
            f"Write a concise analyst briefing about {company}'s {category} profile.\n"
            f"Use ## headers and bullet points. Be specific and factual."
        ))
        prompt += f"\n\nBase your analysis on this research context:\n\n{context}"

        briefing = await self.generate(prompt)
        if not briefing or len(briefing.strip()) < 50:
            return f"## {category.title()} Analysis\n\nInsufficient data to generate a {category} briefing for {company}."
        # Ensure it starts with a markdown header
        stripped = briefing.strip()
        if not stripped.startswith("#"):
            briefing = f"## {category.title()} Analysis\n\n{stripped}"
        return briefing


def get_llm() -> BaseLLM:
    groq_key = os.getenv("GROQ_API_KEY", "")
    use_mocks = os.getenv("USE_MOCKS", "true").lower() == "true"
    if use_mocks or not groq_key:
        return MockLLM()
    try:
        return GroqLLM()
    except Exception as e:
        print(f"WARNING: Failed to initialize GroqLLM: {e}")
        print("  Install with: pip install langchain-groq")
        print("  Falling back to MockLLM")
        return MockLLM()


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
