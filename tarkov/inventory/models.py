from __future__ import annotations

import datetime
import enum
from typing import Any, Dict, List, Literal, NewType, Optional, TYPE_CHECKING, Union

from pydantic import (
    Extra,
    Field,
    PrivateAttr,
    StrictBool,
    ValidationError,
    root_validator,
    validator,
)

from server import logger
from tarkov.inventory.prop_models import (
    AnyProp,
    BaseItemProps,
    FilterProperty,
    props_models_map,
)
from tarkov.inventory.types import ItemId, TemplateId
from tarkov.models import Base

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.inventory import MutableInventory


class NodeTemplateBase(Base):
    class Config:
        extra = Extra.allow

        allow_mutation = False
        fields = {
            "id": "_id",
            "name": "_name",
            "parent": "_parent",
            "type": "_type",
            "props": "_props",
            "proto": "_proto",
        }

    id: TemplateId
    name: str
    parent: TemplateId
    proto: Optional[str] = None


class NodeTemplate(NodeTemplateBase):
    type: Literal["Node"]


class ItemTemplate(NodeTemplateBase):
    type: Literal["Item"]
    props: AnyProp

    @root_validator(pre=True)
    def assign_prop(cls, values: dict) -> dict:  # pylint: disable=no-self-argument, no-self-use
        if values["_type"] != "Item":
            return values
        if isinstance(values["_props"], BaseItemProps):
            return values

        props = values["_props"]
        try:
            model = props_models_map[values["_parent"]]
        except KeyError as e:
            raise KeyError(f"Props class for node with id {values['_parent']} was not found") from e
        try:
            values["_props"] = model.parse_obj(props)
        except ValidationError as e:
            logger.debug(values["_id"])
            logger.debug(e)
            raise
        return values

    def has_in_slots(self, template_id: TemplateId) -> bool:
        """
        Checks if  template has template_id in one of it's filters
        """
        props = self.props
        for slot_filter in ("Cartridges", "Chambers", "Slots"):
            if not hasattr(props, slot_filter):
                continue

            filters: List[FilterProperty] = getattr(props, slot_filter)
            for slot in filters:
                for filter_group in slot.props.filters:
                    if template_id in filter_group.Filter:
                        return True
        return False


class ItemUpdDogtag(Base):
    AccountId: str
    ProfileId: str
    Nickname: str
    Side: str
    Level: int
    Time: datetime.datetime
    Status: str
    KillerAccountId: str
    KillerProfileId: str
    KillerName: str
    WeaponName: str


class ItemUpdTag(Base):
    Name: Optional[str]
    Color: Optional[int]


class ItemUpdTogglable(Base):
    On: bool


class ItemUpdFaceShield(Base):
    Hits: int
    HitSeed: int


class ItemUpdLockable(Base):
    Locked: bool


class ItemUpdRepairable(Base):
    MaxDurability: Optional[float] = None  # TODO: Some items in bot inventories don't have MaxDurability
    Durability: float


class ItemUpdFoldable(Base):
    Folded: bool


class ItemUpdFireMode(Base):
    FireMode: str


class ItemUpdResource(Base):
    Value: float


class ItemUpdFoodDrink(Base):
    HpPercent: int


class ItemUpdKey(Base):
    NumberOfUsages: int


class ItemUpdMedKit(Base):
    HpResource: int


class ItemUpd(Base):
    StackObjectsCount: int = 1
    SpawnedInSession: bool = False
    Repairable: Optional[ItemUpdRepairable] = None
    Foldable: Optional[ItemUpdFoldable] = None
    FireMode: Optional[ItemUpdFireMode] = None
    Resource: Optional[ItemUpdResource] = None
    FoodDrink: Optional[ItemUpdFoodDrink] = None
    Key: Optional[ItemUpdKey] = None
    MedKit: Optional[ItemUpdMedKit] = None
    Lockable: Optional[ItemUpdLockable] = None
    Sight: Optional[Any] = None
    Light: Optional[Any] = None
    FaceShield: Optional[ItemUpdFaceShield] = None
    Togglable: Optional[ItemUpdTogglable] = None
    Tag: Optional[ItemUpdTag] = None
    Dogtag: Optional[ItemUpdDogtag] = None
    UnlimitedCount: StrictBool = False

    def folded(self) -> bool:
        return self.Foldable is not None and self.Foldable.Folded


ItemAmmoStackPosition = NewType("ItemAmmoStackPosition", int)

ItemOrientation = Literal["Horizontal", "Vertical"]


class ItemOrientationEnum(enum.Enum):
    Horizontal = "Horizontal"
    Vertical = "Vertical"


class ItemInventoryLocation(Base):
    x: int
    y: int
    r: str = ItemOrientationEnum.Vertical.value
    isSearched: Optional[bool] = None

    @validator("r", pre=True)
    def validate_rotation(cls, value: Any) -> Any:  # pylint: disable=no-self-argument, no-self-use
        if value == 1:
            return ItemOrientationEnum.Vertical.value
        if value == 0:
            return ItemOrientationEnum.Horizontal.value
        return value


AnyItemLocation = Union[ItemInventoryLocation, ItemAmmoStackPosition]


class Item(Base):
    class Config:
        extra = Extra.forbid

    __inventory__: Optional["MutableInventory"] = PrivateAttr(default=None)  # Link to the inventory

    id: ItemId = Field(alias="_id")
    tpl: TemplateId = Field(alias="_tpl")
    slot_id: Optional[str] = Field(alias="slotId")
    parent_id: Optional[ItemId] = Field(alias="parentId", default=None)
    location: Optional[AnyItemLocation] = None
    upd: ItemUpd = Field(default_factory=ItemUpd)

    def get_inventory(self) -> "MutableInventory":
        if self.__inventory__ is None:
            raise ValueError("Item does not have inventory")
        return self.__inventory__

    # @root_validator(pre=False, skip_on_failure=True)
    # def validate_medkit_hp(cls, values: dict) -> dict:  # pylint: disable=no-self-argument,no-self-use
    #     if "id" not in values:
    #         return values
    #
    #     item_tpl_id: TemplateId = cast(TemplateId, values.get("tpl"))
    #     item_template = tarkov.inventory.item_templates_repository.get_template(item_tpl_id)
    #     if item_template.parent == "5448f39d4bdc2d0a728b4568":  # Medkit Id
    #         assert isinstance(item_template.props, MedsProps)
    #         upd: ItemUpd = cast(ItemUpd, values.get("upd"))
    #         if not isinstance(item_template.props.MaxHpResource, int):
    #             raise ResourceWarning(
    #                 f"""Item template that inherits directly form MedKit does not have MaxHpResource property
    #                 template id: {item_template.id}
    #                 """
    #             )
    #         upd.MedKit = (
    #             upd.MedKit if upd.MedKit else ItemUpdMedKit(HpResource=item_template.props.MaxHpResource)
    #         )
    #
    #     return values
    #
    # @root_validator(pre=False, skip_on_failure=True)
    # def validate_upd_none(cls, values: dict) -> dict:  # pylint: disable=no-self-argument,no-self-use
    #     if "upd" in values and values["upd"] is None:
    #         values["upd"] = ItemUpd()
    #
    #     return values

    def copy(self: Item, **kwargs: Any) -> Item:
        item_inventory = self.__inventory__
        # Avoid copying inventory
        self.__inventory__ = None
        item_copy: Item = super().copy(**kwargs)

        self.__inventory__ = item_inventory

        return item_copy

    def __hash__(self) -> int:
        return hash(self.id)


class InventoryModel(Base):
    class Config(Base.Config):
        pass

    equipment: ItemId
    stash: ItemId
    questRaidItems: ItemId
    questStashItems: ItemId
    fastPanel: Dict[str, ItemId]
    items: List[Item]


class MoveLocation(Base):
    id: ItemId
    container: str
    location: Optional[ItemInventoryLocation]


class CartridgesMoveLocation(Base):
    id: ItemId  # Magazine id
    container: Literal["cartridges"]


AnyMoveLocation = Union[
    CartridgesMoveLocation,
    MoveLocation,
]
