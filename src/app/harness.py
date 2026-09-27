"""Application-side authorization and argument validation for tool calls."""

from pydantic import ValidationError

from app.schemas import GetProductsInput, ProductIdInput, SearchProductsInput, UserRole

class PermissionDenied(Exception):
    """Raised when a role requests a tool it is not allowed to use."""

ROLE_PERMISSIONS: dict[UserRole, frozenset[str]] = {
    UserRole.CUSTOMER: frozenset({"search_products", "check_stock", "get_products", "buy_product"}),
    UserRole.ADMIN: frozenset({"search_products", "check_stock", "delete_product", "get_products", "add_product"}),
}

TOOL_INPUT_SCHEMAS = {
    "search_products": SearchProductsInput,
    "check_stock": ProductIdInput,
    "delete_product": ProductIdInput,
    "get_products": GetProductsInput,
    "add_product": ProductIdInput,
    "buy_product": ProductIdInput,
}

def validate_tool_call(role: UserRole, tool_name: str, arguments: object) -> dict[str, object]:
    """Authorize a known tool and validate its arguments before MCP execution."""
    if tool_name not in TOOL_INPUT_SCHEMAS:
        raise PermissionDenied(f"Tool '{tool_name}' is not on the application's allowlist.")

    if tool_name not in ROLE_PERMISSIONS[role]:
        raise PermissionDenied(f"The {role.value} role is not allowed to use '{tool_name}'.")

    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a JSON object.")

    try:
        validated = TOOL_INPUT_SCHEMAS[tool_name].model_validate(arguments)

    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )

        raise ValueError(f"Invalid arguments for '{tool_name}': {details}") from exc

    return validated.model_dump()
