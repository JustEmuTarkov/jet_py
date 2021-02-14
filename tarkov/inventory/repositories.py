import copy
from typing import Dict, Iterable, List, Tuple, Union

import pydantic
import ujson
from pydantic import parse_obj_as

from server import db_dir
from tarkov.exceptions import NotFoundError
from .helpers import generate_item_id, regenerate_items_ids
from .models import Item, ItemTemplate, ItemUpdMedKit, NodeTemplate
from .prop_models import MedsProps
from .types import TemplateId

AnyTemplate = Union[ItemTemplate, NodeTemplate]


class ItemTemplatesRepository:
    def __init__(self):
        items, nodes = self.__read_templates()
        self._item_templates: Dict[TemplateId, ItemTemplate] = items
        self._node_templates: Dict[TemplateId, NodeTemplate] = nodes
        self._item_categories: dict = self.__read_item_categories()
        self.globals = ujson.load(
            db_dir.joinpath("base", "globals.json").open(encoding="utf8")
        )

    @staticmethod
    def __read_templates() -> Tuple[
        Dict[TemplateId, ItemTemplate],
        Dict[TemplateId, NodeTemplate],
    ]:
        item_templates: List[ItemTemplate] = []
        node_templates: List[NodeTemplate] = []

        # Read every file from db/items
        for item_file_path in db_dir.joinpath("items").glob("*"):
            file_data: List[dict] = ujson.load(
                item_file_path.open("r", encoding="utf8")
            )
            item_templates.extend(
                pydantic.parse_obj_as(
                    List[ItemTemplate],
                    (item for item in file_data if item["_type"] == "Item"),
                )
            )
            node_templates.extend(
                pydantic.parse_obj_as(
                    List[NodeTemplate],
                    (item for item in file_data if item["_type"] == "Node"),
                )
            )
        return (
            {tpl.id: tpl for tpl in item_templates},
            {tpl.id: tpl for tpl in node_templates},
        )

    @staticmethod
    def __read_item_categories():
        items = ujson.load(
            db_dir.joinpath("templates", "items.json").open("r", encoding="utf8")
        )
        items = {item["Id"]: item for item in items}
        return items

    @property
    def templates(self):
        return self._item_templates

    @property
    def client_items_view(self) -> Dict[TemplateId, AnyTemplate]:
        return {**self._item_templates, **self._node_templates}

    def get_template(self, item: Union[Item, TemplateId]) -> ItemTemplate:
        """
        Returns template of item
        """
        item_template = self.get_any_template(item)

        if isinstance(item_template, NodeTemplate):
            raise NotFoundError(
                f"Can not found ItemTemplate with id {item_template.id}, however NodeTemplate was found."
            )

        return item_template

    def get_any_template(
            self, item: Union[Item, TemplateId]
    ) -> Union[NodeTemplate, ItemTemplate]:
        if isinstance(item, Item):
            template_id = item.tpl
        else:
            template_id = item

        try:
            item_template = self._item_templates[template_id]
        except KeyError as error:
            raise NotFoundError(
                f"Can not found any template with id {template_id}"
            ) from error

        return item_template

    def iter_template_children(
            self, template_id: TemplateId
    ) -> Iterable[Union[NodeTemplate, ItemTemplate]]:
        templates: List[Union[NodeTemplate, ItemTemplate]] = [
            self.get_any_template(template_id)
        ]
        while templates:
            template = templates.pop()
            yield template

            for child in self._item_templates.values():
                if child.parent == template.id:
                    templates.append(child)

    def get_template_items(self, template_id: TemplateId) -> List[ItemTemplate]:
        """
        Returns all items of given category (all barter items for example)

        :param template_id:
        :return: All items of a category
        """
        template = self.get_any_template(template_id)
        if isinstance(template, ItemTemplate):
            return [template]
        return [
            tpl
            for tpl in self.iter_template_children(template_id)
            if isinstance(tpl, ItemTemplate)
        ]

    def get_category(self, item: Item):
        return self._item_categories[item.tpl]["ParentId"]

    def get_preset(self, template_id: TemplateId) -> dict:
        """
        :param template_id:
        :return: Preset of an item from globals
        """
        item_presets = self.globals["ItemPresets"]
        try:
            items = copy.deepcopy(item_presets[template_id]["_items"])
            regenerate_items_ids(items)
            return items
        except KeyError as e:
            raise NotFoundError() from e

    @staticmethod
    def __create_item(item_template: ItemTemplate, count: int = 1) -> Item:
        """
        Creates new item stack with size of :count:

        :param item_template: Item template to create item from
        :param count: Amount of items in stack
        :return: new Item
        """
        item = Item(
            id=generate_item_id(),
            tpl=item_template.id,
        )

        if count > 1:
            item.upd.StackObjectsCount = count

        #  Item is either medkit or a painkiller
        if item_template.parent in (
                "5448f39d4bdc2d0a728b4568",
                "5448f3a14bdc2d27728b4569",
        ):
            assert isinstance(item_template.props, MedsProps)

            medkit_max_hp = item_template.props.MaxHpResource
            assert medkit_max_hp is not None

            item.upd.MedKit = ItemUpdMedKit(HpResource=medkit_max_hp)

        return item

    @staticmethod
    def create_item(template_id: TemplateId, count: int = 1) -> List[Item]:
        if count == 0:
            raise ValueError("Cannot create 0 items")

        #  Try to return a preset if it exists
        try:
            item: dict = item_templates_repository.get_preset(template_id)
            return [parse_obj_as(Item, item)]
        except NotFoundError:
            pass

        item_template = item_templates_repository.get_template(template_id)

        #  If we need only one item them we will just return it
        if count == 1:
            return [ItemTemplatesRepository.__create_item(item_template)]

        items: List[Item] = []
        stack_size = item_template.props.StackMaxSize

        #  Create multiple stacks of items (Say 80 rounds of 5.45 ammo it will create two stacks (60 and 20))
        for _ in range(count, stack_size, count):
            items.append(ItemTemplatesRepository.__create_item(item_template, count))

        if stack_size % count:
            items.append(
                ItemTemplatesRepository.__create_item(item_template, stack_size % count)
            )

        return items


item_templates_repository = ItemTemplatesRepository()
