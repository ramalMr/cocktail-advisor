import numpy as np
from typing import List, Optional
import logging
from app.config import settings
import torch
from transformers import AutoTokenizer, AutoModel
import faiss
from pathlib import Path
import pickle
from datetime import datetime

logger = logging.getLogger(__name__)

class EmbeddingManager:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
        self.model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2').to(self.device)
        self.index = None
        self.embedding_dim = 384  # MiniLM model dimension
        self._initialize_index()

    def _initialize_index(self):
        """Initialize FAISS index"""
        try:
            index_path = Path(settings.embeddings_dir) / "faiss_index.pkl"
            if index_path.exists():
                with open(index_path, 'rb') as f:
                    self.index = pickle.load(f)
                logger.info("Loaded existing FAISS index")
            else:
                self.index = faiss.IndexFlatL2(self.embedding_dim)
                logger.info("Created new FAISS index")
        except Exception as e:
            logger.error(f"Error initializing FAISS index: {str(e)}")
            raise

    async def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> np.ndarray:
        """Generate embeddings for texts using batched processing"""
        try:
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                inputs = self.tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors='pt'
                ).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    embeddings = self._mean_pooling(outputs, inputs['attention_mask'])
                    embeddings = embeddings.cpu().numpy()
                    all_embeddings.append(embeddings)
                
            return np.vstack(all_embeddings)
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

    def _mean_pooling(self, model_output, attention_mask):
        """Perform mean pooling on token embeddings"""
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    async def add_to_index(
        self,
        embeddings: np.ndarray,
        save: bool = True
    ):
        """Add embeddings to FAISS index"""
        try:
            self.index.add(embeddings)
            
            if save:
                self._save_index()
                
            logger.info(f"Added {len(embeddings)} embeddings to index")
            
        except Exception as e:
            logger.error(f"Error adding embeddings to index: {str(e)}")
            raise

    def _save_index(self):
        """Save FAISS index to disk"""
        try:
            index_path = Path(settings.embeddings_dir)
            index_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Save with timestamp
            save_path = index_path / f"faiss_index_{timestamp}.pkl"
            with open(save_path, 'wb') as f:
                pickle.dump(self.index, f)
                
            # Update symlink to latest
            latest_path = index_path / "faiss_index.pkl"
            if latest_path.exists():
                latest_path.unlink()
            latest_path.symlink_to(save_path)
            
            logger.info("Saved FAISS index")
            
        except Exception as e:
            logger.error(f"Error saving FAISS index: {str(e)}")
            raise

    async def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        distance_threshold: Optional[float] = None
    ) -> tuple[np.ndarray, np.ndarray]:
        """Search for similar embeddings in the index"""
        try:
            distances, indices = self.index.search(
                query_embedding.reshape(1, -1),
                k
            )
            
            if distance_threshold is not None:
                mask = distances[0] < distance_threshold
                distances = distances[:, mask]
                indices = indices[:, mask]
                
            return distances, indices
            
        except Exception as e:
            logger.error(f"Error searching index: {str(e)}")
            raise

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.model = None
            self.tokenizer = None
            torch.cuda.empty_cache()
            logger.info("Cleaned up embedding resources")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")