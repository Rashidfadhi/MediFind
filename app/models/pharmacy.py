# SQLAlchemy Pharmacy model
from sqlalchemy import Column,Integer,String,Float, Boolean, ForeignKey
from app.database import Base

class Pharmacy(Base):
    __tablename__ = 'pharmacies'

    id = Column(Integer, primary_key = True,  index = True)
    name = Column(String(100), nullable = False)
    address = Column(String(255) , nullable = False)
    landmark = Column(String(255), nullable=True)
    phone = Column(String(20),  nullable = False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    latitude = Column(Float,nullable=True )
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default = True, nullable=False)
    owner_id = Column(Integer,ForeignKey("users.id"),nullable=True,unique=True)
    