from __future__ import annotations

from typing import List

import ujson
from flask import request, Blueprint

from mods.tarkov_core.functions.profile import Profile
from mods.tarkov_core.lib.inventory import Inventory, StashMap
from mods.tarkov_core.lib.inventory_actions import MoveAction, ActionType, Action, SplitAction, ExamineAction, \
    MergeAction, TransferAction, TradingConfirmAction, FoldAction, ItemRemoveAction
from mods.tarkov_core.lib.items import MoveLocation
from mods.tarkov_core.lib.trader import TraderInventory, Traders
from server import root_dir, logger
from server.utils import route_decorator

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/game/profile/items/moving', methods=['POST', 'GET'])
@route_decorator()
def client_game_profile_item_move():
    # we are grabbing body decompressed then we loop through variable body.data as []
    # then we switch() by Action key and checking what game want us to do
    session_id = request.cookies['PHPSESSID']
    profile = Profile(session_id)

    data: List[Action] = request.data
    response = {
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

    # with profile.inventory as inventory:
    inventory: Inventory = profile.inventory.inventory
    inventory.sync()

    for action in data['data']:
        action_type = ActionType(action['Action'])
        logger.debug(action)

        if action_type == ActionType.Move:
            action: MoveAction

            item_id = action['item']
            move_location: MoveLocation = action['to']

            item = inventory.get_item(item_id)
            inventory.move_item(item, move_location)

        elif action_type == ActionType.Split:
            action: SplitAction

            item_id = action['item']
            move_location: MoveLocation = action['container']
            item = inventory.get_item(item_id)
            new_item = inventory.split_item(item, move_location, action['count'])
            response['items']['new'].append(new_item)

        elif action_type == ActionType.Examine:
            action: ExamineAction

            if 'fromOwner' in action:
                pass  # TODO trader item examine
            else:
                item_id = action['item']
                item = inventory.get_item(item_id)
                inventory.examine(item)

        elif action_type == ActionType.Merge:
            action: MergeAction

            item = inventory.get_item(action['item'])
            with_ = inventory.get_item(action['with'])

            inventory.merge(item, with_)

            response['items']['del'].append(item)

        elif action_type == ActionType.Transfer:
            action: TransferAction

            item = inventory.get_item(action['item'])
            with_ = inventory.get_item(action['with'])
            inventory.transfer(item, with_, action['count'])

        elif action_type == ActionType.Fold:
            action: FoldAction

            item = inventory.get_item(action['item'])
            inventory.fold(item)

        elif action_type == ActionType.TradingConfirm:
            action: TradingConfirmAction

            if action['type'] == 'buy_from_trader':
                trader_id = action['tid']
                item_id = action['item_id']
                item_count = action['count']
                trader_inventory = TraderInventory(Traders(trader_id))
                # item = trader_inventory.get_item(item_id)

                items, children_items = trader_inventory.buy_item(item_id, item_count)
                inventory.add_items(children_items)
                stash_map = StashMap(inventory)
                for item in items:
                    inventory.add_item(item)
                    location = stash_map.find_location_for_item(item, auto_fill=True)
                    item['location'] = location
                    item['slotId'] = 'hideout'
                    item['parentId'] = inventory.stash_id

                response['items']['new'].extend(items)
                response['items']['new'].extend(children_items)

                for scheme_item in action['scheme_items']:
                    item = inventory.get_item(scheme_item['id'])
                    item['upd']['StackObjectsCount'] -= scheme_item['count']
                    if not item['upd']['StackObjectsCount']:
                        inventory.remove_item(item)
                        response['items']['del'].append(item)
                    else:
                        response['items']['change'].append(item)

                logger.debug(str(items))
                logger.debug(str(children_items))

        elif action_type == ActionType.Remove:
            action: ItemRemoveAction
            item = inventory.get_item(action['item'])
            inventory.remove_item(item)

        else:
            logger.debug(f'Action {action_type} not implemented')

    inventory.flush()
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
