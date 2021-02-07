import datetime
from typing import Dict, List

import tarkov.profile
from .models import DialoguePreviewList, MailDialogue, MailDialogueMessage, MailDialogues
from .notifier import notifier_instance


class Mail:
    profile: 'tarkov.profile.Profile'
    dialogues: MailDialogues

    def __init__(self, profile: 'tarkov.profile.Profile'):
        self.profile = profile
        self.path = self.profile.profile_dir.joinpath('dialogue.json')

    def add_message(self, message: MailDialogueMessage):
        """Adds message to mail and creates notification in notifier"""
        category: MailDialogue = self.dialogues[message.uid]
        category.messages.insert(0, message)

        notifier_instance.add_message_notification(
            profile_id=self.profile.profile_id,
            message=message
        )

    def get_message(self, message_id: str) -> MailDialogueMessage:
        """Returns MailDialogueMessage by it's id"""
        for dialogue in self.dialogues.__root__.values():
            for message in dialogue.messages:
                if message.id == message_id:
                    return message
        raise IndexError(f'DialogueMessage with id {message_id} was not found.')

    def view_dialog_list(self) -> List[Dict]:
        message_previews = DialoguePreviewList.from_dialogues(self.dialogues).__root__
        return [msg_preview.dict() for msg_preview in message_previews]

    def view_dialog(self, dialogue_id: str, time_: float) -> dict:
        if time_:
            # Since we're returning all the messages at once we don't have to return anything if time was specified
            return {'messages': []}

        dialogue = self.dialogues[dialogue_id]

        # attachments_count = 0
        # for message in dialogue.messages:
        #     has_uncollected_rewards: bool = message.hasRewards and not message.rewardCollected
        #     expired: bool = self.__is_message_expired(message)
        #
        #     if has_uncollected_rewards and not expired:
        #         attachments_count += 1

        return {'messages': [msg.dict() for msg in dialogue.messages]}

    def all_attachments_view(self, dialogue_id):
        dialogue = self.dialogues[dialogue_id]

        messages = [msg.dict(exclude_none=True) for msg in dialogue.messages if not self.__is_message_expired(msg)]
        return {'messages': messages}

    def __is_message_expired(self, message: MailDialogueMessage) -> bool:
        datetime_now = datetime.datetime.now()
        message_expires_at = datetime.datetime.fromtimestamp(message.dt + message.maxStorageTime)
        return datetime_now > message_expires_at

    def read(self):
        self.dialogues = MailDialogues.parse_file(self.path)

    def write(self):
        with self.path.open('w', encoding='utf8') as file:
            file.write(self.dialogues.json(by_alias=True, exclude_unset=False, exclude_none=True, indent=4))
