import random
import unittest
import unittest.mock
from unittest.mock import patch
from pathlib import Path
from typing import Callable, List

import pytest  # type: ignore

from server import root_dir
from tarkov.inventory import PlayerInventory, item_templates_repository
from tarkov.inventory.models import Item, ItemTemplate
from tarkov.profile import Profile

TEST_RESOURCES_PATH = root_dir.joinpath("tarkov", "tests", "resources")


@pytest.fixture()
def player_profile() -> Profile:
    return Profile("profile_id")


@pytest.fixture()
def inventory(player_profile: Profile) -> PlayerInventory:
    empty_inventory_path = Path("tarkov/tests/inventory/empty_inventory.json").absolute()
    inventory = PlayerInventory(player_profile)
    with unittest.mock.patch("pathlib.Path.open", empty_inventory_path.open):
        inventory.read()
    return inventory


@pytest.fixture()
def make_inventory(player_profile: Profile) -> Callable:
    def _make_inventory(inventory_path: str) -> PlayerInventory:
        inventory = PlayerInventory(player_profile)
        with patch.object(inventory, "_path", inventory_path):
            inventory.read()
        return inventory

    return _make_inventory


@pytest.fixture()
def random_items() -> List[Item]:
    random_templates = random.choices(
        [tpl for tpl in item_templates_repository._item_templates.values() if isinstance(tpl, ItemTemplate)],
        k=100,
    )

    items: List[Item] = [
        item_templates_repository.create_item(item_templates_repository.get_template(tpl.id))[0]
        for tpl in random_templates
    ]
    return items
