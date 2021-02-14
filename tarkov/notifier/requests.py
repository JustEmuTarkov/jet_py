from pydantic import BaseModel, Field


class MailDialogViewRequest(BaseModel):
    type: int
    dialogue_id: str = Field(alias="dialogId")
    limit: int
    time: float


class GetAllAttachmentsRequest(BaseModel):
    dialogue_id: str = Field(alias="dialogId")
