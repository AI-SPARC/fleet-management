from pydantic import BaseModel
from typing import List, Optional

class NodePosition(BaseModel):
    x: float
    y: float
    theta: float
    mapId: str

class NodeState(BaseModel):
    nodeId: str
    sequenceId: int
    nodeDescription: Optional[str]
    nodePosition: Optional[NodePosition]
    released: bool

class KnotVector(BaseModel):
    degree: int
    knotVector: List[float]
    controlPoints: List[NodePosition]

class EdgeState(BaseModel):
    edgeId: str
    sequenceId: int
    edgeDescription: Optional[str]
    released: bool
    trajectory: Optional[KnotVector]

class AGVPosition(BaseModel):
    x: float
    y: float
    theta: float
    mapId: str
    mapDescription: Optional[str]
    positionInitialized: bool
    localizationScore: Optional[float]
    deviationRange: Optional[float]

class Velocity(BaseModel):
    vx: Optional[float]
    vy: Optional[float]
    omega: Optional[float]

class BoundingBoxReference(BaseModel):
    x: float
    y: float
    z: float
    theta: Optional[float]

class LoadDimensions(BaseModel):
    length: float
    width: float
    height: Optional[float]

class Load(BaseModel):
    loadId: Optional[str]
    loadType: Optional[str]
    loadPosition: Optional[str]
    boundingBoxReference: Optional[BoundingBoxReference]
    loadDimensions: Optional[LoadDimensions]
    weight: Optional[float]

class ActionState(BaseModel):
    actionId: str
    actionType: Optional[str]
    actionDescription: Optional[str]
    actionStatus: str
    resultDescription: Optional[str]

class BatteryState(BaseModel):
    batteryCharge: float
    batteryVoltage: Optional[float]
    batteryHealth: Optional[float]
    charging: bool
    reach: Optional[float]

class ErrorReference(BaseModel):
    referenceKey: str
    referenceValue: str

class Error(BaseModel):
    errorType: str
    errorReferences: Optional[List[ErrorReference]]
    errorDescription: Optional[str]
    errorLevel: str

class InfoReference(BaseModel):
    referenceKey: str
    referenceValue: str

class Information(BaseModel):
    infoType: str
    infoReferences: Optional[List[InfoReference]]
    infoDescription: Optional[str]
    infoLevel: str

class SafetyState(BaseModel):
    eStop: str
    fieldViolation: bool

class State(BaseModel):
    headerId: int
    timestamp: str
    version: str
    manufacturer: str
    serialNumber: str
    orderId: str
    orderUpdateId: int
    zoneSetId: Optional[str]
    lastNodeId: str
    lastNodeSequenceId: int
    driving: bool
    paused: Optional[bool]
    newBaseRequest: Optional[bool]
    distanceSinceLastNode: Optional[float]
    operatingMode: str
    nodeStates: List[NodeState]
    edgeStates: List[EdgeState]
    agvPosition: Optional[AGVPosition]
    velocity: Optional[Velocity]
    loads: Optional[List[Load]]
    actionStates: List[ActionState]
    batteryState: BatteryState
    errors: List[Error]
    information: Optional[List[Information]]
    safetyState: SafetyState
