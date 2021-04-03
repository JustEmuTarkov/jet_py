from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from server import db_dir
from tarkov.exceptions import NotFoundError
from .models import GlobalsModel, ItemPreset

if TYPE_CHECKING:
    from tarkov.inventory.models import ItemTemplate


class GlobalsRepository:
    def __init__(self) -> None:
        self.globals: GlobalsModel = GlobalsModel.parse_file(db_dir.joinpath("base", "globals.json"))

    def has_preset(self, item_template: ItemTemplate) -> bool:
        return item_template.id in self.globals.ItemPresets

    def item_preset(self, item_template: ItemTemplate) -> ItemPreset:
        try:
            return self.globals.ItemPresets[item_template.id]
        except KeyError as error:
            raise NotFoundError from error
