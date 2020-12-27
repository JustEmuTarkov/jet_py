from __future__ import annotations

from typing import Optional, List

import ujson
from flask import request, Blueprint

from mods.tarkov_core.functions.profile import Profile
from mods.tarkov_core.lib.inventory import StashMap
from mods.tarkov_core.lib.inventory_actions import MoveAction, ActionType, SplitAction, ExamineAction, \
    MergeAction, TransferAction, TradingConfirmAction, FoldAction, ItemRemoveAction, Action
from mods.tarkov_core.lib.items import MoveLocation
from mods.tarkov_core.lib.trader import TraderInventory, Traders
from server import root_dir, logger
from server.utils import route_decorator
from tarkov_core.lib.adapters import InventoryToRequestAdapter

blueprint = Blueprint(__name__, __name__)


class ProfileItemsMovingDispatcher:
    def __init__(self, session_id: str):
        self.profile = Profile(session_id)
        self.inventory_manager = self.profile.inventory
        self.inventory: Optional[InventoryToRequestAdapter] = None
        self.request = request
        self.response = {
            "items": {
                "new": [],
                "change": [],
                "del": []
            },
            "badRequest": [],
            "quests": [],
            "ragFairOffers": [],
            "builds": [],
            "currentSalesSums": {}
        }

    @property
    def dispatch(self) -> dict:
        actions_map = {
            ActionType.Move: self._move,
            ActionType.Split: self._split,
            ActionType.Examine: self._examine,
            ActionType.Merge: self._merge,
            ActionType.Transfer: self._transfer,
            ActionType.Fold: self._fold,
            ActionType.Remove: self._remove,
            ActionType.TradingConfirm: self._trading_confirm,
        }

        with self.inventory_manager as inventory:
            self.inventory = InventoryToRequestAdapter(inventory)

            # request.data should be dict at this moment
            # noinspection PyTypeChecker
            actions: List[Action] = request.data['data']
            for action in actions:
                try:
                    method = actions_map[ActionType(action['Action'])]
                except KeyError:
                    action_type = action['Action']
                    raise NotImplementedError(f'Action with type {action_type} not implemented')

                # noinspection PyArgumentList
                method(action)
        return self.response

    def _move(self, action: MoveAction):
        item_id = action['item']
        move_location: MoveLocation = action['to']

        item = self.inventory.get_item(item_id)
        self.inventory.move_item(item, move_location)

    def _split(self, action: SplitAction):
        item_id = action['item']
        move_location: MoveLocation = action['container']
        item = self.inventory.get_item(item_id)
        new_item = self.inventory.split_item(item, move_location, action['count'])
        self.response['items']['new'].append(new_item)

    def _examine(self, action: ExamineAction):
        if 'fromOwner' in action:
            pass  # TODO trader item examine
        else:
            item_id = action['item']
            item = self.inventory.get_item(item_id)
            self.inventory.examine(item)

    def _merge(self, action: MergeAction):
        item = self.inventory.get_item(action['item'])
        with_ = self.inventory.get_item(action['with'])

        self.inventory.merge(item, with_)
        self.response['items']['del'].append(item)

    def _transfer(self, action: TransferAction):
        item = self.inventory.get_item(action['item'])
        with_ = self.inventory.get_item(action['with'])
        self.inventory.transfer(item, with_, action['count'])

    def _fold(self, action: FoldAction):
        item = self.inventory.get_item(action['item'])
        self.inventory.fold(item, action['value'])

    def _remove(self, action: ItemRemoveAction):
        item = self.inventory.get_item(action['item'])
        self.inventory.remove_item(item)

    def _trading_confirm(self, action: TradingConfirmAction):
        if action['type'] == 'buy_from_trader':
            self.__buy_from_trader(action)

    def __buy_from_trader(self, action: TradingConfirmAction):
        trader_id = action['tid']
        item_id = action['item_id']
        item_count = action['count']
        trader_inventory = TraderInventory(Traders(trader_id))
        # item = trader_inventory.get_item(item_id)

        items, children_items = trader_inventory.buy_item(item_id, item_count)
        self.inventory.add_items(children_items)
        stash_map = StashMap(self.inventory)
        for item in items:
            self.inventory.add_item(item)
            location = stash_map.find_location_for_item(item, auto_fill=True)
            item['location'] = location
            item['slotId'] = 'hideout'
            item['parentId'] = self.inventory.stash_id

        self.response['items']['new'].extend(items)
        self.response['items']['new'].extend(children_items)

        for scheme_item in action['scheme_items']:
            item = self.inventory.get_item(scheme_item['id'])
            item['upd']['StackObjectsCount'] -= scheme_item['count']
            if not item['upd']['StackObjectsCount']:
                self.inventory.remove_item(item)
                self.response['items']['del'].append(item)
            else:
                self.response['items']['change'].append(item)

        logger.debug(str(items))
        logger.debug(str(children_items))


@blueprint.route('/client/game/profile/items/moving', methods=['POST', 'GET'])
@route_decorator()
def client_game_profile_item_move():
    dispatcher = ProfileItemsMovingDispatcher(request.cookies['PHPSESSID'])
    response = dispatcher.dispatch

    return response


@blueprint.route('/client/game/profile/list', methods=['POST', 'GET'])
@route_decorator()
def client_game_profile_list():
    session_id = request.cookies['PHPSESSID']
    profile_manager = Profile(session_id)

    pmc = profile_manager.get_profile()
    profile_dir = root_dir.joinpath('resources', 'profiles', session_id)
    scav_profile = ujson.load((profile_dir / 'character_scav.json').open('r'))

    return [
        pmc,
        scav_profile,
    ]


@blueprint.route('/client/game/profile/select', methods=['POST', 'GET'])
@route_decorator()
def client_game_profile_list_select():
    return {
        'status': 'ok',
        'notifier': {
            'server': f'{request.url_root}/',
            'channel_id': 'testChannel',
        },
    }


@blueprint.route('/client/profile/status', methods=['POST', 'GET'])
@route_decorator()
def client_profile_status():
    session_id = request.cookies['PHPSESSID']
    response = []
    for profile_type in ('scav', 'pmc'):
        response.append({
            'profileid': f'{profile_type}{session_id}',
            'status': 'Free',
            'sid': '',
            'ip': '',
            'port': 0
        })

    return response
