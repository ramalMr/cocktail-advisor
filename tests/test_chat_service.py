import pytest
from app.services.chat_service import ChatService
from app.models.schemas import ChatResponse
import json

@pytest.mark.asyncio
async def test_process_message(chat_service):
    message = "What cocktails can I make with rum and lime?"
    response = await chat_service.process_message(message)
    
    assert isinstance(response, ChatResponse)
    assert response.message
    assert response.confidence_score >= 0.0
    assert response.confidence_score <= 1.0

@pytest.mark.asyncio
async def test_analyze_intent(chat_service):
    message = "I like rum and mint"
    intent = await chat_service._analyze_intent(message)
    
    assert isinstance(intent, dict)
    assert "type" in intent

@pytest.mark.asyncio
async def test_handle_recommendation_intent(chat_service):
    message = "Recommend me a cocktail with rum"
    response = await chat_service._handle_recommendation_intent(message, "test_user")
    
    assert isinstance(response, ChatResponse)
    assert response.cocktails is not None
    assert len(response.cocktails) > 0

@pytest.mark.asyncio
async def test_handle_ingredient_query(chat_service):
    message = "What can I make with vodka?"
    response = await chat_service._handle_ingredient_query(message)
    
    assert isinstance(response, ChatResponse)
    assert response.message
    assert "vodka" in response.message.lower()

@pytest.mark.asyncio
async def test_handle_preference_update(chat_service):
    message = "I like rum and mint, but I'm allergic to nuts"
    response = await chat_service._handle_preference_update(message, "test_user")
    
    assert isinstance(response, ChatResponse)
    assert response.message
    assert response.confidence_score == 1.0