""" Here are the configuration settings for the application. """

MODEL = "gemma4"
MODEL_BASE_URL = "http://localhost:11434"

MCP_HOST = "127.0.0.1"
MCP_PORT = 8000
MCP_BASE_URL = f"http://{MCP_HOST}:{MCP_PORT}/mcp"

MAX_ITERATIONS = 6
MAX_TOOL_CALLS = 8

SYSTEM_PROMPT = """You are a helpful shopping assistant for a small product catalog.
Use the available tools when current catalog or stock information is needed.
You may call multiple tools in sequence, using tool results to decide what to do next.
Never claim that an action succeeded unless its tool result confirms it.
If a tool reports an error or permission denial, explain that clearly and offer a safe alternative.
Answer concisely when the request is satisfied."""