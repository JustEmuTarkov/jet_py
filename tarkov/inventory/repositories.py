from typing import Dict, Iterable, List, Tuple, Union

import pydantic
import ujson

from server import db_dir
from tarkov.exceptions import NotFoundError
from .models import Item, ItemTemplate, NodeTemplate
from .types import TemplateId

AnyTemplate = Union[ItemTemplate, NodeTemplate]


class ItemTemplatesRepository:
    def __init__(self) -> None:
        items, nodes = self.__read_templates()
        self._item_templates: Dict[TemplateId, ItemTemplate] = items
        self._node_templates: Dict[TemplateId, NodeTemplate] = nodes
        self._item_categories: dict = self.__read_item_categories()

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

        if template_id in self._item_templates:
            return self._item_templates[template_id]

        if template_id in self._node_templates:
            return self._node_templates[template_id]

        raise NotFoundError(f"Can not found any template with id {template_id}")

    def iter_template_children(self, template_id: TemplateId) -> Iterable[Union[NodeTemplate, ItemTemplate]]:
        templates: List[Union[NodeTemplate, ItemTemplate]] = [self.get_any_template(template_id)]
        while templates:
            template = templates.pop()
            yield template

            for child_node in self._item_templates.values():
                if child_node.parent == template.id:
                    templates.append(child_node)

            for child_item in self._node_templates.values():
                if child_item.parent == template.id:
                    templates.append(child_item)

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


item_templates_repository = ItemTemplatesRepository()
