from sqlalchemy import Column,Integer, String
from app.database import Base

class User(Base): # Parent class for database models
    __tablename__ = 'users'

    id = Column(Integer, primary_key = True, index = True)
    name = Column(String(100), nullable = False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    role = Column(String(20), default="customer", nullable=False)


#SQLAlchemy applies the default role of customer.