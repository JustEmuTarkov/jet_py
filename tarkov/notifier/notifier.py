from __future__ import annotations

import collections
from datetime import datetime
from typing import DefaultDict, Dict, List, Optional, TYPE_CHECKING

from tarkov.mail.models import MailDialogueMessage
from .models import MessageNotification, MessageNotificationData

if TYPE_CHECKING:
    from tarkov.profile import Profile


class ProfileNotifier:
    """Notifier for a profile"""

    def __init__(self, profile: Optional[Profile]):
        self.unsent_notifications: List[MessageNotification] = []

        if profile is None:
            return
        self.__add_profile_notifications(profile)

    def __add_profile_notifications(self, profile: Profile):
        now = datetime.now()
        for dialogue in profile.notifier.dialogues.__root__.values():
            for msg in dialogue.messages:
                if datetime.fromtimestamp(msg.dt) < now:
                    # Message already should be sent
                    continue

                notification = MessageNotification(
                    event_id=msg.id,
                    data=MessageNotificationData(dialogue_id=msg.uid, message=msg),
                )
                self.unsent_notifications.append(notification)

    @staticmethod
    def ready_to_send(notification: MessageNotification, now: datetime):
        print(now, datetime.fromtimestamp(notification.data.message.dt))
        return now > datetime.fromtimestamp(notification.data.message.dt)

    @property
    def has_new_notifications(self) -> bool:
        now = datetime.now()
        return bool(
            [
                notification
                for notification in self.unsent_notifications
                if self.ready_to_send(notification, now)
            ]
        )

    def notifications_ready_to_send_view(self) -> List[dict]:
        now = datetime.now()
        messages_ready_to_send = [
            notification.dict(exclude_none=True)
            for notification in self.unsent_notifications
            if self.ready_to_send(notification, now)
        ]
        self.unsent_notifications = [
            notification
            for notification in self.unsent_notifications
            if not self.ready_to_send(notification, now)
        ]

        return messages_ready_to_send

    def add_mail_notification(self, notification: MessageNotification):
        self.unsent_notifications.append(notification)


class Notifier:
    """Notifier that contains multiple Profile Notifiers"""

    def __init__(self):
        self.notifications: DefaultDict[str, ProfileNotifier] = collections.defaultdict(
            lambda: ProfileNotifier(None)
        )

    def has_notifications(self, profile_id: str) -> bool:
        return self.notifications[profile_id].has_new_notifications

    def get_notifications_view(self, profile_id) -> List[Dict]:
        profile_notifier = self.notifications[profile_id]
        return profile_notifier.notifications_ready_to_send_view()

    def add_message_notification(
        self, profile_id: str, message: MailDialogueMessage
    ) -> None:
        notification = MessageNotification(
            event_id=message.id,
            data=MessageNotificationData(dialogue_id=message.uid, message=message),
        )
        self.notifications[profile_id].add_mail_notification(notification)

    @staticmethod
    def get_empty_notification() -> dict:
        return {"type": "ping", "eventId": "ping"}


notifier_instance = Notifier()
