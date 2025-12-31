from typing import Annotated
from annotated_types import Ge, Le
from pydantic import BaseModel, ConfigDict, StringConstraints

# ---------- Reusable type aliases ----------
ChannelStr = Annotated[str, StringConstraints(min_length=1, max_length=100)]
MessageStr = Annotated[str, StringConstraints(min_length=1, max_length=2000)]
StatusStr = Annotated[str, StringConstraints(min_length=1, max_length=32)]


class NotificationCreate(BaseModel):
    user_id: int
    channel: ChannelStr
    message: MessageStr


class NotificationRead(BaseModel):
    id: int
    status: StatusStr

    model_config = ConfigDict(from_attributes=True)