from __future__ import annotations

import collections
import random
from typing import Any, ClassVar, DefaultDict, Dict, Final, List, Tuple, Union

import ujson

from server import db_dir
from tarkov.exceptions import NoSpaceError
from tarkov.inventory import (
    GridInventory,
    GridInventoryStashMap,
    item_templates_repository,
)
from tarkov.inventory.helpers import regenerate_item_ids_dict
from tarkov.inventory.models import Item, ItemTemplate
from tarkov.inventory.prop_models import CompoundProps, LootContainerProps, StackableItemProps
from tarkov.inventory.factories import item_factory
from tarkov.inventory.types import ItemId, TemplateId
from tarkov.models import Base


class ContainerModel(Base):
    Id: str
    IsStatic: bool
    useGravity: bool
    randomRotation: bool
    IsGroupPosition: bool
    Root: ItemId
    Position: dict
    Rotation: dict
    GroupPositions: list
    Items: List[Item]


class ContainerInventory(GridInventory):
    container: ContainerModel

    def __init__(self, container: ContainerModel):
        self.container = container
        self._items = {i.id: i for i in self.container.Items}

        root_item = self.get(self.container.Root)
        self.template = item_templates_repository.get_template(root_item.tpl)
        self.stash_map = GridInventoryStashMap(self)

    @property
    def items_list_view(self) -> List[dict]:
        return list(i.dict(exclude_none=True) for i in self._items.values())

    @property
    def root_id(self) -> ItemId:
        return self.container.Root

    @property
    def grid_size(self) -> Tuple[int, int]:
        # Let's assume we have only one grid
        assert isinstance(self.template.props, CompoundProps)
        grid_props = self.template.props.Grids[0].props
        return grid_props.width, grid_props.height

    @property
    def items(self) -> Dict[ItemId, Item]:
        return self._items

    def place_item(
        self,
        item: Item,
        **kwargs: Any,
    ) -> None:
        super().place_item(item, **kwargs)
        item.slot_id = "main"


class ContainerLootGenerator:
    ATTEMPTS_TO_PLACE_LOOT: Final[ClassVar[int]] = 10

    def __init__(self, location_generator: LocationGenerator, container: ContainerModel):
        # Reference to location generator
        self.location_generator = location_generator
        # Container model
        self.container = container

        self.container_template = item_templates_repository.get_template(container.Items[0].tpl)
        assert isinstance(self.container_template.props, LootContainerProps)

        # List of item templates that are allowed to spawn inside container
        self.__item_templates: List[ItemTemplate] = []
        for template_id in self.container_template.props.SpawnFilter:
            self.__item_templates.extend(self.location_generator.get_category_items(template_id))
        # Chances of templates to spawn
        self.__item_templates_weights: List[float] = [
            self.location_generator.template_weight(tpl) for tpl in self.__item_templates
        ]

    @staticmethod
    def __get_amount_of_items() -> int:
        """Returns amount of items that should be generated in container"""
        mean, deviation = 2.5, 2.5
        return max(round(random.gauss(mean, deviation)), 0)

    def __generate_random_item(self) -> Tuple[Item, List[Item]]:
        """Generates random item for this container"""
        random_template = random.choices(self.__item_templates, self.__item_templates_weights, k=1)[0]
        count = 1
        if isinstance(random_template.props, StackableItemProps):
            count = random.randint(random_template.props.StackMinRandom, random_template.props.StackMaxRandom)

        return item_factory.create_item(random_template, count=count)

    def generate_items(self) -> List[Item]:
        """Generates list of items for container"""

        # If no templates can spawn we can safely return empty list
        if not self.__item_templates:
            return []

        container_inventory = ContainerInventory(self.container)

        for _ in range(self.__get_amount_of_items()):
            for _ in range(self.ATTEMPTS_TO_PLACE_LOOT):
                try:
                    item, children = self.__generate_random_item()
                    container_inventory.place_item(item, child_items=children)
                    break
                except NoSpaceError:
                    pass
        return list(container_inventory.items.values())


class LocationGenerator:
    def __init__(self, location: str):
        location_file_path = db_dir.joinpath("locations", f"{location}.json")
        self.__location: dict = ujson.load(location_file_path.open(encoding="utf8"))
        self.__base: dict = self.__location["base"]
        self.__loot: dict = self.__location["loot"]

        # Cache to store pairs of categories and it's items
        # for example - Medkits category and all it's medkits
        self.__category_cache: Dict[str, List[ItemTemplate]] = {}

    def generate_location(self) -> dict:
        self._generate_containers_loot()
        self._generate_dynamic_loot()
        return self.__base

    def _generate_containers_loot(self) -> None:
        for container in self.__loot["static"]:
            container_model = ContainerModel.parse_obj(container)
            container_generator = ContainerLootGenerator(self, container_model)
            container_model.Items = container_generator.generate_items()

            self.__base["Loot"].append(container_model.dict(exclude_none=True))

    def _generate_dynamic_loot(self) -> None:
        # Grouping containers by their positions in world
        dynamic_loot_locations: DefaultDict[str, list] = collections.defaultdict(list)
        for dynamic_loot in self.__loot["dynamic"]:
            dynamic_loot = dynamic_loot["data"][0]
            position = dynamic_loot["Position"]
            position = ";".join(str(position[key]) for key in "xyz")
            dynamic_loot_locations[position].append(dynamic_loot)

        for position, loot_points in dynamic_loot_locations.items():
            loot_point = random.choice(loot_points)

            regenerate_item_ids_dict(loot_point["Items"])
            root_item = loot_point["Items"][0]
            loot_point["Root"] = loot_point["Items"][0]["_id"]

            root_item_template = item_templates_repository.get_template(root_item["_tpl"])
            should_spawn = random.uniform(0, 100) < root_item_template.props.SpawnChance
            if not should_spawn:
                continue

            self.__base["Loot"].append(loot_point)

    def get_category_items(self, template_id: TemplateId) -> List[ItemTemplate]:
        if template_id not in self.__category_cache:
            self.__category_cache[template_id] = list(
                tpl for tpl in item_templates_repository.get_template_items(template_id)
            )

        return self.__category_cache[template_id]

    def template_weight(self, template: ItemTemplate) -> Union[int, float]:
        if (
            template.props.AllowSpawnOnLocations
            and not self.__base["Id"] in template.props.AllowSpawnOnLocations
        ):
            return 0

        rarity_coefficients = {
            "Common": 1,
            "Rare": 1,
            "Superrare": 1,
            "Not_exist": 0,
        }
        template_rarity = template.props.Rarity
        spawn_chance_coefficient = rarity_coefficients[template_rarity]
        return template.props.SpawnChance * spawn_chance_coefficient
