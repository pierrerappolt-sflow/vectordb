#!/usr/bin/env python3
"""Quick test script to verify Cohere embeddings are working correctly."""

import asyncio
import os

import cohere
import numpy as np


async def test_embeddings():
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        print("ERROR: COHERE_API_KEY environment variable not set")
        return

    co = cohere.AsyncClient(api_key=api_key)

    bicycle_doc = """
    A bicycle, also called a pedal cycle, bike, push-bike or cycle, is a human-powered or
    motor-assisted, pedal-driven, single-track vehicle, with two wheels attached to a frame,
    one behind the other. A bicycle rider is called a cyclist, or bicyclist.

    Bicycles were introduced in the 19th century in Europe. By the early 21st century,
    more than 1 billion were in existence. These numbers far exceed the number of cars,
    both in total and ranked by the number of individual models produced.
    """

    query = "Bicycle"

    unrelated_doc = """
    Python is a high-level, general-purpose programming language. Its design philosophy
    emphasizes code readability with the use of significant indentation. Python is
    dynamically typed and garbage-collected.
    """

    query_response = await co.embed(
        texts=[query],
        model="embed-english-v3.0",
        input_type="search_query",
        embedding_types=["float"],
    )
    query_embedding = np.array(query_response.embeddings.float_[0])

    doc_response = await co.embed(
        texts=[bicycle_doc, unrelated_doc],
        model="embed-english-v3.0",
        input_type="search_document",
        embedding_types=["float"],
    )
    bicycle_embedding = np.array(doc_response.embeddings.float_[0])
    unrelated_embedding = np.array(doc_response.embeddings.float_[1])

    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    bicycle_similarity = cosine_similarity(query_embedding, bicycle_embedding)
    unrelated_similarity = cosine_similarity(query_embedding, unrelated_embedding)

    if bicycle_similarity > 0.5 and bicycle_similarity > unrelated_similarity:
        print("✅ PASS: Embeddings are working correctly!")
        print(f"   - Bicycle doc is more similar ({bicycle_similarity:.4f}) than unrelated doc ({unrelated_similarity:.4f})")
    else:
        print("❌ FAIL: Embeddings seem incorrect!")
        print(f"   - Expected bicycle_similarity > 0.5 and > unrelated_similarity")
        print(f"   - Got bicycle={bicycle_similarity:.4f}, unrelated={unrelated_similarity:.4f}")

    bicycle_l2 = np.linalg.norm(query_embedding - bicycle_embedding)
    unrelated_l2 = np.linalg.norm(query_embedding - unrelated_embedding)

    if bicycle_l2 < unrelated_l2:
        print("✅ PASS: L2 distances are correct!")
    else:
        print("❌ FAIL: L2 distances seem incorrect!")

    query_norm = np.linalg.norm(query_embedding)
    bicycle_norm = np.linalg.norm(bicycle_embedding)
    unrelated_norm = np.linalg.norm(unrelated_embedding)

    if 0.99 < query_norm < 1.01 and 0.99 < bicycle_norm < 1.01:
        print("✅ Embeddings are normalized (unit vectors)")
    else:
        print("⚠️  Embeddings are NOT normalized")

    await co.close()


if __name__ == "__main__":
    asyncio.run(test_embeddings())
