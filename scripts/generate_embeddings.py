import numpy as np
from pathlib import Path
import json
import logging
import sys
import os
import asyncio
from typing import List, Dict
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_service import LLMService
from app.models.schemas import Cocktail
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingsGenerator:
    def __init__(self):
        self.llm_service = LLMService()
        self.processed_data_path = Path(settings.processed_data_dir)
        self.embeddings_path = Path(settings.embeddings_dir)
        
    async def generate(self):
        """Generate embeddings for cocktail data"""
        try:
            logger.info("Starting embeddings generation...")
            
            # Create necessary directories
            self.embeddings_path.mkdir(parents=True, exist_ok=True)
            
            # Load processed data
            cocktails = self._load_processed_data()
            
            # Generate embeddings
            embeddings = await self._generate_embeddings(cocktails)
            
            # Save embeddings
            self._save_embeddings(embeddings)
            
            logger.info("Embeddings generation completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during embeddings generation: {str(e)}")
            raise
            
    def _load_processed_data(self) -> List[Dict]:
        """Load processed cocktail data"""
        latest_data_path = self.processed_data_path / "latest_processed_cocktails.json"
        
        if not latest_data_path.exists():
            raise FileNotFoundError("Processed cocktail data not found!")
            
        with open(latest_data_path) as f:
            return json.load(f)
            
    async def _generate_embeddings(self, cocktails: List[Dict]) -> np.ndarray:
        """Generate embeddings for cocktails"""
        logger.info(f"Generating embeddings for {len(cocktails)} cocktails...")
        
        # Prepare texts for embedding
        texts = []
        for cocktail in cocktails:
            text = (
                f"{cocktail['name']} {' '.join(cocktail['ingredients'])} "
                f"{cocktail['instructions']}"
            )
            texts.append(text)
            
        # Generate embeddings in batches
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}...")
            
            batch_embeddings = await self.llm_service.generate_embeddings(batch)
            all_embeddings.extend(batch_embeddings)
            
            # Add small delay to avoid rate limits
            await asyncio.sleep(0.1)
            
        return np.array(all_embeddings)
        
    def _save_embeddings(self, embeddings: np.ndarray):
        """Save generated embeddings"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save embeddings
        embeddings_file = self.embeddings_path / f"cocktail_embeddings_{timestamp}.npy"
        np.save(str(embeddings_file), embeddings)
        
        # Update latest symlink
        self._update_symlink(embeddings_file, "latest_cocktail_embeddings.npy")
        
    def _update_symlink(self, target_path: Path, link_name: str):
        """Update symlink to point to latest file"""
        link_path = self.embeddings_path / link_name
        if link_path.exists():
            link_path.unlink()
        link_path.symlink_to(target_path)

if __name__ == "__main__":
    generator = EmbeddingsGenerator()
    asyncio.run(generator.generate())