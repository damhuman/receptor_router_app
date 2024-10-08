from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class RoutingIntentModel(BaseModel):
    destinationName: str
    important: bool = Field(..., description="Indicates if the destination is important")
    bytes: int = Field(..., description="Size in bytes for routing decisions")
    additionalParams: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for routing")


class EventRequestModel(BaseModel):
    payload: Dict[str, Any]
    routingIntents: List[RoutingIntentModel]
    strategy: Optional[str] = None
