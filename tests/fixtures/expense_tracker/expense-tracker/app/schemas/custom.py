# Generated from the Contract. Do not edit.
# Custom shapes, one class per endpoint body: <EndpointId in CamelCase><Request|Response>.
from pydantic import BaseModel


class MonthlySummaryResponse(BaseModel):
    month: str
    total: float
    count: int
