from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal

class CameraCreate(BaseModel):
    camera_id: str = Field(min_length=1,max_length=64)
    name: str
    source: str
    protocol: str = "file"
    location: str = ""
    sector: str = ""
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_accuracy_m: float | None = Field(default=None, ge=0)
    location_source: str = "manual"
    enabled: bool = True

class CameraLocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_m: float | None = Field(default=None, ge=0)
    location: str | None = None
    source: Literal["browser","manual","geocoded"] = "manual"

class FenceCreate(BaseModel):
    id: str
    name: str
    camera_id: str
    geometry_type: Literal["polygon","line","circle"] = "polygon"
    coordinates: list = Field(default_factory=list)
    allowed_objects: list[str] = Field(default_factory=list)
    severity: Literal["INFO","LOW","MEDIUM","HIGH","CRITICAL"] = "HIGH"
    active: bool = True

class FenceUpdate(BaseModel):
    name: str | None = None
    coordinates: list | None = None
    allowed_objects: list[str] | None = None
    severity: Literal["INFO","LOW","MEDIUM","HIGH","CRITICAL"] | None = None
    active: bool | None = None

class IncidentUpdate(BaseModel):
    status: Literal["NEW","INVESTIGATING","ESCALATED","RESOLVED"]
    notes: str | None = None
