"""Request/response schemas for the shopping agent."""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """User input for product search."""

    budget: str = Field(..., description="Budget constraint (e.g. '$200', 'under 100')")
    deadline: str = Field(..., description="Delivery deadline (e.g. '3 days', '1 week')")
    size: str = Field(..., description="Size (e.g. 'M', '10', 'one size')")
    style: str = Field(..., description="Style preference (e.g. 'casual', 'minimal')")
    target: str = Field("", description="Target audience (e.g. 'women', 'men', 'kids')")
    color: str = Field("", description="Preferred color (e.g. 'black', 'navy')")
    items: list[str] = Field(..., description="Items to find (e.g. ['shirt', 'pants'])")


class ProductVariants(BaseModel):
    """Available variants for a product."""

    sizes: list[str] = Field(default_factory=list, description="Available sizes")
    colors: list[str] = Field(default_factory=list, description="Available colors")
    material: list[str] = Field(default_factory=list, description="Materials")


class SearchResultItem(BaseModel):
    """Single product result for the agent response."""

    name: str
    price: float
    delivery_estimate: str
    variants: ProductVariants
    retailer: str
    image_url: str | None = Field(default=None, description="URL of the product image")
    link: str | None = Field(default=None, description="Product page URL")
    short_description: str | None = Field(default=None, description="Short product description")
    item: str | None = Field(default=None, description="Requested item category (e.g. shirt, pants)")


class SearchResponseStructured(BaseModel):
    """Structured JSON response for the shopping search agent."""

    query: dict = Field(description="Echo of search constraints")
    results_by_item: dict = Field(description="Products grouped by requested item")
    total_count: int = Field(description="Total number of products returned")
    retailers: list[str] = Field(default_factory=list, description="Unique retailers in results")


SearchResultResponse = list[SearchResultItem]
