from typing import Any, Dict, List, Tuple

from pydantic import Field, root_validator

from tarkov.inventory.helpers import regenerate_items_ids
from tarkov.inventory.models import Item
from tarkov.inventory.types import ItemId, TemplateId
from tarkov.models import Base


class ItemPreset(Base):
    change_weapon_name: bool = Field(alias="_changeWeaponName")
    encyclopedia_id: TemplateId = Field(alias="_encyclopedia")
    id: str = Field(alias="_id")  # This id is meaningful
    items: List[Item] = Field(alias="_items")
    name: str = Field(alias="_name")
    root_id: ItemId = Field(alias="_parent")  # Id of the root item in this preset
    type: str = Field(alias="_type")

    def get_items(self) -> Tuple[Item, List[Item]]:
        root_item = next(i for i in self.items if i.id == self.root_id).copy()
        children = [i.copy() for i in self.items if i != root_item]
        regenerate_items_ids([root_item, *children])
        return root_item, children


class GlobalsModel(Base):
    bot_presets: Any
    BotWeaponScatterings: Any
    config: Any
    HealthEffect: Any
    ItemPresets: Dict[TemplateId, ItemPreset]

    time: int

    @root_validator(pre=True)
    def transform_item_presets(  # pylint: disable=no-self-argument, no-self-use
        cls, values: dict
    ) -> dict:
        presets: dict = values["ItemPresets"]
        # Take only these presets that have _encyclopedia (TemplateId) In them
        values["ItemPresets"] = {
            preset["_encyclopedia"]: preset
            for preset in presets.values()
            if "_encyclopedia" in preset
        }
        return values
