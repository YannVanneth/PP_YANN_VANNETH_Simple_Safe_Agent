""" Here is my schema definition """
from pydantic import BaseModel, Field, ConfigDict

""" Product Schema """
class Product(BaseModel):
    product_id: int = Field(gt=0, description="Positive product ID")
    name: str = Field(min_length=1, description="Product name")
    quantity: int = Field(ge=0, description="Units currently in stock")
    price: float = Field(gt=0, description="Price in USD")

""" Defining Input Schema """
class GetProductsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

class InsertProductInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

class BuyProductInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(gt=0, description="Positive product ID")

class SearchProductsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=100, description="Product name or keyword")

class ProductIdInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(gt=0, description="Positive product ID")

""" User role class in the app """
from enum import StrEnum

class UserRole(StrEnum):
    ADMIN = "admin"
    CUSTOMER = "customer"