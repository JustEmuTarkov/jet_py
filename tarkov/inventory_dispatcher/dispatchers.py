import typing
from typing import Callable, Dict, List, Optional

from pydantic import StrictInt

import tarkov.inventory
from server import logger
from tarkov import quests
from tarkov.hideout.models import HideoutAreaType
from tarkov.inventory import (MutableInventory, PlayerInventory, generate_item_id,
                              item_templates_repository, )
from tarkov.inventory.implementations import SimpleInventory
from tarkov.inventory.models import Item, TemplateId
from tarkov.lib.trader import TraderInventory, Traders
from tarkov.notifier.models import MailDialogueMessage, MailMessageItems
from tarkov.profile import Profile
from tarkov.quests.models import QuestMessageType, QuestRewardItem
from . import manager as manager_  # pylint: disable=unused-import
from .models import ActionModel, ActionType, HideoutActions, InventoryActions, Owner, QuestActions, TradingActions


class Dispatcher:
    dispatch_map: Dict[ActionType, Callable]
    inventory: PlayerInventory
    profile: Profile
    response: 'manager_.DispatcherResponse'

    def __init__(self, manager: 'manager_.DispatcherManager'):
        self.manager = manager
        self.inventory = manager.inventory
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
    def __init__(self, manager: 'manager_.DispatcherManager'):
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

    def get_owner_inventory(self, owner: Optional[Owner] = None) -> MutableInventory:
        if owner is None:
            return self.inventory

        if owner.type == 'Mail':
            message = self.profile.notifier.get_message(owner.id)
            return SimpleInventory(message.items.data)

        raise ValueError(f'Cannot find inventory for owner: {owner}')

    def _move(self, action: InventoryActions.Move):
        donor_inventory = self.get_owner_inventory(action.fromOwner)
        item = donor_inventory.get_item(action.item)

        self.inventory.move_item(
            item=item,
            move_location=action.to,
        )
        self.response.items.new.append(item)

    def _split(self, action: InventoryActions.Split):
        donor_inventory = self.get_owner_inventory(action.fromOwner)
        item = donor_inventory.get_item(action.item)

        new_item = self.inventory.split_item(
            item=item,
            split_location=action.container,
            count=action.count
        )

        if new_item:
            self.response.items.new.append(new_item)

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
            item_tpl_id = tarkov.inventory.models.TemplateId(action.item)
            self.profile.encyclopedia.examine(item_tpl_id)

    def _merge(self, action: InventoryActions.Merge):
        donor_inventory = self.get_owner_inventory(action.fromOwner)
        item = donor_inventory.get_item(item_id=action.item)
        with_ = self.inventory.get_item(action.with_)

        self.inventory.merge(item=item, with_=with_)

        self.response.items.del_.append(item)
        self.response.items.change.append(with_)

    def _transfer(self, action: InventoryActions.Transfer):
        donor_inventory = self.get_owner_inventory(action.fromOwner)
        item = donor_inventory.get_item(item_id=action.item)
        with_ = self.inventory.get_item(action.with_)

        self.inventory.transfer(item=item, with_=with_, count=action.count)
        self.response.items.change.extend((item, with_))

    def _fold(self, action: InventoryActions.Fold):
        item = self.inventory.get_item(action.item)
        self.inventory.fold(item, action.value)

    def _remove(self, action: InventoryActions.Remove):
        item = self.inventory.get_item(action.item)
        self.inventory.remove_item(item)

        self.response.items.del_.append(item)

    def _read_encyclopedia(self, action: InventoryActions.ReadEncyclopedia):
        for template_id in action.ids:
            self.profile.encyclopedia.read(template_id)

    def _apply_inventory_changes(self, action: InventoryActions.ApplyInventoryChanges):
        if action.changedItems is not None:
            for changed_item in action.changedItems:
                item = self.inventory.get_item(changed_item.id)

                child_items = list(self.inventory.iter_item_children_recursively(item))
                self.inventory.remove_item(item, remove_children=True)
                self.inventory.add_item(changed_item, child_items)

                self.response.items.change.append(changed_item)

        if action.deletedItems is not None:
            for deleted_item in action.deletedItems:
                item = self.profile.inventory.get_item(deleted_item.id)
                self.profile.inventory.remove_item(item)
                self.response.items.del_.append(item)

    def _insure(self, action: InventoryActions.Insure):
        trader = Traders(action.tid)
        trader_inventory = TraderInventory(
            trader=trader,
            player_inventory=self.profile.inventory,
        )

        rubles_tpl_id = tarkov.inventory.models.TemplateId('5449016a4bdc2d6f028b456f')
        total_price = 0
        for item_id in action.items:
            item = self.profile.inventory.get_item(item_id)
            total_price += trader_inventory.calculate_insurance_price(item)
            self.profile.add_insurance(item, trader)

        affected_items, deleted_items = self.profile.inventory.take_item(rubles_tpl_id, total_price)

        self.response.items.change.extend(affected_items)
        self.response.items.del_.extend(deleted_items)


class HideoutDispatcher(Dispatcher):
    def __init__(self, manager: 'manager_.DispatcherManager'):
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
            item.upd.StackObjectsCount -= count
            if not item.upd.StackObjectsCount:
                self.profile.inventory.remove_item(item)
                self.response.items.del_.append(item)
            else:
                self.response.items.change.append(item)

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
                splitted_item = self.profile.inventory.simple_split_item(item=item, count=count)
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
                self.response.items.del_.append(item)
                continue

            inventory.simple_split_item(item=item, count=count)  # Simply throw away splitted item
            if not item.upd.StackObjectsCount:
                self.response.items.del_.append(item)
            else:
                self.response.items.change.append(item)

        self.profile.hideout.start_single_production(recipe_id=action.recipeId)

    def _hideout_take_production(self, action: HideoutActions.TakeProduction):
        items = self.profile.hideout.take_production(action.recipeId)
        self.response.items.new.extend(items)
        for item in items:
            self.inventory.place_item(item)

    def _hideout_take_items_from_area_slots(self, action: HideoutActions.TakeItemsFromAreaSlots):
        hideout = self.profile.hideout
        area_type = HideoutAreaType(action.areaType)
        for slot_id in action.slots:
            item = hideout.take_item_from_area_slot(area_type=area_type, slot_id=slot_id)

            self.inventory.place_item(item)
            self.response.items.new.append(item)


class TradingDispatcher(Dispatcher):
    def __init__(self, manager: 'manager_.DispatcherManager'):
        super().__init__(manager)
        self.dispatch_map = {
            ActionType.TradingConfirm: self._trading_confirm,
        }

    def _trading_confirm(self, action: TradingActions.Trading):
        if action.type == 'buy_from_trader':
            self.__buy_from_trader(TradingActions.BuyFromTrader(**action.dict()))
            return

        if action.type == 'sell_to_trader':
            self.__sell_to_trader(TradingActions.SellToTrader(**action.dict()))
            return

        raise NotImplementedError(f'Trading action {action} not implemented')

    def __buy_from_trader(self, action: TradingActions.BuyFromTrader):
        trader_inventory = TraderInventory(Traders(action.tid), self.inventory)

        bought_items_list = trader_inventory.buy_item(action.item_id, action.count)

        for bought_item in bought_items_list:
            item = bought_item.item
            children = bought_item.children_items

            self.inventory.place_item(item, child_items=children)

            self.response.items.new.append(item)
            self.response.items.new.extend(children)

        # Take required items from inventory
        for scheme_item in action.scheme_items:
            item = self.inventory.get_item(scheme_item.id)
            item.upd.StackObjectsCount -= scheme_item.count
            if not item.upd.StackObjectsCount:
                self.inventory.remove_item(item)
                self.response.items.del_.append(item)
            else:
                self.response.items.change.append(item)

    def __sell_to_trader(self, action: TradingActions.SellToTrader):
        trader_id = action.tid
        items_to_sell = action.items
        trader_inventory = TraderInventory(Traders(trader_id), self.inventory)

        items = list(self.inventory.get_item(i.id) for i in items_to_sell)
        price_sum: int = sum(trader_inventory.get_sell_price(item) for item in items)

        self.response.items.del_.extend(items)
        self.inventory.remove_items(items)

        rubles_tpl = item_templates_repository.get_template(
            tarkov.inventory.models.TemplateId('5449016a4bdc2d6f028b456f'))
        money_max_stack_size = rubles_tpl.props.StackMaxSize

        while price_sum:
            stack_size = min(money_max_stack_size, price_sum)
            price_sum -= stack_size

            money_stack = tarkov.inventory.models.Item(
                id=generate_item_id(),
                tpl=TemplateId('5449016a4bdc2d6f028b456f'),
                parent_id=self.inventory.root_id,
                slotId='hideout',
            )
            money_stack.upd.StackObjectsCount = stack_size

            self.inventory.place_item(money_stack)
            self.response.items.new.append(money_stack)


class QuestDispatcher(Dispatcher):
    def __init__(self, manager: 'manager_.DispatcherManager') -> None:
        super().__init__(manager)
        self.dispatch_map = {
            ActionType.QuestAccept: self._quest_accept,
            ActionType.QuestHandover: self._quest_handover,
            ActionType.QuestComplete: self._quest_complete,
        }

    def _quest_accept(self, action: QuestActions.Accept) -> None:
        self.profile.quests.accept_quest(action.qid)

    def _quest_handover(self, action: QuestActions.Handover) -> None:
        items_dict = {item.id: item.count for item in action.items}
        removed, changed = self.profile.quests.handover_items(action.qid, action.conditionId, items_dict)

        self.response.items.change.extend(changed)
        self.response.items.del_.extend(removed)

    def _quest_complete(self, action: QuestActions.Complete) -> None:
        quest = self.profile.quests.get_quest(action.qid)
        quest_template = quests.quests_repository.get_quest_template(action.qid)

        logger.debug(action)
        logger.debug(quest)
        logger.debug(quest_template)

        reward_items: List[Item] = []
        for reward in quest_template.rewards.Success:
            if isinstance(reward, QuestRewardItem):
                reward_items.extend(reward.items)

        message = MailDialogueMessage(
            uid=quest_template.traderId,
            type=StrictInt(QuestMessageType.questSuccess.value),
            templateId='5ab0f32686f7745dd409f56b',  # TODO: Right now this is a placeholder
            systemData={},
            items=MailMessageItems.from_items(reward_items),
            hasRewards=True,
        )
        self.profile.notifier.add_message(message)
        # raise NotImplementedError
