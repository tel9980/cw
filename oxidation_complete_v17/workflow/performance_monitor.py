"""
Performance Monitoring and Optimization System

This module implements comprehensive performance monitoring, automatic backup,
error recovery, and scalability optimization for the V1.5 workflow system.

Requirements: 10.1, 10.2, 10.3, 10.4
"""

import time
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from collections import deque
import statistics


@dataclass
class PerformanceMetric:
    """Records a single performance measurement"""
    operation: str
    duration_ms: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BackupInfo:
    """Information about a backup operation"""
    backup_id: str
    timestamp: datetime
    file_path: str
    size_bytes: int
    success: bool
    error_message: Optional[str] = None


@dataclass
class SystemHealth:
    """Overall system health status"""
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate: float
    total_operations: int
    last_backup: Optional[datetime]
    backup_success_rate: float
    memory_usage_mb: float
    active_sessions: int


class PerformanceMonitor:
    """
    Monitors system performance and ensures reliability standards.
    
    Features:
    - Response time monitoring (200ms target)
    - Automatic backup system (5-minute intervals)
    - Graceful error recovery
    - Scalability optimization
    """
    
    def __init__(self, backup_dir: str = "backups", backup_interval_minutes: int = 5):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        self.backup_interval = timedelta(minutes=backup_interval_minutes)
        self.last_backup_time: Optional[datetime] = None
        self.backup_thread: Optional[threading.Thread] = None
        self.backup_active = False
        
        # Performance metrics storage (keep last 10000 operations)
        self.metrics: deque = deque(maxlen=10000)
        self.metrics_lock = threading.Lock()
        
        # Backup history (keep last 100 backups)
        self.backup_history: deque = deque(maxlen=100)
        
        # Error recovery state
        self.error_recovery_handlers: Dict[str, Callable] = {}
        self.recovery_attempts: Dict[str, int] = {}
        
        # Scalability tracking
        self.transaction_count = 0
        self.customer_count = 0
        self.active_sessions: Dict[str, datetime] = {}
        
        # Performance thresholds
        self.response_time_target_ms = 200
        self.max_transactions = 10000
        self.max_customers = 1000
    
    def start_backup_service(self):
        """Start automatic backup service"""
        if self.backup_active:
            return
        
        self.backup_active = True
        self.backup_thread = threading.Thread(target=self._backup_loop, daemon=True)
        self.backup_thread.start()
    
    def stop_backup_service(self):
        """Stop automatic backup service"""
        self.backup_active = False
        if self.backup_thread:
            self.backup_thread.join(timeout=1)
    
    def _backup_loop(self):
        """Background thread for automatic backups"""
        while self.backup_active:
            time.sleep(60)  # Check every minute
            
            if self._should_perform_backup():
                try:
                    self.perform_backup({})
                except Exception as e:
                    print(f"Backup error: {e}")
    
    def _should_perform_backup(self) -> bool:
        """Check if backup should be performed"""
        if not self.last_backup_time:
            return True
        
        # Only backup if there's been activity
        if not self.active_sessions:
            return False
        
        time_since_backup = datetime.now() - self.last_backup_time
        return time_since_backup >= self.backup_interval
    
    def perform_backup(self, data: Dict[str, Any]) -> BackupInfo:
        """
        Perform a backup of system data.
        
        Args:
            data: Data to backup
            
        Returns:
            BackupInfo with backup details
        """
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / f"{backup_id}.json"
        
        try:
            # Add metadata
            backup_data = {
                "backup_id": backup_id,
                "timestamp": datetime.now().isoformat(),
                "transaction_count": self.transaction_count,
                "customer_count": self.customer_count,
                "active_sessions": len(self.active_sessions),
                "data": data
            }
            
            # Write backup file
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            size_bytes = backup_path.stat().st_size
            
            backup_info = BackupInfo(
                backup_id=backup_id,
                timestamp=datetime.now(),
                file_path=str(backup_path),
                size_bytes=size_bytes,
                success=True
            )
            
            self.backup_history.append(backup_info)
            self.last_backup_time = datetime.now()
            
            return backup_info
            
        except Exception as e:
            backup_info = BackupInfo(
                backup_id=backup_id,
                timestamp=datetime.now(),
                file_path=str(backup_path),
                size_bytes=0,
                success=False,
                error_message=str(e)
            )
            self.backup_history.append(backup_info)
            raise
    
    def restore_from_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Restore data from a backup.
        
        Args:
            backup_id: ID of backup to restore
            
        Returns:
            Restored data
        """
        backup_path = self.backup_dir / f"{backup_id}.json"
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup {backup_id} not found")
        
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        return backup_data.get("data", {})
    
    def measure_operation(self, operation: str):
        """
        Context manager for measuring operation performance.
        
        Usage:
            with monitor.measure_operation("transaction_entry"):
                # perform operation
                pass
        """
        return OperationTimer(self, operation)
    
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        with self.metrics_lock:
            self.metrics.append(metric)
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health status"""
        with self.metrics_lock:
            if not self.metrics:
                return SystemHealth(
                    avg_response_time_ms=0,
                    p95_response_time_ms=0,
                    p99_response_time_ms=0,
                    error_rate=0,
                    total_operations=0,
                    last_backup=self.last_backup_time,
                    backup_success_rate=self._calculate_backup_success_rate(),
                    memory_usage_mb=0,
                    active_sessions=len(self.active_sessions)
                )
            
            # Calculate response time statistics
            durations = [m.duration_ms for m in self.metrics]
            avg_time = statistics.mean(durations)
            
            sorted_durations = sorted(durations)
            p95_idx = int(len(sorted_durations) * 0.95)
            p99_idx = int(len(sorted_durations) * 0.99)
            p95_time = sorted_durations[p95_idx] if p95_idx < len(sorted_durations) else sorted_durations[-1]
            p99_time = sorted_durations[p99_idx] if p99_idx < len(sorted_durations) else sorted_durations[-1]
            
            # Calculate error rate
            errors = sum(1 for m in self.metrics if not m.success)
            error_rate = errors / len(self.metrics) if self.metrics else 0
            
            return SystemHealth(
                avg_response_time_ms=avg_time,
                p95_response_time_ms=p95_time,
                p99_response_time_ms=p99_time,
                error_rate=error_rate,
                total_operations=len(self.metrics),
                last_backup=self.last_backup_time,
                backup_success_rate=self._calculate_backup_success_rate(),
                memory_usage_mb=0,  # Could integrate psutil for real memory tracking
                active_sessions=len(self.active_sessions)
            )
    
    def _calculate_backup_success_rate(self) -> float:
        """Calculate backup success rate"""
        if not self.backup_history:
            return 1.0
        
        successful = sum(1 for b in self.backup_history if b.success)
        return successful / len(self.backup_history)
    
    def check_performance_threshold(self) -> bool:
        """
        Check if system is meeting performance targets.
        
        Returns:
            True if meeting targets, False otherwise
        """
        health = self.get_system_health()
        return health.avg_response_time_ms <= self.response_time_target_ms
    
    def register_error_handler(self, error_type: str, handler: Callable):
        """
        Register an error recovery handler.
        
        Args:
            error_type: Type of error to handle
            handler: Function to call for recovery
        """
        self.error_recovery_handlers[error_type] = handler
    
    def recover_from_error(self, error_type: str, context: Dict[str, Any]) -> bool:
        """
        Attempt to recover from an error gracefully.
        
        Args:
            error_type: Type of error
            context: Error context information
            
        Returns:
            True if recovery successful, False otherwise
        """
        if error_type not in self.error_recovery_handlers:
            return False
        
        # Track recovery attempts
        self.recovery_attempts[error_type] = self.recovery_attempts.get(error_type, 0) + 1
        
        try:
            handler = self.error_recovery_handlers[error_type]
            handler(context)
            return True
        except Exception as e:
            print(f"Recovery failed for {error_type}: {e}")
            return False
    
    def track_transaction(self):
        """Track a new transaction for scalability monitoring"""
        self.transaction_count += 1
    
    def track_customer(self):
        """Track a new customer for scalability monitoring"""
        self.customer_count += 1
    
    def register_session(self, session_id: str):
        """Register an active session"""
        self.active_sessions[session_id] = datetime.now()
    
    def unregister_session(self, session_id: str):
        """Unregister an active session"""
        self.active_sessions.pop(session_id, None)
    
    def check_scalability_limits(self) -> Dict[str, bool]:
        """
        Check if system is within scalability limits.
        
        Returns:
            Dict with limit checks
        """
        return {
            "transactions_ok": self.transaction_count <= self.max_transactions,
            "customers_ok": self.customer_count <= self.max_customers,
            "transaction_count": self.transaction_count,
            "customer_count": self.customer_count,
            "max_transactions": self.max_transactions,
            "max_customers": self.max_customers
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Returns:
            Dict with performance metrics and recommendations
        """
        health = self.get_system_health()
        scalability = self.check_scalability_limits()
        
        # Generate recommendations
        recommendations = []
        if health.avg_response_time_ms > self.response_time_target_ms:
            recommendations.append(
                f"Average response time ({health.avg_response_time_ms:.1f}ms) "
                f"exceeds target ({self.response_time_target_ms}ms)"
            )
        
        if health.error_rate > 0.01:  # More than 1% errors
            recommendations.append(
                f"Error rate ({health.error_rate:.2%}) is elevated"
            )
        
        if not scalability["transactions_ok"]:
            recommendations.append(
                f"Transaction count ({scalability['transaction_count']}) "
                f"exceeds limit ({scalability['max_transactions']})"
            )
        
        if not scalability["customers_ok"]:
            recommendations.append(
                f"Customer count ({scalability['customer_count']}) "
                f"exceeds limit ({scalability['max_customers']})"
            )
        
        return {
            "health": asdict(health),
            "scalability": scalability,
            "recommendations": recommendations,
            "meeting_targets": len(recommendations) == 0
        }


class OperationTimer:
    """Context manager for timing operations"""
    
    def __init__(self, monitor: PerformanceMonitor, operation: str):
        self.monitor = monitor
        self.operation = operation
        self.start_time = None
        self.error = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        
        metric = PerformanceMetric(
            operation=self.operation,
            duration_ms=duration_ms,
            timestamp=datetime.now(),
            success=exc_type is None,
            error_message=str(exc_val) if exc_val else None
        )
        
        self.monitor.record_metric(metric)
        
        # Don't suppress exceptions
        return False
