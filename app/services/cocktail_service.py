from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from app.database.vector_store import VectorStore
from app.models.schemas import Cocktail, UserPreference, CocktailIngredient
from app.services.llm_service import LLMService
from app.config import settings
import logging
import asyncio
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class CocktailService:
    def __init__(self):
        self.vector_store = VectorStore()
        self.llm_service = LLMService()
        self.cocktails_df = None
        self.ingredient_index = {}
        
    async def initialize_data(self):
        """Initialize service with cocktail data"""
        try:
            # Load and process cocktail data
            self.cocktails_df = pd.read_csv(f"{settings.data_dir}/cocktails.csv")
            
            # Process ingredients
            self.cocktails_df['ingredients_list'] = self.cocktails_df['ingredients'].apply(
                lambda x: [ing.strip() for ing in eval(x)]
            )
            
            # Create ingredient index
            for idx, row in self.cocktails_df.iterrows():
                for ingredient in row['ingredients_list']:
                    if ingredient not in self.ingredient_index:
                        self.ingredient_index[ingredient] = []
                    self.ingredient_index[ingredient].append(idx)
            
            # Generate and store embeddings
            await self._initialize_embeddings()
            
            logger.info("Successfully initialized cocktail service")
            
        except Exception as e:
            logger.error(f"Error initializing cocktail service: {str(e)}")
            raise

    async def _initialize_embeddings(self):
        """Generate and store embeddings for cocktails"""
        try:
            cocktails = [
                self._create_cocktail_object(row)
                for _, row in self.cocktails_df.iterrows()
            ]
            
            # Generate embeddings in batches
            batch_size = 100
            for i in range(0, len(cocktails), batch_size):
                batch = cocktails[i:i + batch_size]
                texts = [
                    f"{c.name} {' '.join([i.name for i in c.ingredients])} {c.instructions}"
                    for c in batch
                ]
                embeddings = await self.llm_service.generate_embeddings(texts)
                await self.vector_store.add_cocktail_embeddings(batch, embeddings)
            
            logger.info("Successfully initialized embeddings")
            
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            raise

    def _create_cocktail_object(self, row) -> Cocktail:
        """Create Cocktail object from DataFrame row"""
        ingredients = [
            CocktailIngredient(
                name=ing.strip(),
                measure=measure.strip() if pd.notna(measure) else None
            )
            for ing, measure in zip(
                eval(row['ingredients']),
                eval(row['ingredientMeasures'])
            )
        ]
        
        return Cocktail(
            id=row['id'],
            name=row['name'],
            alcoholic=row['alcoholic'].lower() == 'alcoholic',
            category=row['category'],
            glass_type=row['glassType'],
            instructions=row['instructions'],
            thumbnail_url=row['drinkThumbnail'],
            ingredients=ingredients,
            complexity_score=self._calculate_complexity_score(row),
            popularity_score=0.5  # Default score, could be updated based on user interactions
        )

    def _calculate_complexity_score(self, row) -> float:
        """Calculate cocktail complexity score"""
        # Factors considered:
        # 1. Number of ingredients
        # 2. Length of instructions
        # 3. Presence of special techniques
        
        ingredients_score = min(len(eval(row['ingredients'])) / 10, 1.0)
        
        instructions_score = min(len(row['instructions']) / 500, 1.0)
        
        technique_words = ['shake', 'stir', 'blend', 'muddle', 'layer', 'float']
        technique_score = sum(
            1 for word in technique_words
            if word in row['instructions'].lower()
        ) / len(technique_words)
        
        return (ingredients_score * 0.4 + instructions_score * 0.3 + technique_score * 0.3)

    async def recommend_cocktails(
        self,
        query: str,
        user_prefs: Optional[UserPreference] = None,
        limit: int = 5
    ) -> List[Cocktail]:
        """Get personalized cocktail recommendations"""
        try:
            # Generate query embedding
            query_embedding = await self.llm_service.generate_embeddings([query])
            
            # Get similar cocktails
            similar_cocktails = await self.vector_store.find_similar_cocktails(
                query_embedding[0],
                k=limit * 2  # Get more for filtering
            )
            
            # Apply user preferences if available
            if user_prefs:
                filtered_cocktails = self._apply_user_preferences(
                    [c for c, _ in similar_cocktails],
                    user_prefs
                )
            else:
                filtered_cocktails = [c for c, _ in similar_cocktails]
            
            return filtered_cocktails[:limit]
            
        except Exception as e:
            logger.error(f"Error recommending cocktails: {str(e)}")
            return []

    def _apply_user_preferences(
        self,
        cocktails: List[Cocktail],
        prefs: UserPreference
    ) -> List[Cocktail]:
        """Filter and sort cocktails based on user preferences"""
        scored_cocktails = []
        
        for cocktail in cocktails:
            score = 0.0
            
            # Check favorite ingredients
            for ing in prefs.favorite_ingredients:
                if any(i.name.lower() == ing.lower() for i in cocktail.ingredients):
                    score += 0.3
                    
            # Check allergies (exclude cocktails with allergens)
            if any(
                any(a.lower() in i.name.lower() for i in cocktail.ingredients)
                for a in prefs.allergies
            ):
                continue
                
            # Check preferred alcohol types
            if any(
                any(p.lower() in i.name.lower() for i in cocktail.ingredients)
                for p in prefs.preferred_alcohol_types
            ):
                score += 0.2
                
            # Check favorite cocktails
            if cocktail.name in prefs.favorite_cocktails:
                score += 0.5
                
            scored_cocktails.append((cocktail, score))
            
        # Sort by score and return cocktails
        return [
            c for c, s in sorted(scored_cocktails, key=lambda x: x[1], reverse=True)
        ]

    async def get_cocktails_by_ingredients(
        self,
        ingredients: List[str],
        limit: int = 5
    ) -> List[Cocktail]:
        """Find cocktails containing specific ingredients"""
        try:
            # Get cocktail indices for each ingredient
            cocktail_sets = [
                set(self.ingredient_index.get(ing.lower(), []))
                for ing in ingredients
            ]
            
            if not cocktail_sets:
                return []
            
            # Find cocktails containing all ingredients
            matching_indices = set.intersection(*cocktail_sets)
            
            # Create cocktail objects
            matching_cocktails = [
                self._create_cocktail_object(self.cocktails_df.iloc[idx])
                for idx in matching_indices
            ]
            
            # Sort by complexity score
            matching_cocktails.sort(key=lambda x: x.complexity_score, reverse=True)
            
            return matching_cocktails[:limit]
            
        except Exception as e:
            logger.error(f"Error finding cocktails by ingredients: {str(e)}")
            return []

    async def search_cocktails(
        self,
        query: str,
        limit: int = 5,
        user_id: Optional[str] = None
    ) -> List[Cocktail]:
        """Search cocktails based on query"""
        try:
            # Generate query embedding
            query_embedding = await self.llm_service.generate_embeddings([query])
            
            # Get similar cocktails
            similar_cocktails = await self.vector_store.find_similar_cocktails(
                query_embedding[0],
                k=limit
            )
            
            # If user_id provided, personalize results
            if user_id:
                user_prefs = await self.get_user_preferences(user_id)
                if user_prefs:
                    similar_cocktails = self._apply_user_preferences(
                        [c for c, _ in similar_cocktails],
                        user_prefs
                    )
                    return similar_cocktails[:limit]
            
            return [c for c, _ in similar_cocktails][:limit]
            
        except Exception as e:
            logger.error(f"Error searching cocktails: {str(e)}")
            return []

    async def get_user_preferences(
        self,
        user_id: str
    ) -> Optional[UserPreference]:
        """Get user preferences from storage"""
        try:
            return await self.vector_store.get_user_preferences(user_id)
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return None

    async def update_user_preferences(
        self,
        user_id: str,
        preferences: UserPreference
    ) -> bool:
        """Update user preferences"""
        try:
            # Generate embedding for preferences
            pref_text = (
                f"{' '.join(preferences.favorite_ingredients)} "
                f"{' '.join(preferences.favorite_cocktails)} "
                f"{' '.join(preferences.preferred_alcohol_types)}"
            )
            embedding = await self.llm_service.generate_embeddings([pref_text])
            
            # Store preferences and embedding
            await self.vector_store.update_user_preferences(
                user_id,
                preferences,
                embedding[0]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
            return False