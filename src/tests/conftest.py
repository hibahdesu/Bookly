from src.db.main import get_session
from src import app
from unittest.mock import Mock
import pytest


mock_session = Mock()

mock_user_service = Mock()

def get_mock_session():
    yield mock_session

app.dependency_overrides(get_session) = get_mock_session

@pytest.fixture
def fake_session(): 
    return mock_session

@pytest.fixture
def fake_user_service():
    return mock_user_service