from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


db_url="postgresql://postgres:ddagarr@localhost:5432/Smart_Task_Manager"
engine= create_engine(db_url) 
session_x=sessionmaker(autocommit=False, autoflush=False, bind=engine)