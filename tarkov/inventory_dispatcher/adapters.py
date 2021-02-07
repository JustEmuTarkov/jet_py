import copy
from typing import Optional

from tarkov.inventory import (AmmoStackPosition, Item, ItemLocation, MoveLocation, PlayerInventory,
                              item_templates_repository, )
from tarkov.inventory.helpers import generate_item_id


class InventoryToRequestAdapter:
    def __init__(self, inventory: PlayerInventory):
        self.inventory = inventory

    def _split_ammo_into_magazine(self, ammo: Item, magazine: Item) -> Item:
        magazine_template = item_templates_repository.get_template(magazine)

        assert magazine_template.props.Cartridges is not None
        magazine_capacity: int = magazine_template.props.Cartridges[0].max_count
        # magazine_capacity: int = magazine_template['_props']['Cartridges'][0]['_max_count']

        bullet_stacks_inside_mag = list(self.inventory.iter_item_children(magazine))
        ammo_to_full = magazine_capacity - sum(stack.upd.StackObjectsCount for stack in bullet_stacks_inside_mag)

        # Remove ammo from inventory if stack fully fits into magazine
        if ammo.upd.StackObjectsCount <= ammo_to_full:
            self.inventory.remove_item(ammo)
            return ammo

        # Else if stack is too big to fit into magazine copy ammo and assign it new id and proper stack count
        ammo.upd.StackObjectsCount -= ammo_to_full

        ammo_copy = copy.deepcopy(ammo)
        ammo_copy.id = generate_item_id()
        ammo_copy.upd.StackObjectsCount = ammo_to_full
        self._move_ammo_into_magazine(ammo_copy, magazine)

        return ammo_copy

    def split_item(self, item: Item, location: MoveLocation, count: int) -> Item:
        """
        Splits count from item into location

        :return: New item
        """

        container_type = location['container']

        if container_type == 'cartridges':
            magazine = self.inventory.get_item(location['id'])
            ammo = self._split_ammo_into_magazine(ammo=item, magazine=magazine)
            # We have to return new ammo stack to the client
            return ammo

        #  Placing ammo into chamber
        if container_type == 'patron_in_weapon':
            bullet = self.inventory.split_item(item, count=1)
            bullet.slotId = 'patron_in_weapon'
            bullet.parent_id = location['id']

            return bullet

        is_pocket_container = container_type.startswith('pocket')
        if container_type in ('main', 'hideout') or is_pocket_container:
            new_item = copy.deepcopy(item)
            new_item.upd.StackObjectsCount = count
            item.upd.StackObjectsCount -= count

            new_item.id = generate_item_id()
            new_item.location = ItemLocation(**location['location'])
            new_item.parent_id = location['id']
            new_item.slotId = location['container']
            return new_item

        raise NotImplementedError(f'Unknown split container: {container_type}')

    def _move_ammo_into_magazine(self, ammo: Item, magazine: Item) -> Optional[Item]:
        bullet_stacks_inside_mag = list(self.inventory.iter_item_children(magazine))

        if bullet_stacks_inside_mag:
            def ammo_stack_position(item: Item) -> int:
                if isinstance(item.location, int):
                    return item.location
                return 0

            last_bullet_stack: Item = max(bullet_stacks_inside_mag, key=ammo_stack_position)

            # Stack ammo stack with last if possible
            if last_bullet_stack.tpl == ammo.tpl:
                last_bullet_stack.upd.StackObjectsCount += ammo.upd.StackObjectsCount
                self.inventory.remove_item(ammo)
                return None

            ammo.location = AmmoStackPosition(len(bullet_stacks_inside_mag))

        # Add new ammo stack to magazine
        else:
            ammo.location = AmmoStackPosition(0)
        return ammo

    def move_item(self, item: Item, location: MoveLocation):
        """
        Moves item to location
        """
        if 'location' in location:
            item.location = ItemLocation(**location['location'])
        else:
            del item.location

        if location['container'] == 'cartridges':
            magazine = self.inventory.get_item(location['id'])
            self._move_ammo_into_magazine(ammo=item, magazine=magazine)

        item.parent_id = location['id']
        item.slotId = location['container']
