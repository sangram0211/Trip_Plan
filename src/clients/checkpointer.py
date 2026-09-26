"""PostgreSQL checkpointer used by LangGraph to persist conversation threads."""

from functools import lru_cache

import psycopg
from psycopg.rows import dict_row

from langgraph.checkpoint.postgres import PostgresSaver

from src.config.session import require, resolve_database_url
from src.config.settings import normalize_database_url


@lru_cache(maxsize=4)
def get_connection(database_url: str) -> psycopg.Connection:
    return psycopg.connect(
        normalize_database_url(database_url),
        row_factory=dict_row,
        autocommit=True,
    )


def get_checkpointer(database_url: str | None = None) -> PostgresSaver:
    url = database_url or resolve_database_url()
    conn = get_connection(url)
    saver = PostgresSaver(conn)
    saver.setup()
    return saver
