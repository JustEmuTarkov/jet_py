from typing import List

import orjson
import pydantic

from server import root_dir
from server.utils import atomic_write
from .models import Account
from tarkov.exceptions import NotFoundError
from tarkov.inventory import generate_item_id


class AccountService:
    def __init__(self) -> None:
        self.accounts: List[Account] = []
        self.path = root_dir.joinpath("resources", "profiles.json")

        self.__read()

    def create_account(self, email: str, password: str, edition: str) -> Account:
        for account in self.accounts:
            if account.email == email:
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

    def find(self, email: str, password: str) -> Account:
        for account in self.accounts:
            if account.email == email and account.password == password:
                return account
        raise NotFoundError

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
        atomic_write(orjson.dumps(accounts).decode("utf8"), self.path)


account_service = AccountService()
