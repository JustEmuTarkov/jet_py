from typing import Dict, List, NewType, Optional, Union

import pydantic

from server import db_dir
from tarkov.inventory.types import TemplateId
from tarkov.models import Base

CategoryId = NewType("CategoryId", str)


class CategoryModel(Base):
    Id: CategoryId
    ParentId: Optional[CategoryId]
    Icon: str
    Color: str = ""
    Order: str


class ItemTemplateCategoryModel(Base):
    Id: TemplateId
    ParentId: CategoryId
    Price: int


class CategoryRepository:
    def __init__(self) -> None:
        self.categories: Dict[CategoryId, CategoryModel] = self._read_categories()
        self.item_categories: Dict[
            TemplateId, ItemTemplateCategoryModel
        ] = self._read_item_template_categories()

    @staticmethod
    def _read_categories() -> Dict[CategoryId, CategoryModel]:
        categories: List[CategoryModel] = pydantic.parse_file_as(
            List[CategoryModel],
            db_dir.joinpath("templates", "categories.json"),
        )
        return {category.Id: category for category in categories}

    @staticmethod
    def _read_item_template_categories() -> Dict[TemplateId, ItemTemplateCategoryModel]:
        template_categories: List[ItemTemplateCategoryModel] = pydantic.parse_file_as(
            List[ItemTemplateCategoryModel],
            db_dir.joinpath("templates", "items.json"),
        )
        return {tpl.Id: tpl for tpl in template_categories}

    def get_category(self, template_id: TemplateId) -> CategoryModel:
        """Returns node category for given item template"""

        tpl_category = self.item_categories[template_id]
        return self.categories[tpl_category.ParentId]

    def has_parent_category(
        self,
        category: CategoryModel,
        category_id: Union[TemplateId, CategoryId],
        including_self: bool = True,
    ) -> bool:
        child_category = category
        if including_self and child_category.Id == category_id:
            return True

        while child_category.ParentId in self.categories:
            child_category = self.categories[child_category.ParentId]
            if child_category.Id == category_id:
                return True
        return False


category_repository = CategoryRepository()
