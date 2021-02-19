from __future__ import annotations

import datetime
from typing import Dict, List, TYPE_CHECKING

from server.utils import atomic_write
from tarkov.mail.models import (
    DialoguePreviewList,
    MailDialogue,
    MailDialogueMessage,
    MailDialoguePreview,
    MailDialogues,
)
from tarkov.notifier.notifier import notifier_instance

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.profile import Profile


class MailView:
    mail: Mail

    def __init__(self, mail: Mail):
        self.mail = mail

    def view_dialogue_preview_list(self) -> List[Dict]:
        dialogues_previews = DialoguePreviewList.from_dialogues(self.mail.dialogues).__root__
        return [dialogue_preview.dict() for dialogue_preview in dialogues_previews]

    def view_dialog_preview(self, dialogue_id: str) -> dict:
        dialogue = self.mail.get_dialogue(dialogue_id)
        return MailDialoguePreview.from_dialogue(dialogue).dict(exclude_none=True)

    def view_dialog(self, dialogue_id: str, time_: float) -> dict:
        if time_:
            # Since we're returning all the messages at once we don't have to return anything if time was specified
            return {"messages": []}

        dialogue = self.mail.get_dialogue(dialogue_id)

        # attachments_count = 0
        # for message in dialogue.messages:
        #     has_uncollected_rewards: bool = message.hasRewards and not message.rewardCollected
        #     expired: bool = self.__is_message_expired(message)
        #
        #     if has_uncollected_rewards and not expired:
        #         attachments_count += 1

        return {"messages": [msg.dict() for msg in dialogue.messages]}

    def all_attachments_view(self, dialogue_id: str) -> dict:
        dialogue = self.mail.get_dialogue(dialogue_id)

        messages = [
            msg.dict(exclude_none=True) for msg in dialogue.messages if not self.mail.is_message_expired(msg)
        ]
        return {"messages": messages}


class Mail:
    profile: "Profile"
    dialogues: MailDialogues
    view: MailView

    def __init__(self, profile: Profile):
        self.profile = profile
        self.view = MailView(mail=self)
        self.path = self.profile.profile_dir.joinpath("dialogue.json")

    def get_dialogue(self, trader_id: str) -> MailDialogue:
        """Returns trader dialogue by trader id"""
        try:
            return self.dialogues[trader_id]
        except KeyError:
            dialogue = MailDialogue(id=trader_id)
            self.dialogues[trader_id] = dialogue
            return dialogue

    def add_message(self, message: MailDialogueMessage) -> None:
        """Adds message to mail and creates notification in notifier"""
        category: MailDialogue = self.get_dialogue(message.uid)
        category.messages.insert(0, message)

        notifier_instance.add_message_notification(profile_id=self.profile.profile_id, message=message)

    def get_message(self, message_id: str) -> MailDialogueMessage:
        """Returns MailDialogueMessage by it's id"""
        for dialogue in self.dialogues.__root__.values():
            for message in dialogue.messages:
                if message.id == message_id:
                    return message
        raise IndexError(f"DialogueMessage with id {message_id} was not found.")

    @staticmethod
    def is_message_expired(message: MailDialogueMessage) -> bool:
        datetime_now = datetime.datetime.now()
        message_expires_at = datetime.datetime.fromtimestamp(message.dt + message.maxStorageTime)
        return datetime_now > message_expires_at

    def read(self) -> None:
        try:
            self.dialogues = MailDialogues.parse_file(self.path)
        except FileNotFoundError:
            self.dialogues = MailDialogues()

    def write(self) -> None:
        atomic_write(
            self.dialogues.json(by_alias=True, exclude_unset=False, exclude_none=True, indent=4),
            self.path,
        )
