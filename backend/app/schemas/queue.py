import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import EntryStatus


class JoinRequest(BaseModel):
    email: EmailStr


class CallRequest(BaseModel):
    counter_id: uuid.UUID


class EntryResponse(BaseModel):
    # from_attributes: lets Pydantic read a SQLAlchemy object, not just a dict.
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    position: int
    status: EntryStatus


class CalledEntryResponse(EntryResponse):
    # Staff-facing: they need the email to call the person out loud.
    email: EmailStr
