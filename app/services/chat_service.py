from typing import List, Optional, Dict
from datetime import datetime
import logging
import asyncio
import time
from app.models.schemas import ChatMessage, ChatResponse, Cocktail
from app.services.llm_service import LLMService
from app.services.cocktail_service import CocktailService
from app.database.vector_store import VectorStore
from app.config import settings

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.llm_service = LLMService()
        self.cocktail_service = CocktailService()
        self.vector_store = VectorStore()
        self.conversation_history: Dict[str, List[ChatMessage]] = {}
        
    async def process_message(
        self,
        message: str,
        user_id: str = "ramalMr"
    ) -> ChatResponse:
        """Process incoming chat messages and generate responses"""
        start_time = time.time()
        
        try:
            # Add message to conversation history
            self._add_to_history(user_id, "user", message)
            
            # Analyze intent
            intent = await self._analyze_intent(message)
            
            # Process based on intent
            if intent.get("type") == "recommendation":
                response = await self._handle_recommendation_intent(message, user_id)
            elif intent.get("type") == "ingredient_query":
                response = await self._handle_ingredient_query(message)
            elif intent.get("type") == "preference_update":
                response = await self._handle_preference_update(message, user_id)
            else:
                response = await self._handle_general_query(message)
            
            # Add response to conversation history
            self._add_to_history(user_id, "assistant", response.message)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            response.processing_time = processing_time
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return ChatResponse(
                message="I apologize, but I encountered an error. Please try again.",
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                timestamp=datetime.utcnow()
            )

    async def _analyze_intent(self, message: str) -> Dict:
        """Analyze user message intent using LLM"""
        prompt = f"""
        Analyze the following message and determine the user's intent:
        Message: {message}
        
        Classify into one of these categories:
        1. recommendation (looking for cocktail recommendations)
        2. ingredient_query (asking about specific ingredients)
        3. preference_update (stating preferences)
        4. general_query (other queries)
        
        Also extract any relevant entities (ingredients, cocktail names, etc.)
        """
        
        response = await self.llm_service.analyze_text(prompt)
        return response

    async def _handle_recommendation_intent(
        self,
        message: str,
        user_id: str
    ) -> ChatResponse:
        """Handle requests for cocktail recommendations"""
        try:
            # Get user preferences
            user_prefs = await self.cocktail_service.get_user_preferences(user_id)
            
            # Get recommended cocktails
            recommended_cocktails = await self.cocktail_service.recommend_cocktails(
                message,
                user_prefs,
                limit=5
            )
            
            # Generate response using LLM
            context = self._prepare_cocktail_context(recommended_cocktails)
            response_text = await self.llm_service.generate_response(
                message,
                context=context
            )
            
            return ChatResponse(
                message=response_text,
                cocktails=recommended_cocktails,
                confidence_score=0.95,
                processing_time=0.0,  # Will be updated by caller
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error handling recommendation: {str(e)}")
            raise

    async def _handle_ingredient_query(self, message: str) -> ChatResponse:
        """Handle queries about specific ingredients"""
        try:
            # Extract ingredients from message
            ingredients = await self.llm_service.extract_ingredients(message)
            
            # Get cocktails with these ingredients
            cocktails = await self.cocktail_service.get_cocktails_by_ingredients(
                ingredients
            )
            
            # Generate response
            response_text = await self.llm_service.generate_ingredient_response(
                message,
                ingredients,
                cocktails
            )
            
            return ChatResponse(
                message=response_text,
                cocktails=cocktails,
                confidence_score=0.9,
                processing_time=0.0,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error handling ingredient query: {str(e)}")
            raise

    async def _handle_preference_update(
        self,
        message: str,
        user_id: str
    ) -> ChatResponse:
        """Handle user preference updates"""
        try:
            # Extract preferences from message
            preferences = await self.llm_service.extract_preferences(message)
            
            # Update user preferences
            await self.cocktail_service.update_user_preferences(
                user_id,
                preferences
            )
            
            # Generate confirmation response
            response_text = (
                "I've updated your preferences! I'll keep these in mind for future "
                "recommendations. Would you like me to suggest some cocktails based "
                "on your updated preferences?"
            )
            
            return ChatResponse(
                message=response_text,
                confidence_score=1.0,
                processing_time=0.0,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
            raise

    async def _handle_general_query(self, message: str) -> ChatResponse:
        """Handle general cocktail-related queries"""
        try:
            # Get relevant cocktail context
            relevant_cocktails = await self.cocktail_service.search_cocktails(
                message,
                limit=3
            )
            
            # Generate response using LLM with context
            context = self._prepare_cocktail_context(relevant_cocktails)
            response_text = await self.llm_service.generate_response(
                message,
                context=context
            )
            
            return ChatResponse(
                message=response_text,
                cocktails=relevant_cocktails if relevant_cocktails else None,
                confidence_score=0.85,
                processing_time=0.0,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error handling general query: {str(e)}")
            raise

    def _add_to_history(self, user_id: str, role: str, content: str):
        """Add message to conversation history"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
            
        self.conversation_history[user_id].append(
            ChatMessage(
                role=role,
                content=content,
                timestamp=datetime.utcnow()
            )
        )
        
        # Keep only last 10 messages
        self.conversation_history[user_id] = self.conversation_history[user_id][-10:]

    def _prepare_cocktail_context(self, cocktails: List[Cocktail]) -> str:
        """Prepare cocktail information as context for LLM"""
        context_parts = []
        for cocktail in cocktails:
            ingredients_text = ", ".join([
                f"{i.measure} {i.name}" if i.measure else i.name
                for i in cocktail.ingredients
            ])
            context_parts.append(
                f"Cocktail: {cocktail.name}\n"
                f"Category: {cocktail.category}\n"
                f"Glass: {cocktail.glass_type}\n"
                f"Ingredients: {ingredients_text}\n"
                f"Instructions: {cocktail.instructions}\n"
            )
        return "\n".join(context_parts)

    async def get_conversation_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[ChatMessage]:
        """Get conversation history for a user"""
        return self.conversation_history.get(user_id, [])[-limit:]