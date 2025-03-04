import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.cocktail_service import CocktailService
from app.services.chat_service import ChatService
from app.database.vector_store import VectorStore
import asyncio
import json

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def cocktail_service():
    return CocktailService()

@pytest.fixture
def chat_service():
    return ChatService()

@pytest.fixture
def vector_store():
    return VectorStore()

@pytest.fixture
def sample_cocktail_data():
    return {
        "id": 1,
        "name": "Test Cocktail",
        "alcoholic": True,
        "category": "Test Category",
        "glass_type": "Test Glass",
        "instructions": "Test instructions",
        "ingredients": [
            {"name": "Test Ingredient 1", "measure": "1 oz"},
            {"name": "Test Ingredient 2", "measure": "2 oz"}
        ]
    }

@pytest.fixture
def sample_user_preferences():
    return {
        "user_id": "test_user",
        "favorite_ingredients": ["rum", "lime"],
        "allergies": ["nuts"],
        "preferred_alcohol_types": ["rum", "vodka"]
    }

@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()