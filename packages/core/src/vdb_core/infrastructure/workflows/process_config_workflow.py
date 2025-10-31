"""Temporal workflow for processing a document with a specific VectorizationConfig.

This is a child workflow that handles vectorization for one config:
1. Load ExtractedContent
2. Chunk content using config's chunking strategy
3. Generate embeddings using config's embedding strategy
4. Index vectors in (library_id, config_id) graph
5. Mark document vectorization as COMPLETED for this config
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from vdb_core.infrastructure.activities.process_config_activities import (
        chunk_content_activity,
        generate_embeddings_activity,
        index_vectors_activity,
        load_extracted_content_activity,
        mark_config_processing_completed_activity,
    )


@dataclass
class ProcessConfigWorkflowInput:
    """Input for processing a document with a VectorizationConfig."""

    document_id: str
    library_id: str
    config_id: str
    extracted_content_ids: list[str]


@dataclass
class ProcessConfigWorkflowResult:
    """Result of processing a document with a config."""

    config_id: str
    status: str  # COMPLETED or FAILED


@workflow.defn
class ProcessConfigWorkflow:
    """Child workflow for document vectorization with one config.

    This workflow processes a document with a specific VectorizationConfig:
    - Chunks content using config's chunking strategy
    - Generates embeddings using config's embedding strategy
    - Indexes vectors in (library_id, config_id) graph

    Spawned as a child workflow by IngestDocumentWorkflow.
    """

    @workflow.run
    async def run(self, input_data: ProcessConfigWorkflowInput) -> ProcessConfigWorkflowResult:
        """Execute vectorization pipeline for one config.

        Args:
            input_data: Document, library, config, and extracted content IDs

        Returns:
            Processing result with counts

        """
        workflow.logger.info(
            f"Processing document {input_data.document_id} with config {input_data.config_id}"
        )

        try:
            # Step 1: Load ExtractedContent from database
            workflow.logger.info("Step 1: Loading ExtractedContent")
            extracted_contents = await workflow.execute_activity(
                load_extracted_content_activity,
                args=[input_data.library_id, input_data.extracted_content_ids],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=1),
                ),
            )

            workflow.logger.info(f"Loaded {len(extracted_contents)} ExtractedContent objects")

            # Step 2: Chunk content using config's chunking strategy
            workflow.logger.info("Step 2: Chunking content")
            chunk_ids = await workflow.execute_activity(
                chunk_content_activity,
                args=[
                    input_data.library_id,
                    input_data.config_id,
                    input_data.document_id,
                    extracted_contents,
                ],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=30),
                    backoff_coefficient=2.0,
                ),
            )

            workflow.logger.info(f"Created {len(chunk_ids)} chunks")

            # Step 3: Generate embeddings using config's embedding strategy
            workflow.logger.info("Step 3: Generating embeddings")
            embedding_result = await workflow.execute_activity(
                generate_embeddings_activity,
                args=[input_data.library_id, input_data.config_id, chunk_ids],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(minutes=1),
                    backoff_coefficient=2.0,
                ),
            )

            embedding_ids = embedding_result["embedding_ids"]
            workflow.logger.info(f"Generated {len(embedding_ids)} embeddings")

            # Step 4: Index vectors in (library_id, config_id) graph
            workflow.logger.info("Step 4: Indexing vectors")
            indexed_count = await workflow.execute_activity(
                index_vectors_activity,
                args=[input_data.library_id, input_data.config_id, embedding_ids],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=30),
                    backoff_coefficient=2.0,
                ),
            )

            workflow.logger.info(f"Indexed {indexed_count} vectors")

            # Step 5: Mark document vectorization as COMPLETED for this config
            workflow.logger.info("Step 5: Marking config processing as completed")
            await workflow.execute_activity(
                mark_config_processing_completed_activity,
                args=[input_data.document_id, input_data.config_id, "completed"],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            workflow.logger.info(
                f"✅ Config {input_data.config_id} processing completed: "
                f"{len(chunk_ids)} chunks, {len(embedding_ids)} embeddings, {indexed_count} indexed"
            )

            return ProcessConfigWorkflowResult(
                config_id=input_data.config_id,
                status="COMPLETED",
            )

        except Exception as e:
            workflow.logger.error(f"❌ Config {input_data.config_id} processing failed: {e}")

            # Mark config processing as failed (best-effort)
            try:
                await workflow.execute_activity(
                    mark_config_processing_completed_activity,
                    args=[input_data.document_id, input_data.config_id, "failed", str(e)],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=1),
                )
            except Exception as mark_err:
                workflow.logger.error(f"Failed to mark config as failed: {mark_err}")

            raise  # Re-raise to mark workflow as failed
