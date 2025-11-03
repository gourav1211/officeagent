# Agents: Roles, Prompts, and Extensibility

The system uses a multi-agent pattern. Each agent inherits from `BaseOfficeAgent`, defines a system prompt, and selects tools from the registry.

## Agents

- DocumentAgent (Word)
- PresentationAgent (PowerPoint)
- SpreadsheetAgent (Excel)
- CommunicationAgent (Outlook/Teams)
- WorkflowAgent (cross-application orchestration)

Each agent:
- Defines `_initialize_tools()` → list of tool names registered in the `OfficeToolRegistry`.
- Defines `_get_system_prompt()` → a comprehensive role description and best practices.
- Exposes `execute(task, context?, user_id?, task_id?)` and `execute_streaming(...)` used by the orchestrator.

## Orchestrator

`OfficeAIAgent` assembles all tools and creates a LangChain tools agent (Gemini via `langchain-google-genai` + `AgentExecutor`). It:
- Accepts a natural-language `task` string.
- Delegates to the appropriate specialized agent or directly uses tools.
- Tracks status, metrics, and execution history.

### Minimal contract

- Input: natural language `task` plus optional JSON `context`.
- Output: dict with `status`, `result` or `error`, `task_id`, and timing.

## Adding a New Agent

1) Create `agents/my_agent.py` inheriting from `BaseOfficeAgent`.
2) Implement `_initialize_tools()` to return the desired tool list.
3) Implement `_get_system_prompt()` with clear, scoped responsibilities.
4) Register it in `core/agent_orchestrator.py` inside `_initialize_agents()` and in `core/config.AgentType` if it’s a new type.

## Selecting Tools

Agents call `self._get_tools_safely(["tool_name"])` to convert tool names into `BaseTool` instances from the registry. Keep names consistent with those registered in `tools/office_tools.py` or `tools/simple_tools.py`.

## Streaming

All agents support streaming via `execute_streaming`, which returns incremental chunks. The server wraps this as Server-Sent Events at `/execute_stream`.
