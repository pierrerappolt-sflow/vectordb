"""Temporal workflow for ingesting a document through parsing and vectorization.

This is the parent workflow that orchestrates the entire document ingestion pipeline:
1. Parse fragments → ExtractedContent
2. Get library VectorizationConfigs
3. Spawn child ProcessConfigWorkflow for each config (parallel)
4. Mark document as COMPLETED (parsing done, child workflows spawned)
5. Monitor child workflows (for observability, doesn't affect document status)

Triggered by DocumentCreated event.

Note: Document status is marked COMPLETED as soon as child workflows are spawned.
Individual config processing status is tracked separately in document_vectorization_status.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from vdb_core.infrastructure.activities.ingestion_activities import (
        get_library_configs_activity,
        mark_document_completed_activity,
        parse_all_fragments_activity,
    )
    from vdb_core.infrastructure.workflows.process_config_workflow import (
        ProcessConfigWorkflow,
        ProcessConfigWorkflowInput,
    )


@dataclass
class IngestDocumentWorkflowInput:
    """Input for document ingestion workflow."""

    document_id: str
    library_id: str


@dataclass
class IngestDocumentWorkflowResult:
    """Result of document ingestion."""

    document_id: str
    status: str  # COMPLETED or FAILED


@workflow.defn
class IngestDocumentWorkflow:
    """Parent workflow for complete document ingestion.

    Flow:
    1. Parse all fragments → ExtractedContent
    2. Get all VectorizationConfigs for library
    3. Spawn child ProcessConfigWorkflow for each config (parallel)
    4. Mark document as COMPLETED (parsing done, workflows spawned)
    5. Monitor child workflows (observability only)

    Document is marked COMPLETED immediately after child workflows spawn.
    Config-specific processing status tracked in document_vectorization_status.
    """

    @workflow.run
    async def run(self, input_data: IngestDocumentWorkflowInput) -> IngestDocumentWorkflowResult:
        """Execute document ingestion workflow.

        Args:
            input_data: Document and library IDs

        Returns:
            Ingestion result with counts and status

        """
        workflow.logger.info(f"Starting ingestion for document {input_data.document_id}")

        try:
            # Step 1: Parse all fragments → ExtractedContent
            workflow.logger.info("Step 1: Parsing all fragments")
            parse_result = await workflow.execute_activity(
                parse_all_fragments_activity,
                args=[input_data.library_id, input_data.document_id],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(minutes=1),
                    backoff_coefficient=2.0,
                ),
            )

            extracted_content_ids = parse_result["extracted_content_ids"]
            workflow.logger.info(f"Parsed {len(extracted_content_ids)} ExtractedContent objects")

            # Step 2: Get all VectorizationConfigs for library
            workflow.logger.info("Step 2: Loading library configs")
            configs = await workflow.execute_activity(
                get_library_configs_activity,
                args=[input_data.library_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            workflow.logger.info(f"Found {len(configs)} configs to process")

            # Step 3: Spawn child ProcessConfigWorkflow for each config (parallel)
            workflow.logger.info("Step 3: Spawning child workflows for each config")
            child_handles = []

            for config in configs:
                config_id = config["config_id"]
                workflow_id = f"process-config-{input_data.document_id}-{config_id}"

                child_input = ProcessConfigWorkflowInput(
                    document_id=input_data.document_id,
                    library_id=input_data.library_id,
                    config_id=config_id,
                    extracted_content_ids=extracted_content_ids,
                )

                # Start child workflow
                child_handle = await workflow.start_child_workflow(
                    ProcessConfigWorkflow.run,
                    child_input,
                    id=workflow_id,
                    task_queue=workflow.info().task_queue,
                )

                child_handles.append((config_id, child_handle))
                workflow.logger.info(f"Started child workflow for config {config_id}")

            # Step 4: Mark document as COMPLETED (parsing done, child workflows spawned)
            workflow.logger.info("Step 4: Marking document as completed (child workflows spawned)")
            await workflow.execute_activity(
                mark_document_completed_activity,
                args=[input_data.library_id, input_data.document_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            # Step 5: Wait for all children to complete (for observability)
            workflow.logger.info("Step 5: Monitoring child workflows (non-blocking for document status)")
            for config_id, handle in child_handles:
                try:
                    result = await handle
                    workflow.logger.info(f"Config {config_id} completed with status: {result.status}")
                except Exception as e:
                    workflow.logger.error(f"Config {config_id} failed: {e}")
                    # Continue monitoring other children - don't fail parent workflow

            workflow.logger.info(f"✅ Document {input_data.document_id} ingestion workflow completed")

            return IngestDocumentWorkflowResult(
                document_id=input_data.document_id,
                status="COMPLETED",
            )

        except Exception as e:
            workflow.logger.error(f"❌ Document ingestion failed: {e}")

            # Mark document as FAILED
            # Note: This is best-effort - if it fails, document remains in PROCESSING state
            try:
                await workflow.execute_activity(
                    mark_document_completed_activity,
                    args=[input_data.library_id, input_data.document_id, str(e)],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=1),
                )
            except Exception as mark_err:
                workflow.logger.error(f"Failed to mark document as failed: {mark_err}")

            return IngestDocumentWorkflowResult(
                document_id=input_data.document_id,
                status="FAILED",
            )
