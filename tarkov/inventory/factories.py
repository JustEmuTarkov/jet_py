from __future__ import annotations

from typing import List, TYPE_CHECKING, Tuple

from dependency_injector.wiring import inject

from tarkov.exceptions import NotFoundError
from tarkov.inventory.helpers import generate_item_id
from tarkov.inventory.models import Item, ItemTemplate, ItemUpdMedKit, ItemUpdResource
from tarkov.inventory.prop_models import AmmoBoxProps, FuelProps, MedsProps
from tarkov.inventory.types import TemplateId

if TYPE_CHECKING:
    from tarkov.globals_.repository import GlobalsRepository
    from tarkov.inventory.repositories import ItemTemplatesRepository


class ItemFactory:
    @inject
    def __init__(
        self,
        globals_repository: GlobalsRepository,
        templates_repository: ItemTemplatesRepository,
    ):
        self.globals_repository = globals_repository
        self.templates_repository = templates_repository

    @inject
    def create_item(
        self,
        item_template: ItemTemplate,
        count: int = 1,
    ) -> Tuple[Item, List[Item]]:
        try:
            return self.globals_repository.item_preset(item_template).get_items()
        except NotFoundError:
            pass

        item = Item(
            id=generate_item_id(),
            tpl=item_template.id,
        )
        if isinstance(item_template.props, AmmoBoxProps):
            ammo_template_id: TemplateId = item_template.props.StackSlots[0]["_props"][
                "filters"
            ][0]["Filter"][0]
            ammo_template = self.templates_repository.get_template(ammo_template_id)
            ammo, _ = self.create_item(ammo_template, 1)
            ammo.upd.StackObjectsCount = count
            ammo.parent_id = item.id
            ammo.slot_id = "cartridges"

            return item, [ammo]

        if count > item_template.props.StackMaxSize:
            raise ValueError(
                f"Trying to create item with template id {item_template} with stack size "
                f"of {count} but maximum stack size is {item_template.props.StackMaxSize}"
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

    def create_items(
        self, template_id: TemplateId, count: int = 1
    ) -> List[Tuple[Item, List[Item]]]:
        """
        Returns list of Tuple[Root Item, [Child items]
        """
        if count == 0:
            raise ValueError("Cannot create 0 items")

        item_template = self.templates_repository.get_template(template_id)

        #  If we need only one item them we will just return it
        if count == 1:
            return [self.create_item(item_template)]

        items: List[Tuple[Item, List[Item]]] = []
        stack_max_size = item_template.props.StackMaxSize

        #  Create multiple stacks of items (Say 80 rounds of 5.45 ammo it will create two stacks (60 and 20))
        amount_to_create = count
        while amount_to_create > 0:
            stack_size = min(stack_max_size, amount_to_create)
            amount_to_create -= stack_size
            root, children = self.create_item(item_template, stack_size)
            root.slot_id = None

            items.append((root, children))

        return items
