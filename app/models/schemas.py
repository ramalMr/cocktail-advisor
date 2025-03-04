from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
import re

class CocktailIngredient(BaseModel):
    name: str
    measure: Optional[str] = None
    
    @validator('name')
    def clean_name(cls, v):
        return v.strip().lower()

class Cocktail(BaseModel):
    id: int
    name: str
    alcoholic: bool
    category: str
    glass_type: str
    instructions: str
    thumbnail_url: Optional[str]
    ingredients: List[CocktailIngredient]
    tags: List[str] = []
    complexity_score: float = Field(ge=0.0, le=1.0)
    popularity_score: float = Field(ge=0.0, le=1.0)
    
    @validator('name')
    def clean_cocktail_name(cls, v):
        return v.strip().title()

class UserPreference(BaseModel):
    user_id: str
    favorite_ingredients: List[str] = []
    favorite_cocktails: List[str] = []
    allergies: List[str] = []
    preferred_alcohol_types: List[str] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('favorite_ingredients', 'allergies', 'preferred_alcohol_types')
    def clean_list_items(cls, v):
        return [item.strip().lower() for item in v if item.strip()]

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = Field(default_factory=dict)

class ChatResponse(BaseModel):
    message: str
    cocktails: Optional[List[Cocktail]] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SearchQuery(BaseModel):
    query: str
    filters: Dict[str, any] = Field(default_factory=dict)
    limit: int = Field(default=5, ge=1, le=20)
    
    @validator('query')
    def clean_query(cls, v):
        # Remove special characters and extra spaces
        v = re.sub(r'[^\w\s]', ' ', v)
        return ' '.join(v.split())