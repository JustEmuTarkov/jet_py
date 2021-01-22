from __future__ import annotations

import enum
import typing
from types import SimpleNamespace
from typing import List, Dict, Callable, Iterable, Literal, Optional, cast

import ujson
from flask import request, Request
from pydantic import StrictBool, StrictInt, Extra

import mods.core.lib.items as items_lib
from mods.core import models
from mods.core.lib.adapters import InventoryToRequestAdapter
from mods.core.lib.inventory import PlayerInventory, StashMap
from mods.core.lib.items import ItemTemplatesRepository, ItemId, generate_item_id, TemplateId, MoveLocation, Item
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


class ActionModel(models.Base):
    Action: ActionType


class InventoryExamineActionOwnerModel(models.Base):
    id: ItemId
    type: Optional[Literal['Trader', 'HideoutUpgrade', 'HideoutProduction']] = None


class InventoryActions(SimpleNamespace):
    class ApplyInventoryChanges(ActionModel):
        changedItems: Optional[List[dict]] = None
        deletedItems: Optional[List[dict]] = None

    class Examine(ActionModel):
        item: ItemId
        fromOwner: InventoryExamineActionOwnerModel

    class Split(ActionModel):
        item: ItemId
        container: dict  # MoveLocation
        count: StrictInt

    class Move(ActionModel):
        item: ItemId
        to: dict  # MoveLocation

    class Merge(ActionModel):
        class Config:
            fields = {'with_': 'with'}

        item: ItemId
        with_: ItemId

    class Transfer(Merge):
        count: int

    class Fold(ActionModel):
        item: ItemId
        value: StrictBool

    class Remove(ActionModel):
        item: ItemId

    class ReadEncyclopedia(ActionModel):
        ids: List[TemplateId]

    class Insure(ActionModel):
        items: List[ItemId]
        tid: str


class HideoutActions(SimpleNamespace):
    class Upgrade(ActionModel):
        areaType: StrictInt
        items: List[dict]
        timestamp: StrictInt

    class UpgradeComplete(ActionModel):
        areaType: StrictInt
        timestamp: StrictInt

    class PutItemsInAreaSlots(ActionModel):
        areaType: StrictInt
        items: dict
        timestamp: StrictInt

    class ToggleArea(ActionModel):
        areaType: StrictInt
        enabled: bool
        timestamp: StrictInt

    class TakeItemsFromAreaSlots(ActionModel):
        areaType: StrictInt
        slots: List[StrictInt]
        timestamp: StrictInt

    class SingleProductionStart(ActionModel):
        recipeId: str
        items: List[dict]
        timestamp: StrictInt

    class TakeProduction(ActionModel):
        recipeId: str
        timestamp: StrictInt


class TradingSchemeItemModel(models.Base):
    id: ItemId
    count: StrictInt
    # scheme_id: Optional[StrictInt]


class TradingActions(SimpleNamespace):
    class Trading(ActionModel):
        class Config:
            extra = Extra.allow

        type: Literal['buy_from_trader', 'sell_to_trader']

    class BuyFromTrader(Trading):
        class Config:
            extra = Extra.forbid

        tid: str
        item_id: str
        count: StrictInt
        scheme_id: StrictInt
        scheme_items: List[TradingSchemeItemModel]

    class SellToTrader(Trading):
        class Config:
            extra = Extra.forbid

        tid: str
        items: List[TradingSchemeItemModel]


class QuestHandoverItem(models.Base):
    id: ItemId
    count: int


class QuestActions(SimpleNamespace):
    class Accept(ActionModel):
        qid: str
        count: int

    class Handover(ActionModel):
        qid: str
        conditionId: str
        items: List[QuestHandoverItem]

    class Complete(ActionModel):
        qid: str
        removeExcessItems: bool


class Dispatcher:
    dispatch_map: Dict[ActionType, Callable]
    inventory: PlayerInventory
    inventory_adapter: InventoryToRequestAdapter
    profile: Profile
    response: dict

    def __init__(self, manager: DispatcherManager):
        self.manager = manager
        self.inventory = manager.inventory
        self.inventory_adapter = manager.inventory_adapter
        self.profile = manager.profile
        self.response = manager.response

    def dispatch(self, action: dict):
        action_type: ActionType = ActionType(action['Action'])

        try:
            method = self.dispatch_map[action_type]
        except KeyError as error:
            raise NotImplementedError(
                f'Action with type {action_type} not implemented in dispatcher {self.__class__}'
            ) from error

        types = typing.get_type_hints(method)
        model_type = types['action'] if issubclass(types['action'], ActionModel) else dict
        # noinspection PyArgumentList
        method(model_type(**action))  # type: ignore


class InventoryDispatcher(Dispatcher):
    def __init__(self, manager: DispatcherManager):
        super().__init__(manager)
        self.dispatch_map = {
            ActionType.Move: self._move,
            ActionType.Split: self._split,
            ActionType.Examine: self._examine,
            ActionType.Merge: self._merge,
            ActionType.Transfer: self._transfer,
            ActionType.Fold: self._fold,
            ActionType.Remove: self._remove,
            ActionType.ReadEncyclopedia: self._read_encyclopedia,

            ActionType.Insure: self._insure,
            ActionType.ApplyInventoryChanges: self._apply_inventory_changes,
        }

    def _move(self, action: InventoryActions.Move):
        item = self.inventory.get_item(action.item)
        self.inventory_adapter.move_item(item, cast(MoveLocation, action.to))

    def _split(self, action: InventoryActions.Split):
        item = self.inventory.get_item(action.item)
        new_item = self.inventory_adapter.split_item(item, cast(MoveLocation, action.container), action.count)

        self.response['items']['new'].append(new_item)
        if not item['upd']['StackObjectsCount']:
            self.response['items']['del'].append(item)

    def _examine(self, action: InventoryActions.Examine):
        item_id = action.item

        if action.fromOwner is None:
            item = self.inventory.get_item(item_id)
            self.profile.encyclopedia.examine(item)
            return

        if action.fromOwner.type == 'Trader':
            trader_id = action.fromOwner.id

            trader_inventory = TraderInventory(Traders(trader_id), self.inventory)
            item = trader_inventory.get_item(item_id)
            self.profile.encyclopedia.examine(item)

        elif action.fromOwner.type in ('HideoutUpgrade', 'HideoutProduction'):
            item_tpl_id = items_lib.TemplateId(action.item)
            self.profile.encyclopedia.examine(item_tpl_id)

    def _merge(self, action: InventoryActions.Merge):
        item = self.inventory.get_item(action.item)
        with_ = self.inventory.get_item(action.with_)

        self.inventory.merge(item, with_)
        self.response['items']['del'].append(item)

    def _transfer(self, action: InventoryActions.Transfer):
        item = self.inventory.get_item(action.item)
        with_ = self.inventory.get_item(action.with_)
        self.inventory.transfer(item, with_, action.count)

    def _fold(self, action: InventoryActions.Fold):
        item = self.inventory.get_item(action.item)
        self.inventory.fold(item, action.value)

    def _remove(self, action: InventoryActions.Remove):
        item = self.inventory.get_item(action.item)
        self.inventory.remove_item(item)

    def _read_encyclopedia(self, action: InventoryActions.ReadEncyclopedia):
        for template_id in action.ids:
            self.profile.encyclopedia.read(template_id)

    def _apply_inventory_changes(self, action: InventoryActions.ApplyInventoryChanges):
        if action.changedItems:
            for changed_item in action.changedItems:
                item = self.profile.inventory.get_item(changed_item['_id'])

                self.inventory.remove_item(item, remove_children=False)
                self.inventory.add_item(cast(Item, changed_item))

                self.response['items']['change'].append(changed_item)

        if action.deletedItems:
            for deleted_item in action.deletedItems:
                item = self.profile.inventory.get_item(deleted_item['_id'])
                self.profile.inventory.remove_item(item)
                self.response['items']['del'].append(item)

    def _insure(self, action: InventoryActions.Insure):
        trader = Traders(action.tid)
        trader_inventory = TraderInventory(
            trader=trader,
            player_inventory=self.profile.inventory,
        )

        rubles_tpl_id = items_lib.TemplateId('5449016a4bdc2d6f028b456f')
        total_price = 0
        for item_id in action.items:
            item = self.profile.inventory.get_item(item_id)
            total_price += trader_inventory.calculate_insurance_price(item)
            self.profile.add_insurance(item, trader)

        affected_items, deleted_items = self.profile.inventory.take_item(rubles_tpl_id, total_price)

        self.response['items']['change'].extend(affected_items)
        self.response['items']['del'].extend(deleted_items)


class HideoutDispatcher(Dispatcher):
    def __init__(self, manager: DispatcherManager):
        super().__init__(manager)
        self.dispatch_map = {
            ActionType.HideoutUpgrade: self._hideout_upgrade_start,
            ActionType.HideoutUpgradeComplete: self._hideout_upgrade_finish,
            ActionType.HideoutPutItemsInAreaSlots: self._hideout_put_items_in_area_slots,
            ActionType.HideoutToggleArea: self._hideout_toggle_area,
            ActionType.HideoutSingleProductionStart: self._hideout_single_production_start,
            ActionType.HideoutTakeProduction: self._hideout_take_production,
            ActionType.HideoutTakeItemsFromAreaSlots: self._hideout_take_items_from_area_slots,
        }

    def _hideout_upgrade_start(self, action: HideoutActions.Upgrade):
        hideout = self.profile.hideout

        area_type = HideoutAreaType(action.areaType)
        hideout.area_upgrade_start(area_type)

        items_required = action.items
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

    def _hideout_upgrade_finish(self, action: HideoutActions.UpgradeComplete):
        hideout = self.profile.hideout

        area_type = HideoutAreaType(action.areaType)
        hideout.area_upgrade_finish(area_type)

    def _hideout_put_items_in_area_slots(self, action: HideoutActions.PutItemsInAreaSlots):
        area_type = HideoutAreaType(action.areaType)

        for slot_id, item_data in action.items.items():
            count, item_id = item_data['count'], item_data['id']
            item = self.profile.inventory.get_item(item_id)

            if self.profile.inventory.can_split(item):
                splitted_item = self.profile.inventory.split_item(item, count)
                self.profile.hideout.put_items_in_area_slots(area_type, int(slot_id), splitted_item)
            else:
                self.profile.inventory.remove_item(item)
                self.profile.hideout.put_items_in_area_slots(area_type, int(slot_id), item)

    def _hideout_toggle_area(self, action: HideoutActions.ToggleArea):
        area_type = HideoutAreaType(action.areaType)
        self.profile.hideout.toggle_area(area_type, action.enabled)

    def _hideout_single_production_start(self, action: HideoutActions.SingleProductionStart):
        items_info = action.items
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

        self.profile.hideout.start_single_production(recipe_id=action.recipeId)

    def _hideout_take_production(self, action: HideoutActions.TakeProduction):
        items = self.profile.hideout.take_production(action.recipeId)
        self.response['items']['new'].extend(items)
        for item in items:
            self.inventory.place_item(item)

    def _hideout_take_items_from_area_slots(self, action: HideoutActions.TakeItemsFromAreaSlots):
        hideout = self.profile.hideout
        area_type = HideoutAreaType(action.areaType)
        for slot_id in action.slots:
            item = hideout.take_item_from_area_slot(area_type=area_type, slot_id=slot_id)

            self.inventory.place_item(item)
            self.response['items']['new'].append(item)


class TradingDispatcher(Dispatcher):
    def __init__(self, manager: DispatcherManager):
        super().__init__(manager)
        self.dispatch_map = {
            ActionType.TradingConfirm: self._trading_confirm,
        }

    def _trading_confirm(self, action: TradingActions.Trading):
        if action.type == 'buy_from_trader':
            print(action.dict())
            self.__buy_from_trader(TradingActions.BuyFromTrader(**action.dict()))
            return

        if action.type == 'sell_to_trader':
            self.__sell_to_trader(TradingActions.SellToTrader(**action.dict()))
            return

        raise NotImplementedError(f'Trading action {action} not implemented')

    def __buy_from_trader(self, action: TradingActions.BuyFromTrader):
        trader_id = action.tid
        item_id = action.item_id
        item_count = action.count
        trader_inventory = TraderInventory(Traders(trader_id), self.inventory)
        # item = trader_inventory.get_item(item_id)

        items, children_items = trader_inventory.buy_item(item_id, item_count)
        self.inventory.add_items(children_items)
        stash_map = StashMap(self.inventory_adapter.inventory)
        for item in items:
            self.inventory.add_item(item)
            location = stash_map.find_location_for_item(item, auto_fill=True)
            item['location'] = location
            item['slotId'] = 'hideout'
            item['parentId'] = self.inventory.stash_id

        self.response['items']['new'].extend(items)
        self.response['items']['new'].extend(children_items)

        for scheme_item in action.scheme_items:
            item = self.inventory.get_item(scheme_item.id)
            item['upd']['StackObjectsCount'] -= scheme_item.count
            if not item['upd']['StackObjectsCount']:
                self.inventory.remove_item(item)
                self.response['items']['del'].append(item)
            else:
                self.response['items']['change'].append(item)

        logger.debug(str(items))
        logger.debug(str(children_items))

    def __sell_to_trader(self, action: TradingActions.SellToTrader):
        trader_id = action.tid
        items_to_sell = action.items
        trader_inventory = TraderInventory(Traders(trader_id), self.inventory)

        items = list(self.inventory.get_item(i.id) for i in items_to_sell)
        price_sum = sum(trader_inventory.get_sell_price(item) for item in items)

        self.response['items']['del'].extend(items)
        self.inventory.remove_items(items)

        rubles_tpl = ItemTemplatesRepository().get_template(items_lib.TemplateId('5449016a4bdc2d6f028b456f'))
        money_max_stack_size = rubles_tpl.props.StackMaxSize

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


class QuestDispatcher(Dispatcher):
    def __init__(self, manager: DispatcherManager):
        super().__init__(manager)
        self.dispatch_map = {
            ActionType.QuestAccept: self._quest_accept,
            ActionType.QuestHandover: self._quest_handover,
        }

    def _quest_accept(self, action: QuestActions.Accept):
        self.profile.quests.accept_quest(action.qid)

    def _quest_handover(self, action: QuestActions.Handover):
        items_dict = {item.id: item.count for item in action.items}
        removed, changed = self.profile.quests.handover_items(action.qid, action.conditionId, items_dict)

        self.response['items']['change'].extend(changed)
        self.response['items']['del'].extend(removed)

    def _quest_finish(self, ):
        pass


class DispatcherManager:
    profile: Profile
    inventory: PlayerInventory
    inventory_adapter: InventoryToRequestAdapter
    request: Request
    response: dict

    dispatchers: Iterable[Dispatcher]

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

    def __make_dispatchers(self):
        self.dispatchers = (
            InventoryDispatcher(self),
            HideoutDispatcher(self),
            TradingDispatcher(self),
            QuestDispatcher(self),
        )

    def dispatch(self) -> dict:
        with self.profile:
            self.inventory = self.profile.inventory
            self.inventory_adapter = InventoryToRequestAdapter(self.inventory)
            self.__make_dispatchers()

            # request.data should be dict at this moment
            # noinspection PyTypeChecker
            actions: List[dict] = request.data['data']  # type: ignore

            for action in actions:
                logger.debug(ujson.dumps(action, indent=4))

                for dispatcher in self.dispatchers:
                    try:
                        dispatcher.dispatch(action)
                        logger.debug(f'Action was dispatched in {dispatcher.__class__.__name__}')
                        break
                    except NotImplementedError:
                        pass
                else:
                    raise NotImplementedError(f'Action {action} not implemented in any of the dispatchers')

        return self.response
