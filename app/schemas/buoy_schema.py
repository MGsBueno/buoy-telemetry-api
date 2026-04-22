from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class BuoyCreate(BaseSchema):
    name: str = Field(..., min_length=1)
    token: str = Field(..., min_length=1)


class BuoyUpdate(BaseSchema):
    name: Optional[str] = None
    token: Optional[str] = None


class BuoyResponse(BaseSchema):
    id: str
    name: str


class MessageResponse(BaseSchema):
    message: str


class ReadingCreate(BaseSchema):
    temperature: float
    battery_voltage: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ReadingResponse(BaseSchema):
    id: str
    temperature: float
    battery_voltage: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: int


class TelemetryIn(BaseSchema):
    device_id: str = Field(..., min_length=1)
    device_name: str = Field(..., min_length=1)
    token: str = Field(..., min_length=1)
    temperature: float
    battery_voltage: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
