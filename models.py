from pydantic import BaseModel
from datetime import date

class register(BaseModel):
    u_id: int
    u_name: str
    pwd: str
    email: str
class LoginRequest(BaseModel):
    u_id: int
    pwd: str

class d_task(BaseModel):
    task: str

class l_task(BaseModel):
    task: str
    due_date: date

    
