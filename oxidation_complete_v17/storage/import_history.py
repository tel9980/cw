"""
Import history management

This module provides storage and management for import operations,
including the ability to track and undo imports.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from ..models.core_models import ImportResult
from .base_storage import BaseStorage

logger = logging.getLogger(__name__)


class ImportRecord:
    """
    Record of an import operation
    
    Stores information needed to undo an import:
    - Import metadata (ID, date, type, etc.)
    - List of imported record IDs
    - Import result details
    """
    
    def __init__(
        self,
        import_id: str,
        import_type: str,  # "transactions" or "counterparties"
        import_date: datetime,
        imported_ids: List[str],
        import_result: ImportResult,
        can_undo: bool = True
    ):
        self.import_id = import_id
        self.import_type = import_type
        self.import_date = import_date
        self.imported_ids = imported_ids
        self.import_result = import_result
        self.can_undo = can_undo
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "import_id": self.import_id,
            "import_type": self.import_type,
            "import_date": self.import_date.isoformat(),
            "imported_ids": self.imported_ids,
            "import_result": self.import_result.to_dict(),
            "can_undo": self.can_undo,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImportRecord":
        """Create from dictionary"""
        # Reconstruct ImportResult
        result_data = data["import_result"]
        from ..models.core_models import ImportError as ImportErrorModel
        
        import_result = ImportResult(
            import_id=result_data["import_id"],
            total_rows=result_data["total_rows"],
            successful_rows=result_data["successful_rows"],
            failed_rows=result_data["failed_rows"],
            errors=[ImportErrorModel(**e) for e in result_data["errors"]],
            import_date=datetime.fromisoformat(result_data["import_date"]),
            can_undo=result_data["can_undo"],
        )
        
        return cls(
            import_id=data["import_id"],
            import_type=data["import_type"],
            import_date=datetime.fromisoformat(data["import_date"]),
            imported_ids=data["imported_ids"],
            import_result=import_result,
            can_undo=data["can_undo"],
        )


class ImportHistory(BaseStorage):
    """
    Import history management
    
    Provides:
    - Recording of import operations
    - Retrieval of import history
    - Undo/rollback of imports
    """
    
    def __init__(self, storage_dir: str = "data"):
        """
        Initialize import history storage
        
        Args:
            storage_dir: Directory to store import history
        """
        super().__init__(storage_dir, "import_history.json")
    
    def record_import(
        self,
        import_id: str,
        import_type: str,
        imported_ids: List[str],
        source_file: str = "",
        import_result: Optional[ImportResult] = None
    ) -> None:
        """
        Record an import operation
        
        Args:
            import_id: Unique import ID
            import_type: Type of import ("transaction" or "counterparty")
            imported_ids: List of IDs of imported records
            source_file: Source file path
            import_result: Result of the import operation (optional)
        """
        items = self._get_all_items()
        
        # Create a simple import result if not provided
        if import_result is None:
            from ..models.core_models import ImportResult as ImportResultModel
            import_result = ImportResultModel(
                import_id=import_id,
                total_rows=len(imported_ids),
                successful_rows=len(imported_ids),
                failed_rows=0,
                errors=[],
                import_date=datetime.now(),
                can_undo=True
            )
        
        record = ImportRecord(
            import_id=import_id,
            import_type=import_type,
            import_date=datetime.now(),
            imported_ids=imported_ids,
            import_result=import_result,
            can_undo=True
        )
        
        items[import_id] = record.to_dict()
        items[import_id]['source_file'] = source_file  # Add source file
        items[import_id]['undone'] = False  # Add undone flag
        self._save_all_items(items)
        logger.info(f"记录导入操作: {import_id}, 类型: {import_type}, 记录数: {len(imported_ids)}")
    
    def get_import_by_id(self, import_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an import record by ID (returns raw dict)
        
        Args:
            import_id: Import ID
        
        Returns:
            Import record dict or None if not found
        """
        items = self._get_all_items()
        return items.get(import_id)
    
    def get_import_record(self, import_id: str) -> Optional[ImportRecord]:
        """
        Get an import record by ID
        
        Args:
            import_id: Import ID
        
        Returns:
            Import record or None if not found
        """
        items = self._get_all_items()
        data = items.get(import_id)
        
        if data:
            return ImportRecord.from_dict(data)
        return None
    
    def get_all_imports(self) -> List[ImportRecord]:
        """
        Get all import records
        
        Returns:
            List of all import records, sorted by date (newest first)
        """
        items = self._get_all_items()
        records = [ImportRecord.from_dict(data) for data in items.values()]
        return sorted(records, key=lambda r: r.import_date, reverse=True)
    
    def get_imports_by_type(self, import_type: str) -> List[ImportRecord]:
        """
        Get import records by type
        
        Args:
            import_type: Type of import ("transactions" or "counterparties")
        
        Returns:
            List of import records of the specified type
        """
        all_imports = self.get_all_imports()
        return [r for r in all_imports if r.import_type == import_type]
    
    def get_undoable_imports(self) -> List[ImportRecord]:
        """
        Get imports that can be undone
        
        Returns:
            List of undoable import records
        """
        all_imports = self.get_all_imports()
        return [r for r in all_imports if r.can_undo]
    
    def mark_as_undone(self, import_id: str) -> None:
        """
        Mark an import as undone (cannot be undone again)
        
        Args:
            import_id: Import ID
        
        Raises:
            ValueError: If import doesn't exist
        """
        items = self._get_all_items()
        
        if import_id not in items:
            raise ValueError(f"导入记录不存在: {import_id}")
        
        items[import_id]["can_undo"] = False
        items[import_id]["undone"] = True
        self._save_all_items(items)
        logger.info(f"标记导入为已撤销: {import_id}")
    
    def can_undo_import(self, import_id: str) -> bool:
        """
        Check if an import can be undone
        
        Args:
            import_id: Import ID
        
        Returns:
            True if import can be undone, False otherwise
        """
        record = self.get_import_record(import_id)
        if not record:
            return False
        return record.can_undo
    
    def get_imported_ids(self, import_id: str) -> List[str]:
        """
        Get the list of IDs imported in a specific import operation
        
        Args:
            import_id: Import ID
        
        Returns:
            List of imported record IDs
        
        Raises:
            ValueError: If import doesn't exist
        """
        record = self.get_import_record(import_id)
        if not record:
            raise ValueError(f"导入记录不存在: {import_id}")
        return record.imported_ids
    
    def delete_import_record(self, import_id: str) -> None:
        """
        Delete an import record
        
        Args:
            import_id: Import ID to delete
        
        Raises:
            ValueError: If import doesn't exist
        """
        items = self._get_all_items()
        
        if import_id not in items:
            raise ValueError(f"导入记录不存在: {import_id}")
        
        del items[import_id]
        self._save_all_items(items)
        logger.info(f"删除导入记录: {import_id}")
    
    def get_recent_imports(self, limit: int = 10) -> List[ImportRecord]:
        """
        Get the most recent import records
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            List of recent import records
        """
        all_imports = self.get_all_imports()
        return all_imports[:limit]
    
    def count(self) -> int:
        """
        Count total number of import records
        
        Returns:
            Number of import records
        """
        return len(self._get_all_items())
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get import statistics
        
        Returns:
            Dictionary with import statistics
        """
        all_imports = self.get_all_imports()
        
        total_imports = len(all_imports)
        transaction_imports = len([r for r in all_imports if r.import_type == "transactions"])
        counterparty_imports = len([r for r in all_imports if r.import_type == "counterparties"])
        
        total_records_imported = sum(
            r.import_result.successful_rows for r in all_imports
        )
        total_failed_records = sum(
            r.import_result.failed_rows for r in all_imports
        )
        
        return {
            "total_imports": total_imports,
            "transaction_imports": transaction_imports,
            "counterparty_imports": counterparty_imports,
            "total_records_imported": total_records_imported,
            "total_failed_records": total_failed_records,
            "undoable_imports": len(self.get_undoable_imports()),
        }
