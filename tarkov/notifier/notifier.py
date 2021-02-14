import collections
from typing import DefaultDict, Dict, List

from .models import MailDialogueMessage


class Notifier:
    def __init__(self):
        self.notifications: DefaultDict[str, List[dict]] = collections.defaultdict(list)

    def has_notifications(self, profile_id: str) -> bool:
        return bool(self.notifications[profile_id])

    def get_notifications(self, profile_id) -> List[Dict]:
        notifications = self.notifications[profile_id]
        self.notifications[profile_id] = []
        return notifications

    def add_message_notification(self, profile_id: str, message: MailDialogueMessage) -> None:
        notification = {
            "type": "new_message",
            "eventId": message.id,
            "data": {"dialogId": message.uid, "message": message.dict()},
        }
        self.notifications[profile_id].append(notification)

    @staticmethod
    def get_empty_notification() -> dict:
        return {"type": "ping", "eventId": "ping"}


notifier_instance = Notifier()
