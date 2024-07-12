from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

class Position(BaseModel):
    x: float
    y: float

class WheelDefinition(BaseModel):
    type: str
    isActiveDriven: bool
    isActiveSteered: bool
    position: Position
    diameter: float
    width: float
    centerDisplacement: Optional[float]
    constraints: Optional[str]

class Envelope2D(BaseModel):
    set: str
    polygonPoints: List[Position]
    description: Optional[str]

class Envelope3D(BaseModel):
    set: str
    format: str
    data: dict
    url: str
    description: Optional[int]

class TypeSpecification(BaseModel):
    seriesName: str
    seriesDescription: Optional[str]
    agvKinematic: str
    agvClass: str
    maxLoadMass: float
    localizationTypes: List[str]
    navigationTypes: List[str]

class PhysicalParameters(BaseModel):
    speedMin: float
    speedMax: float
    accelerationMax: float
    decelerationMax: float
    heightMin: Optional[float]
    heightMax: float
    width: float
    length: float

class ProtocolLimits(BaseModel):
    maxStringLens: dict
    maxArrayLens: dict
    timing: dict

class ProtocolFeatures(BaseModel):
    optionalParameters: List[dict]
    agvActions: List[dict]

class LoadSpecification(BaseModel):
    loadPositions: Optional[List[str]]
    loadSets: Optional[List[dict]]

class AgvGeometry(BaseModel):
    wheelDefinitions: List[WheelDefinition]
    envelopes2d: List[Envelope2D]
    envelopes3d: List[Envelope3D]

class Factsheet(BaseModel):
    version: str
    manufacturer: str
    serialNumber: str
    typeSpecification: TypeSpecification
    physicalParameters: PhysicalParameters
    protocolLimits: ProtocolLimits
    protocolFeatures: ProtocolFeatures
    agvGeometry: AgvGeometry
    loadSpecification: LoadSpecification
    headerId: Optional[int]
    timestamp: Optional[datetime]