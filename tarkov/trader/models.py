from dataclasses import dataclass
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Literal,
    NamedTuple,
    Optional,
    ValuesView,
)

from pydantic import Field, StrictBool

from tarkov.inventory.models import Item
from tarkov.inventory.types import ItemId, TemplateId
from tarkov.models import Base
from tarkov.repositories.categories import CategoryId


class TraderType(Enum):
    Mechanic = "5a7c2eca46aef81a7ca2145d"
    Ragman = "5ac3b934156ae10c4430e83c"
    Jaeger = "5c0647fdd443bc2504c2d371"
    Prapor = "54cb50c76803fa8b248b4571"
    Therapist = "54cb57776803fa99248b456e"
    Fence = "579dc571d53a0658a154fbec"
    Peacekeeper = "5935c25fb3acc3127c3d8cd9"
    Skier = "58330581ace78e27b8b10cee"


@dataclass
class Price:
    template_id: TemplateId
    amount: int


class BoughtItems(NamedTuple):
    item: Item
    children_items: List[Item]


class ItemInsurance(Base):
    item_id: ItemId = Field(alias="itemId")
    trader_id: str = Field(alias="tid")


class TraderLoyaltyLevel(Base):
    min_level: int = Field(alias="minLevel")
    min_sales_sum: int = Field(alias="minSalesSum")
    minStanding: float = Field(alias="minStanding")

    heal_price_coef: Optional[float] = None
    buy_price_coef: Optional[float] = None
    exchange_price_coef: Optional[float] = None
    insurance_price_coef: Optional[float] = None
    repair_price_coef: Optional[float] = None


class TraderStanding(Base):
    current_level: int = Field(alias="currentLevel")
    current_standing: float = Field(alias="currentStanding")
    current_sales_sum: int = Field(alias="currentSalesSum")
    next_loyalty: Any = Field(alias="NextLoyalty", const=None)
    loyalty_levels: Dict[Literal["0", "1", "2", "3"], TraderLoyaltyLevel] = Field(alias="loyaltyLevels")
    display: Optional[StrictBool] = None
    current_loyalty: Optional[float] = Field(alias="CurrentLoyalty", default=None)


class TraderInsurance(Base):
    availability: StrictBool
    min_payment: int
    min_return_hour: int
    max_return_hour: int
    max_storage_time: int
    excluded_category: list


class TraderRepair(Base):
    availability: StrictBool
    quality: str
    excluded_id_list: list
    excluded_category: list
    currency: Optional[TemplateId]
    currency_coefficient: Optional[int]
    price_rate: int


class TraderBase(Base):
    id: str = Field(alias="_id")
    working: StrictBool
    customization_seller: StrictBool
    name: str
    surname: str
    nickname: str
    location: str
    avatar: str
    balance_rub: int
    balance_dol: int
    balance_eur: int
    display: StrictBool
    discount: int
    discount_end: int
    buyer_up: StrictBool
    currency: Literal["RUB", "USD", "EUR"]
    supply_next_time: int
    medic: bool = False

    grid_height: int = Field(alias="gridHeight")

    repair: TraderRepair
    insurance: TraderInsurance
    loyalty: TraderStanding
    sell_category: List[CategoryId]


class BarterSchemeEntry(Base):
    count: int
    item_required: TemplateId = Field(alias="_tpl")
    level: Optional[int] = None
    side: Optional[str] = None


class BarterScheme(Base):
    __root__: Dict[ItemId, List[List[BarterSchemeEntry]]] = Field(default_factory=dict)

    def __getitem__(self, item_id: ItemId) -> List[List[BarterSchemeEntry]]:
        return self.__root__[item_id]

    def __setitem__(self, key: ItemId, value: List[List[BarterSchemeEntry]]) -> None:
        self.__root__[key] = value

    def values(self) -> ValuesView[List[List[BarterSchemeEntry]]]:
        return self.__root__.values()
