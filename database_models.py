from sqlalchemy import Column, Integer, String, func , Date, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class login(Base):

    __tablename__ = "Login_Credentials"

    u_id= Column(Integer, primary_key=True, index=True)
    u_name= Column(String)
    pwd_hash= Column(String(200))
    email= Column(String)
    
class daily_tasks(Base):

    __tablename__ = "Daily_Tasks"

    u_id= Column(Integer, ForeignKey("Login_Credentials.u_id"), nullable=False)
    t_id= Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task= Column(String)
    date= Column(Date, default=func.current_date())
    is_done = Column(Boolean, default=False)
    complete_date = Column(Date, nullable=True)

class long_term_tasks(Base):

    __tablename__ = "Long_Term_Tasks" 
    u_id= Column(Integer, ForeignKey("Login_Credentials.u_id"), nullable=False)
    t_id= Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task= Column(String)
    add_date= Column(Date, default=func.current_date())
    due_date= Column(Date)
    is_done = Column(Boolean, default=False)
    complete_date = Column(Date, nullable=True)


    
    