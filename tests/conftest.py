# Shared fixtures for msg2po tests.

import os
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def msg_file():
    return os.path.join(FIXTURES_DIR, "sample.msg")


@pytest.fixture
def sve_file():
    return os.path.join(FIXTURES_DIR, "sample.sve")


@pytest.fixture
def txt_indexed_file():
    return os.path.join(FIXTURES_DIR, "sample_indexed.txt")


@pytest.fixture
def txt_nonindexed_file():
    return os.path.join(FIXTURES_DIR, "sample_nonindexed.txt")


@pytest.fixture
def tra_file():
    return os.path.join(FIXTURES_DIR, "sample.tra")


@pytest.fixture
def msg_translated_file():
    return os.path.join(FIXTURES_DIR, "sample_translated.msg")


@pytest.fixture
def tra_translated_file():
    return os.path.join(FIXTURES_DIR, "sample_translated.tra")
