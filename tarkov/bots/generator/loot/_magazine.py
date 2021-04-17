import random
from typing import List

from tarkov.exceptions import NoSpaceError, NotFoundError
from tarkov.inventory.models import Item, ItemAmmoStackPosition, ItemTemplate, ItemUpd
from tarkov.inventory.prop_models import MagazineProps, MagazineReloadType
from tarkov.inventory.types import TemplateId
from ._base import BaseLootGenerator


class BotMagazineGenerator(BaseLootGenerator):
    ATTEMPTS_TO_PLACE = 10

    def generate(self) -> None:
        slots = ["FirstPrimaryWeapon", "SecondPrimaryWeapon", "Holster"]
        for slot in slots:
            try:
                weapon = self.bot_inventory.get_equipment(slot)
            except NotFoundError:
                continue
            self.generate_magazines_for_weapon(weapon)

    def generate_magazines_for_weapon(self, weapon: Item) -> None:
        # Magazine template to generate for a bot
        magazine_template: ItemTemplate
        # Magazine that is currently in the weapon
        magazine_in_weapon: Item

        for item in self.bot_inventory.items.values():
            item_template = self.templates_repository.get_template(item.tpl)
            if (
                isinstance(item_template.props, MagazineProps)
                and item.parent_id == weapon.id
            ):
                magazine_template = item_template
                magazine_in_weapon = item
                break
        else:
            raise ValueError("Magazine wasn't found")

        assert isinstance(magazine_template.props, MagazineProps)
        cartridges = random.choice(magazine_template.props.Cartridges)
        ammo_types: List[TemplateId] = self.preset.inventory["mods"][
            magazine_template.id
        ]["cartridges"]
        ammo_type = self.templates_repository.get_template(random.choice(ammo_types))

        # Generate ammo for current magazine
        self.bot_inventory.add_item(
            self.make_ammo(ammo_type, magazine_in_weapon, cartridges.max_count)
        )

        reload_type = MagazineReloadType(magazine_template.props.ReloadMagType)

        # Generate additional magazines if magazine is external
        if reload_type == MagazineReloadType.ExternalMagazine:
            for _ in range(
                random.randint(self.config.magazines.min, self.config.magazines.max)
            ):
                for _ in range(self.ATTEMPTS_TO_PLACE):
                    container = self.inventory_containers.random_container(
                        include=["Pockets", "TacticalVest"]
                    )

                    try:
                        mag = Item(tpl=magazine_template.id)
                        container.place_randomly(item=mag)
                        self.bot_inventory.add_item(
                            self.make_ammo(ammo_type, mag, cartridges.max_count)
                        )
                        break
                    except NoSpaceError:
                        pass

    @staticmethod
    def make_ammo(ammo_template: ItemTemplate, parent: Item, count: int) -> Item:
        return Item(
            tpl=ammo_template.id,
            parent_id=parent.id,
            slot_id="cartridges",
            location=ItemAmmoStackPosition(0),
            upd=ItemUpd(StackObjectsCount=count, SpawnedInSession=True),
        )
