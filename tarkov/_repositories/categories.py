from typing import Dict, List, NewType, Optional, Union

import pydantic

from server import db_dir
from tarkov.inventory.models import Item
from tarkov.inventory.types import TemplateId
from tarkov.models import Base

CategoryId = NewType("CategoryId", str)


class CategoryModel(Base):
    Id: CategoryId
    ParentId: Optional[CategoryId]
    Icon: str
    Color: str = ""
    Order: str


class TemplateCategoryModel(Base):
    Id: TemplateId
    ParentId: CategoryId
    Price: int


class CategoryRepository:
    def __init__(self):
        self.categories = self._read_categories()
        self.template_categories = self._read_template_categories()

    @staticmethod
    def _read_categories() -> Dict[CategoryId, CategoryModel]:
        categories: List[CategoryModel] = pydantic.parse_file_as(
            List[CategoryModel],
            db_dir.joinpath("templates", "categories.json"),
        )
        return {category.Id: category for category in categories}

    @staticmethod
    def _read_template_categories() -> Dict[TemplateId, TemplateCategoryModel]:
        template_categories: List[TemplateCategoryModel] = pydantic.parse_file_as(
            List[TemplateCategoryModel],
            db_dir.joinpath("templates", "items.json"),
        )
        return {tpl.Id: tpl for tpl in template_categories}

    def get_category(self, item: Union[Item, TemplateId]) -> CategoryModel:
        if isinstance(item, Item):
            item = item.tpl
        tpl_category = self.template_categories[item]
        return self.categories[tpl_category.ParentId]

    def has_parent_category(
        self, category: CategoryModel, category_id: CategoryId, including_self=True
    ):
        child_category = category
        if including_self and child_category.Id == category_id:
            return True

        while child_category.ParentId in self.categories:
            child_category = self.categories[child_category.ParentId]
            if child_category.Id == category_id:
                return True


category_repository = CategoryRepository()
