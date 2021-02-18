import time
from typing import Dict, List, TYPE_CHECKING, cast

import ujson
from pydantic import parse_obj_as

from server import db_dir, logger
from server.utils import atomic_write
from tarkov import inventory
from tarkov.inventory import item_templates_repository
from tarkov.inventory.models import Item
from .models import HideoutArea, HideoutAreaType, HideoutProduction

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.profile import Profile


class Hideout:
    # Fuel burn rate, per second
    __FUEL_BURN_RATE = 60 / (14 * 60 * 60 + 27 * 60 + 28)
    __GENERATOR_SPEED_WITHOUT_FUEL = 0.15
    # __FUEL_BURN_RATE = 0.0011527777777778
    data: Dict
    metadata: Dict

    time_elapsed: int
    work_time_elapsed: int
    current_time: int

    def __init__(self, profile: "Profile"):
        self.path = profile.profile_dir.joinpath("pmc_hideout.json")
        self.meta_path = profile.profile_dir.joinpath("pmc_hideout.meta.json")

        self.profile: "Profile" = profile

    @staticmethod
    def get_recipe(recipe_id: str) -> dict:
        recipe_path = db_dir.joinpath("hideout", "production", f"{recipe_id}.json")
        return ujson.load(recipe_path.open("r", encoding="utf8"))

    def get_area(self, area_type: HideoutAreaType) -> HideoutArea:
        area = (a for a in self.data["Areas"] if a["type"] == area_type.value)
        try:
            return next(area)
        except StopIteration as e:
            raise ValueError(f"Hideout are with type {area_type} does not exist") from e

    def area_upgrade_start(self, area_type: HideoutAreaType) -> None:
        area = self.get_area(area_type)
        area["completeTime"] = 0  # Todo: grab construction time from db/hideout/areas and current time
        area["constructing"] = True

    def area_upgrade_finish(self, area_type: HideoutAreaType) -> None:
        area = self.get_area(area_type)
        area["constructing"] = False
        area["completeTime"] = 0
        area["level"] += 1

    def put_items_in_area_slots(
        self, area_type: HideoutAreaType, slot_id: int, item: inventory.models.Item
    ) -> None:
        area = self.get_area(area_type)

        item.location = None
        item.parent_id = None
        item.slotId = None

        area_slots = area["slots"]
        diff = slot_id + 1 - len(area_slots)
        if diff > 0:
            area_slots.extend([{"item": None} for _ in range(diff)])

        area_slots[slot_id]["item"] = [item.dict()]

    def take_item_from_area_slot(self, area_type: HideoutAreaType, slot_id: int) -> inventory.models.Item:
        area = self.get_area(area_type)
        slot = area["slots"][slot_id]
        item: dict = slot["item"][0]
        slot["item"] = None
        return parse_obj_as(Item, item)

    def start_single_production(self, recipe_id: str, timestamp: int = None) -> None:
        if not timestamp:
            timestamp = int(time.time())

        production = HideoutProduction(
            inProgress=True,
            RecipeId=recipe_id,
            StartTime=timestamp,
            Progress=0,
            SkipTime=0,
            Products=[],
        )

        self.data["Production"][recipe_id] = production

    def take_production(self, recipe_id: str) -> List[inventory.models.Item]:
        recipe = self.get_recipe(recipe_id)

        product_tpl = recipe["endProduct"]
        count = recipe["count"]

        items = item_templates_repository.create_items(product_tpl, count)
        items_list: List[Item] = []
        for item, child_items in items:
            items_list.append(item)
            items_list.extend(child_items)

            item.upd.SpawnedInSession = True
            for child in child_items:
                child.upd.SpawnedInSession = True

        del self.data["Production"][recipe_id]
        return items_list

    def toggle_area(self, area_type: HideoutAreaType, enabled: bool) -> None:
        area = self.get_area(area_type)
        area["active"] = enabled

    def __update_production_time(self, time_elapsed: int, generator_work_time: int) -> None:
        for production in self.data["Production"].values():
            production = cast(HideoutProduction, production)

            generator_idle_time = time_elapsed - generator_work_time
            assert generator_idle_time >= 0
            assert generator_work_time >= 0

            # TODO: Move 0.15 into settings
            production["Progress"] += generator_work_time + generator_idle_time * 0.15
            # production['SkipTime'] +=

    def __update_fuel(self) -> int:
        """
        :returns: Amount of time hideout had a generator working
        """
        # Return 0 if generator was not active
        generator_area = self.get_area(HideoutAreaType.Generator)
        if not generator_area["active"]:
            return 0

        fuel_should_be_consumed = self.time_elapsed * Hideout.__FUEL_BURN_RATE
        fuel_consumed = 0

        for slot in generator_area["slots"]:
            if not fuel_should_be_consumed:
                break

            if not slot["item"]:
                continue

            fuel_tank = slot["item"][0]

            # TODO: hideout will crash if fuel tank doesn't have these properties
            fuel_in_tank = fuel_tank["upd"]["Resource"]["Value"]

            consumed = min(fuel_should_be_consumed, fuel_in_tank)
            fuel_consumed += consumed
            fuel_tank["upd"]["Resource"]["Value"] -= consumed
            fuel_should_be_consumed -= consumed

        if fuel_consumed < fuel_should_be_consumed:
            self.toggle_area(HideoutAreaType.Generator, False)

        return int(fuel_consumed / self.__FUEL_BURN_RATE)

    def read(self) -> None:
        self.data: dict = ujson.load(self.path.open("r", encoding="utf8"))

        if not self.meta_path.exists():
            self.metadata = {"updated_at": int(time.time())}
        else:
            self.metadata = ujson.load(self.meta_path.open("r", encoding="utf8"))

        self.current_time = int(time.time())
        self.time_elapsed = self.current_time - self.metadata["updated_at"]
        time_generator_worked = self.__update_fuel()
        skip_time = self.time_elapsed - time_generator_worked

        logger.debug(f"Generator worked for: {time_generator_worked}")
        logger.debug(f"Time skipped: {skip_time}")

        self.__update_production_time(self.time_elapsed, time_generator_worked)

        self.metadata["updated_at"] = self.current_time

    def write(self) -> None:
        atomic_write(ujson.dumps(self.data, indent=4), self.path)
        atomic_write(ujson.dumps(self.metadata, indent=4), self.meta_path)
