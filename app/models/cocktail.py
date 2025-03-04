from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
import json

class CocktailBase(BaseModel):
    name: str
    alcoholic: bool
    category: str
    glass_type: str
    instructions: str
    thumbnail_url: Optional[str] = None
    
    @validator('name')
    def clean_name(cls, v):
        return v.strip().title()

class CocktailIngredientBase(BaseModel):
    name: str
    measure: Optional[str] = None
    
    @validator('name')
    def clean_ingredient_name(cls, v):
        return v.strip().lower()
    
    @validator('measure')
    def clean_measure(cls, v):
        if v:
            return v.strip()
        return v

class CocktailCreate(CocktailBase):
    ingredients: List[CocktailIngredientBase]
    tags: List[str] = []
    complexity_score: float = Field(ge=0.0, le=1.0)
    popularity_score: float = Field(ge=0.0, le=1.0)

class CocktailInDB(CocktailBase):
    id: int
    ingredients: List[CocktailIngredientBase]
    tags: List[str] = []
    complexity_score: float
    popularity_score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CocktailStats(BaseModel):
    total_cocktails: int
    total_ingredients: int
    average_complexity: float
    most_common_ingredients: List[Dict[str, int]]
    popular_categories: List[Dict[str, int]]
    
    @validator('average_complexity')
    def round_complexity(cls, v):
        return round(v, 2)

class CocktailRating(BaseModel):
    cocktail_id: int
    user_id: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('rating')
    def validate_rating(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

class CocktailFilter(BaseModel):
    alcoholic: Optional[bool] = None
    category: Optional[str] = None
    ingredients: Optional[List[str]] = None
    max_complexity: Optional[float] = Field(None, ge=0.0, le=1.0)
    min_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    exclude_ingredients: Optional[List[str]] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.dict().items() if v is not None}

class CocktailSearchResult(BaseModel):
    cocktail: CocktailInDB
    relevance_score: float
    matched_terms: List[str]
    
    @validator('relevance_score')
    def round_score(cls, v):
        return round(v, 3)

class BatchCocktailCreate(BaseModel):
    cocktails: List[CocktailCreate]
    overwrite_existing: bool = False

    @validator('cocktails')
    def validate_batch_size(cls, v):
        if len(v) > 100:
            raise ValueError('Maximum batch size is 100 cocktails')
        return v

class CocktailExport(BaseModel):
    cocktails: List[CocktailInDB]
    export_date: datetime = Field(default_factory=datetime.utcnow)
    format_version: str = "1.0"
    
    def to_json(self) -> str:
        return json.dumps(self.dict(), default=str, indent=2)