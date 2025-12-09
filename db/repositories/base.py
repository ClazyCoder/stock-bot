from typing import Callable
from sqlalchemy.orm import Session
import logging


class BaseRepository:
    def __init__(self, session_local: Callable[[], Session]):
        self.session_local = session_local
        self.logger = logging.getLogger(__name__)
