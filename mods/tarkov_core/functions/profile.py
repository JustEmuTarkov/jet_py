from typing import TypedDict, List, Generator, Tuple

import ujson

from mods.tarkov_core.functions.items import get_item_templates
from server.main import root_dir


class ItemBase(TypedDict):
    _id: str
    _tpl: str


class Item(ItemBase):
    parentId: str
    slotId: str


class ItemNotFoundError(Exception):
    pass


class Inventory:
    def __init__(self):
        self.stash = ujson.load(root_dir.joinpath(
            'resources', 'profiles', 'AID8131647517931710690RF', 'pmc_inventory.json').open('r', encoding='utf8'))
        self.items: List[Item] = self.stash['items']
        self.stash_id: str = self.stash['stash']
        self.equipment_id: str = self.stash['equipment']

    def get_item(self, item_id: str):
        try:
            return next(item for item in self.items if item['_id'] == item_id)
        except StopIteration:
            raise ItemNotFoundError

    def get_item_size(self, item_id: str) -> Tuple[int, int]:
        item_templates = {key: item for key, item in get_item_templates().items() if '_props' in item}
        items: List[Item] = list(self.iter_item_recursively(item_id=item_id))

        item = self.get_item(item_id)
        item_tpl_id = item['_tpl']
        width = item_templates[item_tpl_id]['_props']['Width']
        height = item_templates[item_tpl_id]['_props']['Height']

        for item in items:
            template = item_templates[item['_tpl']]
            width += template['_props']['ExtraSizeLeft']
            width += template['_props']['ExtraSizeRight']

            height += template['_props']['ExtraSizeUp']
            height += template['_props']['ExtraSizeDown']

        return width, height

    def iter_children(self, item_id: str) -> Generator[Item, None, None]:
        """
        Iterates over item children
        """
        for item in self.items:
            try:
                if item['parentId'] == item_id:
                    yield item
            except KeyError:
                pass

    def iter_item_recursively(self, item_id: str):
        """
        Iterates recursively over item and it's children recursively
        """
        items = [self.get_item(item_id=item_id)]
        while items:
            item: Item = items.pop()
            items.extend(list(self.iter_children(item['_id'])))
            yield item

    def add_item(self, item):
        raise NotImplementedError()


class Profile:
    profiles = {}

    def __init__(self):
        profiles_path = root_dir.joinpath('resources', 'profiles')
        profile_paths = set(profiles_path.glob('*'))
        profile_data = {}
        for profile_id in profile_paths:
            single_dir = set(profiles_path.joinpath(profile_id).glob('pmc_*.json'))
            profile_data[profile_id.stem] = {file.stem: ujson.load(file.open('r', encoding='utf8')) for file in
                                             single_dir}
        self.profiles = profile_data
        pass

    def save_profile(self, profile_id):
        saving_profile_path = root_dir.joinpath('resources', 'profiles', profile_id)
        pmc_data_field_names = ['profile', 'hideout', 'inventory', 'quests', 'stats', 'traders']
        for field in pmc_data_field_names:
            ujson.dump(self.profiles[profile_id][f"pmc_{field}"], saving_profile_path.joinpath(f"pmc_{field}.json"))

    # just for testing
    def get_all_profiles(self):
        return self.profiles

    def get_profile(self, profile_id):
        profile_base = self.profiles[profile_id]['pmc_profile']
        profile_base['Inventory'] = self.profiles[profile_id]['pmc_inventory']
        profile_base['Hideout'] = self.profiles[profile_id]['pmc_hideout']
        profile_base['TraderStandings'] = self.profiles[profile_id]['pmc_traders']
        profile_base['Stats'] = self.profiles[profile_id]['pmc_stats']
        profile_base['Quests'] = self.profiles[profile_id]['pmc_quests']
        return profile_base

    def build_save(self):
        pass

    def build_remove(self):
        pass

    def customization_wear(self):
        pass

    def customization_buy(self):
        pass

    def encyclopedia_read(self):
        pass

    def inventory_insure_item(self):
        pass

    def inventory_add_item(self, data, profile_id):
        character_inventory = self.profiles[profile_id]["pmc_inventory"]
        pass

    def inventory_remove_item(self, data, profile_id):
        character_inventory = self.profiles[profile_id]["pmc_inventory"]
        pass

    def inventory_move_item(self, data, profile_id):
        character_inventory = self.profiles[profile_id]["pmc_inventory"]
        pass

    def inventory_split_item(self, data, profile_id):
        character_inventory = self.profiles[profile_id]["pmc_inventory"]
        pass

    def inventory_merge_item(self, data, profile_id):
        character_inventory = self.profiles[profile_id]["pmc_inventory"]
        pass

    def inventory_transfer_item(self, data, profile_id):
        character_inventory = self.profiles[profile_id]["pmc_inventory"]
        pass

    def inventory_swap_item(self, data, profile_id):
        character_inventory = self.profiles[profile_id]["pmc_inventory"]
        pass

    def inventory_fold_item(self, data, profile_id):
        character_inventory = self.profiles[profile_id]["pmc_inventory"]
        pass

    def inventory_toggle_item(self, data, profile_id):
        character_inventory = self.profiles[profile_id]["pmc_inventory"]
        pass

    def inventory_tag_item(self, data, profile_id):
        character_inventory = self.profiles[profile_id]["pmc_inventory"]
        pass

    def inventory_bind_item(self, data, profile_id):
        character_inventory = self.profiles[profile_id]["pmc_inventory"]
        pass

    def inventory_examine_item(self, data, profile_id):
        character_inventory = self.profiles[profile_id]["pmc_inventory"]
        pass

    def note_add(self):
        pass

    def node_edit(self):
        pass

    def note_delete(self):
        pass

    def player_heal(self):
        pass

    def player_eat(self):
        pass

    def player_restore_health(self):
        pass

    def quest_accept(self):
        pass

    def quest_complete(self):
        pass

    def quest_handover(self):
        pass
