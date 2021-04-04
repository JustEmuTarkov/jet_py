from pydantic import Field

from tarkov.mail.models import MailDialogueMessage
from tarkov.models import Base


class MessageNotificationData(Base):
    """Model bound to MessageNotification"""

    dialogue_id: str = Field(alias="dialogId")
    message: MailDialogueMessage


class MessageNotification(Base):
    """Notification for a mail message"""

    type: str = "new_message"
    event_id: str = Field(alias="eventId")
    data: MessageNotificationData
