# ProposalPilot AI: Backend Architectural Guide

This guide provides a comprehensive overview of the design patterns, layer roles, request lifecycle, agent node states, and production readiness of the ProposalPilot AI backend.

---

## 1. Visual Architecture Diagram
Below is the end-to-end request-response lifecycle and LangGraph agent workflow:

```text
+-------------------------------------------------------+
|                    Client / UI                        |
+---------------------------+---------------------------+
                            |
                            | HTTP POST /api/proposals (ProposalRequest payload)
                            v
+-------------------------------------------------------+
|            FastAPI Router & Validation Layer          |
+---------------------------+---------------------------+
                            |
                            | - Parses JSON & Maps Enums (schemas/request.py)
                            | - Trims Whitespace & Sanitizes Inputs
                            v
+-------------------------------------------------------+
|             Proposal Service Orchestrator             |
+---------------------------+---------------------------+
                            |
                            | - Initializes AgentState (agents/state.py)
                            | - Sets status = "init", starts stopwatch
                            v
+-------------------------------------------------------+
|              LangGraph Workflow Engine                |
+---------------------------+---------------------------+
                            |
                            v [Node 1]
+-------------------------------------------------------+
|                    Planner Node                       |
| - build_planner_prompt() (llm/prompt_builder.py)       |
| - PLANNER_SYSTEM_PROMPT (llm/prompts.py)              |
| - GroqLLMService.generate_json()                      |
+---------------------------+---------------------------+
                            | Updates execution_plan list (Deduplicated)
                            v [Node 2 Loop]
+-------------------------------------------------------+
|                    Executor Node                      |
| - build_executor_prompt() (llm/prompt_builder.py)     |
| - EXECUTOR_SYSTEM_PROMPT (llm/prompts.py)             |
| - GroqLLMService.generate_text() (with retry loop)    |
| - Section Validation (min length & duplicate checks)  |
+---------------------------+---------------------------+
                            | Repeat until all tasks marked completed
                            v
+-------------------------------------------------------+
|             Reflection / DOCX Export Node             |
+-------------------------------------------------------+
                            |
                            v
+-------------------------------------------------------+
|                     File System                       |
|         Stores generated proposals (.docx)            |
+-------------------------------------------------------+
```

> [!NOTE]
> All logs during this lifecycle are captured and formatted by a centralized Loguru logger (`core/logger.py`), tracking execution metrics, token counts, and API latencies.

---

## 2. Deep Dive: Module Explanations

### Module 1: `backend/app/core/config.py`
- **Purpose**: Centralizes the loading, parsing, and validation of all environment configurations.
- **Responsibilities**: Resolves relative paths, loads workspace `.env` values, converts data types, and exposes a validated settings singleton.
- **Why it exists**: Prevents dispersed, unvalidated calls to `os.getenv` or `os.environ` from polluting the business logic.
- **How it interacts with other modules**: Exposes the `settings` instance imported by loggers, API routers, and LLM services.
- **Real-world industry usage**: Protects secrets from being committed to version control. Uses strict type checks to ensure the application crashes immediately upon deployment if environment keys (e.g., `GROQ_API_KEY`) are missing or incorrectly typed.
- **Interview explanation**: *“This file acts as our application's configuration manager. It reads parameters from the environment and maps them to a strongly typed Pydantic Settings class. If a parameter is missing or has the wrong type, the app crashes immediately during startup rather than failing unpredictably at runtime.”*
- **Best practices followed**: Default values, path resolution logic, boundaries validation, and strict Pydantic model validation.
- **Future scalability considerations**: Can be adapted to retrieve secrets from cloud providers (e.g., AWS Secrets Manager or Vault) without altering downstream class references.

---

### Module 2: `backend/app/core/logger.py`
- **Purpose**: Configures the centralized logging pipeline using Loguru.
- **Responsibilities**: Formats log messages with timestamps and locations, routes logs to stdout with color codes, manages file logging, and implements rotation policies.
- **Why it exists**: Replaces print statements with standardized, production-grade logs that write to console and log files, preventing resource contention.
- **How it interacts with other modules**: Provides a single `logger` instance imported globally to record informational events, warnings, or errors.
- **Real-world industry usage**: Auto-rotates files to prevent disk usage overflow. Compresses archives into zip format. Prepares logs to be forwarded to centralized telemetry (e.g., Datadog, ELK).
- **Interview explanation**: *“We use a customized Loguru configuration to manage all app logs. It automatically captures logs from internal services, formats them with timestamp, module name, and level, and writes them to console and file sinks. Old files are rotated at 10MB, retained for 10 days, and zipped.”*
- **Best practices followed**: Automated directory creation, zip compression, 10-day retention policies, and single-handler enforcement.
- **Future scalability considerations**: Can easily be configured to output JSON formatted logs for automated parsing by log aggregators.

---

### Module 3: `backend/app/main.py`
- **Purpose**: Acts as the ASGI application entry point that initializes FastAPI.
- **Responsibilities**: Bootstraps the application, configures metadata, registers routes, and implements the async lifespan context hook.
- **Why it exists**: Serves as the central hook connecting routers, database connections, and configurations to start the Uvicorn web server.
- **How it interacts with other modules**: Registers `health.py` routers and sets up global state configs on application startup.
- **Real-world industry usage**: Handles connection pooling setups, coordinates microservices lifecycle events, and serves as the deployment target for Docker containers.
- **Interview explanation**: *“This is the entry point of our backend. It bootstraps our FastAPI application, registers global middlewares and routers, and utilizes the lifespan context manager to run startup validation checks (like confirming directories exist) and handle graceful shutdowns.”*
- **Best practices followed**: Async/await context handlers, startup validation, isolated routers, and separation of app config from business logic.
- **Future scalability considerations**: Can be extended to plug in rate limiters, global exception managers, or CORS middleware when scaling the client-side app.

---

### Module 4: `backend/app/api/health.py`
- **Purpose**: Implements a lightweight system health check endpoint.
- **Responsibilities**: Exposes the `GET /health` route, returning a validated status payload containing environment parameters and dynamic uptime metrics.
- **Why it exists**: Provides monitoring systems and container orchestrators with a rapid way to test application viability without hitting slow downstream services.
- **How it interacts with other modules**: Registered inside `main.py` and reads startup state data initialized during application boot.
- **Real-world industry usage**: Monitored by Kubernetes readiness and liveness probes to verify when to restart containers or direct load balancer traffic.
- **Interview explanation**: *“This module provides a lightweight health check endpoint. It returns a validated payload containing uptime and environment metrics. Since it avoids invoking heavy resources (like databases or AI models), it's highly performant and safe for continuous polling by load balancers.”*
- **Best practices followed**: Pydantic response models validation, precise UTC timestamp serialization, and framework-independent business telemetry tracking.
- **Future scalability considerations**: Can be expanded to verify database connections or cache pools before returning a `200 OK` status.

---

### Module 5: `backend/app/schemas/request.py`
- **Purpose**: Defines request validation schemas for incoming API payloads.
- **Responsibilities**: Models the `ProposalRequest` and its enums, applying string length validation and whitespace sanitization.
- **Why it exists**: Intercepts invalid, empty, or malicious client requests before they can trigger expensive downstream AI model invocations.
- **How it interacts with other modules**: Imported by routers and controllers to validate incoming POST requests.
- **Real-world industry usage**: Acts as an input validation firewall, protecting downstream agents from prompt injections, formatting errors, or buffer overflows.
- **Interview explanation**: *“We use Pydantic v2 schemas to validate incoming client requests. For instance, the `ProposalRequest` ensures the prompt text is present, strips whitespaces, validates optional parameter types, and blocks inputs that do not meet length limits.”*
- **Best practices followed**: Input sanitization via custom field validators, enum validation constraints, and descriptive Swagger decorators.
- **Future scalability considerations**: Can easily accommodate advanced metadata parameters (like priority tiers, target domains, or budget scopes) as SaaS features grow.

---

### Module 6: `backend/app/schemas/response.py`
- **Purpose**: Defines and standardizes the structure of all API response payloads.
- **Responsibilities**: Implements the base response envelope structures (`BaseResponse`, `ProposalResponse`, `ErrorResponse`, `ValidationErrorResponse`) and handles transaction timestamps.
- **Why it exists**: Guarantees that clients always receive a uniform and predictable response layout (containing success status, descriptive message, and timestamp).
- **How it interacts with other modules**: Controllers serialize their return statements directly to these validated models.
- **Real-world industry usage**: Simplifies error parsing on client frontends and standardizes logging metrics across systems.
- **Interview explanation**: *“We implemented response schemas to guarantee client contract consistency. All responses share a `BaseResponse` containing a timestamp and success flag. Specific classes like `ProposalResponse` inherit this base to attach domain-specific fields.”*
- **Best practices followed**: Pydantic inheritance strategy, dynamic timezone-aware default factories, and schema extras examples for automated OpenAPI documentation.
- **Future scalability considerations**: Can add validation metrics, execution trace IDs, and cost logs to response payloads.

---

### Module 7: `backend/app/llm/groq_client.py` & `backend/app/llm/llm_service.py`
- **Purpose**: Establishes connection to the Groq API provider for LLM completion tasks.
- **Responsibilities**: Manages lazy initialization of `AsyncGroq`, maps provider API errors to custom exceptions, logs duration/token metrics, and handles retry backoffs on transient errors.
- **Why it exists**: Decouples LLM provider details, timeouts, and API clients from agents, keeping core logic provider-agnostic.
- **How it interacts with other modules**: Used by the Planner and Executor agents to request JSON and plain text generation.
- **Real-world industry usage**: Utilizes exponential backoff to handle transient API issues (timeouts, rate limits, 5xx errors). Maps provider exceptions to domain exceptions so calling nodes don't depend on provider-specific imports.
- **Interview explanation**: *“This layer manages our LLM interactions. It uses a singleton `GroqClientManager` for lifecycle management, and maps raw API errors (like 401s or rate limits) into custom exceptions. It uses an async retry loop with exponential backoff on transient errors and logs token usage.”*
- **Best practices followed**: Dependency Inversion Principle, custom error wrapping, logging tracebacks, and non-blocking retry mechanisms.
- **Future scalability considerations**: Multiple provider clients (Gemini, OpenAI) can be registered to support runtime fallback or cost-based load balancing.

---

### Module 8: `backend/app/llm/prompts.py` & `backend/app/llm/prompt_builder.py`
- **Purpose**: Centralizes the system instructions and dynamic prompt building logic.
- **Responsibilities**: Defines prompt structures for Planner, Executor, and Reflector agents. Implements builders that combine user requests with previously generated sections.
- **Why it exists**: Separates prompt engineering from code logic. Ensures no hardcoded prompt strings are scattered across the codebase.
- **How it interacts with other modules**: Utilized by agents before sending prompt strings to the LLM Service.
- **Real-world industry usage**: Allows prompt versions to be modified or updated without changing application code.
- **Interview explanation**: *“We isolate all our prompts in prompts.py, and construct them at runtime using builder utilities. This ensures agents don't contain hardcoded strings. If we need to edit instructions, we change them in one place without touching the agent code.”*
- **Best practices followed**: Single responsibility, unified writing style guidelines, tone parameters reuse, and input context sanitization.
- **Future scalability considerations**: Prompt templates can be fetched dynamically from databases or templates files to enable prompt hot-reloading.

---

### Module 9: `backend/app/agents/state.py` & `backend/app/agents/planner.py`
- **Purpose**: Defines shared agent execution state and implements the Planner agent node.
- **Responsibilities**: Represents `AgentState` TypedDict. Analyzes request prompts, builds dynamic instructions, validates JSON plan formats, and deduplicates tasks.
- **Why it exists**: Represents the initial node in our LangGraph workflow. Translates natural language requests into structured execution plans.
- **How it interacts with other modules**: Updates state task parameters, builds prompt contexts, and calls the LLM Service.
- **Real-world industry usage**: Dynamically breaks down user goals into ordered tasks, establishing trace boundaries for agents.
- **Interview explanation**: *“The planner node is the first node in our LangGraph workflow. It takes the user request, asks the LLM to generate a task list, validates the JSON output, removes any duplicate tasks, and populates the shared `AgentState`.”*
- **Best practices followed**: Composable state containers, explicit status updates, robust parsing validation with fallbacks, and logging traces.
- **Future scalability considerations**: The planner can dynamically select custom tools or resources depending on the request's domain.

---

### Module 10: `backend/app/agents/executor.py`
- **Purpose**: Implements the Executor agent node to draft individual proposal sections.
- **Responsibilities**: Processes tasks sequentially, drafts content, validates length and uniqueness, retries on failure, and updates section mappings.
- **Why it exists**: Generates proposal sections one at a time, keeping content highly detailed while preventing context window dilution.
- **How it interacts with other modules**: Reads state task parameters, uses prompt builders, calls the LLM Service, and writes sections to the shared state.
- **Real-world industry usage**: Feeds previously generated sections back into the next task's prompt context to ensure document tone and figures align perfectly.
- **Interview explanation**: *“The executor node processes tasks one at a time. It finds the next pending task, builds a prompt containing all previously written sections to keep tone and numbers aligned, calls the LLM, validates length and duplicate constraints, and saves it to state.”*
- **Best practices followed**: Task-by-task division, quality validation filters (length checks), context accumulation, and safe exception logging.
- **Future scalability considerations**: Can run independent tasks in parallel (e.g., concurrently generating Scope and Risks sections) to reduce runtime latency.
