from typing import Callable
from sqlalchemy.orm import Session


class BaseRepository:
    def __init__(self, session_local: Callable[[], Session]):
        self.session_local = session_local
