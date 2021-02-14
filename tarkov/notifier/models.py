import datetime
import time
from typing import Dict, List

from pydantic import Field, StrictBool, StrictInt

from tarkov.inventory import generate_item_id, regenerate_items_ids
from tarkov.inventory.models import Item
from tarkov.models import Base


class MailMessageItems(Base):
    stash: str = Field(default_factory=generate_item_id)  # Stash (root) id
    data: List[Item] = Field(default_factory=list)  # List of items in message

    @staticmethod
    def from_items(items: List[Item]):
        stash_id = generate_item_id()

        for item in items:
            if not item.parent_id:
                item.parent_id = stash_id
            if not item.slotId:
                item.slotId = "main"

        regenerate_items_ids(items)

        return MailMessageItems(
            stash=stash_id,
            data=items,
        )


class MailDialogueMessage(Base):
    class Config:
        fields = {
            "id": "_id",
        }

    id: str = Field(default_factory=generate_item_id)  # Message id
    uid: str  # Trader id (Same as MailDialogue id)
    type: StrictInt
    dt: float = Field(default_factory=time.time)  # Send datetime
    templateId: str  # Locale template id
    hasRewards: StrictBool = False
    rewardCollected: StrictBool = False
    items: MailMessageItems = Field(
        default_factory=MailMessageItems
    )  # Empty if it has no items
    maxStorageTime: int = StrictInt(
        datetime.timedelta(days=3).total_seconds()
    )  # Storage time in seconds
    systemData: dict = Field(default_factory=dict)


class MailDialogue(Base):
    class Config:
        fields = {
            "id": "_id",
        }

    id: str  # Trader id
    messages: List[MailDialogueMessage] = Field(
        default_factory=list
    )  # List of messages in this dialogue
    pinned: StrictBool = False
    new: int = 0
    attachmentsNew: int = 0


class MailDialogues(Base):
    __root__: Dict[str, MailDialogue] = Field(default_factory=dict)

    def __getitem__(self, trader_id: str) -> MailDialogue:
        return self.__root__[trader_id]

    def __setitem__(self, trader_id: str, dialogue: MailDialogue) -> None:
        self.__root__[trader_id] = dialogue

    def items(self):
        return self.__root__.items()


class MailMessagePreview(Base):
    dt: float
    type: StrictInt
    templateId: str
    uid: str

    @staticmethod
    def from_dialogue(dialogue: MailDialogue) -> "MailMessagePreview":
        last_message = dialogue.messages[-1]
        return MailMessagePreview(
            dt=last_message.dt,
            type=last_message.type,
            templateId=last_message.templateId,
            uid=dialogue.id,
        )


class MailDialoguePreview(Base):
    class Config:
        fields = {
            "id": "_id",
        }

    id: str
    message: MailMessagePreview
    pinned: StrictBool
    new: int
    attachmentsNew: int
    type: int = 2

    @staticmethod
    def from_dialogue(dialogue: MailDialogue) -> "MailDialoguePreview":
        return MailDialoguePreview(
            id=dialogue.id,
            message=MailMessagePreview.from_dialogue(dialogue),
            pinned=dialogue.pinned,
            new=dialogue.new,
            attachmentsNew=dialogue.attachmentsNew,
        )


class DialoguePreviewList(Base):
    __root__: List[MailDialoguePreview]

    @staticmethod
    def from_dialogues(dialogue_list: MailDialogues) -> "DialoguePreviewList":
        dialogues = [d for d in dialogue_list.__root__.values() if d.messages]
        return DialoguePreviewList(
            __root__=[MailDialoguePreview.from_dialogue(d) for d in dialogues]
        )
