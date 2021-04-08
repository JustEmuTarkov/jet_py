from typing import Dict, List, Optional, Union

from fastapi.params import Cookie, Depends

from server.utils import make_router
from tarkov.dependencies import profile_manager
from tarkov.inventory.models import Item
from tarkov.inventory.types import ItemId
from tarkov.models import Base, TarkovErrorResponse, TarkovSuccessResponse
from tarkov.profile.profile import Profile
from tarkov.trader.models import TraderType
from tarkov.trader.models import BarterSchemeEntry
from tarkov.trader.trader import Trader

trader_router = make_router(tags=["Traders"])


@trader_router.post(
    "/client/trading/customization/storage",
    response_model=TarkovSuccessResponse[dict],
)
async def customization_storage(
    profile_id: Optional[str] = Cookie(alias="PHPSESSID", default=None),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    if profile_id is None:
        return TarkovErrorResponse(data="", err=True, errmsg="No session cookie provided")
    # customization_data = ujson.load(
    #     root_dir.joinpath('resources', 'profiles', profile_id, 'storage.json').open('r', encoding='utf8')
    # )
    return TarkovSuccessResponse(data={})


@trader_router.post("/client/trading/customization/{trader_id}")
async def customization(
    trader_id: str,  # pylint: disable=unused-argument
) -> TarkovSuccessResponse:
    # suits_path = db_dir.joinpath('assort', trader_id, 'suits.json')
    # if not suits_path.exists():
    #     return TarkovError(600, "This Trader Doesn't have any suits for sale")
    # profile_data = {"Info": {"Side": "Bear"}}  # TODO: After making profile handler load profile here
    # suits_data = ujson.load(suits_path.open('r', encoding='utf8'))
    # for suit in suits_data:
    #     is_suit = suit_side for suit_side in suits_data[suit]['_props']['Side']
    #       if suit_side == profile_data['Info']['Side']:
    # output is { "item._id": [[{ "_tpl": "", "count": 0 }]] }
    return TarkovSuccessResponse(data=[])


@trader_router.post(
    "/client/trading/api/getUserAssortPrice/trader/{trader_id}",
    response_model=TarkovSuccessResponse[Dict[ItemId, List[List[dict]]]],
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_user_assort_price(
    trader_id: str,
    profile: Profile = Depends(profile_manager.with_profile_readonly),  # type: ignore
) -> Union[TarkovSuccessResponse[Dict[ItemId, List[List[dict]]]], TarkovErrorResponse]:
    trader = Trader(TraderType(trader_id))
    items = {}

    for item in profile.inventory.items.values():
        if item.parent_id != profile.inventory.root_id:
            continue
        if not trader.can_sell(item):
            continue

        children_items = profile.inventory.iter_item_children_recursively(item)
        price = trader.get_sell_price(item, children_items=children_items)
        items[item.id] = [[{"_tpl": price.template_id, "count": price.amount}]]

    # TODO: Calculate price for items to sell in specified trader
    # output is { "item._id": [[{ "_tpl": "", "count": 0 }]] }
    return TarkovSuccessResponse(data=items)


@trader_router.post("/client/trading/api/getTradersList")
async def get_trader_list(
    profile: Profile = Depends(profile_manager.with_profile),  # type: ignore
) -> TarkovSuccessResponse[List[dict]]:
    response = []
    for trader_type in TraderType:
        trader = Trader(trader_type)
        trader_view = trader.view(profile)
        response.append(trader_view.base.dict(exclude_none=True))
    response.sort(key=lambda base: base["_id"])
    return TarkovSuccessResponse(data=response)


class TraderAssortResponse(Base):
    barter_scheme: Dict[ItemId, List[List[BarterSchemeEntry]]]
    items: List[Item]
    loyal_level_items: dict


@trader_router.post(
    "/client/trading/api/getTraderAssort/{trader_id}",
    response_model=TarkovSuccessResponse[TraderAssortResponse],
    response_model_exclude_none=True,
)
async def get_trader_assort(
    trader_id: str,
    profile: Profile = Depends(profile_manager.with_profile_readonly),  # type: ignore
) -> Union[TarkovSuccessResponse[TraderAssortResponse], TarkovErrorResponse]:
    trader = Trader(TraderType(trader_id))
    view = trader.view(player_profile=profile)

    assort_response = TraderAssortResponse(
        barter_scheme=view.barter_scheme.__root__,
        items=view.assort,
        loyal_level_items=view.loyal_level_items,
    )
    return TarkovSuccessResponse(data=assort_response)


@trader_router.post("/client/trading/api/getTrader/{trader_id}")
async def trading_api_get_trader(
    trader_id: str,
    profile: Profile = Depends(profile_manager.with_profile),  # type: ignore
) -> TarkovSuccessResponse[dict]:
    trader = Trader(TraderType(trader_id))
    trader_view = trader.view(player_profile=profile)
    return TarkovSuccessResponse(data=trader_view.base.dict(exclude_none=True))
