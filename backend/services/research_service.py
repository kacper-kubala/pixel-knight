"""Deep Research Agent service."""
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from ..models import SearchProvider


@dataclass
class ResearchStep:
    """A single step in the research process."""
    query: str
    results: List[Dict[str, Any]]
    analysis: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ResearchReport:
    """Complete research report."""
    original_query: str
    steps: List[ResearchStep]
    final_summary: str
    sources: List[Dict[str, Any]]
    total_sources_analyzed: int
    duration_seconds: float


class DeepResearchService:
    """Service for conducting deep, multi-round research."""
    
    def __init__(self):
        self.max_iterations = 5
        self.max_sources_per_round = 5
    
    async def conduct_research(
        self,
        query: str,
        search_service,
        llm_service,
        model: str,
        max_iterations: int = 5,
        search_provider: SearchProvider = SearchProvider.DUCKDUCKGO,
        progress_callback=None,
    ) -> ResearchReport:
        """
        Conduct deep research on a topic.
        
        Args:
            query: The research question
            search_service: Search service instance
            llm_service: LLM service instance
            model: Model to use for analysis
            max_iterations: Maximum research rounds
            search_provider: Search provider to use
            progress_callback: Optional async callback for progress updates
        """
        start_time = datetime.now()
        steps: List[ResearchStep] = []
        all_sources: List[Dict[str, Any]] = []
        seen_urls = set()
        
        current_query = query
        
        for iteration in range(max_iterations):
            if progress_callback:
                await progress_callback({
                    "type": "progress",
                    "iteration": iteration + 1,
                    "max_iterations": max_iterations,
                    "query": current_query,
                    "status": "searching"
                })
            
            # Search for information
            try:
                results = await search_service.search(
                    current_query,
                    provider=search_provider,
                    max_results=self.max_sources_per_round
                )
            except Exception as e:
                print(f"Search error in iteration {iteration}: {e}")
                results = []
            
            # Filter out already seen sources
            new_results = []
            for r in results:
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    new_results.append(r)
                    all_sources.append(r)
            
            if not new_results and iteration > 0:
                # No new information found, stop research
                break
            
            if progress_callback:
                await progress_callback({
                    "type": "progress",
                    "iteration": iteration + 1,
                    "status": "analyzing",
                    "sources_found": len(new_results)
                })
            
            # Analyze results
            context = "\n\n".join([
                f"Source: {r.get('title', 'Unknown')}\nURL: {r.get('url', '')}\nContent: {r.get('snippet', '')}"
                for r in new_results
            ])
            
            analysis_prompt = f"""You are a research analyst. Analyze the following search results for the query: "{current_query}"

Search Results:
{context}

Previous findings:
{self._summarize_steps(steps) if steps else "None yet."}

Provide:
1. Key findings from these sources
2. What information is still missing or unclear
3. A suggested follow-up search query to fill gaps (or "RESEARCH_COMPLETE" if sufficient info gathered)

Be concise but thorough."""

            try:
                analysis, _ = await llm_service.chat_completion(
                    messages=[],
                    model=model,
                    system_prompt=analysis_prompt,
                    temperature=0.3,
                    max_tokens=1000,
                )
            except Exception as e:
                analysis = f"Error analyzing results: {e}"
            
            step = ResearchStep(
                query=current_query,
                results=new_results,
                analysis=analysis,
            )
            steps.append(step)
            
            # Check if research is complete or extract next query
            if "RESEARCH_COMPLETE" in analysis.upper():
                break
            
            # Extract next query from analysis
            next_query = self._extract_next_query(analysis, query)
            if next_query and next_query != current_query:
                current_query = next_query
            else:
                break
        
        if progress_callback:
            await progress_callback({
                "type": "progress",
                "status": "summarizing"
            })
        
        # Generate final summary
        final_summary = await self._generate_final_summary(
            query, steps, llm_service, model
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return ResearchReport(
            original_query=query,
            steps=steps,
            final_summary=final_summary,
            sources=all_sources,
            total_sources_analyzed=len(all_sources),
            duration_seconds=duration,
        )
    
    def _summarize_steps(self, steps: List[ResearchStep]) -> str:
        """Summarize previous research steps."""
        if not steps:
            return ""
        
        summaries = []
        for i, step in enumerate(steps, 1):
            summaries.append(f"Round {i} ({step.query}): {step.analysis[:500]}...")
        
        return "\n".join(summaries)
    
    def _extract_next_query(self, analysis: str, original_query: str) -> Optional[str]:
        """Extract the suggested follow-up query from analysis."""
        # Look for suggested query in the analysis
        lines = analysis.split('\n')
        for line in lines:
            line_lower = line.lower()
            if 'follow-up' in line_lower or 'next query' in line_lower or 'search for' in line_lower:
                # Extract the query part
                if ':' in line:
                    query = line.split(':', 1)[1].strip().strip('"\'')
                    if len(query) > 10:
                        return query
        
        return None
    
    async def _generate_final_summary(
        self,
        original_query: str,
        steps: List[ResearchStep],
        llm_service,
        model: str,
    ) -> str:
        """Generate the final research summary."""
        all_findings = "\n\n".join([
            f"### Research Round {i+1}: {step.query}\n{step.analysis}"
            for i, step in enumerate(steps)
        ])
        
        summary_prompt = f"""Based on the following multi-round research on "{original_query}", provide a comprehensive final summary.

Research Findings:
{all_findings}

Create a well-structured summary that:
1. Directly answers the original question
2. Synthesizes key findings from all rounds
3. Notes any limitations or areas needing more research
4. Lists the most important sources

Format with clear headings and bullet points where appropriate."""

        try:
            summary, _ = await llm_service.chat_completion(
                messages=[],
                model=model,
                system_prompt=summary_prompt,
                temperature=0.3,
                max_tokens=2000,
            )
            return summary
        except Exception as e:
            return f"Error generating summary: {e}"


deep_research_service = DeepResearchService()

