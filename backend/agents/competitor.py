import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


if __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.state import ResearchState
from backend.tools.tavily_tools import get_search_tool
from backend.tools.llm import get_llm


class CompetitorAnalyst:
    def __init__(self):
        self.search_tool = get_search_tool()
        self.llm = get_llm()

    async def run(self, state: ResearchState) -> dict:
        company = state["company_name"]
        industry = state.get("industry", "")
        print(f"CompetitorAnalyst running for: {company}")
        self.search_tool = get_search_tool(state.get("tavily_api_key", ""))
        self.llm = get_llm()

        use_mocks = os.getenv("USE_MOCKS", "true").lower() == "true"
        if use_mocks:
            competitors = self._fallback_competitors(company, industry)
        else:
            competitors = await self._find_competitors(company, industry)

        return {"competitors": competitors}

    async def _find_competitors(self, company: str, industry: str) -> list:
        query = f"{company} competitors {industry} major rivals"
        try:
            results = await self.search_tool.search(query)
            
            try:
                context_parts = []
                for r in results:
                    context_parts.append(f"Title: {r.get('title', '')}\nContent: {r.get('content', '')}")
                context = "\n\n".join(context_parts)
                
                prompt = (
                    f"Based on this research, identify the 3 most important DIRECT competitors to {company}. "
                    f"Choose companies that compete for the SAME customers with similar products or services. "
                    f"Prefer companies that are the biggest competitive threat by revenue or market share. "
                    f"Return ONLY the company names. If a competitor is known by a specific product, format it as 'Company (Product)', e.g., 'Google (Gemini)'. "
                    f"Return one per line. No numbering, no descriptions, no explanations.\n\n"
                    f"Context:\n{context}"
                )
                
                llm_response = await self.llm.generate(prompt)
                names = [line.strip() for line in llm_response.split('\n') if line.strip()]
                
                competitors = []
                for name in names:
                    if len(name) > 2 and company.lower() not in name.lower() and name.lower() not in company.lower():
                        combo_prompt = (
                            f"About {name} competing with {company} in {industry or 'their market'}:\n"
                            f"Line 1: One-sentence description of {name} as a competitor.\n"
                            f"Line 2: Their single biggest competitive advantage in 5-10 words.\n"
                            f"Return exactly 2 lines, nothing else."
                        )
                        combo_response = await self.llm.generate(combo_prompt)
                        lines = [l.strip().strip('"') for l in combo_response.strip().split('\n') if l.strip()]
                        desc = lines[0] if lines else self._competitor_description(name, company, industry)
                        strength = lines[1].rstrip('.') if len(lines) > 1 else "Established market presence"

                        competitors.append({
                            "name": name,
                            "description": desc,
                            "strength": strength,
                        })
                        if len(competitors) == 3:
                            break
                if competitors:
                    return competitors
            except Exception as e:
                print(f"LLM extraction failed: {e}, falling back to regex parsing.")

            competitors = []
            seen_names = set()
            for result in results:
                names = self._candidate_names_from_result(company, result)
                if not names:
                    names = [self._name_from_result(result)]
                for name in names:
                    if not self._is_valid_competitor_name(name, company, seen_names):
                        continue
                    seen_names.add(name.lower())
                    competitors.append({
                        "name": name,
                        "description": self._competitor_description(
                            name,
                            company,
                            industry,
                        ),
                        "strength": "Established market presence and comparable customer segment",
                    })
                    if len(competitors) == 3:
                        break
                if len(competitors) == 3:
                    break
            return competitors or self._fallback_competitors(company, industry)
        except Exception as e:
            print(f"Competitor search failed: {e}")
            if os.getenv("USE_MOCKS", "true").lower() == "true":
                return self._fallback_competitors(company, industry)
            raise RuntimeError(f"Competitor search failed: {e}") from e

    def _name_from_result(self, result: dict) -> str:
        url = result.get("url", "")
        domain = urlparse(url).netloc.replace("www.", "")
        source_name = domain.split(".")[0].replace("-", " ").title() if domain else ""

        title = result.get("title", "").split("|")[0].strip()
        if title and not self._looks_like_article_title(title):
            return title.split(":")[0].strip()[:80]
        return source_name or title[:80]

    def _candidate_names_from_result(self, company: str, result: dict) -> list:
        text = " ".join([
            result.get("title", ""),
            result.get("content", ""),
        ])
        candidates = []
        patterns = [
            r"competitors include\s+([^.;]+)",
            r"competitors are\s+([^.;]+)",
            r"alternatives include\s+([^.;]+)",
            r"alternatives are:?\s+([^.;]+)",
            r"alternatives to use in \d{4}\.?\s*([^.;]+)",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                candidates.extend(self._split_candidate_names(match.group(1)))

        numbered = re.findall(r"(?:^|[\s;,])\d+\.\s*([A-Z][A-Za-z0-9&.\- ]{1,40})", text)
        candidates.extend(numbered)

        cleaned = []
        seen = set()
        for candidate in candidates:
            name = self._clean_name(candidate)
            if self._is_valid_competitor_name(name, company, seen):
                seen.add(name.lower())
                cleaned.append(name)
        return cleaned

    def _split_candidate_names(self, text: str) -> list:
        clean = re.sub(r"\band\b", ",", text, flags=re.IGNORECASE)
        return re.split(r"[,;/|]", clean)

    def _clean_name(self, name: str) -> str:
        clean = re.sub(r"^[\s\d.)\-:]+", "", name or "")
        clean = re.sub(r"\s+", " ", clean).strip(" .,:;-*#`")
        clean = re.sub(
            r"\b(the best|leading|top|major|key|main)\b",
            "",
            clean,
            flags=re.IGNORECASE,
        )
        clean = re.sub(r"\s+", " ", clean).strip(" .,:;-")
        return clean[:80]

    def _is_valid_competitor_name(
        self,
        name: str,
        company: str,
        seen_names: set,
    ) -> bool:
        if not name:
            return False
        lower_name = name.lower().strip()
        lower_company = company.lower()
        blocked = {
            lower_company,
            "mbaskool",
            "thebrandhopper",
            "globaldata",
            "metacto",
            "cabin",
            "cabin.ai",
            "company profile",
            "competitors",
            "alternatives",
            "google search",
        }
        if lower_name in seen_names or lower_name in blocked:
            return False
        # Block names that contain the target company name
        if lower_company in lower_name or lower_name in lower_company:
            return False
        junk_words = (
            "competitor", "alternative", "guide", "official", "site",
            "best", "list", "review", "wiki", "homepage", "website",
            "overview", "profile", "analysis",
        )
        if any(word in lower_name for word in junk_words):
            return False
        if len(name) < 3 or len(name.split()) > 5:
            return False
        # Block names that are just numbers or single chars with numbers
        if re.match(r"^[\d\s]+$", name):
            return False
        return bool(re.search(r"[A-Za-z]{2,}", name))

    def _competitor_description(
        self,
        name: str,
        company: str,
        industry: str,
    ) -> str:
        industry_phrase = f" in {industry}" if industry else ""
        return f"{name} is a direct competitor to {company}{industry_phrase}, competing across similar product categories and customer segments."

    def _looks_like_article_title(self, title: str) -> bool:
        markers = [
            " alternative",
            " alternatives",
            " competitor",
            " competitors",
            " vs ",
            "best ",
            "top ",
            "guide",
            "comparison",
        ]
        lower_title = title.lower()
        return any(marker in lower_title for marker in markers)

    def _looks_like_promo_sentence(self, sentence: str) -> bool:
        markers = [
            "talk to our",
            "book a demo",
            "schedule a demo",
            "contact us",
            "pricing",
            "sign up",
            "learn more",
        ]
        lower_sentence = sentence.lower()
        return any(marker in lower_sentence for marker in markers)

    def _clean_description(self, text: str) -> str:
        clean = re.sub(r"\s+", " ", text or "").strip()
        if not clean:
            return "Potential competitor with comparable market positioning."

        sentences = re.split(r"(?<=[.!?])\s+", clean)
        if len(sentences) > 1 and self._looks_like_article_title(sentences[0]):
            sentences = sentences[1:]
        sentences = [
            sentence for sentence in sentences
            if not self._looks_like_promo_sentence(sentence)
        ]
        if not sentences:
            return "Potential competitor with comparable market positioning."

        description = sentences[0]
        if len(sentences) > 1 and len(description) < 140:
            description = f"{description} {sentences[1]}"
        if len(description) > 260:
            description = description[:260].rsplit(" ", 1)[0].rstrip(" ,;:")
            description = f"{description}."
        if description[-1] not in ".!?":
            description = f"{description}."
        return description

    def _fallback_competitors(self, company: str, industry: str) -> list:
        return [
            {
                "name": f"{company} Competitor A",
                "description": f"Leading alternative to {company}",
                "strength": "Established market presence",
            },
            {
                "name": f"{company} Competitor B",
                "description": f"Fast-growing rival in {industry}",
                "strength": "Innovation and pricing",
            },
            {
                "name": f"{company} Competitor C",
                "description": f"International competitor to {company}",
                "strength": "Global distribution network",
            },
        ]


if __name__ == "__main__":
    import asyncio
    from backend.state import create_initial_state

    async def test():
        agent = CompetitorAnalyst()
        state = create_initial_state("t001", "Tesla", industry="electric vehicles")
        result = await agent.run(state)
        competitors = result["competitors"]
        assert len(competitors) == 3
        assert "name" in competitors[0]
        assert "description" in competitors[0]
        assert "strength" in competitors[0]
        print(f"✅ CompetitorAnalyst: {len(competitors)} competitors")
        print(f"   First: {competitors[0]['name']}")

    asyncio.run(test())
