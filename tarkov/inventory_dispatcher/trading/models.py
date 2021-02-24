from typing import List, Literal, Optional

from pydantic import Extra, StrictInt

from tarkov import models
from tarkov.inventory.types import ItemId
from tarkov.inventory_dispatcher.models import ActionModel


class TradingSchemeItemModel(models.Base):
    id: ItemId
    count: StrictInt
    scheme_id: Optional[int]


class Trading(ActionModel):
    class Config:
        extra = Extra.allow

    type: Literal["buy_from_trader", "sell_to_trader"]


class BuyFromTrader(Trading):
    class Config:
        extra = Extra.forbid

    tid: str
    item_id: ItemId
    count: StrictInt
    scheme_id: StrictInt
    scheme_items: List[TradingSchemeItemModel]


class SellToTrader(Trading):
    class Config:
        extra = Extra.forbid

    tid: str
    items: List[TradingSchemeItemModel]
