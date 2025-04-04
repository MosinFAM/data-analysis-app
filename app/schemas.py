from pydantic import BaseModel


class UserCreateSchema(BaseModel):
    name: str


class DeviceStatisticSchema(BaseModel):
    x: float
    y: float
    z: float
    device_id: int


class DeviceSchema(BaseModel):
    name: str
    user_id: int


class UserSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class DeviceOutSchema(BaseModel):
    id: int
    name: str
    user_id: int

    class Config:
        orm_mode = True
