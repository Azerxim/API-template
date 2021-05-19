from typing import List, Optional
from pydantic import BaseModel


class TableComTime(BaseModel):
    playerid: int
    command: str
    time: str = None

    class Config:
        orm_mode = True



class TableCore(BaseModel):
    playerid: int
    discord_id: str
    pseudo: str
    lang: str
    guild: str
    level: int
    xp: int
    devise: int
    super_devise: int
    godparent: int
    com_time: List[TableComTime] = []

    class Config:
        orm_mode = True
