from __future__ import annotations

import datetime
import enum
import time
from typing import Dict, ItemsView, List

from pydantic import Field, StrictBool, StrictInt

from tarkov.inventory.helpers import (
    clean_items_relationships,
    generate_item_id,
    regenerate_items_ids,
)
from tarkov.inventory.models import Item
from tarkov.models import Base
from tarkov.trader.types import TraderId


class MailMessageItems(Base):
    stash: str = Field(default_factory=generate_item_id)  # Stash (root) id
    data: List[Item] = Field(default_factory=list)  # List of items in message

    @classmethod
    def from_items(cls, items: List[Item]) -> MailMessageItems:
        """
        Creates MailMessageItems from list of items
        """
        # We have to remove parent_id and slot_id
        # from items that have no parent in this list of items.
        items = clean_items_relationships(items)

        stash_id = generate_item_id()
        for item in items:
            if not item.parent_id:
                item.parent_id = stash_id
            if not item.slot_id:
                item.slot_id = "main"
                item.location = None

        regenerate_items_ids(items)
        return cls(
            stash=stash_id,
            data=items,
        )


class MailDialogueMessage(Base):
    """
    Represents single message in MailDialogue
    """

    id: str = Field(alias="_id", default_factory=generate_item_id)  # Message id
    uid: TraderId  # Trader id (Same as parent MailDialogue id)
    type: int
    dt: float = Field(default_factory=time.time)  # Timestamp when message was sent
    templateId: str  # Locale template id
    hasRewards: StrictBool = False
    rewardCollected: StrictBool = False
    items: MailMessageItems = Field(
        default_factory=MailMessageItems
    )  # Items bound to message
    maxStorageTime: int = StrictInt(
        datetime.timedelta(days=3).total_seconds()
    )  # Storage time in seconds
    systemData: dict = Field(default_factory=dict)

    @property
    def arrived(self) -> bool:
        return time.time() > self.dt


class MailDialogue(Base):
    """
    Dialogues with specific trader e.g. Ragman, Prapor.
    """

    id: str = Field(alias="_id")  # Trader id
    messages: List[MailDialogueMessage] = Field(
        default_factory=list
    )  # List of messages in this dialogue
    pinned: StrictBool = False
    new: int = 0
    attachmentsNew: int = 0


class MailDialogues(Base):
    """
    Dictionary with all the dialogues with trader id's as keys
    """

    __root__: Dict[str, MailDialogue] = Field(default_factory=dict)

    def __getitem__(self, trader_id: str) -> MailDialogue:
        return self.__root__[trader_id]

    def __setitem__(self, trader_id: str, dialogue: MailDialogue) -> None:
        self.__root__[trader_id] = dialogue

    def __contains__(self, trader_id: str) -> bool:
        return trader_id in self.__root__

    def items(self) -> ItemsView[str, MailDialogue]:
        return self.__root__.items()


class MailMessagePreview(Base):
    dt: float
    type: int
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


class MailMessageType(enum.Enum):
    UserMessage = 1
    NpcTraderMessage = 2
    AuctionMessage = 3
    FleamarketMessage = 4
    AdminMessage = 5
    GroupChatMessage = 6
    SystemMessage = 7
    InsuranceReturn = 8
    GlobalChat = 9
    QuestStart = 10
    QuestFail = 11
    QuestSuccess = 12
    MessageWithItems = 13
