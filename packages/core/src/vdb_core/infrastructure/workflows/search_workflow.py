"""Temporal workflow for orchestrating vector search operations.

Workflows define the high-level orchestration logic but don't perform
actual work themselves. All business logic is delegated to activities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from vdb_core.infrastructure.activities import (
        enrich_search_results_activity,
        generate_query_embedding_activity,
        search_vectors_activity,
        update_query_status_activity,
    )


@dataclass
class SearchWorkflowInput:
    """Input parameters for search workflow."""

    query_id: str  # Query ID for updating DB
    library_id: str
    config_id: str
    query_text: str
    top_k: int
    strategy: str


@dataclass
class SearchWorkflowResult:
    """Result from search workflow."""

    results: list[dict[str, str | float]]
    query_text: str
    result_count: int


@workflow.defn
class SearchWorkflow:
    """Workflow for orchestrating vector similarity search.

    This workflow coordinates the following steps:
    1. Generate embedding for the query text
    2. Search the vector index for similar embeddings
    3. Enrich results with chunk and document details

    Each step is executed as a Temporal activity with automatic retries,
    timeouts, and durability guarantees.
    """

    @workflow.run
    async def run(
        self,
        input_data: SearchWorkflowInput,
    ) -> SearchWorkflowResult:
        """Execute the search workflow.

        Args:
            input_data: Search parameters (library_id, query_text, top_k, strategy)

        Returns:
            Search results with enriched details

        """
        workflow.logger.info(f"Starting search workflow for query {input_data.query_id}")

        # Update status to PROCESSING
        await workflow.execute_activity(
            update_query_status_activity,
            args=[input_data.query_id, "PROCESSING", None, None],
            start_to_close_timeout=timedelta(seconds=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        # Step 1: Generate query embedding
        workflow.logger.info("Step 1: Generating query embedding")
        query_vector = await workflow.execute_activity(
            generate_query_embedding_activity,
            args=[input_data.query_text, input_data.library_id, input_data.config_id],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
            ),
        )

        # Step 2: Search vector index
        workflow.logger.info("Step 2: Searching vector index")
        raw_results = await workflow.execute_activity(
            search_vectors_activity,
            args=[
                input_data.library_id,
                input_data.config_id,
                query_vector,
                input_data.top_k,
            ],
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=5),
            ),
        )

        # Step 3: Enrich results with chunk details
        workflow.logger.info("Step 3: Enriching results")
        enriched_results = await workflow.execute_activity(
            enrich_search_results_activity,
            args=[raw_results],
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=5),
            ),
        )

        workflow.logger.info(f"Search workflow completed with {len(enriched_results)} results")

        # Store result data (chunk_id, score, embedding_id, start/end) for hydration
        # We don't store text/document_id as those can be re-fetched from chunks table
        results_data = [
            {
                "chunk_id": result["chunk_id"],
                "embedding_id": result["embedding_id"],
                "score": result["score"],
                "start_index": 0,
                "end_index": 0,
            }
            for result in enriched_results
        ]

        # Update query with results and status COMPLETED
        await workflow.execute_activity(
            update_query_status_activity,
            args=[input_data.query_id, "COMPLETED", results_data, None],
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        return SearchWorkflowResult(
            results=enriched_results,
            query_text=input_data.query_text,
            result_count=len(enriched_results),
        )
