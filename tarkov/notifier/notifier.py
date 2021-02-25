from __future__ import annotations

import collections
from datetime import datetime
from typing import DefaultDict, Dict, List, Optional, TYPE_CHECKING

from tarkov.mail.models import MailDialogueMessage
from .models import MessageNotification, MessageNotificationData

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.profile import Profile


class ProfileNotifier:
    """Notifier for a profile"""

    def __init__(self, profile: Optional[Profile]):
        self.unsent_notifications: List[MessageNotification] = []

        if profile is None:
            return
        self.__add_profile_notifications(profile)

    def __add_profile_notifications(self, profile: Profile) -> None:
        now = datetime.now()
        for dialogue in profile.mail.dialogues.__root__.values():
            for msg in dialogue.messages:
                if datetime.fromtimestamp(msg.dt) < now:
                    # Message already should be sent
                    continue

                notification = MessageNotification(
                    event_id=msg.id,
                    data=MessageNotificationData(dialogue_id=msg.uid, message=msg),
                )
                self.unsent_notifications.append(notification)

    @property
    def has_new_notifications(self) -> bool:
        return bool(
            [notification for notification in self.unsent_notifications if notification.data.message.arrived]
        )

    def notifications_ready_to_send_view(self) -> List[dict]:
        messages_ready_to_send = [
            notification.dict(exclude_none=True)
            for notification in self.unsent_notifications
            if notification.data.message.arrived
        ]
        self.unsent_notifications = [
            notification for notification in self.unsent_notifications if not notification.data.message.arrived
        ]

        return messages_ready_to_send

    def add_mail_notification(self, notification: MessageNotification) -> None:
        self.unsent_notifications.append(notification)


class Notifier:
    """Notifier that contains multiple Profile Notifiers"""

    def __init__(self) -> None:
        self.notifications: DefaultDict[str, ProfileNotifier] = collections.defaultdict(
            lambda: ProfileNotifier(None)
        )

    def has_notifications(self, profile_id: str) -> bool:
        return self.notifications[profile_id].has_new_notifications

    def get_notifications_view(self, profile_id: str) -> List[Dict]:
        profile_notifier = self.notifications[profile_id]
        return profile_notifier.notifications_ready_to_send_view()

    def add_message_notification(self, profile_id: str, message: MailDialogueMessage) -> None:
        notification = MessageNotification(
            event_id=message.id,
            data=MessageNotificationData(dialogue_id=message.uid, message=message),
        )
        self.notifications[profile_id].add_mail_notification(notification)

    @staticmethod
    def get_empty_notification() -> dict:
        return {"type": "ping", "eventId": "ping"}


notifier_instance = Notifier()
