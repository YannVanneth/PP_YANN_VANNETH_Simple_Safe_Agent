""" Here is my mock data definition """
from app import config
from app.schemas import NewProduct, Product

MOCK_DATA = [
    Product(product_id=1, name="Laptop", quantity=10, price=999.99),
    Product(product_id=2, name="Smartphone", quantity=5, price=499.99),
    Product(product_id=3, name="Headphones", quantity=2, price=29.99),
    Product(product_id=4, name="Camera", quantity=15, price=1299.99),
    Product(product_id=5, name="TV", quantity=8, price=1999.99),
]

""" Here is my tool definition """

# frist, i create a MCPServer instance
from mcp.server import MCPServer

server = MCPServer("Simple Safe Agent MCP Tools")

# second, I start to provide the tool implementation here.
from typing import Annotated
from pydantic import Field

@server.tool()
async def get_products() -> dict[str, object]:
    """Get a list of all products in the catalog."""

    return {
        "products": [product.model_dump() for product in MOCK_DATA],
        "count": len(MOCK_DATA),
        "message": "Product retrieved Successfully..."
    }


@server.tool()
async def add_product(product: NewProduct) -> dict[str, object]:
    """Add a product using name, price, and quantity (or stock). The app checks admin permission."""

    product_id = max((item.product_id for item in MOCK_DATA), default=0) + 1
    saved_product = Product(product_id=product_id, **product.model_dump())
    MOCK_DATA.append(saved_product)

    return {
        "product_id": saved_product.product_id,
        "product_name": saved_product.name
    }


@server.tool()
async def check_stock(
    product_id: Annotated[int, Field(gt=0, description="Positive product ID")],
) -> dict[str, object]:

    """Check the available quantity for one product."""
    product = _find_product(product_id)

    if product is None:
        return {"error": f"Product {product_id} was not found."}

    return {
        "product_id": product.product_id,
        "product_name": product.name,
        "in_stock": product.quantity > 0,
        "quantity": product.quantity,
    }


@server.tool()
async def search_products(
    query: Annotated[str, Field(min_length=1, max_length=100, description="Product name or keyword")],
) -> dict[str, object]:

    """Find products whose names contain the search text."""

    normalized_query = query.strip().casefold()

    if not normalized_query:
        return {"error": "Search query cannot be blank."}

    matches = [
        product.model_dump() for product in MOCK_DATA
        if normalized_query in product.name.casefold()
    ]

    return {
        "products": matches,
        "count": len(matches)
    }


@server.tool()
async def delete_product(
    product_id: Annotated[int, Field(gt=0, description="Positive product ID")],
) -> dict[str, object]:

    """Delete a product from the demo catalog. The app checks admin permission."""
    product = _find_product(product_id)

    if product is None:
        return {"error": f"Product {product_id} was not found."}

    MOCK_DATA.remove(product)

    return {
        "deleted": True,
        "product_id": product_id,
        "product_name": product.name
    }


@server.tool()
async def buy_product(product_id: int) -> dict[str, object]:

    """Buy a product from the catalog. The app checks customer permission."""
    product = _find_product(product_id)

    if product is None:
        return {"error": f"Product {product_id} was not found."}

    if product.quantity <= 0:
        return {"error": f"Product {product_id} is out of stock."}

    product.quantity -= 1

    return {
        "success": True,
        "product_id": product_id,
        "product_name": product.name
    }


def _find_product(product_id: int) -> Product | None:
    """ Helper function to find a product in the demo catalog. """
    for product in MOCK_DATA:
        if product.product_id == product_id:
            return product
    return None

if __name__ == "__main__":
    server.run(transport="streamable-http", port=config.MCP_PORT, host=config.MCP_HOST)
