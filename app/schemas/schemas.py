from pydantic import BaseModel
from typing import Optional
from pydantic import ConfigDict


class UserCreateSchema(BaseModel):
    name: str


class DeviceStatisticSchema(BaseModel):
    x: Optional[float]
    y: Optional[float]
    z: Optional[float]
    device_id: int

    model_config = ConfigDict(from_attributes=True)


class DeviceSchema(BaseModel):
    name: str
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class UserSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class DeviceOutSchema(BaseModel):
    id: int
    name: str
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class BaseResponse(BaseModel):
    ok: bool


class CreatedResponse(BaseResponse):
    id: int


class AxisStatisticSchema(BaseModel):
    min: Optional[float]
    max: Optional[float]
    count: int
    sum: Optional[float]
    median: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class FullStatisticsResponse(BaseModel):
    x: AxisStatisticSchema
    y: AxisStatisticSchema
    z: AxisStatisticSchema

    model_config = ConfigDict(from_attributes=True)
