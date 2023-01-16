import datetime

from sqlalchemy import Column, DateTime, func

from bot.db import Base


class BaseModel(Base):
    __abstract__ = True


class TimedBaseModel(BaseModel):
    __abstract__ = True

    created_at = Column(DateTime(True), server_default=func.now())
    updated_at = Column(
        DateTime(True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        server_default=func.now(),
    )
