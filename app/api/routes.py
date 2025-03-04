from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.services.chat_service import ChatService
from app.services.cocktail_service import CocktailService
from app.models.schemas import ChatResponse, UserPreference, Cocktail
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
chat_service = ChatService()
cocktail_service = CocktailService()

@router.post("/chat", response_model=ChatResponse)
async def process_chat_message(
    message: str,
    user_id: str = "ramalMr",
    db: AsyncSession = Depends(get_db)
):
    """Process chat message and return response"""
    try:
        start_time = datetime.utcnow()
        response = await chat_service.process_message(message, user_id)
        
        # Log interaction
        await db.execute(
            """
            INSERT INTO interactions (user_id, interaction_type, created_at)
            VALUES (:user_id, :type, :created_at)
            """,
            {
                "user_id": user_id,
                "type": "chat",
                "created_at": start_time
            }
        )
        await db.commit()
        
        return response
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing message")

@router.get("/preferences", response_model=UserPreference)
async def get_user_preferences(
    user_id: str = "ramalMr",
    db: AsyncSession = Depends(get_db)
):
    """Get user preferences"""
    try:
        result = await db.execute(
            """
            SELECT * FROM user_preferences WHERE user_id = :user_id
            """,
            {"user_id": user_id}
        )
        prefs = result.first()
        
        if not prefs:
            raise HTTPException(status_code=404, detail="User preferences not found")
            
        return UserPreference(**dict(prefs))
    except Exception as e:
        logger.error(f"Error getting user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting preferences")

@router.post("/preferences", response_model=UserPreference)
async def update_user_preferences(
    preferences: UserPreference,
    db: AsyncSession = Depends(get_db)
):
    """Update user preferences"""
    try:
        await cocktail_service.update_user_preferences(preferences.user_id, preferences)
        
        # Update in database
        await db.execute(
            """
            INSERT INTO user_preferences (
                user_id,
                favorite_ingredients,
                favorite_cocktails,
                allergies,
                preferred_alcohol_types,
                updated_at
            )
            VALUES (
                :user_id,
                :favorite_ingredients,
                :favorite_cocktails,
                :allergies,
                :preferred_alcohol_types,
                :updated_at
            )
            ON CONFLICT (user_id) DO UPDATE SET
                favorite_ingredients = EXCLUDED.favorite_ingredients,
                favorite_cocktails = EXCLUDED.favorite_cocktails,
                allergies = EXCLUDED.allergies,
                preferred_alcohol_types = EXCLUDED.preferred_alcohol_types,
                updated_at = EXCLUDED.updated_at
            """,
            {
                "user_id": preferences.user_id,
                "favorite_ingredients": preferences.favorite_ingredients,
                "favorite_cocktails": preferences.favorite_cocktails,
                "allergies": preferences.allergies,
                "preferred_alcohol_types": preferences.preferred_alcohol_types,
                "updated_at": datetime.utcnow()
            }
        )
        await db.commit()
        
        return preferences
    except Exception as e:
        logger.error(f"Error updating user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating preferences")

@router.get("/cocktails/search", response_model=List[Cocktail])
async def search_cocktails(
    query: str,
    limit: int = 5,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Search cocktails based on query"""
    try:
        results = await cocktail_service.search_cocktails(
            query,
            limit,
            user_id
        )
        
        if user_id:
            # Log search interaction
            await db.execute(
                """
                INSERT INTO interactions (
                    user_id,
                    interaction_type,
                    created_at
                )
                VALUES (:user_id, :type, :created_at)
                """,
                {
                    "user_id": user_id,
                    "type": "search",
                    "created_at": datetime.utcnow()
                }
            )
            await db.commit()
            
        return results
    except Exception as e:
        logger.error(f"Error searching cocktails: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching cocktails")

@router.get("/cocktails/recommend", response_model=List[Cocktail])
async def get_recommendations(
    user_id: str = "ramalMr",
    limit: int = 5,
    db: AsyncSession = Depends(get_db)
):
    """Get personalized cocktail recommendations"""
    try:
        # Get user preferences
        result = await db.execute(
            """
            SELECT * FROM user_preferences WHERE user_id = :user_id
            """,
            {"user_id": user_id}
        )
        prefs = result.first()
        
        if not prefs:
            # If no preferences, return popular cocktails
            result = await db.execute(
                """
                SELECT c.* 
                FROM cocktails c
                JOIN (
                    SELECT cocktail_id, COUNT(*) as interaction_count
                    FROM interactions
                    WHERE cocktail_id IS NOT NULL
                    GROUP BY cocktail_id
                    ORDER BY interaction_count DESC
                    LIMIT :limit
                ) i ON c.id = i.cocktail_id
                """,
                {"limit": limit}
            )
            return [Cocktail(**dict(row)) for row in result]
            
        # Get personalized recommendations
        recommendations = await cocktail_service.recommend_cocktails(
            "recommend cocktails",
            UserPreference(**dict(prefs)),
            limit
        )
        
        # Log recommendation interaction
        await db.execute(
            """
            INSERT INTO interactions (user_id, interaction_type, created_at)
            VALUES (:user_id, :type, :created_at)
            """,
            {
                "user_id": user_id,
                "type": "recommendation",
                "created_at": datetime.utcnow()
            }
        )
        await db.commit()
        
        return recommendations
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting recommendations")

@router.get("/cocktails/{cocktail_id}", response_model=Cocktail)
async def get_cocktail(
    cocktail_id: int,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get cocktail details by ID"""
    try:
        result = await db.execute(
            """
            SELECT * FROM cocktails WHERE id = :id
            """,
            {"id": cocktail_id}
        )
        cocktail = result.first()
        
        if not cocktail:
            raise HTTPException(status_code=404, detail="Cocktail not found")
            
        if user_id:
            # Log view interaction
            await db.execute(
                """
                INSERT INTO interactions (
                    user_id,
                    cocktail_id,
                    interaction_type,
                    created_at
                )
                VALUES (
                    :user_id,
                    :cocktail_id,
                    :type,
                    :created_at
                )
                """,
                {
                    "user_id": user_id,
                    "cocktail_id": cocktail_id,
                    "type": "view",
                    "created_at": datetime.utcnow()
                }
            )
            await db.commit()
            
        return Cocktail(**dict(cocktail))
    except Exception as e:
        logger.error(f"Error getting cocktail details: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting cocktail details")

@router.get("/ingredients", response_model=List[str])
async def get_ingredients(
    query: Optional[str] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get list of available ingredients"""
    try:
        if query:
            result = await db.execute(
                """
                SELECT DISTINCT name
                FROM ingredients
                WHERE name ILIKE :query
                ORDER BY name
                LIMIT :limit
                """,
                {"query": f"%{query}%", "limit": limit}
            )
        else:
            result = await db.execute(
                """
                SELECT DISTINCT name
                FROM ingredients
                ORDER BY name
                LIMIT :limit
                """,
                {"limit": limit}
            )
            
        return [row[0] for row in result]
    except Exception as e:
        logger.error(f"Error getting ingredients: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting ingredients")

@router.get("/stats/popular", response_model=dict)
async def get_popular_stats(db: AsyncSession = Depends(get_db)):
    """Get popular cocktails and ingredients statistics"""
    try:
        # Get popular cocktails
        popular_cocktails = await db.execute(
            """
            SELECT 
                c.name,
                COUNT(*) as interaction_count
            FROM interactions i
            JOIN cocktails c ON i.cocktail_id = c.id
            WHERE i.cocktail_id IS NOT NULL
            GROUP BY c.name
            ORDER BY interaction_count DESC
            LIMIT 5
            """
        )
        
        # Get popular ingredients
        popular_ingredients = await db.execute(
            """
            SELECT 
                name,
                COUNT(*) as usage_count
            FROM ingredients i
            JOIN cocktail_ingredients ci ON i.id = ci.ingredient_id
            GROUP BY name
            ORDER BY usage_count DESC
            LIMIT 5
            """
        )
        
        return {
            "popular_cocktails": {
                row[0]: row[1] for row in popular_cocktails
            },
            "popular_ingredients": {
                row[0]: row[1] for row in popular_ingredients
            }
        }
    except Exception as e:
        logger.error(f"Error getting popular stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting statistics")