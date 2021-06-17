from __future__ import annotations

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.inventory.models import Item, ItemTemplate
    from tarkov.inventory.repositories import ItemTemplatesRepository
    from tarkov.inventory.types import TemplateId
    from tarkov.profile.profile import Profile


class Encyclopedia:
    def __init__(
        self,
        profile: Profile,
        templates_repository: ItemTemplatesRepository,
    ):
        self.__templates_repository = templates_repository

        self.profile = profile
        self.data = profile.pmc.Encyclopedia

    def examine(
        self,
        item: Union[Item, TemplateId],
    ) -> None:
        template: ItemTemplate = self.__templates_repository.get_template(item)
        self.data[template.id] = False
        self.profile.receive_experience(template.props.ExamineExperience)

    def read(self, item: Union[Item, TemplateId]) -> None:
        if isinstance(item, Item):
            item_tpl_id = item.tpl
        else:
            item_tpl_id = item

        self.data[item_tpl_id] = True
