"""
Retrieval Agent (PRE Phase)

Retrieves relevant patterns and examples from RAG:
- Uses LLM to decide what to search
- Executes RAG searches via Qdrant/Neo4j (hybrid search)
- Ranks results by relevance
- Anti-hallucination verification
"""

import json
import logging
import time
import asyncio
from typing import Optional, List, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class RetrievalAgent:
    """
    PRE Phase Agent: Retrieves relevant patterns and examples

    Uses vLLM to generate search queries, then executes RAG searches.
    Features:
    - Hybrid search (semantic + graph)
    - Anti-hallucination verification
    - Result ranking and deduplication
    - Comprehensive error handling
    - Performance metrics
    """

    def __init__(self, vllm_url: str = "http://localhost:8000", rag_url: str = "http://localhost:8081", timeout: float = 30.0):
        self.vllm_url = vllm_url
        self.rag_url = rag_url
        self.model = "motadata-coder"
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.metrics = {
            "total_requests": 0,
            "successful_retrievals": 0,
            "partial_retrievals": 0,
            "failed_retrievals": 0,
            "total_latency": 0.0,
            "total_results": 0
        }
    
    async def run(self, state: dict) -> dict:
        """
        Retrieve relevant patterns and examples.

        Args:
            state: AgentState containing request_analysis results

        Returns:
            Dictionary with:
            - status: SUCCESS | PARTIAL | FAILED
            - retrieved_patterns: List of relevant patterns
            - retrieved_examples: List of example implementations
            - search_queries_used: Queries executed
            - coverage_score: 0.0-1.0
            - latency_ms: Processing time
        """

        start_time = time.time()
        self.metrics["total_requests"] += 1

        requirements = state.get("request_analysis", {}).get("extracted_requirements", {})
        task_type = state.get("task_type", "NEW_FEATURE")

        logger.info(f"Retrieving context for task type: {task_type}")

        try:
            # Step 1: Generate search queries using LLM
            search_queries = await self._generate_search_queries(requirements, task_type)
            logger.info(f"Generated {len(search_queries)} search queries")

            # Step 2: Execute hybrid RAG searches (parallel)
            results = await self._execute_hybrid_searches(search_queries)

            patterns = results.get("patterns", [])
            examples = results.get("examples", [])

            # Step 3: Rank and deduplicate
            patterns = self._rank_results(patterns, top_k=5)
            examples = self._rank_results(examples, top_k=5)

            # Step 4: Anti-hallucination verification
            if patterns or examples:
                verified = await self._verify_context(search_queries[0] if search_queries else "")
                if not verified:
                    logger.warning("Anti-hallucination check failed")
                    return {
                        "status": "FAILED",
                        "error": "Insufficient context for reliable generation",
                        "retrieved_patterns": [],
                        "retrieved_examples": [],
                        "search_queries_used": search_queries,
                        "coverage_score": 0.0,
                        "latency_ms": (time.time() - start_time) * 1000
                    }

            coverage_score = min(1.0, (len(patterns) + len(examples)) / 10.0)

            # Update metrics
            latency_ms = (time.time() - start_time) * 1000
            self.metrics["total_latency"] += latency_ms
            self.metrics["total_results"] += len(patterns) + len(examples)

            status = "SUCCESS" if patterns or examples else "PARTIAL"
            if status == "SUCCESS":
                self.metrics["successful_retrievals"] += 1
            else:
                self.metrics["partial_retrievals"] += 1

            logger.info(f"Retrieved {len(patterns)} patterns and {len(examples)} examples. Latency: {latency_ms:.2f}ms")

            return {
                "status": status,
                "retrieved_patterns": patterns,
                "retrieved_examples": examples,
                "search_queries_used": search_queries,
                "coverage_score": coverage_score,
                "latency_ms": latency_ms
            }

        except httpx.TimeoutException:
            logger.error("RAG service timeout")
            self.metrics["failed_retrievals"] += 1
            return {
                "status": "FAILED",
                "error": "RAG service timeout",
                "retrieved_patterns": [],
                "retrieved_examples": [],
                "search_queries_used": [],
                "coverage_score": 0.0,
                "latency_ms": (time.time() - start_time) * 1000
            }
        except Exception as e:
            logger.error(f"Error in Retrieval Agent: {e}", exc_info=True)
            self.metrics["failed_retrievals"] += 1
            return {
                "status": "FAILED",
                "error": str(e),
                "retrieved_patterns": [],
                "retrieved_examples": [],
                "search_queries_used": [],
                "coverage_score": 0.0,
                "latency_ms": (time.time() - start_time) * 1000
            }
    
    async def _generate_search_queries(self, requirements: dict, task_type: str) -> list:
        """Generate search queries using LLM"""
        
        prompt = f"""Based on these requirements, generate 3-5 specific search queries to find relevant code patterns:

Requirements:
{json.dumps(requirements, indent=2)}

Task Type: {task_type}

Return ONLY a JSON array of query strings:
["query1", "query2", "query3"]"""
        
        try:
            response = await self._call_vllm(prompt)
            
            # Extract JSON array
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            queries = json.loads(response[json_start:json_end])
            
            return queries if isinstance(queries, list) else []
            
        except Exception as e:
            logger.warning(f"Failed to generate search queries: {e}")
            # Fallback queries
            lang = requirements.get("programming_language", "Java")
            framework = requirements.get("frameworks", ["Vert.x"])[0]
            return [f"{lang} {framework} example", f"{framework} pattern"]
    
    async def _execute_hybrid_searches(self, queries: List[str]) -> Dict[str, List]:
        """Execute hybrid searches for all queries in parallel"""

        patterns = []
        examples = []

        # Execute searches in parallel
        tasks = [self._hybrid_search(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Search failed: {result}")
                continue

            patterns.extend(result.get("patterns", []))
            examples.extend(result.get("examples", []))

        return {"patterns": patterns, "examples": examples}

    async def _hybrid_search(self, query: str) -> Dict[str, List]:
        """Execute hybrid search (semantic + graph) for a single query"""

        try:
            response = await self.client.post(
                f"{self.rag_url}/search/hybrid",
                json={
                    "query": query,
                    "top_k": 5,
                    "include_callers": True,
                    "include_callees": True
                }
            )
            response.raise_for_status()
            data = response.json()

            # Extract patterns and examples from results
            # Note: Hybrid search returns HybridResult objects with nested 'code' field
            results = data.get("results", [])
            patterns = []
            examples = []

            for result in results:
                # Handle both direct results and nested HybridResult structure
                code_obj = result.get("code", result)
                node_type = code_obj.get("node_type", "")

                # Enrich with graph context if available
                enriched = {
                    **code_obj,
                    "callers": result.get("callers", []),
                    "callees": result.get("callees", []),
                    "inherits_from": result.get("inherits_from"),
                    "implemented_by": result.get("implemented_by", [])
                }

                if node_type in ["class", "method"]:
                    patterns.append(enriched)
                elif node_type == "function":
                    examples.append(enriched)

            return {"patterns": patterns, "examples": examples}

        except Exception as e:
            logger.warning(f"Hybrid search failed for '{query}': {e}")
            return {"patterns": [], "examples": []}

    async def _verify_context(self, query: str) -> bool:
        """Verify that sufficient context exists (anti-hallucination check)"""

        try:
            response = await self.client.post(
                f"{self.rag_url}/verify",
                params={"query": query, "min_results": 1}
            )
            response.raise_for_status()
            data = response.json()

            # Check for either has_context or has_sufficient_context
            return data.get("has_sufficient_context", data.get("has_context", False))

        except Exception as e:
            logger.warning(f"Context verification failed: {e}")
            return False
    
    def _rank_results(self, results: list, top_k: int = 5) -> list:
        """Rank and deduplicate results"""

        # Sort by relevance score
        sorted_results = sorted(
            results,
            key=lambda x: x.get("relevance_score", x.get("score", 0)),
            reverse=True
        )

        # Deduplicate by file_path
        seen = set()
        deduped = []
        for result in sorted_results:
            path = result.get("file_path", "")
            if path not in seen:
                seen.add(path)
                deduped.append(result)

        return deduped[:top_k]

    async def _call_vllm(self, prompt: str) -> str:
        """Call vLLM API"""

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 500
        }

        response = await self.client.post(
            f"{self.vllm_url}/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def get_metrics(self) -> dict:
        """Get performance metrics"""
        avg_latency = (
            self.metrics["total_latency"] / self.metrics["total_requests"]
            if self.metrics["total_requests"] > 0 else 0.0
        )

        success_rate = (
            self.metrics["successful_retrievals"] / self.metrics["total_requests"]
            if self.metrics["total_requests"] > 0 else 0.0
        )

        avg_results = (
            self.metrics["total_results"] / self.metrics["total_requests"]
            if self.metrics["total_requests"] > 0 else 0.0
        )

        return {
            "total_requests": self.metrics["total_requests"],
            "successful_retrievals": self.metrics["successful_retrievals"],
            "partial_retrievals": self.metrics["partial_retrievals"],
            "failed_retrievals": self.metrics["failed_retrievals"],
            "success_rate": success_rate,
            "avg_latency_ms": avg_latency,
            "avg_results_per_request": avg_results
        }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

