import copy
from typing import Iterable

from tarkov_core.functions.items import item_templates_repository
from tarkov_core.lib.inventory import Inventory, generate_item_id
from tarkov_core.lib.items import MoveLocation, Item, ItemId


class InventoryToRequestAdapter:
    def __init__(self, inventory: Inventory):
        self.inventory = inventory

    @property
    def stash_id(self):
        return self.inventory.stash_id

    def add_item(self, item: Item):
        self.inventory.add_item(item)

    def add_items(self, items: Iterable[Item]):
        self.inventory.add_items(items)

    def get_item(self, item_id: ItemId):
        return self.inventory.get_item(item_id)

    def _split_ammo_into_magazine(self, ammo: Item, magazine: Item):
        magazine_template = item_templates_repository.get_template(magazine)
        magazine_capacity: int = magazine_template['_props']['Cartridges'][0]['_max_count']

        bullet_stacks_inside_mag = list(self.inventory.iter_item_children(magazine))
        ammo_to_full = magazine_capacity - sum(stack['upd']['StackObjectsCount'] for stack in bullet_stacks_inside_mag)

        # Remove ammo from inventory if stack fully fits into magazine
        if ammo['upd']['StackObjectsCount'] <= ammo_to_full:
            # self.remove_item(ammo)
            pass
        # Else if stack is too big to fit into magazine copy ammo and assign it new id and proper stack count
        else:
            ammo['upd']['StackObjectsCount'] -= ammo_to_full

            ammo = copy.deepcopy(ammo)
            ammo['_id'] = generate_item_id()
            ammo['upd']['StackObjectsCount'] = ammo_to_full
        self.inventory.add_item(ammo)
        return ammo

    def split_item(self, item: Item, location: MoveLocation, count: int) -> Item:
        """
        Splits count from item into location

        :return: New item
        """
        if location['container'] == 'cartridges':
            magazine = self.get_item(location['id'])
            ammo = self._split_ammo_into_magazine(ammo=item, magazine=magazine)
            # We have to return new ammo stack to the client
            return ammo

        new_item = copy.deepcopy(item)
        new_item['upd']['StackObjectsCount'] = count
        item['upd']['StackObjectsCount'] -= count

        new_item['_id'] = generate_item_id()
        new_item['location'] = location['location']
        new_item['parentId'] = location['id']
        new_item['slotId'] = location['container']
        self.inventory.items.append(new_item)
        return new_item

    def _move_ammo_into_magazine(self, ammo: Item, magazine: Item):
        bullet_stacks_inside_mag = list(self.inventory.iter_item_children(magazine))

        if bullet_stacks_inside_mag:
            last_bullet_stack = max(bullet_stacks_inside_mag, key=lambda stack: stack['location'])

            # Stack ammo stack with last if possible
            if last_bullet_stack['_tpl'] == ammo['_tpl']:
                last_bullet_stack['upd']['StackObjectsCount'] += ammo['upd']['StackObjectsCount']
                self.inventory.remove_item(ammo)
                return

        # Add new ammo stack to magazine
        else:
            ammo['location'] = 0
        return ammo

    def move_item(self, item: Item, location: MoveLocation):
        """
        Moves item to location
        """
        if 'location' in location:
            item['location'] = location['location']
        else:
            del item['location']

        if location['container'] == 'cartridges':
            magazine = self.get_item(location['id'])
            self._move_ammo_into_magazine(ammo=item, magazine=magazine)

        item['parentId'] = location['id']
        item['slotId'] = location['container']

    def examine(self, item: Item):
        pass

    def merge(self, item: Item, with_: Item):
        return self.inventory.merge(item, with_)

    def remove_item(self, item: Item):
        return self.inventory.remove_item(item)

    def transfer(self, item: Item, with_: Item, count: int):
        return self.inventory.transfer(item, with_, count)

    def fold(self, item: Item, folded: bool):
        return self.inventory.fold(item, folded)
