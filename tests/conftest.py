from __future__ import annotations

import copy
import json
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.common.database import Base, build_engine

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def sample_transmission() -> dict:
    with (ROOT / "test-data/valid/transmission-json.json").open(encoding="utf-8") as handle:
        return copy.deepcopy(json.load(handle))


@pytest.fixture
def sample_xml_transmission() -> dict:
    with (ROOT / "test-data/valid/transmission-xml.json").open(encoding="utf-8") as handle:
        return copy.deepcopy(json.load(handle))


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()
