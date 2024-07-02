from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime

class ActionParameter(BaseModel):
    key: str
    value: Union[List[Union[str, float, bool]], bool, float, str]

class Action(BaseModel):
    actionType: str
    actionId: str
    actionDescription: Optional[str]
    blockingType: str
    actionParameters: Optional[List[ActionParameter]] = []

class NodePosition(BaseModel):
    x: float
    y: float
    theta: Optional[float] = None
    allowedDeviationXy: Optional[float] = None
    allowedDeviationTheta: Optional[float] = None
    mapId: str
    mapDescription: Optional[str]

class Node(BaseModel):
    nodeId: str
    sequenceId: int
    nodeDescription: Optional[str]
    released: bool
    nodePosition: Optional[NodePosition]
    actions: List[Action]

class ControlPoint(BaseModel):
    x: float
    y: float
    weight: Optional[float] = 1.0

class Trajectory(BaseModel):
    degree: int
    knotVector: List[float]
    controlPoints: List[ControlPoint]

class Edge(BaseModel):
    edgeId: str
    sequenceId: int
    edgeDescription: Optional[str]
    released: bool
    startNodeId: str
    endNodeId: str
    maxSpeed: Optional[float]
    maxHeight: Optional[float]
    minHeight: Optional[float]
    orientation: Optional[float]
    orientationType: Optional[str] = "TANGENTIAL"
    direction: Optional[str]
    rotationAllowed: Optional[bool]
    maxRotationSpeed: Optional[float]
    length: Optional[float]
    trajectory: Optional[Trajectory]
    actions: List[Action]

class Order(BaseModel):
    headerId: int
    timestamp: datetime
    version: str
    manufacturer: str
    serialNumber: str
    orderId: str
    orderUpdateId: int
    zoneSetId: Optional[str]
    nodes: List[Node]
    edges: List[Edge]
