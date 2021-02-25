from tarkov.models import Base


class Account(Base):
    id: str
    nickname: str
    email: str
    password: str
    wipe: bool = False
    edition: str
