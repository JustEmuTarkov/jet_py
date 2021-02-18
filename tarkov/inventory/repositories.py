import copy
from typing import Dict, Iterable, List, Tuple, Union

import pydantic
import ujson

from server import db_dir
from tarkov.exceptions import NotFoundError
from .helpers import generate_item_id, regenerate_items_ids
from .models import Item, ItemTemplate, ItemUpdMedKit, ItemUpdResource, NodeTemplate
from .prop_models import FuelProps, MedsProps
from .types import ItemId, TemplateId
from ..repositories.categories import CategoryId

AnyTemplate = Union[ItemTemplate, NodeTemplate]


class ItemTemplatesRepository:
    def __init__(self) -> None:
        items, nodes = self.__read_templates()
        self._item_templates: Dict[TemplateId, ItemTemplate] = items
        self._node_templates: Dict[TemplateId, NodeTemplate] = nodes
        self._item_categories: dict = self.__read_item_categories()
        self.globals = ujson.load(db_dir.joinpath("base", "globals.json").open(encoding="utf8"))

    @staticmethod
    def __read_templates() -> Tuple[
        Dict[TemplateId, ItemTemplate],
        Dict[TemplateId, NodeTemplate],
    ]:
        item_templates: List[ItemTemplate] = []
        node_templates: List[NodeTemplate] = []

        # Read every file from db/items
        for item_file_path in db_dir.joinpath("items").glob("*"):
            file_data: List[dict] = ujson.load(item_file_path.open("r", encoding="utf8"))
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
    def __read_item_categories() -> dict:
        items = ujson.load(db_dir.joinpath("templates", "items.json").open("r", encoding="utf8"))
        items = {item["Id"]: item for item in items}
        return items

    @property
    def templates(self) -> Dict[TemplateId, ItemTemplate]:
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

    def get_any_template(self, item: Union[Item, TemplateId]) -> Union[NodeTemplate, ItemTemplate]:
        if isinstance(item, Item):
            template_id = item.tpl
        else:
            template_id = item

        try:
            item_template = self._item_templates[template_id]
        except KeyError as error:
            raise NotFoundError(f"Can not found any template with id {template_id}") from error

        return item_template

    def iter_template_children(self, template_id: TemplateId) -> Iterable[Union[NodeTemplate, ItemTemplate]]:
        templates: List[Union[NodeTemplate, ItemTemplate]] = [self.get_any_template(template_id)]
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
        return [tpl for tpl in self.iter_template_children(template_id) if isinstance(tpl, ItemTemplate)]

    def get_category(self, item: Item) -> CategoryId:
        return self._item_categories[item.tpl]["ParentId"]

    def get_preset(self, template_id: TemplateId) -> Tuple[Item, List[Item]]:
        """
        :param template_id:
        :return: Preset of an item from globals
        """
        item_presets = self.globals["ItemPresets"]
        try:
            preset = copy.deepcopy(item_presets[template_id])
        except KeyError as e:
            raise NotFoundError() from e
        root_item_id: ItemId = preset["_parent"]
        # All the items in preset
        items: List[Item] = pydantic.parse_obj_as(List[Item], preset["_items"])
        # Let's grab root item (parent) And remove it from items list
        root_item = next(i for i in items if i.id == root_item_id)
        items.remove(root_item)

        # Regenerate item ids
        regenerate_items_ids([root_item, *items])
        return root_item, items

    @staticmethod
    def create_item(item_template: ItemTemplate, count: int = 1) -> Tuple[Item, List[Item]]:
        try:
            return item_templates_repository.get_preset(item_template.id)
        except NotFoundError:
            pass

        if count > item_template.props.StackMaxSize:
            raise ValueError(
                f"Trying to create item with template id {item_template} with stack size "
                f"of {count} but maximum stack size is {item_template.props.StackMaxSize}"
            )

        item = Item(
            id=generate_item_id(),
            tpl=item_template.id,
        )

        if count > 1:
            item.upd.StackObjectsCount = count

        #  Item is either medkit or a painkiller
        if isinstance(item_template.props, MedsProps):
            medkit_max_hp = item_template.props.MaxHpResource

            item.upd.MedKit = ItemUpdMedKit(HpResource=medkit_max_hp)

        if isinstance(item_template.props, FuelProps):
            item.upd.Resource = ItemUpdResource(Value=item_template.props.MaxResource)

        item.parent_id = None
        return item, []

    @staticmethod
    def create_items(template_id: TemplateId, count: int = 1) -> List[Tuple[Item, List[Item]]]:
        """
        Returns list of Tuple[Root Item, [Child items]
        """
        if count == 0:
            raise ValueError("Cannot create 0 items")

        item_template = item_templates_repository.get_template(template_id)

        #  If we need only one item them we will just return it
        if count == 1:
            return [ItemTemplatesRepository.create_item(item_template)]

        items: List[Tuple[Item, List[Item]]] = []
        stack_max_size = item_template.props.StackMaxSize

        #  Create multiple stacks of items (Say 80 rounds of 5.45 ammo it will create two stacks (60 and 20))
        amount_to_create = count
        while amount_to_create > 0:
            stack_size = min(stack_max_size, amount_to_create)
            amount_to_create -= stack_size
            root, children = ItemTemplatesRepository.create_item(item_template, stack_size)
            root.slot_id = None

            items.append((root, children))

        return items


item_templates_repository = ItemTemplatesRepository()
