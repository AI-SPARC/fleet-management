from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime

class ActionParameter(BaseModel):
    key: str
    value: Union[List[Union[str, float, bool]], bool, float, str]

class Action(BaseModel):
    actionType: str
    actionId: str
    actionDescription: Optional[str] = None
    blockingType: str
    actionParameters: Optional[List[ActionParameter]] = []

class InstantActions(BaseModel):
    headerId: int
    timestamp: datetime
    version: str
    manufacturer: str
    serialNumber: str
    actions: List[Action]