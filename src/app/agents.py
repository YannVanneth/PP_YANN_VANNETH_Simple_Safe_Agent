import json
from typing import TypedDict, Annotated, Literal
from langgraph.graph import add_messages

from dataclasses import dataclass
from langchain_core.messages import BaseMessage
from app.schemas import UserRole

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    role: UserRole
    model_turns: int
    tool_calls: int
    stop_reason: str | None

@dataclass
class AgentResult:
    answer: str
    model_turns: int
    tool_calls: int
    messages: list[BaseMessage]


""" Here is my helper function """

from app import config
from app.harness import TOOL_INPUT_SCHEMAS, PermissionDenied, validate_tool_call


from mcp import Client
from mcp.types import CallToolResult
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from langchain_ollama import ChatOllama
from langgraph.constants import START, END
from langgraph.graph import StateGraph

def tool_result_text(result: CallToolResult) -> str:
    """ Convert MCP result into a readable observation for the model."""
    if result.is_error:
        return json.dumps({"error": "The tool could not complete the request."})

    if result.structured_content is not None:
        return json.dumps(result.structured_content)

    return "\n".join(item.text for item in result.content if hasattr(item, "text")) or "{}"


def build_graph(model, client: Client):
    """ Building the graph for the model """

    async def call_model(state: AgentState) -> dict:

        response = await model.ainvoke(state["messages"])

        return {
            "messages": [response],
            "model_turns": state["model_turns"] + 1
        }

    async def call_tools(state: AgentState) -> dict:
        response = state["messages"][-1]
        observations: list[ToolMessage] = []
        tool_calls = state["tool_calls"]
        stop_reason = None

        for call_index, call in enumerate(response.tool_calls, start=1):
            name = call["name"]
            print(f"Tool: {name}({json.dumps(call['args'])})")

            if tool_calls >= config.MAX_TOOL_CALLS:
                observation = json.dumps({"error": "Tool-call limit reached; this call was not executed."})
                stop_reason = "Stopped because the tool-call limit was reached."
            else:
                tool_calls += 1
                try:
                    arguments = validate_tool_call(state["role"], name, call["args"])
                    result = await client.call_tool(name, arguments)
                    observation = tool_result_text(result)

                except PermissionDenied as exc:
                    observation = json.dumps({"error": str(exc), "code": "PERMISSION_DENIED"})

                except ValueError as exc:
                    observation = json.dumps({"error": str(exc), "code": "INVALID_ARGUMENT"})

                except Exception:
                    observation = json.dumps({"error": f"Tool '{name}' could not be completed."})

            print(f"Observation: {observation}")
            observations.append(
                ToolMessage(
                    content=observation,
                    tool_call_id=str(call.get("id") or f"call-{state['model_turns']}-{call_index}"),
                )
            )

        return {
            "messages": observations,
            "tool_calls": tool_calls,
            "stop_reason": stop_reason
        }

    async def after_model(state: AgentState) -> Literal["tools", "__end__"]:
        return "tools" if state["messages"][-1].tool_calls else END

    async def after_tools(state: AgentState) -> Literal["model", "stop"]:
        if state["stop_reason"] or state["model_turns"] >= config.MAX_ITERATIONS:
            return "stop"
        return "model"

    async def stop(state: AgentState) -> dict:
        answer = state["stop_reason"] or "I stopped because the model-turn limit was reached."
        return {"messages": [AIMessage(content=answer)]}

    """ Graph Building """
    builder = StateGraph(AgentState)
    builder.add_node("model", call_model)
    builder.add_node("tools", call_tools)
    builder.add_node("stop", stop)
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", after_model)
    builder.add_conditional_edges("tools", after_tools)
    builder.add_edge("stop", END)

    return builder.compile()


async def run_agent(
    request: str,
    role: UserRole,
    history: list[BaseMessage] | None = None,
) -> AgentResult:
    messages: list[BaseMessage] = list(history) if history else [SystemMessage(content=config.SYSTEM_PROMPT)]
    messages.append(HumanMessage(content=request))

    if config.MAX_ITERATIONS < 1:
        answer = "Stopped because the model-turn limit was reached."
        messages.append(AIMessage(content=answer))
        return AgentResult(answer, 0, 0, messages)

    try:
        async with Client(config.MCP_BASE_URL) as client:
            listed_tools = await client.list_tools()
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.input_schema,
                    },
                }
                for tool in listed_tools.tools
                if tool.name in TOOL_INPUT_SCHEMAS
            ]
            model = ChatOllama(
                base_url=config.MODEL_BASE_URL,
                model=config.MODEL,
                temperature=0,
            ).bind_tools(tools)

            graph = build_graph(model, client)

            state = await graph.ainvoke(
                {
                    "messages": messages,
                    "role": role,
                    "model_turns": 0,
                    "tool_calls": 0,
                    "stop_reason": None,
                }
            )

            answer = str(state["messages"][-1].content).strip() or "I could not answer that request."

            return AgentResult(answer, state["model_turns"], state["tool_calls"], state["messages"])

    except Exception:

        answer = "I could not connect to the local model or MCP server. Check that both are running."

        messages.append(AIMessage(content=answer))

        return AgentResult(answer, 0, 0, messages)
