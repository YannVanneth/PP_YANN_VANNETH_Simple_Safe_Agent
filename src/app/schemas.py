""" Here is my schema definition """

from pydantic import BaseModel, Field

""" Product Schema """
class Product(BaseModel):
    product_id: int = Field(gt=0, description="Positive product ID")
    name: str = Field(min_length=1, description="Product name")
    quantity: int = Field(ge=0, description="Units currently in stock")
    price: float = Field(gt=0, description="Price in USD")


""" User role class in the app """
from enum import StrEnum

class UserRole(StrEnum):
    ADMIN = "admin"
    CUSTOMER = "customer"