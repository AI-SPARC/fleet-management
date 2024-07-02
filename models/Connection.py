from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class Connection(BaseModel):
    headerId: int
    timestamp: datetime 
    version: str 
    manufacturer: str
    serialNumber: str
    connectionState: Literal['ONLINE', 'OFFLINE', 'CONNECTIONBROKEN']