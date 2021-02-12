from typing import Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException
from fastapi.params import Cookie

from tarkov.inventory.models import Item, ItemId
from tarkov.models import Base, TarkovErrorResponse, TarkovSuccessResponse
from tarkov.profile import Profile
from tarkov.trader import TraderInventory, TraderType, get_trader_base, get_trader_bases
from tarkov.trader.models import BarterSchemeEntry

trader_router = APIRouter(prefix='', tags=['Traders'])


@trader_router.post(
    '/client/trading/customization/storage',
    response_model=TarkovSuccessResponse[dict],
)
def customization_storage(
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None)  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    if profile_id is None:
        return TarkovErrorResponse(
            data='',
            err=True,
            errmsg='No session cookie provided'
        )
    # customization_data = ujson.load(
    #     root_dir.joinpath('resources', 'profiles', profile_id, 'storage.json').open('r', encoding='utf8')
    # )
    return TarkovSuccessResponse(data={})


@trader_router.post('/client/trading/customization/{trader_id}')
def customization(trader_id: str):  # pylint: disable=unused-argument
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
    '/client/trading/api/getUserAssortPrice/trader/{trader_id}',
    response_model=TarkovSuccessResponse[Dict[ItemId, List[List[dict]]]],
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
def get_user_assort_price(
        trader_id: str,
        profile_id: Optional[str] = Cookie('', alias='PHPSESSID'),  # type: ignore
) -> TarkovSuccessResponse[Dict[ItemId, List[List[dict]]]]:
    if profile_id is None:
        return TarkovErrorResponse(errmsg="Profile id is None", data=None)

    if not Profile.exists(profile_id):
        raise HTTPException(status_code=404, detail=fr'Profile with id {profile_id} was not found')

    with Profile(profile_id) as player_profile:
        trader_inventory = TraderInventory(TraderType(trader_id), profile=player_profile)
        items = {}
        for item in player_profile.inventory.items:
            if not trader_inventory.can_sell(item):
                continue

            price = trader_inventory.get_sell_price(item)
            items[item.id] = [[{'_tpl': '5449016a4bdc2d6f028b456f', 'count': price}]]

        # TODO: Calculate price for items to sell in specified trader
        # output is { "item._id": [[{ "_tpl": "", "count": 0 }]] }
    return TarkovSuccessResponse(data=items)


@trader_router.post('/client/trading/api/getTradersList')
def get_trader_list() -> TarkovSuccessResponse[List[dict]]:
    return TarkovSuccessResponse(
        data=get_trader_bases()
    )


class TraderAssortResponse(Base):
    barter_scheme: Dict[ItemId, List[List[BarterSchemeEntry]]]
    items: List[Item]
    loyal_level_items: dict


@trader_router.post(
    '/client/trading/api/getTraderAssort/{trader_id}',
    response_model=TarkovSuccessResponse[TraderAssortResponse],
    response_model_exclude_none=True,
)
def get_trader_assort(
        trader_id: str,
        # profile_id: Optional[str] = Cookie(None, alias='PHPSESSID'),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    # if profile_id is None:
    #     return TarkovErrorResponse.profile_id_is_none()

    # with Profile(profile_id) as profile:
    with Profile('AID8131647517931710690RF') as profile:
        trader_inventory = TraderInventory(TraderType(trader_id), profile=profile)
        assort_response = TraderAssortResponse(
            barter_scheme=trader_inventory.barter_scheme.__root__,
            items=trader_inventory.assort,
            loyal_level_items=trader_inventory.loyal_level_items
        )
        return TarkovSuccessResponse(data=assort_response)


@trader_router.post('/client/trading/api/getTrader/{trader_id}')
def trader_base(trader_id: str) -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(
        data=get_trader_base(trader_id=trader_id)
    )
