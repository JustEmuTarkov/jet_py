import enum
from typing import NewType

ItemId = NewType("ItemId", str)
TemplateId = NewType("TemplateId", str)


class CurrencyEnum(enum.Enum):
    USD = "5696686a4bdc2da3298b456a"
    RUB = "5449016a4bdc2d6f028b456f"
    EUR = "569668774bdc2da2298b4568"
