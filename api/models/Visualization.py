from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class AGVPosition(BaseModel):
    x: float
    y: float
    theta: float
    mapId: str
    positionInitialized: bool
    localizationScore: Optional[float]
    deviationRange: Optional[float]

class Velocity(BaseModel):
    vx: Optional[float]
    vy: Optional[float]
    omega: Optional[float]

class Visualization(BaseModel):
    headerId: Optional[int]
    timestamp: Optional[datetime]
    version: Optional[str]
    manufacturer: Optional[str]
    serialNumber: Optional[str]
    agvPosition: Optional[AGVPosition]
    velocity: Optional[Velocity]
