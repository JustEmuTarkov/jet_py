import json
from typing import List

import orjson
import pydantic

from server import root_dir
from server.utils import atomic_write
from tarkov.exceptions import NotFoundError
from tarkov.inventory.helpers import generate_item_id
from .models import Account


class AccountService:
    def __init__(self) -> None:
        self.accounts: List[Account] = []
        self.path = root_dir.joinpath("resources", "profiles.json")

        self.__read()

    def is_nickname_taken(self, nickname: str) -> bool:
        return any(account.nickname == nickname for account in self.accounts)

    def create_account(self, email: str, password: str, edition: str) -> Account:
        if any(account.email == email for account in self.accounts):
            raise ValueError(f"Account with email {email} already exists")

        account = Account(
            id=generate_item_id(),
            email=email,
            password=password,
            edition=edition,
            nickname="",
        )

        self.accounts.append(account)
        self.__write()
        return account

    def get_account(self, account_id: str) -> Account:
        try:
            return next(acc for acc in self.accounts if acc.id == account_id)
        except StopIteration as error:
            raise NotFoundError from error

    def find(self, email: str, password: str) -> Account:
        try:
            return next(
                acc
                for acc in self.accounts
                if acc.email == email and acc.password == password
            )
        except StopIteration as error:
            raise NotFoundError from error

    def __read(self) -> None:
        try:
            accounts: list = orjson.loads(self.path.open().read())
            self.accounts = pydantic.parse_obj_as(List[Account], accounts)
        except FileNotFoundError:
            self.accounts = []
            self.__write()

    def __write(self) -> None:
        self.path.parent.mkdir(exist_ok=True, parents=True)
        accounts = [a.dict() for a in self.accounts]
        atomic_write(json.dumps(accounts, indent=4, ensure_ascii=False), self.path)
