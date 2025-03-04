import pytest
from app.services.cocktail_service import CocktailService
from app.models.schemas import Cocktail, UserPreference

@pytest.mark.asyncio
async def test_initialize_data(cocktail_service):
    await cocktail_service.initialize_data()
    assert cocktail_service.cocktails_df is not None
    assert len(cocktail_service.ingredient_index) > 0

@pytest.mark.asyncio
async def test_recommend_cocktails(cocktail_service):
    preferences = UserPreference(
        user_id="test_user",
        favorite_ingredients=["rum", "lime"],
        allergies=["nuts"]
    )
    
    recommendations = await cocktail_service.recommend_cocktails(
        "something refreshing",
        preferences
    )
    
    assert isinstance(recommendations, list)
    assert all(isinstance(c, Cocktail) for c in recommendations)

@pytest.mark.asyncio
async def test_search_cocktails(cocktail_service):
    results = await cocktail_service.search_cocktails("mojito")
    
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(c, Cocktail) for c in results)

@pytest.mark.asyncio
async def test_get_cocktails_by_ingredients(cocktail_service):
    ingredients = ["rum", "lime"]
    results = await cocktail_service.get_cocktails_by_ingredients(ingredients)
    
    assert isinstance(results, list)
    assert all(isinstance(c, Cocktail) for c in results)
    assert all(
        any(i in [ing.name.lower() for ing in c.ingredients] for i in ingredients)
        for c in results
    )