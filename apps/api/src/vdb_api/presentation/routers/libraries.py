"""Library and document management endpoints.

# TODO: Consistently add Command or Query handler to all routes.
# TODO: Split read/write servers.
"""

import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, File, HTTPException, Path, Query, Request, UploadFile
from temporalio.client import Client
from vdb_core.application.commands import CreateLibraryInput, UploadDocumentInput
from vdb_core.application.queries import (
    GetDocumentByIdQuery,
    GetDocumentsQuery,
    GetEventLogsQuery,
    GetLibrariesQuery,
)

from ...infrastructure import DIContainer
from ..schemas.document_schemas import (
    ChunkWithContextResponse,
    DocumentFragmentResponse,
    DocumentResponse,
    DocumentUploadResponse,
    GetDocumentsResponse,
)
from ..schemas.library_schemas import (
    AddConfigToLibraryRequest,
    AddConfigToLibraryResponse,
    CreateLibraryRequest,
    CreateLibraryResponse,
    CreateQueryRequest,
    CreateQueryResponse,
    DocumentVectorizationStatusResponse,
    EventLogResponse,
    GetEventLogsResponse,
    GetLibrariesResponse,
    GetLibraryConfigsResponse,
    GetQueriesResponse,
    GetVectorizationConfigsResponse,
    LibraryResponse,
    QueryResponse,
    SearchResult,
    VectorizationConfigResponse,
)

router = APIRouter(prefix="/libraries")

# Create a separate router for global events endpoint (no prefix)
events_router = APIRouter(tags=["events"])

# Create a separate router for global vectorization configs endpoint (no prefix)
configs_router = APIRouter(tags=["vectorization-configs"])


def get_container(request: Request) -> DIContainer:
    """Get DI container from app state.

    Args:
        request: FastAPI request object

    Returns:
        DI container instance
    """
    return request.app.state.container


def get_temporal_client(request: Request) -> Client:
    """Get Temporal client from app state.

    Args:
        request: FastAPI request object

    Returns:
        Temporal client instance
    """
    return request.app.state.temporal_client


def validate_uuid(value: str, param_name: str) -> None:
    """Validate that a string is a valid UUID.

    Args:
        value: String to validate
        param_name: Name of the parameter for error message

    Raises:
        HTTPException: 400 if value is not a valid UUID
    """
    from uuid import UUID

    try:
        UUID(value)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {param_name} format: must be a valid UUID, got '{value}'"
        )


@router.get("", response_model=GetLibrariesResponse, tags=["libraries"])
async def get_libraries(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    container: DIContainer = Depends(get_container),
) -> GetLibrariesResponse:
    """Get all libraries with pagination.

    Following CQRS pattern:
    - Uses query handler (read side)
    - Returns read models via query repository
    - Separate from write operations

    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
        container: DI container with query handlers

    Returns:
        GetLibrariesResponse with list of libraries
    """
    # Get query handler from container
    get_libraries_query = container.application.get_libraries_query

    # Create query and execute
    query = GetLibrariesQuery(limit=limit, offset=offset)
    libraries = await get_libraries_query.execute(query)

    # Build response
    return GetLibrariesResponse(
        libraries=[
            LibraryResponse(
                id=lib.id,
                name=lib.name,
                status=lib.status,
                created_at=lib.created_at.isoformat(),
                updated_at=lib.updated_at.isoformat(),
                document_count=lib.document_count,
            )
            for lib in libraries
        ],
        total=len(libraries),  # In production, would query total count separately
        limit=limit,
        offset=offset,
    )


@router.get("/{library_id}", response_model=LibraryResponse, tags=["libraries"])
async def get_library(
    library_id: str = Path(..., description="Library ID"),
    container: DIContainer = Depends(get_container),
) -> LibraryResponse:
    """Get a specific library by ID.

    Args:
        library_id: ID of the library to retrieve
        container: DI container with query handlers

    Returns:
        LibraryResponse with library details

    Raises:
        HTTPException: 400 if library_id is not a valid UUID
        HTTPException: 404 if library not found
    """
    from vdb_core.application.queries import GetLibraryByIdQuery

    # Validate UUID format
    validate_uuid(library_id, "library_id")

    # Get query handler from container
    get_library_by_id_query = container.application.get_library_by_id_query

    # Create query and execute (raises LibraryNotFoundError if not found)
    query = GetLibraryByIdQuery(library_id=library_id)
    library = await get_library_by_id_query.execute(query)

    return LibraryResponse(
        id=library.id,
        name=library.name,
        status=library.status,
        created_at=library.created_at.isoformat() if isinstance(library.created_at, datetime) else library.created_at,
        updated_at=library.updated_at.isoformat() if isinstance(library.updated_at, datetime) else library.updated_at,
        document_count=library.document_count,
    )


@router.delete("/{library_id}", status_code=204, tags=["libraries"])
async def delete_library(
    library_id: str = Path(..., description="Library ID"),
    container: DIContainer = Depends(get_container),
) -> None:
    """Soft-delete a library by marking its status as DELETED.

    The library is not removed from the database but will be filtered out
    from all query results. This preserves data integrity and audit trail.

    Args:
        library_id: ID of the library to delete
        container: DI container with commands

    Raises:
        HTTPException: 400 if library_id is not a valid UUID
        HTTPException: 404 if library not found
    """
    from vdb_core.application.commands import DeleteLibraryInput

    # Validate UUID format
    validate_uuid(library_id, "library_id")

    # Get command from container
    command = container.application.delete_library_command

    # Execute command (raises LibraryNotFoundError if not found)
    input_data = DeleteLibraryInput(library_id=library_id)
    await command.execute(input_data)


@router.post("", response_model=CreateLibraryResponse, status_code=201, tags=["libraries"])
async def create_library(
    request: CreateLibraryRequest,
    container: DIContainer = Depends(get_container),
) -> CreateLibraryResponse:
    """Create a new library.

    Args:
        request: Library creation request with name
        container: DI container with commands

    Returns:
        CreateLibraryResponse with library details
    """
    # Get command from container
    command = container.application.create_library_command

    # Create input and execute command
    input_data = CreateLibraryInput(name=request.name)
    library_id = await command.execute(input_data)

    # Query the created library to get full details (CQRS pattern)
    # Raises LibraryNotFoundError if not found (which would indicate a serious bug)
    get_library_by_id_query = container.application.get_library_by_id_query
    from vdb_core.application.queries import GetLibraryByIdQuery

    query = GetLibraryByIdQuery(library_id=str(library_id))
    library = await get_library_by_id_query.execute(query)

    return CreateLibraryResponse(
        library=LibraryResponse(
            id=library.id,
            name=library.name,
            status=library.status,
            created_at=library.created_at.isoformat()
            if isinstance(library.created_at, datetime)
            else library.created_at,
            updated_at=library.updated_at.isoformat()
            if isinstance(library.updated_at, datetime)
            else library.updated_at,
            document_count=library.document_count,
        ),
        message="Library created successfully",
    )


@router.get("/{library_id}/documents", response_model=GetDocumentsResponse, tags=["documents"])
async def get_documents(
    library_id: str = Path(..., description="Library ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    container: DIContainer = Depends(get_container),
) -> GetDocumentsResponse:
    """Get all documents in a library with pagination.

    TODO: This should use a Query handler.

    Following CQRS pattern:
    - Uses query handler (read side)
    - Returns read models via query repository
    - Separate from write operations

    Args:
        library_id: ID of the library to get documents from
        limit: Maximum number of results to return
        offset: Number of results to skip
        container: DI container with query handlers

    Returns:
        GetDocumentsResponse with list of documents

    Raises:
        HTTPException: 400 if library_id is not a valid UUID
    """
    # Validate UUID format
    validate_uuid(library_id, "library_id")

    # Get query handler from container
    get_documents_query = container.application.get_documents_query

    # Create query and execute
    query = GetDocumentsQuery(library_id=library_id, limit=limit, offset=offset)
    documents = await get_documents_query.execute(query)

    # Build response
    return GetDocumentsResponse(
        documents=[
            DocumentResponse(
                id=doc.id,
                library_id=doc.library_id,
                name=doc.name,
                status=doc.status,
                created_at=doc.created_at if isinstance(doc.created_at, str) else doc.created_at.isoformat(),
                updated_at=doc.updated_at if isinstance(doc.updated_at, str) else doc.updated_at.isoformat(),
                upload_complete=doc.upload_complete,
                fragment_count=doc.fragment_count,
                total_bytes=doc.total_bytes,
                embeddings_count=doc.embeddings_count,
                embeddings_by_config_id=doc.embeddings_by_config_id,
                vectorization_statuses=[
                    DocumentVectorizationStatusResponse(
                        document_id=status.document_id,
                        config_id=status.config_id,
                        status=status.status,
                        error_message=status.error_message,
                        created_at=status.created_at if isinstance(status.created_at, str) else status.created_at.isoformat(),
                        updated_at=status.updated_at if isinstance(status.updated_at, str) else status.updated_at.isoformat(),
                    )
                    for status in doc.vectorization_statuses
                ],
            )
            for doc in documents
        ],
        total=0, # TODO: Fix this.
        limit=limit,
        offset=offset,
    )


@router.get("/{library_id}/documents/{document_id}", response_model=DocumentResponse, tags=["documents"])
async def get_document(
    library_id: str = Path(..., description="Library ID"),
    document_id: str = Path(..., description="Document ID"),
    container: DIContainer = Depends(get_container),
) -> DocumentResponse:
    """Get a specific document by ID (metadata only, no content).

    Returns lightweight metadata including:
    - Document ID, name, status
    - Upload status and timestamps
    - Fragment count and total bytes

    To retrieve actual document content, use the fragments endpoint.

    Following CQRS pattern:
    - Uses query handler (read side)
    - Returns read model from query repository

    Args:
        library_id: ID of the parent library
        document_id: ID of the document to retrieve
        container: DI container with query handlers

    Returns:
        DocumentResponse with metadata (no content)

    Raises:
        HTTPException: 400 if library_id or document_id is not a valid UUID
        HTTPException: 404 if document not found
    """
    # Validate UUID formats
    validate_uuid(library_id, "library_id")
    validate_uuid(document_id, "document_id")

    # Get query handler from container
    get_document_by_id_query = container.application.get_document_by_id_query

    # Create query and execute
    query = GetDocumentByIdQuery(library_id=library_id, document_id=document_id)
    document = await get_document_by_id_query.execute(query)

    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found in library {library_id}",
        )

    return DocumentResponse(
        id=document.id,
        library_id=document.library_id,
        name=document.name,
        status=document.status,
        created_at=document.created_at if isinstance(document.created_at, str) else document.created_at.isoformat(),
        updated_at=document.updated_at if isinstance(document.updated_at, str) else document.updated_at.isoformat(),
        upload_complete=document.upload_complete,
        fragment_count=document.fragment_count,
        total_bytes=document.total_bytes,
        embeddings_count=document.embeddings_count,
        embeddings_by_config_id=document.embeddings_by_config_id,
        vectorization_statuses=[
            DocumentVectorizationStatusResponse(
                document_id=status.document_id,
                config_id=status.config_id,
                status=status.status,
                error_message=status.error_message,
                created_at=status.created_at if isinstance(status.created_at, str) else status.created_at.isoformat(),
                updated_at=status.updated_at if isinstance(status.updated_at, str) else status.updated_at.isoformat(),
            )
            for status in document.vectorization_statuses
        ],
        fragments=[
            DocumentFragmentResponse(
                id=frag.id,
                document_id=frag.document_id,
                sequence_number=frag.sequence_number,
                size_bytes=frag.size_bytes,
                content=frag.content,
                content_hash=frag.content_hash,
                is_final=frag.is_final,
                created_at=frag.created_at if isinstance(frag.created_at, str) else frag.created_at.isoformat(),
                updated_at=frag.updated_at if isinstance(frag.updated_at, str) else frag.updated_at.isoformat(),
            )
            for frag in document.fragments
        ],
    )


@router.delete("/{library_id}/documents/{document_id}", status_code=204, tags=["documents"])
async def delete_document(
    library_id: str = Path(..., description="Library ID"),
    document_id: str = Path(..., description="Document ID"),
    container: DIContainer = Depends(get_container),
) -> None:
    """Soft-delete a document by marking its status as DELETED.

    The document is not removed from the database but will be filtered out
    from all query results. This preserves data integrity and audit trail.

    Args:
        library_id: ID of the parent library
        document_id: ID of the document to delete
        container: DI container with commands

    Raises:
        HTTPException: 400 if library_id or document_id is not a valid UUID
        HTTPException: 404 if document not found
    """
    from vdb_core.application.commands import DeleteDocumentInput

    # Validate UUID formats
    validate_uuid(library_id, "library_id")
    validate_uuid(document_id, "document_id")

    # Get command from container
    command = container.application.delete_document_command

    # Execute command (raises DocumentNotFoundError if not found)
    input_data = DeleteDocumentInput(document_id=document_id)
    await command.execute(input_data)


@router.post("/{library_id}/documents", response_model=DocumentUploadResponse, status_code=201, tags=["documents"])
async def upload_document(
    library_id: str = Path(..., description="Library ID"),
    file: UploadFile = File(..., description="Document file to upload"),
    container: DIContainer = Depends(get_container),
) -> DocumentUploadResponse:
    """Upload a document to a library with streaming support.

    This endpoint streams the document in chunks, creating DocumentFragments
    as data arrives. Each fragment automatically triggers ParseDocumentWorkflow
    via event handlers for streaming document processing.

    Args:
        library_id: ID of the library to upload to
        file: Uploaded file from multipart/form-data
        container: DI container with commands

    Returns:
        DocumentUploadResponse with upload details

    Raises:
        HTTPException: 400 if library_id is not a valid UUID
    """
    from vdb_core.domain.value_objects import LibraryId

    # Validate UUID format
    validate_uuid(library_id, "library_id")

    # Verify library exists BEFORE uploading (raises LibraryNotFoundError if not found)
    uow = container.get_unit_of_work()
    async with uow:
        await uow.libraries.get(LibraryId(library_id))

    # Get command from container
    command = container.application.upload_document_command

    async def chunk_iterator() -> AsyncIterator[bytes]:
        """Stream file chunks from uploaded file."""
        chunk_size = 1024 * 1024  # 1MB chunks
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            yield chunk

    # Execute command with streaming chunks
    input_data = UploadDocumentInput(
        library_id=library_id,
        filename=file.filename or "untitled",
    )
    document_id = await command.execute(input_data, chunks=chunk_iterator())

    # Build response
    return DocumentUploadResponse(
        document_id=str(document_id),
        library_id=library_id,
        filename=file.filename or "untitled",
        fragments_received=0,  # Would need to track this in use case
        total_bytes=0,  # Would need to track this in use case
        upload_complete=True,
        message="Document uploaded successfully. Parse workflows triggered for each fragment.",
    )


@router.post("/{library_id}/queries", response_model=CreateQueryResponse, status_code=201, tags=["queries"])
async def create_query(
    library_id: str = Path(..., description="Library ID"),
    request: CreateQueryRequest = Body(...),
    container: DIContainer = Depends(get_container),
    temporal_client: Client = Depends(get_temporal_client),
) -> CreateQueryResponse:
    """Create an async query for semantic search using Temporal workflow.

    This endpoint creates a query and processes it asynchronously via Temporal:
    1. Writes query to DB with status PENDING
    2. Starts a SearchWorkflow with the query ID as workflow ID
    3. Returns the query_id immediately
    4. Workflow updates DB with results when complete

    Args:
        library_id: ID of the library to search
        request: Query request with query text, top_k, and config_id
        container: DI container with database access
        temporal_client: Temporal client for starting workflows

    Returns:
        CreateQueryResponse with query ID and status

    Raises:
        HTTPException: 400 if library_id or config_id is not a valid UUID
    """
    from vdb_core.infrastructure.workflows.search_workflow import (
        SearchWorkflow,
        SearchWorkflowInput,
    )

    # Validate UUID formats
    validate_uuid(library_id, "library_id")
    validate_uuid(request.config_id, "config_id")

    # Generate query ID
    query_id = str(uuid.uuid4())

    # Write query to database with status PENDING
    uow = container.get_unit_of_work()
    async with uow:
        # Use raw SQL for now (no domain model for queries yet)
        from sqlalchemy import text

        await uow.session.execute(
            text("""
                INSERT INTO queries (id, library_id, config_id, query_text, top_k, status, result_count)
                VALUES (:id, :library_id, :config_id, :query_text, :top_k, :status, :result_count)
            """),
            {
                "id": query_id,
                "library_id": library_id,
                "config_id": request.config_id,
                "query_text": request.query,
                "top_k": request.top_k,
                "status": "PENDING",
                "result_count": 0,
            }
        )
        await uow.commit()

    # Start Temporal SearchWorkflow
    workflow_input = SearchWorkflowInput(
        query_id=query_id,
        library_id=library_id,
        config_id=request.config_id,
        query_text=request.query,
        top_k=request.top_k,
        strategy="default",  # TODO: Load strategy from config
    )

    await temporal_client.start_workflow(
        SearchWorkflow.run,
        workflow_input,
        id=query_id,
        task_queue="vdb-search-tasks",  # Dedicated search worker queue
    )

    return CreateQueryResponse(
        query_id=query_id,
        library_id=library_id,
        status="PENDING",
        message="Query created and processing via Temporal workflow",
    )


@router.get("/{library_id}/queries", response_model=GetQueriesResponse, tags=["queries"])
async def get_queries(
    library_id: str = Path(..., description="Library ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
) -> GetQueriesResponse:
    """Get all queries for a library with pagination.

    Returns query history for the specified library, ordered by creation time (newest first).

    Args:
        library_id: ID of the library to get queries for
        limit: Maximum number of queries to return
        offset: Number of queries to skip

    Returns:
        GetQueriesResponse with paginated list of queries

    Note:
        TODO: Implement query history storage. Temporal workflows don't provide
        built-in "list by attribute" queries. Options:
        1. Store query metadata in PostgreSQL with workflow_id reference
        2. Use Temporal visibility API with custom search attributes
        3. Use Redis/cache for recent query history

        For now, returns empty list. Query individual queries via
        GET /libraries/{library_id}/queries/{query_id} using the query_id
        returned from POST /libraries/{library_id}/queries.
    """
    # Validate UUID format
    validate_uuid(library_id, "library_id")

    # TODO: Implement persistent query history
    return GetQueriesResponse(
        queries=[],
        total=0,
        limit=limit,
        offset=offset,
    )


@router.get("/{library_id}/queries/{query_id}", response_model=QueryResponse, tags=["queries"])
async def get_query(
    library_id: str = Path(..., description="Library ID"),
    query_id: str = Path(..., description="Query ID"),
    container: DIContainer = Depends(get_container),
) -> QueryResponse:
    """Get the status and results of an async query from database.

    Poll this endpoint to check if the query has completed and retrieve results.

    Query status values:
    - PENDING: Query created, workflow starting
    - PROCESSING: Workflow is being executed
    - COMPLETED: Workflow finished successfully, results available
    - FAILED: Workflow failed with an error

    Args:
        library_id: ID of the library (for validation)
        query_id: ID of the query
        container: DI container with database access

    Returns:
        QueryResponse with query status and results (if completed)

    Raises:
        HTTPException: 404 if query not found
    """
    # Validate UUID formats
    validate_uuid(library_id, "library_id")
    validate_uuid(query_id, "query_id")

    # Read query from database
    uow = container.get_unit_of_work()
    async with uow:
        from sqlalchemy import text

        result = await uow.session.execute(
            text("""
                SELECT id, library_id, query_text, status, results, result_count,
                       created_at, completed_at, error_message
                FROM queries
                WHERE id = :query_id AND library_id = :library_id
            """),
            {"query_id": query_id, "library_id": library_id}
        )
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail=f"Query {query_id} not found")

        # Extract query data
        status = row.status
        query_text = row.query_text
        results_json = row.results  # JSONB: [{"chunk_id": "...", "score": 0.95}, ...]
        result_count = row.result_count
        created_at = row.created_at.isoformat()
        completed_at = row.completed_at.isoformat() if row.completed_at else None

        # Hydrate results if COMPLETED
        results = None
        if status == "COMPLETED" and results_json:
            import json
            results_data = json.loads(results_json) if isinstance(results_json, str) else results_json

            # Extract chunk_ids for fetching
            chunk_ids = [r["chunk_id"] for r in results_data]

            # Fetch chunk data for hydration
            # Convert UUIDs to strings and use bindparam with expanding=True for IN clause
            from sqlalchemy import bindparam
            chunk_ids_str = [str(cid) for cid in chunk_ids]
            chunk_result = await uow.session.execute(
                text("""
                    SELECT c.id::text, c.document_id::text, c.content, c.sequence_number
                    FROM chunks c
                    WHERE c.id::text IN :chunk_ids
                """).bindparams(bindparam("chunk_ids", expanding=True)),
                {"chunk_ids": chunk_ids_str}
            )
            chunk_rows = chunk_result.fetchall()

            # Build mapping of chunk_id -> chunk data
            chunk_map = {r[0]: r for r in chunk_rows}

            # Hydrate results preserving order, scores, and positions
            results = []
            for result_data in results_data:
                chunk_id = result_data["chunk_id"]
                chunk = chunk_map.get(chunk_id)
                if chunk:
                    # chunk is tuple: (id, document_id, content, sequence_number)
                    results.append(
                        SearchResult(
                            chunk_id=chunk_id,
                            embedding_id=result_data.get("embedding_id", ""),
                            document_id=chunk[1],  # document_id
                            similarity_score=result_data["score"],
                            text=chunk[2],  # content
                            start_index=result_data.get("start_index", chunk[3] * 1000),  # sequence_number
                            end_index=result_data.get("end_index", (chunk[3] + 1) * 1000),
                        )
                    )

        return QueryResponse(
            query_id=query_id,
            library_id=library_id,
            query_text=query_text,
            status=status,
            results=results,
            total_results=result_count,
            created_at=created_at,
            completed_at=completed_at,
        )


@router.get("/{library_id}/chunks/{chunk_id}/context", response_model=ChunkWithContextResponse, tags=["documents"])
async def get_chunk_with_context(
    library_id: str = Path(..., description="Library ID"),
    chunk_id: str = Path(..., description="Chunk ID"),
    context_size: int = Query(2, ge=0, le=10, description="Number of chunks before/after to include"),
    container: DIContainer = Depends(get_container),
) -> ChunkWithContextResponse:
    """Get a chunk with surrounding context for viewing.

    Returns the requested chunk along with N chunks before and after it
    for contextual reading. Useful for expanding search results to see
    more of the document around a match.

    Args:
        library_id: ID of the library
        chunk_id: ID of the chunk to retrieve
        context_size: Number of chunks to include before and after (default: 2)
        container: DI container with query handlers

    Returns:
        ChunkWithContextResponse with chunk, surrounding chunks, and document metadata

    Raises:
        HTTPException: 404 if chunk or document not found
    """
    # For now, we need to find which document this chunk belongs to
    # In production, chunks should have a document_id field we can query
    # For this demo, we'll fetch chunks and find the match
    # TODO: Add proper chunk lookup by ID in query handlers

    raise HTTPException(
        status_code=501,
        detail="Chunk context endpoint not yet implemented - requires chunk repository",
    )


@router.post(
    "/{library_id}/configs",
    response_model=AddConfigToLibraryResponse,
    status_code=201,
    tags=["vectorization-configs"],
)
async def add_config_to_library(
    library_id: str = Path(..., description="Library ID"),
    request: AddConfigToLibraryRequest = Body(...),
    container: DIContainer = Depends(get_container),
) -> AddConfigToLibraryResponse:
    """Add a vectorization config to a library.

    Associates a global VectorizationConfig with a library. This triggers
    processing of all existing documents in the library with the new config.

    Following Cosmic Python pattern:
    - Calls AddConfigToLibraryCommand
    - Command raises LibraryConfigAdded event
    - Event handler creates DocumentVectorizationStatus entries and starts processing

    Args:
        library_id: ID of the library
        request: Request with config_id to add
        container: DI container with commands

    Returns:
        AddConfigToLibraryResponse confirming the association

    Raises:
        HTTPException: 400 if library_id or config_id is not a valid UUID
        HTTPException: 404 if library or config not found
        HTTPException: 409 if config already associated with library
    """
    from vdb_core.application.commands import AddConfigToLibraryInput

    # Validate UUID formats
    validate_uuid(library_id, "library_id")
    validate_uuid(request.config_id, "config_id")

    # Get command from container
    command = container.application.add_config_to_library_command

    # Execute command (raises LibraryConfigAdded event as side effect)
    input_data = AddConfigToLibraryInput(library_id=library_id, config_id=request.config_id)
    await command.execute(input_data)

    return AddConfigToLibraryResponse(
        library_id=library_id,
        config_id=request.config_id,
        message="Config added to library successfully. Document processing will begin.",
    )


@router.delete(
    "/{library_id}/configs/{config_id}",
    status_code=204,
    tags=["vectorization-configs"],
)
async def remove_config_from_library(
    library_id: str = Path(..., description="Library ID"),
    config_id: str = Path(..., description="Config ID"),
    container: DIContainer = Depends(get_container),
) -> None:
    """Remove a vectorization config from a library.

    Disassociates a VectorizationConfig from a library. Does NOT delete the
    config itself (configs are global). Stops processing with this config.

    Following Cosmic Python pattern:
    - Calls RemoveConfigFromLibraryCommand
    - Command raises LibraryConfigRemoved event
    - Event handler may clean up DocumentVectorizationStatus entries

    Args:
        library_id: ID of the library
        config_id: ID of the config to remove
        container: DI container with commands

    Raises:
        HTTPException: 400 if library_id or config_id is not a valid UUID
        HTTPException: 404 if library not found or config not associated with library
    """
    from vdb_core.application.commands import RemoveConfigFromLibraryInput

    # Validate UUID formats
    validate_uuid(library_id, "library_id")
    validate_uuid(config_id, "config_id")

    # Get command from container
    command = container.application.remove_config_from_library_command

    # Execute command (raises LibraryConfigRemoved event as side effect)
    input_data = RemoveConfigFromLibraryInput(library_id=library_id, config_id=config_id)
    await command.execute(input_data)


@router.get(
    "/{library_id}/configs",
    response_model=GetLibraryConfigsResponse,
    tags=["vectorization-configs"],
)
async def get_library_configs(
    library_id: str = Path(..., description="Library ID"),
    container: DIContainer = Depends(get_container),
) -> GetLibraryConfigsResponse:
    """Get all vectorization configs associated with a library.

    Returns the list of VectorizationConfigs that are currently associated
    with this library. Documents in the library are processed with all these configs.

    Following CQRS pattern:
    - Uses query handler (read side)
    - Returns read models from query repository

    Args:
        library_id: ID of the library
        container: DI container with query handlers

    Returns:
        GetLibraryConfigsResponse with list of configs

    Raises:
        HTTPException: 400 if library_id is not a valid UUID
        HTTPException: 404 if library not found
    """
    # Validate UUID format
    validate_uuid(library_id, "library_id")

    from vdb_core.domain.value_objects import LibraryId

    uow = container.get_unit_of_work()
    async with uow:
        library = await uow.libraries.get(LibraryId(library_id))

        if not library:
            raise HTTPException(status_code=404, detail=f"Library {library_id} not found")

        # Map library.configs (tuple of VectorizationConfig entities) to response schemas
        configs = [
            VectorizationConfigResponse(
                id=str(config.id),
                version=config.version,
                status=str(config.status),
                description=config.description,
                previous_version_id=str(config.previous_version_id) if config.previous_version_id else None,
                chunking_strategy_ids=[str(sid) for sid in config.chunking_strategy_ids],
                embedding_strategy_ids=[str(sid) for sid in config.embedding_strategy_ids],
                vector_indexing_strategy=str(config.vector_indexing_strategy),
                vector_similarity_metric=str(config.vector_similarity_metric),
            )
            for config in library.configs
        ]

        return GetLibraryConfigsResponse(
            library_id=library_id,
            configs=configs,
            total=len(configs),
        )


# Global events endpoint (no library filtering)
@events_router.get("/events", response_model=GetEventLogsResponse)
async def get_all_events(
    event_type: str | None = Query(None, description="Filter by event type (e.g., DocumentCreated)"),
    aggregate_type: str | None = Query(None, description="Filter by aggregate type (e.g., Document, Chunk)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    container: DIContainer = Depends(get_container),
) -> GetEventLogsResponse:
    """Get event logs across all libraries with optional filtering.

    Returns event history for all libraries, ordered by occurred_at descending.
    Events represent domain actions like DocumentCreated, ChunkProcessed, etc.

    Following CQRS pattern:
    - Uses query handler (read side)
    - Returns read models via event log query repository
    - Supports filtering by event_type and aggregate_type

    Args:
        event_type: Optional filter by event type (e.g., "DocumentCreated")
        aggregate_type: Optional filter by aggregate type (e.g., "Document")
        limit: Maximum number of events to return
        offset: Number of events to skip
        container: DI container with query handlers

    Returns:
        GetEventLogsResponse with paginated list of events

    Example:
        GET /events?event_type=DocumentCreated&limit=50
    """
    # Get query handler from container
    get_event_logs_query = container.application.get_event_logs_query

    # Create query to get all events (no library filtering)
    query = GetEventLogsQuery(
        event_type=event_type,
        aggregate_type=aggregate_type,
        limit=limit,
        offset=offset,
    )
    events = await get_event_logs_query.execute(query)

    # Build response
    event_responses = [
        EventLogResponse(
            id=event.id,
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            payload=event.payload,
            occurred_at=event.occurred_at.isoformat(),
            created_at=event.created_at.isoformat(),
        )
        for event in events
    ]

    # Get total count for pagination
    total = len(events) + offset if len(events) == limit else offset + len(events)

    return GetEventLogsResponse(
        events=event_responses,
        total=total,
        limit=limit,
        offset=offset,
    )


@configs_router.get(
    "/vectorization-configs",
    response_model=GetVectorizationConfigsResponse,
    tags=["vectorization-configs"],
)
async def get_vectorization_configs(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of configs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    container: DIContainer = Depends(get_container),
) -> GetVectorizationConfigsResponse:
    """Get all global vectorization configs.

    Lists all vectorization configs in the system. These are global entities
    that can be associated with multiple libraries.

    Following CQRS pattern:
    - Uses read repository provider (read side)
    - Returns read models (DTOs)

    Args:
        limit: Maximum number of configs to return
        offset: Offset for pagination
        container: DI container with read repository provider

    Returns:
        GetVectorizationConfigsResponse with list of configs

    """
    # Get read repository provider for CQRS queries
    provider = container.get_read_repository_provider()

    # Query configs using read repository (enter context to initialize repos)
    async with provider:
        config_read_models = await provider.vectorization_configs.get_all(
            limit=limit, offset=offset, statuses=None  # Don't filter by status
        )
        # Get total count while still in context
        total = await provider.vectorization_configs.count(statuses=None)

    # Map read models to response schemas
    configs = [
        VectorizationConfigResponse(
            id=config.id,
            version=config.version,
            status=config.status,
            description=config.description,
            previous_version_id=config.previous_version_id,
            chunking_strategy_ids=config.chunking_strategy_ids,
            embedding_strategy_ids=config.embedding_strategy_ids,
            vector_indexing_strategy=config.vector_indexing_strategy,
            vector_similarity_metric=config.vector_similarity_metric,
        )
        for config in config_read_models
    ]

    return GetVectorizationConfigsResponse(
        configs=configs,
        total=total,
        limit=limit,
        offset=offset,
    )
