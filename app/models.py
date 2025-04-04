from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime
)
from app.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship


class UserModel(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    devices = relationship("DeviceModel", back_populates="user")


class DeviceModel(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    user = relationship("UserModel", back_populates="devices")
    statistics = relationship("DeviceStatisticModel", back_populates="device")


class DeviceStatisticModel(Base):
    __tablename__ = 'device_statistics'

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)

    device = relationship("DeviceModel", back_populates="statistics")

    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
