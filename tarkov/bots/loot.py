from __future__ import annotations

import random
from typing import Dict, Generic, List, Optional, Sequence, TYPE_CHECKING, Tuple, TypeVar

from pydantic import BaseModel, Field, PrivateAttr
from pydantic.generics import GenericModel

from tarkov.exceptions import NoSpaceError, NotFoundError
from tarkov.inventory import item_templates_repository
from tarkov.inventory.factories import item_factory
from tarkov.inventory.implementations import MultiGridContainer
from tarkov.inventory.models import Item, ItemAmmoStackPosition, ItemTemplate, ItemUpd
from tarkov.inventory.prop_models import MagazineProps, MagazineReloadType, MedsProps
from tarkov.inventory.types import TemplateId

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.bots.bots import BotGenerator, BotInventory

T = TypeVar("T")  # pylint: disable=invalid-name


class MinMax(GenericModel, Generic[T]):
    max: T
    min: T


class LootGenerationConfig(BaseModel):
    healing: MinMax[int]
    loose_loot: MinMax[int] = Field(alias="looseLoot")
    magazines: MinMax[int]
    grenades: MinMax[int]


class BotInventoryContainers(BaseModel):
    """
    Class to hold containers for backpack, rig and pockets
    """

    class Config:
        arbitrary_types_allowed = True

    __bot_inventory__: BotInventory = PrivateAttr()

    TacticalVest: Optional[MultiGridContainer]
    Pockets: MultiGridContainer
    Backpack: Optional[MultiGridContainer]

    def containers(self, include: Sequence[str] = None) -> Sequence[MultiGridContainer]:
        """
        :param include: List of slot ids to include, includes everything by default
        :return: Sequence of containers with slot_id that are present in include parameter
        """
        if not include:
            include = tuple(self.__fields__.keys())

        for slot_id in include:
            if slot_id not in self.__fields__:
                raise ValueError(
                    f"{slot_id} element of include argument is not present in fields of {self.__class__.__name__}"
                )

        containers = []

        for slot_id in self.__fields__:
            if slot_id not in include:
                continue
            container: Optional[MultiGridContainer] = self.__getattribute__(slot_id)
            if container is None:
                continue

            containers.append(container)

        return containers

    @classmethod
    def from_inventory(cls, bot_inventory: BotInventory) -> BotInventoryContainers:
        containers: Dict[str, MultiGridContainer] = {}
        for slot_id in cls.__fields__:
            try:
                containers[slot_id] = MultiGridContainer.from_item(
                    bot_inventory.get_equipment(slot_id), slot_id
                )
            except NotFoundError:
                pass

        obj = cls.parse_obj(
            containers,
        )
        obj.__bot_inventory__ = bot_inventory
        return obj

    def flush(self) -> None:
        """
        Flushes inventories items into bot inventory
        """
        for container in self.containers():
            for sub_inventory in container.inventories:
                self.__bot_inventory__.items.update(sub_inventory.items)

    def random_container(self, include: Sequence[str] = None) -> MultiGridContainer:
        """
        :param include: slot id's to include, will include all containers if none
        :return: Randomly chosen container, weighted by it's size
        """
        containers = self.containers(include=include)
        weights = [container.size for container in containers]

        return random.choices(containers, weights=weights, k=1)[0]


class MedsGenerator:
    def __init__(self, bot_loot_generator: BotLootGenerator):
        self.bot_loot_generator = bot_loot_generator

        self._meds_templates = [
            tpl
            for tpl in item_templates_repository.templates.values()
            if isinstance(tpl.props, MedsProps) and tpl.props.Rarity != "Not_Exists"
        ]

    def generate(self, amount: int) -> None:
        """
        Generates med items in tactical vest and pockets

        :param amount: Amount of med items to generate
        :return: None
        """
        inventory_containers = self.bot_loot_generator.bot_inventory_containers
        for _ in range(amount):
            container = inventory_containers.random_container(include=["TacticalVest", "Pockets"])
            try:
                container.place_randomly(self._make_random_meds())
            except NoSpaceError:
                pass

    def _make_random_meds(self) -> Item:
        template = random.choices(
            population=self._meds_templates,
            weights=[tpl.props.SpawnChance for tpl in self._meds_templates],
            k=1,
        )[0]
        return Item(tpl=template.id)


class LooseLootGenerator:
    def __init__(self, bot_loot_generator: BotLootGenerator):
        self.bot_loot_generator = bot_loot_generator
        self.inventory_preset: dict = self.bot_loot_generator.bot_generator.inventory_preset

    def generate(self, amount: int) -> None:
        """
        Generates loose loot items in backpack, tactical vest or pockets.

        :param amount: Amount of items to generate
        :return: None
        """
        inventory_containers = self.bot_loot_generator.bot_inventory_containers
        for _ in range(amount):
            for _ in range(10):
                try:
                    container = inventory_containers.random_container()
                    item, child_items = self._make_random_item(container.slot_id)
                    container.place_randomly(item, child_items)
                    break
                except NoSpaceError:
                    continue

    def _make_random_item(self, slot_id: str) -> Tuple[Item, List[Item]]:
        templates: List[ItemTemplate] = [
            item_templates_repository.get_template(tpl) for tpl in self.inventory_preset["items"][slot_id]
        ]
        templates_chances: List[float] = [t.props.SpawnChance for t in templates]
        item_template: ItemTemplate = random.choices(templates, templates_chances, k=1)[0]
        return item_factory.create_item(item_template, 1)


class BotMagazineGenerator:
    ATTEMPTS_TO_PLACE = 10

    def __init__(self, bot_loot_generator: BotLootGenerator):
        self.bot_loot_generator = bot_loot_generator
        self.bot_inventory = self.bot_loot_generator.bot_inventory

        self.magazines_to_generate = random.randint(
            self.bot_loot_generator.config.magazines.min,
            self.bot_loot_generator.config.magazines.max,
        )

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
            item_template = item_templates_repository.get_template(item.tpl)
            if isinstance(item_template.props, MagazineProps) and item.parent_id == weapon.id:
                magazine_template = item_template
                magazine_in_weapon = item
                break
        else:
            raise ValueError("Magazine wasn't found")

        assert isinstance(magazine_template.props, MagazineProps)
        cartridges = random.choice(magazine_template.props.Cartridges)
        ammo_types: List[TemplateId] = self.bot_loot_generator.bot_generator.inventory_preset["mods"][
            magazine_template.id
        ]["cartridges"]
        ammo_type = item_templates_repository.get_template(random.choice(ammo_types))

        # Generate ammo for current magazine
        self.bot_inventory.add_item(self.make_ammo(ammo_type, magazine_in_weapon, cartridges.max_count))

        reload_type = MagazineReloadType(magazine_template.props.ReloadMagType)
        containers = self.bot_loot_generator.bot_inventory_containers

        # Generate additional magazines if magazine is external
        if reload_type == MagazineReloadType.ExternalMagazine:
            for _ in range(self.magazines_to_generate):
                for _ in range(self.ATTEMPTS_TO_PLACE):
                    container = containers.random_container(include=["Pockets", "TacticalVest"])

                    try:
                        mag = Item(tpl=magazine_template.id)
                        container.place_randomly(item=mag)
                        self.bot_inventory.add_item(self.make_ammo(ammo_type, mag, cartridges.max_count))
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


class BotLootGenerator:
    bot_generator: BotGenerator
    bot_inventory: BotInventory
    config: LootGenerationConfig
    bot_inventory_containers: BotInventoryContainers

    def __init__(self, bot_generator: BotGenerator):
        self.bot_generator = bot_generator
        self.bot_inventory = self.bot_generator.bot_inventory
        self.config = LootGenerationConfig.parse_obj(bot_generator.generation_preset["items"])
        self.bot_inventory_containers = BotInventoryContainers.from_inventory(self.bot_inventory)

    def generate(self) -> None:
        """
        Generates loot in bot inventory

        :return: None
        """
        meds_generator = MedsGenerator(self)
        meds_generator.generate(random.randint(self.config.healing.min, self.config.healing.max))
        self.bot_inventory_containers.flush()

        bot_magazine_generator = BotMagazineGenerator(self)
        bot_magazine_generator.generate()

        loose_loot_generator = LooseLootGenerator(self)
        loose_loot_generator.generate(random.randint(self.config.loose_loot.min, self.config.loose_loot.max))

        self.bot_inventory_containers.flush()
