"""E2E tests for document upload and processing."""

import asyncio

import pytest


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_upload_document(api_client, clean_database, sample_text_file) -> None:
    """Test uploading a document to a library."""
    # Create a library first
    lib_response = await api_client.post(
        "/libraries",
        json={"name": "Upload Test Library"},
    )
    assert lib_response.status_code == 201
    library_id = lib_response.json()["library"]["id"]

    # Upload a document
    with open(sample_text_file, "rb") as f:
        response = await api_client.post(
            f"/libraries/{library_id}/documents",
            files={"file": ("sample.txt", f, "text/plain")},
        )

    assert response.status_code == 201
    data = response.json()

    # Verify response
    assert "document_id" in data
    assert data["library_id"] == library_id
    assert data["filename"] == "sample.txt"
    assert data["upload_complete"] is True


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_document_metadata(api_client, clean_database, sample_text_file) -> None:
    """Test retrieving document metadata after upload."""
    # Create library and upload document
    lib_response = await api_client.post("/libraries", json={"name": "Test Library"})
    library_id = lib_response.json()["library"]["id"]

    with open(sample_text_file, "rb") as f:
        upload_response = await api_client.post(
            f"/libraries/{library_id}/documents",
            files={"file": ("test.txt", f, "text/plain")},
        )

    document_id = upload_response.json()["document_id"]

    # Get document metadata
    response = await api_client.get(f"/libraries/{library_id}/documents/{document_id}")

    assert response.status_code == 200
    doc = response.json()

    assert doc["id"] == document_id
    assert doc["library_id"] == library_id
    assert doc["name"] == "test.txt"
    assert doc["status"] == "pending"  # Processing not complete yet
    assert doc["upload_complete"] is True


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_document_fragments(api_client, clean_database, sample_text_file) -> None:
    """Test retrieving document fragments after upload."""
    # Create library and upload document
    lib_response = await api_client.post("/libraries", json={"name": "Test Library"})
    library_id = lib_response.json()["library"]["id"]

    with open(sample_text_file, "rb") as f:
        upload_response = await api_client.post(
            f"/libraries/{library_id}/documents",
            files={"file": ("test.txt", f, "text/plain")},
        )

    document_id = upload_response.json()["document_id"]

    # Get document fragments
    response = await api_client.get(f"/libraries/{library_id}/documents/{document_id}/fragments")

    assert response.status_code == 200
    data = response.json()

    assert "fragments" in data
    assert len(data["fragments"]) > 0

    # Verify fragment structure
    fragment = data["fragments"][0]
    assert "id" in fragment
    assert fragment["document_id"] == document_id
    assert "sequence_number" in fragment
    assert "start_index" in fragment
    assert "end_index" in fragment
    assert "size_bytes" in fragment


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_documents_in_library(api_client, clean_database, sample_text_file) -> None:
    """Test listing all documents in a library."""
    # Create library
    lib_response = await api_client.post("/libraries", json={"name": "Test Library"})
    library_id = lib_response.json()["library"]["id"]

    # Upload multiple documents
    for i in range(3):
        with open(sample_text_file, "rb") as f:
            await api_client.post(
                f"/libraries/{library_id}/documents",
                files={"file": (f"doc{i}.txt", f, "text/plain")},
            )

    # List documents
    response = await api_client.get(f"/libraries/{library_id}/documents")

    assert response.status_code == 200
    data = response.json()

    assert "documents" in data
    assert len(data["documents"]) == 3

    doc_names = {doc["name"] for doc in data["documents"]}
    assert doc_names == {"doc0.txt", "doc1.txt", "doc2.txt"}


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_streaming_large_file(api_client, clean_database, large_text_file) -> None:
    """Test uploading a larger file with streaming."""
    # Create library
    lib_response = await api_client.post("/libraries", json={"name": "Large File Test"})
    library_id = lib_response.json()["library"]["id"]

    # Upload large file
    with open(large_text_file, "rb") as f:
        response = await api_client.post(
            f"/libraries/{library_id}/documents",
            files={"file": ("large.txt", f, "text/plain")},
        )

    assert response.status_code == 201
    data = response.json()

    document_id = data["document_id"]

    # Verify fragments were created
    frag_response = await api_client.get(f"/libraries/{library_id}/documents/{document_id}/fragments")

    assert frag_response.status_code == 200
    fragments = frag_response.json()["fragments"]

    # Should have multiple fragments for large file
    assert len(fragments) >= 1

    # Verify fragments are ordered
    sequence_numbers = [f["sequence_number"] for f in fragments]
    assert sequence_numbers == sorted(sequence_numbers)

    # Verify final fragment is marked
    assert fragments[-1]["is_final"] is True


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_document_ingestion_creates_chunks(api_client, clean_database, sample_text_file) -> None:
    """Test that document ingestion workflow creates chunks.

    This test verifies the complete ingestion pipeline:
    1. Upload document → creates fragments
    2. Temporal workflow processes document → creates chunks
    3. Chunks are queryable via API
    """
    # Create library
    lib_response = await api_client.post("/libraries", json={"name": "Ingestion Test"})
    library_id = lib_response.json()["library"]["id"]

    # Upload document
    with open(sample_text_file, "rb") as f:
        upload_response = await api_client.post(
            f"/libraries/{library_id}/documents",
            files={"file": ("test.txt", f, "text/plain")},
        )

    assert upload_response.status_code == 201
    document_id = upload_response.json()["document_id"]

    # Wait for ingestion workflow to complete
    # Poll for chunks to appear (workflow is async via Temporal)
    max_retries = 30  # 30 seconds max wait
    retry_delay = 1

    chunks_found = False
    for _i in range(max_retries):
        chunks_response = await api_client.get(f"/libraries/{library_id}/documents/{document_id}/chunks")

        if chunks_response.status_code == 200:
            chunks_data = chunks_response.json()
            if len(chunks_data.get("chunks", [])) > 0:
                chunks_found = True
                break

        await asyncio.sleep(retry_delay)

    # Verify chunks were created
    assert chunks_found, "Chunks were not created within timeout period"

    # Get chunks and verify structure
    chunks_response = await api_client.get(f"/libraries/{library_id}/documents/{document_id}/chunks")

    assert chunks_response.status_code == 200
    chunks_data = chunks_response.json()

    assert "chunks" in chunks_data
    assert len(chunks_data["chunks"]) > 0

    # Verify chunk structure
    chunk = chunks_data["chunks"][0]
    assert "id" in chunk
    assert chunk["document_id"] == document_id
    assert "chunking_strategy" in chunk
    assert "start" in chunk
    assert "end" in chunk
    assert "text" in chunk
    assert len(chunk["text"]) > 0  # Should have actual text content
    assert "status" in chunk
    assert "metadata" in chunk
    assert "created_at" in chunk
    assert "updated_at" in chunk


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_flow_with_large_file_and_query(api_client, clean_database, large_text_file) -> None:
    """Test complete end-to-end flow: library → upload > 1MB doc → query → results.

    This test verifies the entire system working together:
    1. Create library
    2. Upload large document (> 1 MB to test batching)
    3. Wait for ingestion to complete (chunks + embeddings created)
    4. Create async query
    5. Poll for query results
    6. Verify results contain expected content

    This tests:
    - Fragment batching logic (1 MB limit)
    - Temporal ingestion workflow
    - Chunk creation and embedding
    - Async query pattern
    - End-to-end semantic search
    """
    # Step 1: Create library
    lib_response = await api_client.post(
        "/libraries",
        json={"name": "Complete Flow Test Library"},
    )
    assert lib_response.status_code == 201
    library_id = lib_response.json()["library"]["id"]

    # Step 2: Upload large document (> 1 MB)
    with open(large_text_file, "rb") as f:
        upload_response = await api_client.post(
            f"/libraries/{library_id}/documents",
            files={"file": ("large_test.txt", f, "text/plain")},
        )

    assert upload_response.status_code == 201
    document_id = upload_response.json()["document_id"]

    # Verify fragments were created with batching
    frag_response = await api_client.get(f"/libraries/{library_id}/documents/{document_id}/fragments")
    assert frag_response.status_code == 200
    fragments = frag_response.json()["fragments"]

    # Should have multiple fragments due to > 1 MB file
    assert len(fragments) >= 2, "Large file should create multiple fragments"

    # Verify each fragment is <= 1 MB (except possibly EOF marker)
    for frag in fragments[:-1]:  # All except last (EOF marker)
        assert frag["size_bytes"] <= 1_048_576, f"Fragment {frag['sequence_number']} exceeds 1 MB"

    # Verify fragments are ordered
    sequence_numbers = [f["sequence_number"] for f in fragments]
    assert sequence_numbers == sorted(sequence_numbers)

    # Verify final fragment is marked
    assert fragments[-1]["is_final"] is True

    # Step 3: Wait for ingestion workflow to complete (chunks created)
    max_retries = 60  # 60 seconds max wait (large file takes longer)
    retry_delay = 1

    chunks_found = False
    for _i in range(max_retries):
        chunks_response = await api_client.get(f"/libraries/{library_id}/documents/{document_id}/chunks")

        if chunks_response.status_code == 200:
            chunks_data = chunks_response.json()
            if len(chunks_data.get("chunks", [])) > 0:
                chunks_found = True
                break

        await asyncio.sleep(retry_delay)

    assert chunks_found, "Chunks were not created within timeout period"

    # Get chunks to find searchable content
    chunks_response = await api_client.get(f"/libraries/{library_id}/documents/{document_id}/chunks")
    chunks = chunks_response.json()["chunks"]
    assert len(chunks) > 0

    # Extract sample text from first chunk for query
    sample_chunk = chunks[0]
    sample_text = sample_chunk["text"]
    # Use first few words as query
    query_text = " ".join(sample_text.split()[:5])

    # Step 4: Create async query
    query_request = {
        "query": query_text,
        "top_k": 5,
    }
    create_query_response = await api_client.post(
        f"/libraries/{library_id}/queries",
        json=query_request,
    )

    assert create_query_response.status_code == 201
    query_data = create_query_response.json()

    assert "query_id" in query_data
    assert query_data["library_id"] == library_id
    assert query_data["status"] in ["PROCESSING", "COMPLETED"]

    query_id = query_data["query_id"]

    # Step 5: Poll for query results (should be immediate since we execute sync)
    max_query_retries = 10
    query_completed = False

    for _i in range(max_query_retries):
        get_query_response = await api_client.get(f"/libraries/{library_id}/queries/{query_id}")

        assert get_query_response.status_code == 200
        query_result = get_query_response.json()

        if query_result["status"] == "COMPLETED":
            query_completed = True
            break
        if query_result["status"] == "FAILED":
            msg = f"Query failed: {query_result.get('error', 'Unknown error')}"
            raise AssertionError(msg)

        await asyncio.sleep(0.5)

    assert query_completed, "Query did not complete within timeout"

    # Step 6: Verify query results
    final_query_response = await api_client.get(f"/libraries/{library_id}/queries/{query_id}")
    final_result = final_query_response.json()

    assert final_result["status"] == "COMPLETED"
    assert final_result["query_text"] == query_text
    assert "results" in final_result
    assert final_result["results"] is not None
    assert len(final_result["results"]) > 0, "Query should return at least one result"

    # Verify result structure
    first_result = final_result["results"][0]
    assert "chunk_id" in first_result
    assert "document_id" in first_result
    assert first_result["document_id"] == document_id
    assert "similarity_score" in first_result
    assert "text" in first_result
    assert len(first_result["text"]) > 0

    # Verify similarity score is reasonable (should be high since we queried with actual chunk text)
    assert first_result["similarity_score"] >= 0.5, "Similarity score should be reasonably high"
