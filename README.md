Vector DB
---

## 📋 What Was Built

### Architecture Highlights
- **Modeling**:

  A. ER Model

  I thought of this task as having 2 Aggregate Roots, Library and VectorConfig:

  - Library -> Documents -> Internal sub-doc VO's before seeing a VectorConfig
    - Internal "sub-docs" include DocumentFragment, and ExtractedContent which is a Modality-specific element from a Document. My idea here was
      1) DocumentFragments should be dump and just
         drop memory-limited portions of bytes of an uploaded Document.
      2) To allow for ingestion of a Document with predictable memory usage; and
      3) Create ExtractedContent objects tied to a Modality for Modality-specific chunking strategies. e.g. Images as b64, Text as str.

  - VectorConfig describes how to make Documents searchable
    - It contains some Chunking, Embedding, Indexing, and Similarity Strategies.

  - The combination of these two acting upon some ExtractedContent,
  generates a Chunk -> Embedding -> Index -> Search-function.

  These two are loosely coupled via an associative table.
  Writes to add a Config to a Library are performed via the Library Entity/Repo,
  but could easily be reversed.
  I created LazyLoaders on Libraries child entities and VO's so that
  we could enforce some invariants without loading an entire Library in memory.

  B. Unit of Work / CQRS

  Only my 2 Aggregate Roots have Writable Repositories.
  The Unit of Work is responsible for executing a Command and to
  interact with these 2 Repos to execute the Command. The Command only contains business logic.
  The UoW:
   1. Prepares all DB writes
   2. Collects any Domain Events
   3. On command finish, attempts to write to DB
   4. On fail, rollback all changes
   5. On success, emit Domain Events

  For Read operations, ReadRepos and ReadModels are used instead.
  These are simple and fast DB reads that do not need to enforce domain invariants,
  nor emit events. e.g. What does Doc Id 1 look like, without loading the Library

  In production, I would have separated Read/Write servers, and ofc pointed
  the Read servers at our DB replicas only.


- **Event Handling**:

  From the previous section, I have UoW handle Command's which handle the business
  logic to modify our domain entities, our entities emit domain events,
  which I publish to a queue for dispatch.

  In this code I just used RabbitMQ without much thought, and created 2 separate queues,
  1) to gather all events and simply write them to an event log;
  2) to capture events which require async work, like DocumentCreated, etc.

  This work is dispatched to Temporal workflows for specific events.
  Ideally, I think I would have doen a better job wrapping Temporal around UoW-Command execution.
  Temporal is roughly just an internal executor of Commands, where FastAPI is our external one.
  Another mistake I made was not batch requesting embeddings in my Ingestion workflow,
  I think for future work, I would have created some service mesh, or dedicated server
  to batch multiple embedding requests happening in some time window, but occurring in parallel
  Document processing workflows.

  I created 2 worker servers, 1 to handle the ingestion workflow, and 1 to handle the search workflow.

- **Search Service**:

  I created an internal search server to be where our Embedding Indexing & Searching is handled.
  We create a Search Index, for each Library-Vector Config pair.

  I did not put too much though into this other than this should quickly get put somewhere
  other than the external API server so that we can scale it later without changing the
  API <-> Search API interface.

## 📋 What Was NOT Built

- As I rushed to finish this in time, I left behind a lot of ugly code, poor typing, and bugs.
  e.g. a Library can be soft deleted and then an async job
  can run an operation to INSERT INTO instead of UPDATE
  the necessary fields; marking the Library as ACTIVE again,
  and many other similar things...
- I think what's critically missing is tracking the ordering of Embedding events
  so that the Index remains in-sync with the DB and does not handle out of order events, i.e.,
  implementing a monotonically increasing event sequence or offset for each event,
  and persisting/checking the last processed sequence for the index, so late/out-of-order
  events can be ignored or explicitly flagged. This way, we ensure the search index always
  reflects the true, consistent state of the database.
  Also the status of an Index is sloppy, when is it ready for search,
  which documents has it indexed etc.
- The UI is entirely vibe coded, I did not think about design
  decisions there at all.
- My goal was mostly to draw an overall outline of how I would achieve this system design,
  and ignore the minor details.

---

### Key Technical Choices

**Structure**:
```
packages/core/
├── domain/              # No dependencies (other than Pydantic-like things)
│   ├── entities/        # Library, Document
│   ├── value_objects/   # IDs, names, embeddings
│   ├── repositories/    # Abstract interfaces
│   │   exceptions/      # Domain exceptions
│   └── events/          # Domain events
├── application/         # Use cases, orchestration
│   ├── commands/        # CreateLibrary, UploadDocument
│   └── queries/         # GetLibrary, SearchVectors
└── infrastructure/      # Implementation details
    ├── persistence/     # PostgreSQL, in-memory
    ├── api/             # FastAPI routes
    └── workflows/       # Temporal workflows
```

## 🚀 Running Locally

### Prerequisites
- Docker Desktop (or Docker Engine + Docker Compose)

### Quick Start
1. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your Cohere API key
```

2. **Start all services**
```bash
docker compose up -d
```

This starts:
- **API** (port 8000): REST API
- **Worker** (2 instances): Temporal workers for document processing
- **Search Service** (port 8001): Vector search service
- **PostgreSQL** (port 5432): Database
- **RabbitMQ** (ports 5672, 15672): Message bus
- **Temporal** (port 7233, 8233): Workflow engine
- **Temporal UI** (port 8080): Workflow dashboard
