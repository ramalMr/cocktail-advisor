import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging
from datetime import datetime
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.data_processor import DataProcessor
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataPreprocessor:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.raw_data_path = Path(settings.data_dir) / "cocktails.csv"
        self.processed_data_path = Path(settings.processed_data_dir)
        
    def process(self):
        """Main processing function"""
        try:
            logger.info("Starting data preprocessing...")
            
            # Create necessary directories
            self.processed_data_path.mkdir(parents=True, exist_ok=True)
            
            # Read and process data
            logger.info("Reading raw data from CSV...")
            df = self.data_processor.process_cocktail_data()
            
            # Generate statistics
            logger.info("Generating dataset statistics...")
            stats = self.data_processor.get_ingredient_statistics()
            
            # Save processed data
            logger.info("Saving processed data...")
            self._save_processed_data(df, stats)
            
            logger.info("Data preprocessing completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during data preprocessing: {str(e)}")
            raise
            
    def _save_processed_data(self, df: pd.DataFrame, stats: Dict):
        """Save processed data and statistics"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save processed DataFrame
        processed_file = self.processed_data_path / f"processed_cocktails_{timestamp}.json"
        self.data_processor.export_processed_data(str(processed_file))
        
        # Save statistics
        stats_file = self.processed_data_path / f"statistics_{timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        # Update latest symlinks
        self._update_symlink(processed_file, "latest_processed_cocktails.json")
        self._update_symlink(stats_file, "latest_statistics.json")
        
    def _update_symlink(self, target_path: Path, link_name: str):
        """Update symlink to point to latest file"""
        link_path = self.processed_data_path / link_name
        if link_path.exists():
            link_path.unlink()
        link_path.symlink_to(target_path)

if __name__ == "__main__":
    preprocessor = DataPreprocessor()
    preprocessor.process()