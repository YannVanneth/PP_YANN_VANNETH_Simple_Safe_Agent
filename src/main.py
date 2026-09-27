import asyncio

from langchain_core.messages import BaseMessage

from app.agents import run_agent
from app.schemas import UserRole
import argparse

def parse_args():

    parser = argparse.ArgumentParser(description="Ask the safe product agent about the catalog.")

    parser.add_argument(
        "request",
        nargs="*",
        help="Your request (omit it to be prompted interactively)",
    )
    parser.add_argument(
        "--role",
        choices=[role.value for role in UserRole],
        default=UserRole.CUSTOMER.value,
        help="Application role used by the permission harness (default: customer)",
    )
    return parser.parse_args()

def main():

    args = parse_args()
    role = UserRole(args.role)
    first_request = " ".join(args.request).strip()
    history: list[BaseMessage] | None = None

    print(f"Role: {role.value}")
    print("Type 'exit' or 'quit' to end the chat.")

    try:
        while True:
            if first_request:
                request = first_request
                first_request = ""
                print(f"\nYou: {request}")
            else:
                request = input("\nYou: ").strip()

            if request.lower() in {"exit", "quit", "bye"}:
                break
            if not request:
                continue

            result = asyncio.run(run_agent(request, role, history))
            history = result.messages
            print(f"Agent: {result.answer}")
            print(f"({result.model_turns} model turn(s), {result.tool_calls} tool call(s))")
    except (EOFError, KeyboardInterrupt):
        print()

if __name__ == "__main__":
    main()