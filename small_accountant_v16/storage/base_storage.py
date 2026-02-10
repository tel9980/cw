"""
Base storage class for JSON-based data persistence

This module provides a base class for all storage implementations,
handling common operations like file I/O, locking, and error handling.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class BaseStorage:
    """
    Base class for JSON-based storage
    
    Provides common functionality for:
    - File-based JSON storage
    - Thread-safe operations
    - Error handling
    - Data validation
    """
    
    def __init__(self, storage_dir: str, filename: str):
        """
        Initialize storage
        
        Args:
            storage_dir: Directory to store data files
            filename: Name of the JSON file
        """
        self.storage_dir = Path(storage_dir)
        self.filename = filename
        self.file_path = self.storage_dir / filename
        self._lock = Lock()
        
        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize file if it doesn't exist
        if not self.file_path.exists():
            self._write_data({})
    
    def _read_data(self) -> Dict[str, Any]:
        """
        Read data from JSON file
        
        Returns:
            Dictionary containing all stored data
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解码错误: {e}")
            # Return empty dict if file is corrupted
            return {}
        except Exception as e:
            logger.error(f"读取文件错误: {e}")
            return {}
    
    def _write_data(self, data: Dict[str, Any]) -> None:
        """
        Write data to JSON file
        
        Args:
            data: Dictionary to write to file
        """
        try:
            # Write to temporary file first
            temp_path = self.file_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Atomic rename
            temp_path.replace(self.file_path)
        except Exception as e:
            logger.error(f"写入文件错误: {e}")
            raise
    
    def _get_all_items(self) -> Dict[str, Any]:
        """
        Get all items from storage
        
        Returns:
            Dictionary of all items
        """
        with self._lock:
            return self._read_data()
    
    def _save_all_items(self, items: Dict[str, Any]) -> None:
        """
        Save all items to storage
        
        Args:
            items: Dictionary of items to save
        """
        with self._lock:
            self._write_data(items)
    
    def clear(self) -> None:
        """Clear all data from storage"""
        with self._lock:
            self._write_data({})
    
    def backup(self, backup_path: str) -> None:
        """
        Create a backup of the storage file
        
        Args:
            backup_path: Path to save backup file
        """
        with self._lock:
            data = self._read_data()
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    def restore(self, backup_path: str) -> None:
        """
        Restore storage from a backup file
        
        Args:
            backup_path: Path to backup file
        """
        with self._lock:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._write_data(data)
