import random
from typing import Callable, List
from unittest.mock import patch

import pytest
from dependency_injector.wiring import Provide, inject

from server import root_dir
from server.container import AppContainer
from tarkov.inventory.factories import ItemFactory
from tarkov.inventory.inventory import PlayerInventory
from tarkov.inventory.models import InventoryModel, Item, ItemTemplate
from tarkov.inventory.repositories import ItemTemplatesRepository
from tarkov.profile.models import ProfileModel
from tarkov.profile.profile import Profile

TEST_RESOURCES_PATH = root_dir.joinpath("tarkov", "tests", "resources")


@pytest.fixture()
def player_profile() -> Profile:
    profile = Profile("profile_id")
    profile.pmc = ProfileModel.parse_file(TEST_RESOURCES_PATH.joinpath("pmc_profile.json"))
    return profile


@pytest.fixture()
def inventory(player_profile: Profile) -> PlayerInventory:
    inventory = PlayerInventory(player_profile)
    inventory.read()
    return inventory


@pytest.fixture()
def make_inventory(player_profile: Profile) -> Callable:
    def _make_inventory(inventory_path: str) -> PlayerInventory:
        target_inventory = InventoryModel.parse_file(inventory_path)
        with patch.object(player_profile.pmc, "Inventory", target_inventory):
            inventory = PlayerInventory(player_profile)
            inventory.read()
        return inventory

    return _make_inventory


@pytest.fixture()
@inject
def random_items(
    templates_repository: ItemTemplatesRepository = Provide[AppContainer.repos.templates],
    item_factory: ItemFactory = Provide[AppContainer.items.factory],
) -> List[Item]:
    random.seed(42)
    random_templates = random.sample(
        [tpl for tpl in templates_repository._item_templates.values() if isinstance(tpl, ItemTemplate)],
        k=100,
    )

    items: List[Item] = [
        item_factory.create_item(templates_repository.get_template(tpl.id))[0] for tpl in random_templates
    ]
    return items
