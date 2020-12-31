from typing import Optional, List

import ujson
from flask import request

import lib.items as items_lib
from functions.items import item_templates_repository
from lib.adapters import InventoryToRequestAdapter
from lib.inventory import StashMap, InventoryManager, generate_item_id
from lib.inventory_actions import ActionType, Action, MoveAction, SplitAction, ExamineAction, MergeAction, \
    TransferAction, FoldAction, ItemRemoveAction, TradingConfirmAction, TradingSellAction, TradingAction
from lib.items import MoveLocation
from lib.trader import TraderInventory, Traders
from server import logger, root_dir


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
                except KeyError as error:
                    action_type = action['Action']
                    raise NotImplementedError(f'Action with type {action_type} not implemented') from error

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

    def _trading_confirm(self, action: TradingAction):
        if action['type'] == 'buy_from_trader':
            action: TradingConfirmAction
            self.__buy_from_trader(action)

        elif action['type'] == 'sell_to_trader':
            action: TradingSellAction
            self.__sell_to_trader(action)

    def __buy_from_trader(self, action: TradingConfirmAction):
        trader_id = action['tid']
        item_id = action['item_id']
        item_count = action['count']
        trader_inventory = TraderInventory(Traders(trader_id))
        # item = trader_inventory.get_item(item_id)

        items, children_items = trader_inventory.buy_item(item_id, item_count)
        self.inventory.add_items(children_items)
        stash_map = StashMap(self.inventory.inventory)
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

    def __sell_to_trader(self, action: TradingSellAction):
        logger.debug(ujson.dumps(action))
        trader_id = action['tid']
        items_to_sell = action['items']
        trader_inventory = TraderInventory(Traders(trader_id))

        with self.inventory_manager as player_inventory:
            items = list(player_inventory.get_item(i['id']) for i in items_to_sell)
            price_sum = sum(trader_inventory.get_price(item) for item in items)

            self.response['items']['del'].extend(items)
            for item in items:
                player_inventory.remove_item(item)

            rubles_tpl = item_templates_repository.get_template('5449016a4bdc2d6f028b456f')
            money_max_stack_size = rubles_tpl['_props']['StackMaxSize']

            stash_map = StashMap(player_inventory)
            while price_sum:
                stack_size = min(money_max_stack_size, price_sum)
                price_sum -= stack_size

                money_stack = items_lib.Item(
                    _id=generate_item_id(),
                    _tpl=items_lib.TemplateId('5449016a4bdc2d6f028b456f'),
                    parentId=player_inventory.stash_id,
                    slotId='hideout',
                )
                money_stack['upd'] = items_lib.ItemUpd(StackObjectsCount=stack_size)
                money_stack['location'] = stash_map.find_location_for_item(money_stack, auto_fill=True)
                player_inventory.add_item(money_stack)
                self.response['items']['new'].append(money_stack)

        # TODO loop through items_to_sell get its "id" find it in the inventory then get data from items.json database
        # (or templates.items to get price of item) lower down the price by some global variable in the server and
        # remove them by adding them to del into response
        # we need to search if by selling items we have a space for money (yes we still counting previous items as used
        # space ... this is stupid but that's how bsg is like... we can try to redo this and try to place money in used
        # space by sell'd items)
        # disclaimer: price must be matching: getUserAssortPrice response number
        # make sure to also count items in main item slots like attachments etc. (maybe lower overall price for that so
        # it wont be overpowered)


class Profile:
    def __init__(self, profile_id: str):
        self.profile_id = profile_id
        self.inventory = InventoryManager(profile_id)

        self.profiles_path = root_dir.joinpath('resources', 'profiles')
        #
        # profiles_path = root_dir.joinpath('resources', 'profiles')
        # profile_paths = set(profiles_path.glob('*'))
        # profile_data = {}
        # for profile_id in profile_paths:
        #     single_dir = set(profiles_path.joinpath(profile_id).glob('pmc_*.json'))
        #     profile_data[profile_id.stem] = {file.stem: ujson.load(file.open('r', encoding='utf8')) for file in
        #                                      single_dir}
        # self.profiles = profile_data

    def get_profile(self):
        profile_data = {}
        for file in self.profiles_path.joinpath(self.profile_id).glob('pmc_*.json'):
            profile_data[file.stem] = ujson.load(file.open('r', encoding='utf8'))

        profile_base = profile_data['pmc_profile']
        profile_base['Hideout'] = profile_data['pmc_hideout']
        profile_base['Inventory'] = profile_data['pmc_inventory']
        profile_base['Quests'] = profile_data['pmc_quests']
        profile_base['Stats'] = profile_data['pmc_stats']
        profile_base['TraderStandings'] = profile_data['pmc_traders']
        return profile_base

    #
    # def save_profile(self, profile_id):
    #     saving_profile_path = root_dir.joinpath('resources', 'profiles', profile_id)
    #     pmc_data_field_names = ['profile', 'hideout', 'inventory', 'quests', 'stats', 'traders']
    #     for field in pmc_data_field_names:
    #         ujson.dump(self.profiles[profile_id][f"pmc_{field}"], saving_profile_path.joinpath(f"pmc_{field}.json"))
    #
    # # just for testing
    # def get_all_profiles(self):
    #     return self.profiles
    #
    #
    # def build_save(self):
    #     pass
    #
    # def build_remove(self):
    #     pass
    #
    # def customization_wear(self):
    #     pass
    #
    # def customization_buy(self):
    #     pass
    #
    # def encyclopedia_read(self):
    #     pass
    #
    # def inventory_insure_item(self):
    #     pass
    #
    # def inventory_add_item(self, data, profile_id):
    #     character_inventory = self.profiles[profile_id]["pmc_inventory"]
    #     pass
    #
    # def inventory_remove_item(self, data, profile_id):
    #     character_inventory = self.profiles[profile_id]["pmc_inventory"]
    #     pass
    #
    # def inventory_move_item(self, data, profile_id):
    #     character_inventory = self.profiles[profile_id]["pmc_inventory"]
    #     pass
    #
    # def inventory_split_item(self, data, profile_id):
    #     character_inventory = self.profiles[profile_id]["pmc_inventory"]
    #     pass
    #
    # def inventory_merge_item(self, data, profile_id):
    #     character_inventory = self.profiles[profile_id]["pmc_inventory"]
    #     pass
    #
    # def inventory_transfer_item(self, data, profile_id):
    #     character_inventory = self.profiles[profile_id]["pmc_inventory"]
    #     pass
    #
    # def inventory_swap_item(self, data, profile_id):
    #     character_inventory = self.profiles[profile_id]["pmc_inventory"]
    #     pass
    #
    # def inventory_fold_item(self, data, profile_id):
    #     character_inventory = self.profiles[profile_id]["pmc_inventory"]
    #     pass
    #
    # def inventory_toggle_item(self, data, profile_id):
    #     character_inventory = self.profiles[profile_id]["pmc_inventory"]
    #     pass
    #
    # def inventory_tag_item(self, data, profile_id):
    #     character_inventory = self.profiles[profile_id]["pmc_inventory"]
    #     pass
    #
    # def inventory_bind_item(self, data, profile_id):
    #     character_inventory = self.profiles[profile_id]["pmc_inventory"]
    #     pass
    #
    # def inventory_examine_item(self, data, profile_id):
    #     character_inventory = self.profiles[profile_id]["pmc_inventory"]
    #     pass
    #
    # def note_add(self):
    #     pass
    #
    # def node_edit(self):
    #     pass
    #
    # def note_delete(self):
    #     pass
    #
    # def player_heal(self):
    #     pass
    #
    # def player_eat(self):
    #     pass
    #
    # def player_restore_health(self):
    #     pass
    #
    # def quest_accept(self):
    #     pass
    #
    # def quest_complete(self):
    #     pass
    #
    # def quest_handover(self):
    #     pass
