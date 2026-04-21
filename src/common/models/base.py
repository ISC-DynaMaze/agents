from pydantic import BaseModel


class Base(BaseModel):
    type: str


class RequestBase(Base):
    pass


class ResponseBase(Base):
    pass
