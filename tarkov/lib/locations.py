from __future__ import annotations

import collections
import random
from typing import DefaultDict, Dict, List, Tuple, Union

import ujson
from pydantic import parse_obj_as

from server import db_dir
from tarkov.exceptions import NoSpaceError
from tarkov.inventory import GridInventory, StashMap, item_templates_repository
from tarkov.inventory.helpers import generate_item_id, regenerate_item_ids_dict
from tarkov.inventory.models import AnyItemLocation, Item, ItemId, ItemTemplate, TemplateId
from tarkov.models import Base


class ContainerInventoryModel(Base):
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
    container: ContainerInventoryModel

    def __init__(self, container: dict):
        self.container = parse_obj_as(ContainerInventoryModel, container)

        root_item = self.get_item(self.container.Root)
        self.template = item_templates_repository.get_template(root_item.tpl)
        self.stash_map = StashMap(self)

    @property
    def root_id(self) -> ItemId:
        return self.container.Root

    @property
    def grid_size(self) -> Tuple[int, int]:
        # Let's assume we have only one grid
        assert self.template.props.Grids is not None
        grid_props = self.template.props.Grids[0].props
        return grid_props.width, grid_props.height

    @property
    def items(self) -> List[Item]:
        return self.container.Items

    def place_item(self, item: Item, *, children_items: List[Item] = None, location: AnyItemLocation = None):
        super().place_item(item, children_items=children_items, location=location)
        item.slotId = 'main'


class LocationGenerator:
    def __init__(self, location: str):
        location_file_path = db_dir.joinpath('locations', f'{location}.json')
        self.__location: dict = ujson.load(location_file_path.open(encoding='utf8'))
        self.__base: dict = self.__location['base']
        self.__loot: dict = self.__location['loot']

        # Cache to store pairs of categories and it's items
        # for example - Medkits category and all it's medkits
        self.__category_cache: Dict[str, List[ItemTemplate]] = {}

    def generate_location(self) -> dict:
        self.__generate_location_loot()
        return self.__base

    def __generate_location_loot(self):
        for container in self.__loot['static']:
            self.__populate_container(container)
            self.__base['Loot'].append(container)

        dynamic_loot_locations: DefaultDict[str, list] = collections.defaultdict(list)

        for dynamic_loot in self.__loot['dynamic']:
            dynamic_loot = dynamic_loot['data'][0]
            position = dynamic_loot['Position']
            position = ';'.join(str(position[key]) for key in 'xyz')

            regenerate_item_ids_dict(dynamic_loot['Items'])
            dynamic_loot['Id'] = dynamic_loot['Items'][0]['_id']
            dynamic_loot['Root'] = dynamic_loot['Items'][0]['_id']

            dynamic_loot_locations[position].append(dynamic_loot)

        self.__base['Loot'].extend(random.choice(loot) for loot in dynamic_loot_locations.values())

    def __get_category_items(self, template_id: TemplateId) -> List[ItemTemplate]:
        if template_id not in self.__category_cache:
            self.__category_cache[template_id] = list(
                tpl for tpl in item_templates_repository.iter_template_children(template_id)
                if isinstance(tpl, ItemTemplate)
            )

        return self.__category_cache[template_id]

    def __populate_container(self, container: dict):
        """
        Populates given container with items
        Mutates the container argument
        """
        container_id = container['Root']
        container_template = item_templates_repository.get_template(container['Items'][0]['_tpl'])

        assert container_template.props.SpawnFilter is not None
        container_filter_templates: List[TemplateId] = container_template.props.SpawnFilter

        mean, deviation = 2.5, 2.5
        amount_of_items_in_container = max(round(random.gauss(mean, deviation)), 0)

        container_inventory = ContainerInventory(container)

        item_templates: List[ItemTemplate] = []
        for template_id in container_filter_templates:
            item_templates.extend(self.__get_category_items(template_id))

        item_template_weights = [self.__template_weight(tpl) for tpl in item_templates]

        if not item_templates:
            return

        for _ in range(amount_of_items_in_container):
            retries = 10
            for _ in range(retries):
                random_template = random.choices(item_templates, item_template_weights, k=1)[0]

                item = Item(
                    id=generate_item_id(),
                    tpl=random_template.id,
                    parent_id=container_id,
                    slotId='main',
                )
                try:
                    container_inventory.place_item(item)
                    break
                except NoSpaceError:
                    pass

        container['Items'] = container_inventory.container.dict()['Items']

    @staticmethod
    def __template_weight(template: ItemTemplate) -> Union[int, float]:
        # rarity_coefficients = {
        #     'Common': 1,
        #     'Rare': 0.4,
        #     'Superrare': 0.1,
        #     'Not_exist': 0,
        # }
        # template_rarity = template.props.Rarity
        # spawn_chance_coefficient = rarity_coefficients[template_rarity]
        # return template['_props']['SpawnChance'] * spawn_chance_coefficient
        return template.props.SpawnChance
