import pytest
from fastapi.testclient import TestClient
from src.main import create_app


@pytest.fixture
def app():
    application = create_app(database=":memory:")
    yield application
    application.state.repo.close()


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client
