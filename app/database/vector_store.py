import faiss
import numpy as np
from typing import List, Dict, Optional, Tuple
import pickle
from pathlib import Path
import logging
from app.models.schemas import Cocktail, UserPreference
from app.config import settings
import asyncio
import json
from datetime import datetime
import redis.asyncio as redis
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.dimension = 1536  # OpenAI embedding dimension
        self.cocktail_index = None
        self.user_index = None
        self.redis_client = None
        self.initialize()

    def initialize(self):
        """Initialize FAISS indexes and Redis connection"""
        try:
            # Initialize FAISS indexes
            self.cocktail_index = faiss.IndexFlatL2(self.dimension)
            self.user_index = faiss.IndexFlatL2(self.dimension)
            
            # Add IVF for faster search in production
            if settings.is_production and self.cocktail_index.ntotal > 1000:
                nlist = int(np.sqrt(self.cocktail_index.ntotal))
                self.cocktail_index = faiss.IndexIVFFlat(
                    self.cocktail_index, self.dimension, nlist
                )
            
            # Initialize Redis connection
            self.redis_client = redis.from_url(settings.redis_url)
            
            self.load_indexes()
            logger.info("Successfully initialized vector store")
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            raise

    async def load_indexes(self):
        """Load existing indexes if available"""
        try:
            index_path = Path(settings.vector_db_path)
            
            # Load cocktail index
            if (index_path / "cocktail_index.faiss").exists():
                self.cocktail_index = faiss.read_index(
                    str(index_path / "cocktail_index.faiss")
                )
                logger.info("Loaded existing cocktail index")

            # Load user index
            if (index_path / "user_index.faiss").exists():
                self.user_index = faiss.read_index(
                    str(index_path / "user_index.faiss")
                )
                logger.info("Loaded existing user index")

        except Exception as e:
            logger.error(f"Error loading indexes: {str(e)}")
            # Continue with empty indexes if loading fails

    async def save_indexes(self):
        """Save indexes to disk"""
        try:
            index_path = Path(settings.vector_db_path)
            index_path.mkdir(parents=True, exist_ok=True)

            # Save with timestamp for versioning
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Save cocktail index
            cocktail_index_path = index_path / f"cocktail_index_{timestamp}.faiss"
            faiss.write_index(self.cocktail_index, str(cocktail_index_path))
            
            # Update latest symlink
            latest_link = index_path / "cocktail_index.faiss"
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(cocktail_index_path)

            # Save user index similarly
            user_index_path = index_path / f"user_index_{timestamp}.faiss"
            faiss.write_index(self.user_index, str(user_index_path))
            
            latest_link = index_path / "user_index.faiss"
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(user_index_path)

            logger.info("Successfully saved indexes with timestamp: " + timestamp)

        except Exception as e:
            logger.error(f"Error saving indexes: {str(e)}")
            raise

    async def add_cocktail_embeddings(
        self,
        cocktails: List[Cocktail],
        embeddings: np.ndarray,
        batch_size: int = 1000
    ):
        """Add cocktail embeddings to the index in batches"""
        try:
            if len(cocktails) != embeddings.shape[0]:
                raise ValueError("Number of cocktails and embeddings must match")

            # Process in batches
            for i in range(0, len(cocktails), batch_size):
                batch_cocktails = cocktails[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]
                
                # Add to FAISS index
                self.cocktail_index.add(batch_embeddings)
                
                # Store cocktail data in Redis
                async with self.redis_client.pipeline() as pipe:
                    for cocktail in batch_cocktails:
                        key = f"cocktail:{cocktail.id}"
                        await pipe.set(
                            key,
                            json.dumps(cocktail.dict()),
                            ex=settings.cache_ttl
                        )
                    await pipe.execute()

            # Save indexes periodically
            if len(cocktails) > batch_size:
                await self.save_indexes()

            logger.info(f"Added {len(cocktails)} cocktails to the index")

        except Exception as e:
            logger.error(f"Error adding cocktail embeddings: {str(e)}")
            raise

    async def find_similar_cocktails(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        min_similarity: float = None
    ) -> List[Tuple[Cocktail, float]]:
        """Find similar cocktails using vector similarity"""
        try:
            min_similarity = min_similarity or settings.MIN_SIMILARITY_SCORE
            
            # Search in FAISS index
            D, I = self.cocktail_index.search(
                query_embedding.reshape(1, -1),
                k * 2  # Get more results for filtering
            )
            
            results = []
            for distance, idx in zip(D[0], I[0]):
                # Convert distance to similarity score (inverse of distance)
                similarity = 1 / (1 + distance)
                
                if similarity < min_similarity:
                    continue
                    
                # Get cocktail data from Redis
                cocktail_data = await self.redis_client.get(f"cocktail:{idx}")
                if cocktail_data:
                    cocktail = Cocktail(**json.loads(cocktail_data))
                    results.append((cocktail, similarity))
                
                if len(results) >= k:
                    break
            
            return results

        except Exception as e:
            logger.error(f"Error finding similar cocktails: {str(e)}")
            return []

    @asynccontextmanager
    async def get_redis_connection(self):
        """Context manager for Redis connections"""
        try:
            yield self.redis_client
        except redis.RedisError as e:
            logger.error(f"Redis error: {str(e)}")
            raise
        finally:
            await self.redis_client.close()

    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.save_indexes()
            await self.redis_client.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")