from __future__ import annotations

import time
from typing import List, cast

import ujson
from flask import request

import mods.core.lib.items as items_lib
from mods.core.lib.adapters import InventoryToRequestAdapter
from mods.core.lib.inventory import StashMap, InventoryManager, generate_item_id, Inventory
from mods.core.lib.inventory_actions import ActionType, Action, MoveAction, SplitAction, ExamineAction, MergeAction, \
    TransferAction, FoldAction, ItemRemoveAction, TradingConfirmAction, TradingSellAction, TradingAction, \
    QuestAcceptAction, ReadEncyclopediaAction
from mods.core.lib.items import MoveLocation, ItemTemplatesRepository
from mods.core.lib.trader import TraderInventory, Traders
from server import logger, root_dir


class ProfileItemsMovingDispatcher:
    def __init__(self, session_id: str):
        self.profile = Profile(session_id)

        self.inventory: Inventory
        self.inventory_adapter: InventoryToRequestAdapter

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
            ActionType.QuestAccept: self._accept_quest,
            ActionType.ReadEncyclopedia: self._read_encyclopedia,
        }

        with self.profile:
            self.inventory = self.profile.inventory
            self.inventory_adapter = InventoryToRequestAdapter(self.inventory)

            # request.data should be dict at this moment
            # noinspection PyTypeChecker
            actions: List[Action] = request.data['data']  # type: ignore

            for action in actions:
                # Log any actions into debug
                logger.debug(action)
                try:
                    method = actions_map[ActionType(action['Action'])]
                except KeyError as error:
                    action_type = action['Action']
                    logger.debug(action)
                    raise NotImplementedError(f'Action with type {action_type} not implemented') from error

                # noinspection PyArgumentList
                method(action)  # type: ignore
        return self.response

    def _accept_quest(self, action: QuestAcceptAction):
        self.profile.quests.accept_quest(action['qid'])

    def _move(self, action: MoveAction):
        item_id = action['item']
        move_location: MoveLocation = action['to']

        item = self.inventory_adapter.get_item(item_id)
        self.inventory_adapter.move_item(item, move_location)

    def _split(self, action: SplitAction):
        item_id = action['item']
        move_location: MoveLocation = action['container']
        item = self.inventory_adapter.get_item(item_id)
        new_item = self.inventory_adapter.split_item(item, move_location, action['count'])
        self.response['items']['new'].append(new_item)  # type: ignore

    def _examine(self, action: ExamineAction):
        if 'fromOwner' in action:
            if action['fromOwner']['type'] == 'Trader':
                trader_id = action['fromOwner']['id']
                item_id = action['item']

                trader_inventory = TraderInventory(Traders(trader_id), self.inventory)
                item = trader_inventory.get_item(item_id)
                self.profile.encyclopedia.examine(item)
            else:
                logger.error(f'Unhandled examine action: {action}')
        else:
            item_id = action['item']
            item = self.inventory_adapter.get_item(item_id)
            self.profile.encyclopedia.examine(item)

    def _merge(self, action: MergeAction):
        item = self.inventory_adapter.get_item(action['item'])
        with_ = self.inventory_adapter.get_item(action['with'])

        self.inventory_adapter.merge(item, with_)
        self.response['items']['del'].append(item)  # type: ignore

    def _transfer(self, action: TransferAction):
        item = self.inventory_adapter.get_item(action['item'])
        with_ = self.inventory_adapter.get_item(action['with'])
        self.inventory_adapter.transfer(item, with_, action['count'])

    def _fold(self, action: FoldAction):
        item = self.inventory_adapter.get_item(action['item'])
        self.inventory_adapter.fold(item, action['value'])

    def _remove(self, action: ItemRemoveAction):
        item = self.inventory_adapter.get_item(action['item'])
        self.inventory_adapter.remove_item(item)

    def _trading_confirm(self, action: TradingAction):
        if action['type'] == 'buy_from_trader':
            action = cast(TradingConfirmAction, action)
            self.__buy_from_trader(action)

        elif action['type'] == 'sell_to_trader':
            action = cast(TradingSellAction, action)
            self.__sell_to_trader(action)

    def __buy_from_trader(self, action: TradingConfirmAction):
        trader_id = action['tid']
        item_id = action['item_id']
        item_count = action['count']
        trader_inventory = TraderInventory(Traders(trader_id), self.inventory)
        # item = trader_inventory.get_item(item_id)

        items, children_items = trader_inventory.buy_item(item_id, item_count)
        self.inventory_adapter.add_items(children_items)
        stash_map = StashMap(self.inventory_adapter.inventory)
        for item in items:
            self.inventory_adapter.add_item(item)
            location = stash_map.find_location_for_item(item, auto_fill=True)
            item['location'] = location
            item['slotId'] = 'hideout'
            item['parentId'] = self.inventory_adapter.stash_id

        self.response['items']['new'].extend(items)  # type: ignore
        self.response['items']['new'].extend(children_items)  # type: ignore

        for scheme_item in action['scheme_items']:
            item = self.inventory_adapter.get_item(scheme_item['id'])
            item['upd']['StackObjectsCount'] -= scheme_item['count']
            if not item['upd']['StackObjectsCount']:
                self.inventory_adapter.remove_item(item)
                self.response['items']['del'].append(item)  # type: ignore
            else:
                self.response['items']['change'].append(item)  # type: ignore

        logger.debug(str(items))
        logger.debug(str(children_items))

    def __sell_to_trader(self, action: TradingSellAction):
        logger.debug(ujson.dumps(action))
        trader_id = action['tid']
        items_to_sell = action['items']
        trader_inventory = TraderInventory(Traders(trader_id), self.inventory)

        items = list(self.inventory.get_item(i['id']) for i in items_to_sell)
        price_sum = sum(trader_inventory.get_price(item) for item in items)

        self.response['items']['del'].extend(items)  # type: ignore
        self.inventory.remove_items(items)  # type: ignore

        rubles_tpl = ItemTemplatesRepository().get_template('5449016a4bdc2d6f028b456f')
        money_max_stack_size = rubles_tpl['_props']['StackMaxSize']

        while price_sum:
            stack_size = min(money_max_stack_size, price_sum)
            price_sum -= stack_size

            money_stack = items_lib.Item(
                _id=generate_item_id(),
                _tpl=items_lib.TemplateId('5449016a4bdc2d6f028b456f'),
                parentId=self.inventory.stash_id,
                slotId='hideout',
            )
            money_stack['upd'] = items_lib.ItemUpd(StackObjectsCount=stack_size)

            self.inventory.add_item(money_stack)
            self.response['items']['new'].append(money_stack)  # type: ignore

    def _read_encyclopedia(self, action: ReadEncyclopediaAction):
        for id_ in action['ids']:
            self.profile.encyclopedia.data[id_] = True


class Encyclopedia:
    def __init__(self, profile: Profile):
        self.profile = profile
        self.data = profile.pmc_profile['Encyclopedia']

    def examine(self, item: items_lib.Item):
        self.data[item['_tpl']] = True


class Quests:
    def __init__(self, profile: Profile):
        self.data = profile.quests_data

    def get_quest(self, quest_id: str):
        try:
            return next(quest for quest in self.data if quest['qid'] == quest_id)
        except StopIteration as e:
            raise KeyError from e

    def accept_quest(self, quest_id: str):
        try:
            quest = self.get_quest(quest_id)
            if quest['status'] in ('Started', 'Success'):
                raise ValueError('Quest is already accepted')
        except KeyError:
            pass

        quest = {
            'qid': quest_id,
            'startTime': int(time.time()),
            'completedConditions': [],
            'statusTimers': {},
            'status': 'Started',
        }
        self.data.append(quest)


class Profile:
    # noinspection PyTypeChecker
    def __init__(self, profile_id: str):
        self.profile_id = profile_id
        self.inventory_manager = InventoryManager(profile_id)

        self.profile_path = root_dir.joinpath('resources', 'profiles', profile_id)

        self.pmc_profile_path = self.profile_path.joinpath('pmc_profile.json')
        self.pmc_profile: dict

        self.encyclopedia: Encyclopedia

        self.inventory: Inventory

        self.quests_path = self.profile_path.joinpath('pmc_quests.json')
        self.quests_data: List[dict]
        self.quests: Quests

    def get_profile(self):
        profile_data = {}
        for file in self.profile_path.glob('pmc_*.json'):
            profile_data[file.stem] = ujson.load(file.open('r', encoding='utf8'))

        profile_base = profile_data['pmc_profile']
        profile_base['Hideout'] = profile_data['pmc_hideout']
        profile_base['Inventory'] = profile_data['pmc_inventory']
        profile_base['Quests'] = profile_data['pmc_quests']
        profile_base['Stats'] = profile_data['pmc_stats']
        profile_base['TraderStandings'] = profile_data['pmc_traders']
        return profile_base

    def __read(self):
        self.pmc_profile: dict = ujson.load(self.pmc_profile_path.open('r', encoding='utf8'))

        self.encyclopedia = Encyclopedia(profile=self)

        self.inventory = Inventory(profile_id=self.profile_id)
        self.inventory.sync()

        self.quests_data: List[dict] = ujson.load(self.quests_path.open('r', encoding='utf8'))
        self.quests = Quests(profile=self)

    def __write(self):
        ujson.dump(self.pmc_profile, self.pmc_profile_path.open('w', encoding='utf8'), indent=4)

        self.inventory.flush()

        ujson.dump(self.quests_data, self.quests_path.open('w', encoding='utf8'), indent=4)

    def __enter__(self):
        self.__read()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            raise exc_type from exc_val
        self.__write()
