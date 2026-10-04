import uuid 
from datetime import datetime , date
from enum import Enum 
from typing import List 
from pydantic import BaseModel , ConfigDict, Field ,field_validator
from sqlmodel import SQLModel , Field, Column 
import  sqlalchemy.dialects.postgresql  as pg

class UserModel(SQLModel , table  = True):
    __tablename__ :str  = "deepfake_users"
    uid : uuid.UUID = Field(sa_column = Column(pg.UUID , nullable = False , primary_key = True, default = uuid.uuid4))
    name : str 
    email : str
    password_hash : str = Field(exclude = True)
    is_verified : bool = Field(default = False)
    createdAt : datetime = Field()
    updatedAt : datetime = Field()
    def __repr__(self):
        return f'User <{self.name}>'