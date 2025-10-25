# Repo Objective
---

This is a take-home project with the following objectives.
Described in more detail [here](https://stack-ai.notion.site/Take-at-Home-Task-Backend-Vector-DB-bff06d35e031498fb6469875a40adeea).

## 🎯 Objective
Build a **containerized REST API** that enables users to **index**, **store**, and **query** documents via **vector embeddings** — supporting fast, similarity-based search across text data.

---

## 🧩 Core Concepts
- **Chunk** – piece of text + embedding + metadata
- **Document** – collection of chunks + metadata
- **Library** – collection of documents + metadata

---

## ✅ Requirements

### CRUD & Indexing
- Create, read, update, delete **libraries**
- Create, read, update, delete **documents/chunks** within a library
- Index a library’s contents
- Perform **k-Nearest Neighbor (kNN)** vector search within a library

### Implementation Details
- Language: **Python**
- Framework: **FastAPI**
- Models: **Pydantic**
- Containerization: **Docker**

---

## 🧠 Development Steps

1. **Modeling**
   - Implement `Chunk`, `Document`, and `Library` classes using Pydantic.
   - Use fixed schemas for metadata (optional: dynamic schemas per library).

2. **Indexing Algorithms**
   - Implement 2–3 vector indexing algorithms **without external libraries** (e.g., KD-Tree, Ball Tree, brute force).
   - Document time/space complexity and design choices.

3. **Concurrency Control**
   - Ensure thread-safe reads/writes (locking, synchronization, etc.).
   - Explain design decisions.

4. **CRUD Logic**
   - Implement business logic via **Service** layer decoupled from API endpoints.

5. **API Layer**
   - Expose RESTful endpoints for all operations.

6. **Containerization**
   - Package with Docker (`Dockerfile`, ready to run locally).

---

## 💡 Bonus (Extra Points)

| Feature | Description |
|----------|-------------|
| **Metadata Filtering** | Enable filtering by metadata (e.g., creation date, keyword). |
| **Persistence** | Save DB state to disk; resume after container restart. |
| **Leader–Follower Architecture** | Support replication, failover, and high availability in K8s. |
| **Python SDK Client** | Provide a client library to interact with the API. |
| **Temporal Integration** | Use Temporal Workflows for **durable execution** of queries — including Workflow/Activity separation, signals, and async handling. |

---

## 🚫 Constraints
- ❌ No external vector DB libs (e.g., FAISS, Chroma, Pinecone).
- ✅ You may use **NumPy** for math operations.
- 🚫 No OCR or chunk extraction pipeline required — mock manual chunks are fine.

---

## 🧰 Tech Stack
- **Backend:** Python + FastAPI + Pydantic
- **Container:** Docker
- **Testing:** Pytest (recommended)
- **Embeddings:** [Cohere API](https://cohere.com/embeddings)

## 🧾 Evaluation Criteria

### Code Quality
- SOLID principles
- Static typing
- Clean RESTful design
- Pydantic validation
- Modularity & separation of concerns (API → Service → Repository)
- Pythonic idioms (early returns, composition over inheritance)
- Clear error handling
- Containerized & testable

### Functionality
- Full CRUD support
- Correct and efficient indexing/searching
- Thread-safe data handling
- Runs in Docker and behaves as expected
