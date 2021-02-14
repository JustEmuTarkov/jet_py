import enum
from typing import List, Optional

from pydantic import Field, StrictBool, StrictInt

from tarkov._repositories.categories import CategoryId
from tarkov.inventory.models import Item
from tarkov.inventory.types import ItemId, TemplateId
from tarkov.models import Base


class SortType(enum.Enum):
    Id = 0
    MerchantRating = 3
    OfferTitle = 4
    Price = 5
    ExpiresIn = 6


class FleaMarketRequest(Base):
    buildCount: StrictInt
    buildItems: dict  # Don't know the type yet
    conditionFrom: StrictInt
    conditionTo: StrictInt
    currency: StrictInt
    handbookId: CategoryId
    limit: StrictInt
    linkedSearchId: str
    neededSearchId: str
    offerOwnerType: StrictInt
    oneHourExpiration: StrictBool
    onlyFunctional: StrictBool
    page: StrictInt
    priceFrom: StrictInt
    priceTo: StrictInt
    quantityFrom: StrictInt
    quantityTo: StrictInt
    reload: StrictInt
    removeBartering: StrictBool
    sortDirection: StrictInt
    sortType: StrictInt
    tm: StrictInt
    updateOfferCount: StrictBool


class FleaUser(Base):
    id: str
    memberType: StrictInt
    nickname: str
    rating: float
    isRatingGrowing: bool = True
    avatar: str


class OfferRequirement(Base):
    template_id: TemplateId = Field(alias="_tpl")
    count: int

    level: Optional[int]
    side: Optional[str]


class Offer(Base):
    id: str = Field(alias="_id")
    intId: int
    user: FleaUser
    root: ItemId
    items: List[Item]
    itemsCost: int
    requirements: List[OfferRequirement]
    requirementsCost: int
    summaryCost: int
    sellInOnePiece: bool
    startTime: int
    endTime: int
    priority: bool = False
    loyaltyLevel: int = 0

    @property
    def root_item(self) -> Item:
        return next(item for item in self.items if item.id == self.root)


class FleaMarketResponse(Base):
    offers: List[Offer] = Field(default_factory=list)
    categories: dict
    offersCount: int
    selectedCategory: str
