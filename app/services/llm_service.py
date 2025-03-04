from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from app.config import settings
import numpy as np
from typing import List, Dict, Any
import logging
import asyncio
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=settings.temperature,
            model_name=settings.model_name,
            max_tokens=settings.max_tokens
        )
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002"
        )
        self.memory = ConversationBufferMemory()
        
        # Initialize prompt templates
        self._initialize_prompts()
        
    def _initialize_prompts(self):
        """Initialize various prompt templates"""
        self.cocktail_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
            You are a professional bartender and cocktail expert. Use the following context to answer the question:
            
            Context: {context}
            
            Question: {question}
            
            Provide a detailed and helpful response. If making drink recommendations, include:
            1. Preparation instructions
            2. Ingredient measurements
            3. Special techniques or tips
            4. Suitable occasions
            5. Any relevant warnings or alternatives
            
            Keep the tone professional but friendly.
            """
        )
        
        self.ingredient_analysis_prompt = PromptTemplate(
            input_variables=["ingredients"],
            template="""
            Analyze these cocktail ingredients and provide insights:
            
            Ingredients: {ingredients}
            
            Please provide:
            1. Common cocktail families these ingredients suggest
            2. Potential flavor profiles
            3. Any standard ratios or proportions
            4. Common variations or substitutions
            5. Any special handling requirements
            """
        )
        
        self.preference_extraction_prompt = PromptTemplate(
            input_variables=["message"],
            template="""
            Extract cocktail preferences from this message:
            
            Message: {message}
            
            Please identify:
            1. Favorite ingredients
            2. Preferred types of cocktails
            3. Any mentioned dislikes or restrictions
            4. Preferred serving styles
            5. Any specific occasions mentioned
            
            Format the response as JSON with these categories.
            """
        )

    async def generate_response(
        self,
        query: str,
        context: str = "",
        max_retries: int = 3
    ) -> str:
        """Generate response using LLM"""
        retries = 0
        while retries < max_retries:
            try:
                response = await self.llm.agenerate([
                    self.cocktail_prompt.format(
                        context=context,
                        question=query
                    )
                ])
                return response.generations[0][0].text
                
            except Exception as e:
                retries += 1
                if retries == max_retries:
                    logger.error(f"Error generating response: {str(e)}")
                    return "I apologize, but I'm having trouble generating a response. Please try again."
                await asyncio.sleep(1)  # Wait before retry

    async def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> np.ndarray:
        """Generate embeddings for texts"""
        try:
            all_embeddings = []
            
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embeddings = await self.embeddings.aembed_documents(batch)
                all_embeddings.extend(embeddings)
            
            return np.array(all_embeddings)
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text for intent and entities"""
        try:
            response = await self.llm.agenerate([
                f"""
                Analyze this text and extract:
                1. Primary intent
                2. Mentioned ingredients
                3. Specific cocktail names
                4. User preferences
                5. Questions or queries
                
                Text: {text}
                
                Provide analysis as JSON.
                """
            ])
            
            return json.loads(response.generations[0][0].text)
            
        except Exception as e:
            logger.error(f"Error analyzing text: {str(e)}")
            return {
                "type": "general_query",
                "ingredients": [],
                "cocktails": [],
                "preferences": [],
                "queries": []
            }

    async def extract_ingredients(self, text: str) -> List[str]:
        """Extract ingredient mentions from text"""
        try:
            response = await self.llm.agenerate([
                f"""
                Extract all ingredient mentions from this text:
                
                {text}
                
                Return only the ingredient names as a JSON array.
                """
            ])
            
            return json.loads(response.generations[0][0].text)
            
        except Exception as e:
            logger.error(f"Error extracting ingredients: {str(e)}")
            return []

    async def extract_preferences(self, text: str) -> Dict[str, List[str]]:
        """Extract user preferences from text"""
        try:
            response = await self.llm.agenerate([
                self.preference_extraction_prompt.format(message=text)
            ])
            
            return json.loads(response.generations[0][0].text)
            
        except Exception as e:
            logger.error(f"Error extracting preferences: {str(e)}")
            return {
                "favorite_ingredients": [],
                "favorite_cocktails": [],
                "allergies": [],
                "preferred_alcohol_types": []
            }

    async def generate_ingredient_response(
        self,
        query: str,
        ingredients: List[str],
        cocktails: List[Any]
    ) -> str:
        """Generate response for ingredient-related queries"""
        try:
            # Analyze ingredients
            analysis = await self.llm.agenerate([
                self.ingredient_analysis_prompt.format(
                    ingredients=", ".join(ingredients)
                )
            ])
            
            # Prepare cocktail information
            cocktail_info = "\n".join([
                f"- {c.name}: {', '.join([i.name for i in c.ingredients])}"
                for c in cocktails
            ])
            
            # Generate final response
            response = await self.llm.agenerate([
                f"""
                Based on the ingredient analysis:
                {analysis.generations[0][0].text}
                
                And these cocktail options:
                {cocktail_info}
                
                Provide a detailed response to: {query}
                """
            ])
            
            return response.generations[0][0].text
            
        except Exception as e:
            logger.error(f"Error generating ingredient response: {str(e)}")
            return "I apologize, but I'm having trouble generating a response about these ingredients."