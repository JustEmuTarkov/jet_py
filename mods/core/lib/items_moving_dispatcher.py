import enum
from typing import List, cast, TypedDict, Optional

import ujson
from flask import request

import mods.core.lib.items as items_lib
from mods.core.lib.adapters import InventoryToRequestAdapter
from mods.core.lib.inventory import PlayerInventory, StashMap, generate_item_id
from mods.core.lib.items import MoveLocation, ItemTemplatesRepository, ItemId, Item
from mods.core.lib.profile import Profile, HideoutAreaType
from mods.core.lib.trader import TraderInventory, Traders
from server import logger


class ActionType(enum.Enum):
    Eat = "Eat"
    Heal = "Heal"
    RestoreHealth = "RestoreHealth"

    CustomizationWear = "CustomizationWear"
    CustomizationBuy = "CustomizationBuy"

    HideoutUpgrade = "HideoutUpgrade"
    HideoutUpgradeComplete = "HideoutUpgradeComplete"
    HideoutContinuousProductionStart = "HideoutContinuousProductionStart"
    HideoutSingleProductionStart = "HideoutSingleProductionStart"
    HideoutScavCaseProductionStart = "HideoutScavCaseProductionStart"
    HideoutTakeProduction = "HideoutTakeProduction"
    HideoutPutItemsInAreaSlots = "HideoutPutItemsInAreaSlots"
    HideoutTakeItemsFromAreaSlots = "HideoutTakeItemsFromAreaSlots"
    HideoutToggleArea = "HideoutToggleArea"

    Insure = "Insure"
    Move = "Move"
    Remove = "Remove"
    Split = "Split"
    Merge = "Merge"
    Transfer = "Transfer"
    Swap = "Swap"

    AddNote = "AddNote"
    EditNote = "EditNote"
    DeleteNote = "DeleteNote"

    QuestAccept = "QuestAccept"
    QuestComplete = "QuestComplete"
    QuestHandover = "QuestHandover"

    RagFairAddOffer = "RagFairAddOffer"
    Repair = "Repair"
    Fold = "Fold"
    Toggle = "Toggle"
    Tag = "Tag"
    Bind = "Bind"
    Examine = "Examine"
    ReadEncyclopedia = "ReadEncyclopedia"
    TradingConfirm = "TradingConfirm"
    RagFairBuyOffer = "RagFairBuyOffer"

    SaveBuild = "SaveBuild"
    RemoveBuild = "RemoveBuild"

    AddToWishList = "AddToWishList"
    RemoveFromWishList = "RemoveFromWishList"

    ApplyInventoryChanges = "ApplyInventoryChanges"


class Action(TypedDict):
    Action: ActionType


class MoveAction(Action):
    item: ItemId
    to: MoveLocation


class SplitAction(Action):
    item: ItemId
    container: MoveLocation
    count: int


class FoldAction(Action):
    item: ItemId
    value: bool


MergeAction = TypedDict('MergeAction', {'Action': ActionType, 'item': ItemId, 'with': ItemId})


class TransferAction(MergeAction):
    count: int


class ExamineActionOwner(TypedDict):
    id: ItemId
    type: str


class ExamineAction(Action, total=False):
    item: ItemId
    fromOwner: ExamineActionOwner


class TradingSchemeItem(TypedDict):
    id: ItemId
    count: int
    scheme_id: int


class TradingAction(Action):
    type: str


class TradingConfirmAction(TradingAction):
    tid: str
    item_id: str
    count: int
    scheme_id: int
    scheme_items: List[TradingSchemeItem]


class TradingSellAction(TradingAction):
    tid: str
    items: List[TradingSchemeItem]


class ItemRemoveAction(Action):
    item: ItemId


class QuestAcceptAction(Action):
    qid: str


class ReadEncyclopediaAction(Action):
    ids: List[items_lib.TemplateId]


class HideoutUpgradeAction(Action):
    areaType: int
    items: List[dict]
    timestamp: int


class HideoutUpgradeCompleteAction(Action):
    areaType: int
    timestamp: int


class HideoutPutItemsInAreaSlotsAction(Action):
    areaType: int
    items: dict
    timestamp: int


class HideoutToggleAreaAction(Action):
    areaType: int
    enabled: bool
    timestamp: int


class HideoutTakeItemsFromAreaSlotsAction(Action):
    areaType: int
    slots: List[int]
    timestamp: int


class HideoutSingleProductionStartAction(Action):
    recipeId: str
    items: List[dict]


class HideoutTakeProductionAction(Action):
    recipeId: str
    timestamp: int


class InsureAction(Action):
    items: List[ItemId]
    tid: str


class ApplyInventoryChangesAction(Action):
    changedItems: Optional[List[Item]]
    deletedItems: Optional[List[Item]]


class ProfileItemsMovingDispatcher:
    def __init__(self, session_id: str):
        self.profile = Profile(session_id)

        self.inventory: PlayerInventory
        self.inventory_adapter: InventoryToRequestAdapter

        self.request = request
        self.response: dict = {
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

            ActionType.HideoutUpgrade: self._hideout_upgrade_start,
            ActionType.HideoutUpgradeComplete: self._hideout_upgrade_finish,
            ActionType.HideoutPutItemsInAreaSlots: self._hideout_put_items_in_area_slots,
            ActionType.HideoutToggleArea: self._hideout_toggle_area,
            ActionType.HideoutSingleProductionStart: self._hideout_single_production_start,
            ActionType.HideoutTakeProduction: self._hideout_take_production,

            ActionType.Insure: self._insure,

            ActionType.ApplyInventoryChanges: self._apply_inventory_changes,
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

    def _apply_inventory_changes(self, action: ApplyInventoryChangesAction):
        if action['changedItems'] is not None:
            for changed_item in action['changedItems']:
                item = self.profile.inventory.get_item(changed_item['_id'])

                self.profile.inventory.remove_item(item)
                self.profile.inventory.add_item(changed_item)
                self.response['items']['change'].append(changed_item)

        if action['deletedItems'] is not None:
            for deleted_item in action['deletedItems']:
                item = self.profile.inventory.get_item(deleted_item['_id'])
                self.profile.inventory.remove_item(item)
                self.response['items']['del'].append(item)

    def _insure(self, action: InsureAction):
        trader = Traders(action['tid'])
        trader_inventory = TraderInventory(
            trader=trader,
            player_inventory=self.profile.inventory,
        )

        rubles_tpl_id = items_lib.TemplateId('5449016a4bdc2d6f028b456f')
        total_price = 0
        for item_id in action['items']:
            item = self.profile.inventory.get_item(item_id)
            total_price += trader_inventory.calculate_insurance_price(item)
            self.profile.add_insurance(item, trader)

        affected_items, deleted_items = self.profile.inventory.take_item(rubles_tpl_id, total_price)

        self.response['items']['change'].extend(affected_items)
        self.response['items']['del'].extend(deleted_items)

    def _hideout_upgrade_start(self, action: HideoutUpgradeAction):
        hideout = self.profile.hideout

        area_type = HideoutAreaType(action['areaType'])
        hideout.area_upgrade_start(area_type)

        items_required = action['items']
        for item_required in items_required:
            count = item_required['count']
            item_id = item_required['id']

            item = self.profile.inventory.get_item(item_id)
            item['upd']['StackObjectsCount'] -= count
            if not item['upd']['StackObjectsCount']:
                self.profile.inventory.remove_item(item)
                self.response['items']['del'].append(item)
            else:
                self.response['items']['change'].append(item)

    def _hideout_upgrade_finish(self, action: HideoutUpgradeCompleteAction):
        hideout = self.profile.hideout

        area_type = HideoutAreaType(action['areaType'])
        hideout.area_upgrade_finish(area_type)

    def _hideout_put_items_in_area_slots(self, action: HideoutPutItemsInAreaSlotsAction):
        area_type = HideoutAreaType(action['areaType'])

        for slot_id, item_data in action['items'].items():
            count, item_id = item_data['count'], item_data['id']
            item = self.profile.inventory.get_item(item_id)

            if self.profile.inventory.can_split(item):
                splitted_item = self.profile.inventory.split_item(item, count)
                self.profile.hideout.put_items_in_area_slots(area_type, int(slot_id), splitted_item)
            else:
                self.profile.inventory.remove_item(item)
                self.profile.hideout.put_items_in_area_slots(area_type, int(slot_id), item)

    def _hideout_toggle_area(self, action: HideoutToggleAreaAction):
        area_type = HideoutAreaType(action['areaType'])
        self.profile.hideout.toggle_area(area_type, action['enabled'])

    def _hideout_single_production_start(self, action: HideoutSingleProductionStartAction):
        items_info = action['items']
        inventory = self.profile.inventory

        for item_info in items_info:
            item_id = item_info['id']
            count = item_info['count']

            item = inventory.get_item(item_id=item_id)

            if not inventory.can_split(item):
                inventory.remove_item(item)
                self.response['items']['del'].append(item)
                continue

            inventory.split_item(item=item, count=count)
            if not item['upd']['StackObjectsCount']:
                self.response['items']['del'].append(item)
            else:
                self.response['items']['upd'].append(item)

        self.profile.hideout.start_single_production(recipe_id=action['recipeId'])

    def _hideout_take_production(self, action: HideoutTakeProductionAction):
        items = self.profile.hideout.take_production(action['recipeId'])
        self.response['items']['new'].extend(items)
        for item in items:
            self.inventory.place_item(item)

    def _accept_quest(self, action: QuestAcceptAction):
        self.profile.quests.accept_quest(action['qid'])

    def _move(self, action: MoveAction):
        item_id = action['item']
        move_location: MoveLocation = action['to']

        item = self.profile.inventory.get_item(item_id)
        self.inventory_adapter.move_item(item, move_location)

    def _split(self, action: SplitAction):
        item_id = action['item']
        move_location: MoveLocation = action['container']
        item = self.inventory_adapter.get_item(item_id)
        new_item = self.inventory_adapter.split_item(item, move_location, action['count'])
        self.response['items']['new'].append(new_item)

    def _examine(self, action: ExamineAction):
        if 'fromOwner' in action:
            if action['fromOwner']['type'] == 'Trader':
                trader_id = action['fromOwner']['id']
                item_id = action['item']

                trader_inventory = TraderInventory(Traders(trader_id), self.inventory)
                item = trader_inventory.get_item(item_id)
                self.profile.encyclopedia.examine(item)

            elif action['fromOwner']['type'] in ('HideoutUpgrade', 'HideoutProduction'):
                item_tpl_id = items_lib.TemplateId(action['item'])
                self.profile.encyclopedia.examine(item_tpl_id)

            else:
                raise NotImplementedError(f'Unhandled examine action: {action}')
        else:
            item_id = action['item']
            item = self.inventory_adapter.get_item(item_id)
            self.profile.encyclopedia.examine(item)

    def _merge(self, action: MergeAction):
        item = self.inventory_adapter.get_item(action['item'])
        with_ = self.inventory_adapter.get_item(action['with'])

        self.inventory_adapter.merge(item, with_)
        self.response['items']['del'].append(item)

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

        self.response['items']['new'].extend(items)
        self.response['items']['new'].extend(children_items)

        for scheme_item in action['scheme_items']:
            item = self.inventory_adapter.get_item(scheme_item['id'])
            item['upd']['StackObjectsCount'] -= scheme_item['count']
            if not item['upd']['StackObjectsCount']:
                self.inventory_adapter.remove_item(item)
                self.response['items']['del'].append(item)
            else:
                self.response['items']['change'].append(item)

        logger.debug(str(items))
        logger.debug(str(children_items))

    def __sell_to_trader(self, action: TradingSellAction):
        logger.debug(ujson.dumps(action))
        trader_id = action['tid']
        items_to_sell = action['items']
        trader_inventory = TraderInventory(Traders(trader_id), self.inventory)

        items = list(self.inventory.get_item(i['id']) for i in items_to_sell)
        price_sum = sum(trader_inventory.get_sell_price(item) for item in items)

        self.response['items']['del'].extend(items)
        self.inventory.remove_items(items)

        rubles_tpl = ItemTemplatesRepository().get_template(items_lib.TemplateId('5449016a4bdc2d6f028b456f'))
        money_max_stack_size = rubles_tpl['_props']['StackMaxSize']

        while price_sum:
            stack_size = min(money_max_stack_size, price_sum)
            price_sum -= stack_size

            money_stack = items_lib.Item(
                _id=generate_item_id(),
                _tpl=items_lib.TemplateId('5449016a4bdc2d6f028b456f'),
                parentId=self.inventory.root_id,
                slotId='hideout',
            )
            money_stack['upd'] = items_lib.ItemUpd(StackObjectsCount=stack_size)

            self.inventory.place_item(money_stack)
            self.response['items']['new'].append(money_stack)

    def _read_encyclopedia(self, action: ReadEncyclopediaAction):
        for template_id in action['ids']:
            self.profile.encyclopedia.read(template_id)
