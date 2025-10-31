# Pierre @ Take-at-Home Task - Backend (Vector DB)
---

## Table of Contents

| Section    | Link                         |
|------------|------------------------------|
| Objective  | [README.OBJECTIVE.md](README.OBJECTIVE.md) |

Architectural design decisions are based heavily on: https://www.cosmicpython.com/book/appendix_ds1_table.html

| Layer / Area                | Component                       | Description                                                                                                                                                  |
|-----------------------------|----------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Domain                      |                                  | Defines the business logic.                                                                                                                                  |
|                             | Entity                           | A domain object whose attributes may change but that has a recognizable identity over time.                                                                  |
|                             | Value object                     | An immutable domain object whose attributes entirely define it. It is fungible with other identical objects.                                                 |
|                             | Aggregate                        | Cluster of associated objects that we treat as a unit for the purpose of data changes. Defines and enforces a consistency boundary.                         |
|                             | Event                            | Represents something that happened.                                                                                                                          |
|                             | Command                          | Represents a job the system should perform.                                                                                                                  |
| Service Layer               |                                  | Defines the jobs the system should perform and orchestrates different components.                                                                            |
|                             | Handler                          | Receives a command or an event and performs what needs to happen.                                                                                            |
|                             | Unit of work                     | Abstraction around data integrity. Each unit of work represents an atomic update. Makes repositories available. Tracks new events on retrieved aggregates.   |
|                             | Message bus (internal)           | Handles commands and events by routing them to the appropriate handler.                                                                                      |
| Adapters (Secondary)        |                                  | Concrete implementations of an interface that goes from our system to the outside world (I/O).                                                              |
|                             | Repository                       | Abstraction around persistent storage. Each aggregate has its own repository.                                                                                |
|                             | Event publisher                  | Pushes events onto the external message bus.                                                                                                                 |
| Entrypoints (Primary Adapters) |                              | Translate external inputs into calls into the service layer.                                                                                                 |
|                             | Web                              | Receives web requests and translates them into commands, passing them to the internal message bus.                                                           |
|                             | Event consumer                   | Reads events from the external message bus and translates them into commands, passing them to the internal message bus.                                      |
| N/A                         | External message bus (message broker) | A piece of infrastructure that different services use to intercommunicate, via events.                                                                |
