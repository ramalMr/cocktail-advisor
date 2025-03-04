import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from app.models.schemas import Cocktail, CocktailIngredient
import ast
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.vector_embeddings: Dict[int, np.ndarray] = {}
        
    def process_csv_data(self, csv_content: str) -> List[Cocktail]:
        """Process CSV data and convert to Cocktail objects"""
        try:
            # Parse CSV content
            df = pd.read_csv(csv_content)
            
            # Convert ingredients and measures from string to list
            df['ingredients'] = df['ingredients'].apply(ast.literal_eval)
            df['ingredientMeasures'] = df['ingredientMeasures'].apply(ast.literal_eval)
            
            # Convert to Cocktail objects
            cocktails = []
            for _, row in df.iterrows():
                ingredients = [
                    CocktailIngredient(
                        name=ing,
                        measure=measure if pd.notna(measure) else None
                    )
                    for ing, measure in zip(row['ingredients'], row['ingredientMeasures'])
                ]
                
                cocktail = Cocktail(
                    id=row['id'],
                    name=row['name'],
                    alcoholic=row['alcoholic'].lower() == 'alcoholic',
                    category=row['category'],
                    glass_type=row['glassType'],
                    instructions=row['instructions'],
                    thumbnail_url=row['drinkThumbnail'],
                    ingredients=ingredients
                )
                cocktails.append(cocktail)
            
            return cocktails
            
        except Exception as e:
            logger.error(f"Error processing CSV data: {str(e)}")
            raise ValueError(f"Failed to process cocktail data: {str(e)}")

    def create_search_index(self, cocktails: List[Cocktail]) -> Dict[str, List[int]]:
        """Create inverted index for ingredient-based search"""
        index = {}
        for cocktail in cocktails:
            for ingredient in cocktail.ingredients:
                ing_name = ingredient.name.lower()
                if ing_name not in index:
                    index[ing_name] = []
                index[ing_name].append(cocktail.id)
        return index

    def generate_cocktail_embedding(self, cocktail: Cocktail) -> str:
        """Generate text representation for embedding"""
        ingredients_text = " ".join([i.name for i in cocktail.ingredients])
        return f"{cocktail.name} {ingredients_text} {cocktail.category} {cocktail.instructions}"

    def prepare_training_data(self, cocktails: List[Cocktail]) -> List[Tuple[str, str]]:
        """Prepare training data for RAG system"""
        training_data = []
        for cocktail in cocktails:
            # Create question-answer pairs
            ingredients_list = ", ".join([i.name for i in cocktail.ingredients])
            question = f"How do I make a cocktail with {ingredients_list}?"
            answer = f"To make a {cocktail.name}, {cocktail.instructions}"
            training_data.append((question, answer))
            
            # Create variation with cocktail name
            question2 = f"How do I make a {cocktail.name}?"
            training_data.append((question2, answer))
            
        return training_data