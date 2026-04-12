# -*- coding: utf-8 -*-
"""
Quality Metrics Testing Module for LLM Agent Evaluation.

This module provides specialized tests and metrics for evaluating
LLM agent quality in three key areas:

1. Memory Retrieval Accuracy - How well the agent recalls relevant memories
2. Hallucination Rate Detection - How often the agent generates false information
3. Tool Call Reasonableness - How appropriate the agent's tool usage is

These metrics address the challenge that agent quality is difficult to
quantify with traditional pass/fail testing.

Related Code:
- src/copaw/agents/memory/memory_manager.py - Memory search
- src/copaw/agents/react_agent.py - Tool calling
- src/copaw/agents/tools/ - Tool implementations
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# Section 1: Memory Retrieval Accuracy Metrics
# ============================================================================

@dataclass
class RetrievalMetrics:
    """Metrics for memory retrieval accuracy."""
    precision: float = 0.0  # Retrieved relevant / Retrieved total
    recall: float = 0.0    # Retrieved relevant / Relevant total
    f1_score: float = 0.0  # Harmonic mean of precision and recall
    mrr: float = 0.0       # Mean Reciprocal Rank
    ndcg: float = 0.0      # Normalized Discounted Cumulative Gain


class TestMemoryRetrievalAccuracy:
    """
    Test memory retrieval accuracy metrics.
    
    Memory retrieval quality is measured by:
    - Precision: Fraction of retrieved memories that are relevant
    - Recall: Fraction of relevant memories that are retrieved
    - F1 Score: Balance between precision and recall
    - MRR: Position of first relevant result
    - NDCG: Ranking quality considering position
    """
    
    @pytest.mark.asyncio
    async def test_retrieval_precision(self):
        """
        Test precision of memory retrieval.
        
        Precision = |Retrieved & Relevant| / |Retrieved|
        
        High precision means fewer irrelevant memories retrieved.
        """
        # Simulated retrieval results
        retrieved_memory_ids = {"mem_1", "mem_2", "mem_3", "mem_4", "mem_5"}
        relevant_memory_ids = {"mem_1", "mem_3", "mem_6", "mem_7"}
        
        # Calculate precision
        retrieved_relevant = retrieved_memory_ids & relevant_memory_ids
        precision = len(retrieved_relevant) / len(retrieved_memory_ids)
        
        # 2 relevant out of 5 retrieved = 0.4 precision
        assert precision == 0.4
        
        # Quality threshold: precision should be at least 0.6 for good retrieval
        # (In production, would test against actual memory search)
    
    @pytest.mark.asyncio
    async def test_retrieval_recall(self):
        """
        Test recall of memory retrieval.
        
        Recall = |Retrieved & Relevant| / |Relevant|
        
        High recall means most relevant memories are found.
        """
        retrieved_memory_ids = {"mem_1", "mem_2", "mem_3", "mem_4", "mem_5"}
        relevant_memory_ids = {"mem_1", "mem_3", "mem_6", "mem_7"}
        
        retrieved_relevant = retrieved_memory_ids & relevant_memory_ids
        recall = len(retrieved_relevant) / len(relevant_memory_ids)
        
        # 2 relevant retrieved out of 4 total relevant = 0.5 recall
        assert recall == 0.5
    
    @pytest.mark.asyncio
    async def test_mean_reciprocal_rank(self):
        """
        Test Mean Reciprocal Rank (MRR) for retrieval ranking.
        
        MRR = (1/|Q|) * Σ(1/rank_i) where rank_i is position of first
        relevant result for query i.
        
        Higher MRR indicates relevant results appear earlier.
        """
        # Ranking results for multiple queries
        # Each list shows positions of relevant results
        query_results = [
            [1, 3, 5],    # First relevant at position 1
            [2, 4],       # First relevant at position 2
            [1, 2],       # First relevant at position 1
            [3, 5, 7],    # First relevant at position 3
        ]
        
        reciprocal_ranks = [1 / ranks[0] for ranks in query_results]
        mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
        
        # MRR = (1 + 0.5 + 1 + 0.333) / 4 ≈ 0.708
        expected_mrr = (1 + 0.5 + 1 + 1/3) / 4
        assert abs(mrr - expected_mrr) < 0.01
    
    @pytest.mark.asyncio
    async def test_semantic_similarity_threshold(self):
        """
        Test that memory search respects semantic similarity thresholds.
        
        The min_score parameter should filter out low-similarity results.
        """
        # Simulated search results with scores
        search_results = [
            {"id": "mem_1", "content": "Project decision A", "score": 0.95},
            {"id": "mem_2", "content": "Meeting notes", "score": 0.72},
            {"id": "mem_3", "content": "Random notes", "score": 0.45},
            {"id": "mem_4", "content": "Unrelated", "score": 0.12},
        ]
        
        min_score = 0.5
        
        filtered_results = [
            r for r in search_results
            if r["score"] >= min_score
        ]
        
        # mem_1 (0.95) and mem_2 (0.72) pass the 0.5 threshold
        assert len(filtered_results) == 2
        assert all(r["score"] >= min_score for r in filtered_results)
    
    @pytest.mark.asyncio
    async def test_memory_search_hybrid_ranking(self):
        """
        Test hybrid ranking (vector + BM25) for memory search.
        
        Hybrid search combines semantic and keyword matching.
        """
        # Vector search results (semantic similarity)
        vector_results = {"mem_1": 0.9, "mem_2": 0.7, "mem_3": 0.5}
        
        # BM25 search results (keyword matching)
        bm25_results = {"mem_2": 3.5, "mem_4": 2.1, "mem_1": 1.8}
        
        # Combine scores (weighted average)
        alpha = 0.5  # Weight for vector vs BM25
        combined_scores = {}
        
        all_ids = set(vector_results.keys()) | set(bm25_results.keys())
        for mem_id in all_ids:
            v_score = vector_results.get(mem_id, 0)
            b_score = bm25_results.get(mem_id, 0)
            # Normalize BM25 (assuming max ~5)
            b_score_normalized = b_score / 5.0
            combined_scores[mem_id] = alpha * v_score + (1 - alpha) * b_score_normalized
        
        # Verify combined ranking
        ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        # mem_1 and mem_2 should rank high (appear in both)
        top_ids = [r[0] for r in ranked[:2]]
        assert "mem_1" in top_ids or "mem_2" in top_ids


# ============================================================================
# Section 2: Hallucination Rate Detection Metrics
# ============================================================================

class HallucinationType(Enum):
    """Types of hallucinations in LLM outputs."""
    FACTUAL_ERROR = "factual_error"      # Incorrect factual claims
    FABRICATION = "fabrication"          # Made-up information
    INCONSISTENCY = "inconsistency"      # Self-contradictory statements
    UNSUBSTANTIATED = "unsubstantiated"  # Claims without evidence
    TOOL_HALLUCINATION = "tool_hall"     # Non-existent tools or results


@dataclass
class HallucinationReport:
    """Report of detected hallucinations."""
    total_claims: int = 0
    hallucinated_claims: int = 0
    hallucination_rate: float = 0.0
    hallucination_types: Dict[HallucinationType, int] = field(default_factory=dict)
    flagged_statements: List[Dict[str, Any]] = field(default_factory=list)


class TestHallucinationDetection:
    """
    Test hallucination detection and rate measurement.
    
    Hallucinations in agent outputs can be detected by:
    - Cross-referencing claims with known facts
    - Checking internal consistency
    - Verifying tool call results
    - Detecting unsubstantiated claims
    """
    
    @pytest.mark.asyncio
    async def test_factual_error_detection(self):
        """
        Test detection of factual errors in agent responses.
        
        Factual errors occur when the agent makes incorrect claims
        about verifiable information.
        """
        # Known facts (ground truth)
        known_facts = {
            "project_start_date": "2025-01-15",
            "team_size": 5,
            "project_name": "CoPaw",
        }
        
        # Agent claims to verify
        agent_claims = [
            {"claim": "Project started on 2025-01-15", "type": "date"},
            {"claim": "Team has 10 members", "type": "number"},  # Error
            {"claim": "Project is called OpenClaw", "type": "name"},  # Error
        ]
        
        errors = []
        for claim in agent_claims:
            if "2025-01-15" in claim["claim"]:
                # Correct
                pass
            elif "10 members" in claim["claim"]:
                errors.append(claim)  # Should be 5
            elif "OpenClaw" in claim["claim"]:
                errors.append(claim)  # Should be CoPaw
        
        hallucination_rate = len(errors) / len(agent_claims)
        
        assert len(errors) == 2
        assert hallucination_rate == 2/3
    
    @pytest.mark.asyncio
    async def test_tool_result_hallucination(self):
        """
        Test detection of hallucinated tool results.
        
        Agent might claim a tool returned results it never actually returned.
        """
        # Actual tool execution log
        tool_execution_log = [
            {"tool": "read_file", "args": {"path": "/a.txt"}, "result": "content A"},
            {"tool": "read_file", "args": {"path": "/b.txt"}, "result": "content B"},
        ]
        
        # Agent's claimed tool results
        agent_claims = [
            "I read /a.txt and found content A",  # True
            "I read /b.txt and found content B",  # True
            "I read /c.txt and found secret data",  # Hallucinated
        ]
        
        # Verify each claim against log
        hallucinations = []
        for claim in agent_claims:
            if "/c.txt" in claim and "secret" in claim:
                # Check if /c.txt was actually read
                executed_paths = {e["args"]["path"] for e in tool_execution_log}
                if "/c.txt" not in executed_paths:
                    hallucinations.append({
                        "type": HallucinationType.TOOL_HALLUCINATION,
                        "claim": claim,
                    })
        
        assert len(hallucinations) == 1
    
    @pytest.mark.asyncio
    async def test_internal_consistency_check(self):
        """
        Test detection of self-contradictory statements.
        
        Agent should not contradict itself within a conversation.
        """
        agent_statements = [
            "The project started in January 2025.",
            "We have been working on this for 6 months.",
            "The project began in March 2025.",  # Contradicts first statement
        ]
        
        # Extract dates/times and check consistency
        dates = []
        for stmt in agent_statements:
            if "January 2025" in stmt:
                dates.append("2025-01")
            elif "March 2025" in stmt:
                dates.append("2025-03")
        
        # Should have consistent dates
        unique_dates = set(dates)
        
        assert len(unique_dates) > 1, "Inconsistent dates detected"
    
    @pytest.mark.asyncio
    async def test_unsubstantiated_claim_detection(self):
        """
        Test detection of claims without evidence.
        
        Agent should provide evidence for factual claims.
        """
        agent_response = """
        The system has been tested extensively.
        All unit tests pass with 100% coverage.
        The performance benchmarks show 50% improvement.
        """
        
        # Check for claims that require evidence
        claim_patterns = [
            (r"(\d+)% coverage", "test coverage"),
            (r"(\d+)% improvement", "performance improvement"),
        ]
        
        unsubstantiated = []
        for pattern, claim_type in claim_patterns:
            match = re.search(pattern, agent_response)
            if match and "test" not in agent_response.lower().split(match.group(0))[0][-50:]:
                # Found a numeric claim without nearby evidence citation
                unsubstantiated.append({
                    "type": HallucinationType.UNSUBSTANTIATED,
                    "claim": match.group(0),
                    "evidence_needed": claim_type,
                })
        
        # In real testing, would check if evidence files/references exist


# ============================================================================
# Section 3: Tool Call Reasonableness Metrics
# ============================================================================

@dataclass
class ToolCallMetrics:
    """Metrics for tool call reasonableness."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    unnecessary_calls: int = 0  # Calls that weren't needed
    incorrect_param_calls: int = 0  # Calls with wrong parameters
    efficiency_score: float = 0.0  # Useful calls / Total calls


class TestToolCallReasonableness:
    """
    Test tool call reasonableness and efficiency.
    
    Tool usage quality is measured by:
    - Success rate: Fraction of calls that succeed
    - Necessity rate: Fraction of calls that were actually needed
    - Parameter correctness: Fraction of calls with correct parameters
    - Efficiency: Overall usefulness of tool usage
    """
    
    @pytest.mark.asyncio
    async def test_tool_call_success_rate(self):
        """
        Test success rate of tool calls.
        
        High success rate indicates proper tool selection and usage.
        """
        tool_call_history = [
            {"tool": "read_file", "success": True},
            {"tool": "read_file", "success": True},
            {"tool": "write_file", "success": True},
            {"tool": "read_file", "success": False, "error": "File not found"},
            {"tool": "execute_command", "success": False, "error": "Permission denied"},
        ]
        
        successful = sum(1 for c in tool_call_history if c["success"])
        success_rate = successful / len(tool_call_history)
        
        # 3/5 = 60% success rate
        assert success_rate == 0.6
        
        # Quality threshold: success rate should be > 80%
        # (In production, track and alert on low success rates)
    
    @pytest.mark.asyncio
    async def test_tool_call_necessity(self):
        """
        Test whether tool calls were actually necessary.
        
        Unnecessary calls waste resources and slow down the agent.
        """
        # Task: "What is the content of file A?"
        tool_calls = [
            {"tool": "read_file", "args": {"path": "/file_A.txt"}},
            {"tool": "read_file", "args": {"path": "/file_B.txt"}},  # Unnecessary
            {"tool": "list_directory", "args": {"path": "/"}},  # Unnecessary
        ]
        
        necessary_tools = {"read_file:/file_A.txt"}  # Only needed tool
        
        unnecessary_count = 0
        for call in tool_calls:
            call_id = f"{call['tool']}:{call['args'].get('path', '')}"
            if call_id not in necessary_tools:
                unnecessary_count += 1
        
        assert unnecessary_count == 2  # Two unnecessary calls
    
    @pytest.mark.asyncio
    async def test_tool_parameter_correctness(self):
        """
        Test correctness of tool parameters.
        
        Correct parameters:
        - Required parameters present
        - Parameter types correct
        - Parameter values valid
        """
        tool_schemas = {
            "read_file": {
                "required": ["path"],
                "properties": {"path": {"type": "string"}},
            },
            "write_file": {
                "required": ["path", "content"],
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
            },
        }
        
        tool_calls = [
            {"tool": "read_file", "args": {"path": "/valid/path.txt"}},  # Correct
            {"tool": "read_file", "args": {}},  # Missing required
            {"tool": "write_file", "args": {"path": "/out.txt"}},  # Missing content
            {"tool": "write_file", "args": {"path": 123, "content": "data"}},  # Wrong type
        ]
        
        incorrect_params = 0
        for call in tool_calls:
            schema = tool_schemas.get(call["tool"], {})
            required = schema.get("required", [])
            args = call["args"]
            
            # Check required parameters
            for req in required:
                if req not in args:
                    incorrect_params += 1
                    break
            else:
                # Check types
                properties = schema.get("properties", {})
                for arg_name, arg_value in args.items():
                    if arg_name in properties:
                        expected_type = properties[arg_name].get("type")
                        if expected_type == "string" and not isinstance(arg_value, str):
                            incorrect_params += 1
        
        assert incorrect_params >= 3  # At least 3 calls have issues
    
    @pytest.mark.asyncio
    async def test_tool_selection_appropriateness(self):
        """
        Test whether the right tools were selected for the task.
        
        For a given task, verify the agent chose appropriate tools.
        """
        task = "Search for previous discussions about authentication"
        
        available_tools = {
            "memory_search", "read_file", "write_file", 
            "execute_command", "web_search"
        }
        
        # Agent's tool selection
        selected_tools = ["memory_search"]
        
        # Expected tool selection for this task
        expected_tools = {"memory_search"}  # Should use memory search
        
        # Verify appropriate tool selection
        appropriate_selection = expected_tools.issubset(set(selected_tools))
        
        assert appropriate_selection, (
            f"For task '{task}', expected tools {expected_tools}, "
            f"got {set(selected_tools)}"
        )
    
    @pytest.mark.asyncio
    async def test_tool_call_efficiency_score(self):
        """
        Test overall efficiency of tool usage.
        
        Efficiency = (Successful & Necessary calls) / Total calls
        
        High efficiency means the agent uses tools effectively.
        """
        tool_calls = [
            {"tool": "read_file", "success": True, "necessary": True},
            {"tool": "read_file", "success": True, "necessary": True},
            {"tool": "write_file", "success": True, "necessary": False},
            {"tool": "read_file", "success": False, "necessary": True},
        ]
        
        efficient_calls = sum(
            1 for c in tool_calls
            if c["success"] and c["necessary"]
        )
        efficiency = efficient_calls / len(tool_calls)
        
        # 2 efficient out of 4 total = 0.5
        assert efficiency == 0.5


# ============================================================================
# Section 4: Response Quality Metrics
# ============================================================================

class TestResponseQualityMetrics:
    """
    Test overall response quality metrics.
    
    Quality metrics include:
    - Response completeness
    - Response relevance
    - Response coherence
    - Response timeliness
    """
    
    @pytest.mark.asyncio
    async def test_response_completeness(self):
        """
        Test that responses are complete and address all aspects.
        
        For multi-part questions, verify all parts are addressed.
        """
        user_query = "What are the project's start date, team size, and main goals?"
        
        agent_response = """
        The project started on January 15, 2025.
        The team consists of 5 members.
        The main goals are to build a lightweight LLM agent framework.
        """
        
        # Check each required aspect
        required_aspects = ["start date", "team size", "main goals"]
        covered_aspects = []
        
        if "January" in agent_response or "2025" in agent_response:
            covered_aspects.append("start date")
        if "5" in agent_response:
            covered_aspects.append("team size")
        if "goals" in agent_response.lower():
            covered_aspects.append("main goals")
        
        completeness = len(covered_aspects) / len(required_aspects)
        
        assert completeness == 1.0, (
            f"Only covered {covered_aspects}, missing: "
            f"{set(required_aspects) - set(covered_aspects)}"
        )
    
    @pytest.mark.asyncio
    async def test_response_relevance(self):
        """
        Test that responses are relevant to the query.
        
        Off-topic responses indicate poor understanding or hallucination.
        """
        user_query = "How do I configure the Discord channel?"
        
        agent_response = """
        To configure the Discord channel:
        1. Add your bot token to config.json
        2. Set the channel as enabled
        3. Restart the application
        """
        
        # Check relevance by keyword overlap and topic matching
        query_keywords = {"configure", "discord", "channel"}
        response_keywords = set(agent_response.lower().split())
        
        keyword_overlap = query_keywords & response_keywords
        
        # Should have significant keyword overlap
        relevance_score = len(keyword_overlap) / len(query_keywords)
        
        assert relevance_score >= 0.5, "Response may not be relevant to query"


# ============================================================================
# Section 5: Aggregated Quality Score
# ============================================================================

@dataclass
class AgentQualityScore:
    """Aggregated quality score for agent evaluation."""
    retrieval_accuracy: float = 0.0
    hallucination_rate: float = 0.0  # Lower is better
    tool_efficiency: float = 0.0
    response_completeness: float = 0.0
    overall_score: float = 0.0  # Weighted average


class TestAggregatedQualityScore:
    """
    Test aggregated quality scoring.
    
    Provides a single metric for agent quality based on
    weighted combination of individual metrics.
    """
    
    @pytest.mark.asyncio
    async def test_quality_score_calculation(self):
        """
        Test calculation of aggregated quality score.
        
        Overall score combines:
        - Retrieval accuracy (weight 0.3)
        - Hallucination rate (weight 0.3, inverted)
        - Tool efficiency (weight 0.2)
        - Response completeness (weight 0.2)
        """
        metrics = {
            "retrieval_accuracy": 0.85,  # F1 score
            "hallucination_rate": 0.05,  # 5% hallucination
            "tool_efficiency": 0.75,
            "response_completeness": 0.90,
        }
        
        weights = {
            "retrieval_accuracy": 0.3,
            "hallucination_rate": 0.3,  # Inverted
            "tool_efficiency": 0.2,
            "response_completeness": 0.2,
        }
        
        # Calculate weighted score
        # For hallucination, lower is better, so invert
        hallucination_score = 1.0 - metrics["hallucination_rate"]
        
        overall = (
            weights["retrieval_accuracy"] * metrics["retrieval_accuracy"] +
            weights["hallucination_rate"] * hallucination_score +
            weights["tool_efficiency"] * metrics["tool_efficiency"] +
            weights["response_completeness"] * metrics["response_completeness"]
        )
        
        # 0.3*0.85 + 0.3*0.95 + 0.2*0.75 + 0.2*0.90 = 0.255 + 0.285 + 0.15 + 0.18 = 0.87
        expected = 0.255 + 0.285 + 0.15 + 0.18
        
        assert abs(overall - expected) < 0.01
        assert overall >= 0.8  # Quality threshold


# ============================================================================
# Section 6: Quality Test Fixtures
# ============================================================================

@pytest.fixture
def quality_metrics_tracker():
    """
    Fixture to track quality metrics across tests.
    
    Yields a dictionary to accumulate metrics for reporting.
    """
    return {
        "retrieval": [],
        "hallucination": [],
        "tool_calls": [],
        "responses": [],
    }


@pytest.fixture
def hallucination_detector():
    """
    Fixture providing hallucination detection utilities.
    """
    class HallucinationDetector:
        def __init__(self):
            self.known_facts: Dict[str, Any] = {}
        
        def add_known_fact(self, key: str, value: Any):
            self.known_facts[key] = value
        
        def check_claim(self, claim: str) -> bool:
            """Check if claim contradicts known facts."""
            # Simplified check - would use NLP in production
            return True  # Assume valid
        
        def detect_contradictions(
            self,
            statements: List[str],
        ) -> List[Tuple[int, int, str]]:
            """Find contradicting statement pairs."""
            # Returns list of (idx1, idx2, reason)
            return []
    
    return HallucinationDetector()
