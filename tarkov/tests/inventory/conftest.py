import random
from typing import Callable, List
from unittest.mock import patch

import pytest

from server import root_dir
from tarkov.inventory import PlayerInventory, item_templates_repository
from tarkov.inventory.factories import item_factory
from tarkov.inventory.models import InventoryModel, Item, ItemTemplate
from tarkov.profile import Profile
from tarkov.profile.models import ProfileModel

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
def random_items() -> List[Item]:
    random_templates = random.sample(
        [tpl for tpl in item_templates_repository._item_templates.values() if isinstance(tpl, ItemTemplate)],
        k=100,
    )

    items: List[Item] = [
        item_factory.create_item(item_templates_repository.get_template(tpl.id))[0] for tpl in random_templates
    ]
    return items
