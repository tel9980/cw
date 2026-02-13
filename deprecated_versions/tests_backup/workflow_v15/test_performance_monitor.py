"""
Tests for Performance Monitoring and Optimization System

Requirements: 10.1, 10.2, 10.3, 10.4
"""

import pytest
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from workflow_v15.core.performance_monitor import (
    PerformanceMonitor,
    PerformanceMetric,
    BackupInfo,
    SystemHealth
)


@pytest.fixture
def temp_backup_dir():
    """Create temporary backup directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def monitor(temp_backup_dir):
    """Create performance monitor instance"""
    return PerformanceMonitor(backup_dir=temp_backup_dir, backup_interval_minutes=1)


class TestPerformanceMonitoring:
    """Test performance monitoring functionality"""
    
    def test_monitor_initialization(self, monitor, temp_backup_dir):
        """Test monitor initializes correctly"""
        assert monitor.backup_dir == Path(temp_backup_dir)
        assert monitor.backup_dir.exists()
        assert monitor.response_time_target_ms == 200
        assert monitor.max_transactions == 10000
        assert monitor.max_customers == 1000
    
    def test_measure_operation_success(self, monitor):
        """Test measuring successful operation"""
        with monitor.measure_operation("test_operation"):
            time.sleep(0.01)  # 10ms operation
        
        assert len(monitor.metrics) == 1
        metric = monitor.metrics[0]
        assert metric.operation == "test_operation"
        assert metric.success is True
        assert metric.duration_ms >= 10
        assert metric.error_message is None
    
    def test_measure_operation_failure(self, monitor):
        """Test measuring failed operation"""
        try:
            with monitor.measure_operation("failing_operation"):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        assert len(monitor.metrics) == 1
        metric = monitor.metrics[0]
        assert metric.operation == "failing_operation"
        assert metric.success is False
        assert "Test error" in metric.error_message
    
    def test_multiple_operations_tracking(self, monitor):
        """Test tracking multiple operations"""
        operations = ["op1", "op2", "op3", "op4", "op5"]
        
        for op in operations:
            with monitor.measure_operation(op):
                time.sleep(0.001)
        
        assert len(monitor.metrics) == 5
        recorded_ops = [m.operation for m in monitor.metrics]
        assert recorded_ops == operations
    
    def test_response_time_calculation(self, monitor):
        """Test response time statistics calculation"""
        # Record operations with known durations
        for i in range(100):
            duration = 50 + i  # 50ms to 149ms
            metric = PerformanceMetric(
                operation="test",
                duration_ms=duration,
                timestamp=datetime.now(),
                success=True
            )
            monitor.record_metric(metric)
        
        health = monitor.get_system_health()
        
        # Average should be around 99.5ms
        assert 95 <= health.avg_response_time_ms <= 105
        
        # P95 should be around 144ms
        assert 140 <= health.p95_response_time_ms <= 150
        
        # P99 should be around 148ms
        assert 145 <= health.p99_response_time_ms <= 150
    
    def test_performance_threshold_check(self, monitor):
        """Test performance threshold checking"""
        # Add fast operations (under 200ms)
        for _ in range(10):
            metric = PerformanceMetric(
                operation="fast_op",
                duration_ms=100,
                timestamp=datetime.now(),
                success=True
            )
            monitor.record_metric(metric)
        
        assert monitor.check_performance_threshold() is True
        
        # Add slow operations (over 200ms)
        for _ in range(20):
            metric = PerformanceMetric(
                operation="slow_op",
                duration_ms=300,
                timestamp=datetime.now(),
                success=True
            )
            monitor.record_metric(metric)
        
        assert monitor.check_performance_threshold() is False
    
    def test_error_rate_calculation(self, monitor):
        """Test error rate calculation"""
        # Add 90 successful operations
        for _ in range(90):
            metric = PerformanceMetric(
                operation="success",
                duration_ms=100,
                timestamp=datetime.now(),
                success=True
            )
            monitor.record_metric(metric)
        
        # Add 10 failed operations
        for _ in range(10):
            metric = PerformanceMetric(
                operation="failure",
                duration_ms=100,
                timestamp=datetime.now(),
                success=False,
                error_message="Error"
            )
            monitor.record_metric(metric)
        
        health = monitor.get_system_health()
        assert health.error_rate == 0.1  # 10% error rate


class TestBackupSystem:
    """Test automatic backup functionality"""
    
    def test_perform_backup(self, monitor):
        """Test performing a backup"""
        test_data = {
            "transactions": [{"id": 1, "amount": 100}],
            "customers": [{"id": 1, "name": "Test Customer"}]
        }
        
        backup_info = monitor.perform_backup(test_data)
        
        assert backup_info.success is True
        assert backup_info.backup_id.startswith("backup_")
        assert Path(backup_info.file_path).exists()
        assert backup_info.size_bytes > 0
        assert monitor.last_backup_time is not None
    
    def test_backup_content(self, monitor):
        """Test backup contains correct data"""
        test_data = {"key": "value", "number": 42}
        
        backup_info = monitor.perform_backup(test_data)
        
        # Read backup file
        with open(backup_info.file_path, 'r') as f:
            backup_content = json.load(f)
        
        assert backup_content["data"] == test_data
        assert "backup_id" in backup_content
        assert "timestamp" in backup_content
        assert "transaction_count" in backup_content
    
    def test_restore_from_backup(self, monitor):
        """Test restoring data from backup"""
        original_data = {
            "transactions": [{"id": 1}, {"id": 2}],
            "settings": {"theme": "dark"}
        }
        
        backup_info = monitor.perform_backup(original_data)
        restored_data = monitor.restore_from_backup(backup_info.backup_id)
        
        assert restored_data == original_data
    
    def test_restore_nonexistent_backup(self, monitor):
        """Test restoring from non-existent backup raises error"""
        with pytest.raises(FileNotFoundError):
            monitor.restore_from_backup("nonexistent_backup")
    
    def test_backup_history_tracking(self, monitor):
        """Test backup history is tracked"""
        for i in range(5):
            monitor.perform_backup({"iteration": i})
            time.sleep(0.01)  # Ensure different timestamps
        
        assert len(monitor.backup_history) == 5
        
        # Check backups are in order
        timestamps = [b.timestamp for b in monitor.backup_history]
        assert timestamps == sorted(timestamps)
    
    def test_backup_history_limit(self, monitor):
        """Test backup history respects maximum size"""
        # Create more than 100 backups (the limit)
        for i in range(105):
            monitor.perform_backup({"iteration": i})
        
        # Should only keep last 100
        assert len(monitor.backup_history) == 100
    
    def test_backup_failure_handling(self, monitor, temp_backup_dir):
        """Test backup failure is handled gracefully"""
        # Simulate backup failure by passing invalid JSON data
        import sys
        
        # Create data that will cause JSON serialization to fail
        class UnserializableObject:
            pass
        
        invalid_data = {"obj": UnserializableObject()}
        
        # Attempt backup should fail
        with pytest.raises(TypeError):  # JSON can't serialize custom objects
            monitor.perform_backup(invalid_data)
        
        # Check failure was recorded
        assert len(monitor.backup_history) == 1
        assert monitor.backup_history[0].success is False
        assert monitor.backup_history[0].error_message is not None
    
    def test_backup_success_rate(self, monitor):
        """Test backup success rate calculation"""
        # Perform successful backups
        for i in range(8):
            monitor.perform_backup({"iteration": i})
        
        # Simulate 2 failed backups
        for i in range(2):
            failed_backup = BackupInfo(
                backup_id=f"failed_{i}",
                timestamp=datetime.now(),
                file_path="",
                size_bytes=0,
                success=False,
                error_message="Test failure"
            )
            monitor.backup_history.append(failed_backup)
        
        health = monitor.get_system_health()
        assert health.backup_success_rate == 0.8  # 8/10 successful
    
    def test_should_perform_backup_timing(self, monitor):
        """Test backup timing logic"""
        # No backup yet, should backup
        assert monitor._should_perform_backup() is True
        
        # Just performed backup, shouldn't backup yet
        monitor.last_backup_time = datetime.now()
        monitor.register_session("test_session")
        assert monitor._should_perform_backup() is False
        
        # After interval, should backup
        monitor.last_backup_time = datetime.now() - timedelta(minutes=2)
        assert monitor._should_perform_backup() is True
    
    def test_no_backup_without_activity(self, monitor):
        """Test backup doesn't run without active sessions"""
        monitor.last_backup_time = datetime.now() - timedelta(minutes=10)
        
        # No active sessions
        assert monitor._should_perform_backup() is False
        
        # With active session
        monitor.register_session("test_session")
        assert monitor._should_perform_backup() is True


class TestErrorRecovery:
    """Test error recovery functionality"""
    
    def test_register_error_handler(self, monitor):
        """Test registering error recovery handler"""
        def recovery_handler(context):
            return True
        
        monitor.register_error_handler("database_error", recovery_handler)
        
        assert "database_error" in monitor.error_recovery_handlers
        assert monitor.error_recovery_handlers["database_error"] == recovery_handler
    
    def test_successful_error_recovery(self, monitor):
        """Test successful error recovery"""
        recovered = False
        
        def recovery_handler(context):
            nonlocal recovered
            recovered = True
        
        monitor.register_error_handler("test_error", recovery_handler)
        
        result = monitor.recover_from_error("test_error", {"data": "test"})
        
        assert result is True
        assert recovered is True
        assert monitor.recovery_attempts["test_error"] == 1
    
    def test_failed_error_recovery(self, monitor):
        """Test failed error recovery"""
        def failing_handler(context):
            raise Exception("Recovery failed")
        
        monitor.register_error_handler("test_error", failing_handler)
        
        result = monitor.recover_from_error("test_error", {})
        
        assert result is False
        assert monitor.recovery_attempts["test_error"] == 1
    
    def test_unregistered_error_recovery(self, monitor):
        """Test recovery for unregistered error type"""
        result = monitor.recover_from_error("unknown_error", {})
        
        assert result is False
        assert "unknown_error" not in monitor.recovery_attempts
    
    def test_multiple_recovery_attempts(self, monitor):
        """Test tracking multiple recovery attempts"""
        def recovery_handler(context):
            pass
        
        monitor.register_error_handler("test_error", recovery_handler)
        
        for i in range(5):
            monitor.recover_from_error("test_error", {})
        
        assert monitor.recovery_attempts["test_error"] == 5


class TestScalability:
    """Test scalability monitoring"""
    
    def test_track_transactions(self, monitor):
        """Test transaction tracking"""
        assert monitor.transaction_count == 0
        
        for _ in range(100):
            monitor.track_transaction()
        
        assert monitor.transaction_count == 100
    
    def test_track_customers(self, monitor):
        """Test customer tracking"""
        assert monitor.customer_count == 0
        
        for _ in range(50):
            monitor.track_customer()
        
        assert monitor.customer_count == 50
    
    def test_scalability_limits_within_bounds(self, monitor):
        """Test scalability check when within limits"""
        monitor.transaction_count = 5000
        monitor.customer_count = 500
        
        limits = monitor.check_scalability_limits()
        
        assert limits["transactions_ok"] is True
        assert limits["customers_ok"] is True
        assert limits["transaction_count"] == 5000
        assert limits["customer_count"] == 500
    
    def test_scalability_limits_exceeded(self, monitor):
        """Test scalability check when limits exceeded"""
        monitor.transaction_count = 15000
        monitor.customer_count = 1500
        
        limits = monitor.check_scalability_limits()
        
        assert limits["transactions_ok"] is False
        assert limits["customers_ok"] is False
    
    def test_session_management(self, monitor):
        """Test active session tracking"""
        assert len(monitor.active_sessions) == 0
        
        monitor.register_session("session1")
        monitor.register_session("session2")
        
        assert len(monitor.active_sessions) == 2
        assert "session1" in monitor.active_sessions
        
        monitor.unregister_session("session1")
        
        assert len(monitor.active_sessions) == 1
        assert "session1" not in monitor.active_sessions
    
    def test_session_in_health_report(self, monitor):
        """Test active sessions appear in health report"""
        monitor.register_session("session1")
        monitor.register_session("session2")
        monitor.register_session("session3")
        
        health = monitor.get_system_health()
        
        assert health.active_sessions == 3


class TestSystemHealth:
    """Test system health reporting"""
    
    def test_health_report_empty_metrics(self, monitor):
        """Test health report with no metrics"""
        health = monitor.get_system_health()
        
        assert health.avg_response_time_ms == 0
        assert health.p95_response_time_ms == 0
        assert health.p99_response_time_ms == 0
        assert health.error_rate == 0
        assert health.total_operations == 0
    
    def test_health_report_with_metrics(self, monitor):
        """Test health report with recorded metrics"""
        # Add various operations
        for i in range(50):
            metric = PerformanceMetric(
                operation="test",
                duration_ms=100 + i,
                timestamp=datetime.now(),
                success=True
            )
            monitor.record_metric(metric)
        
        health = monitor.get_system_health()
        
        assert health.total_operations == 50
        assert health.avg_response_time_ms > 0
        assert health.error_rate == 0
    
    def test_performance_report_generation(self, monitor):
        """Test comprehensive performance report"""
        # Add some metrics
        for _ in range(10):
            with monitor.measure_operation("test"):
                time.sleep(0.001)
        
        monitor.track_transaction()
        monitor.track_customer()
        
        report = monitor.get_performance_report()
        
        assert "health" in report
        assert "scalability" in report
        assert "recommendations" in report
        assert "meeting_targets" in report
    
    def test_performance_report_recommendations(self, monitor):
        """Test performance report generates recommendations"""
        # Add slow operations
        for _ in range(10):
            metric = PerformanceMetric(
                operation="slow",
                duration_ms=500,  # Over 200ms target
                timestamp=datetime.now(),
                success=True
            )
            monitor.record_metric(metric)
        
        report = monitor.get_performance_report()
        
        assert len(report["recommendations"]) > 0
        assert report["meeting_targets"] is False
        assert any("response time" in r.lower() for r in report["recommendations"])
    
    def test_performance_report_scalability_warnings(self, monitor):
        """Test report warns about scalability limits"""
        monitor.transaction_count = 12000  # Over limit
        
        report = monitor.get_performance_report()
        
        assert len(report["recommendations"]) > 0
        assert any("transaction count" in r.lower() for r in report["recommendations"])


class TestBackupService:
    """Test automatic backup service"""
    
    def test_start_backup_service(self, monitor):
        """Test starting backup service"""
        assert monitor.backup_active is False
        
        monitor.start_backup_service()
        
        assert monitor.backup_active is True
        assert monitor.backup_thread is not None
        assert monitor.backup_thread.is_alive()
        
        monitor.stop_backup_service()
    
    def test_stop_backup_service(self, monitor):
        """Test stopping backup service"""
        monitor.start_backup_service()
        assert monitor.backup_active is True
        
        monitor.stop_backup_service()
        
        assert monitor.backup_active is False
    
    def test_backup_service_idempotent_start(self, monitor):
        """Test starting service multiple times is safe"""
        monitor.start_backup_service()
        thread1 = monitor.backup_thread
        
        monitor.start_backup_service()
        thread2 = monitor.backup_thread
        
        assert thread1 == thread2
        
        monitor.stop_backup_service()


class TestIntegration:
    """Integration tests for performance monitoring"""
    
    def test_complete_monitoring_workflow(self, monitor):
        """Test complete monitoring workflow"""
        # Start backup service
        monitor.start_backup_service()
        
        # Register session
        monitor.register_session("user_session")
        
        # Perform operations
        for i in range(20):
            with monitor.measure_operation(f"operation_{i}"):
                time.sleep(0.001)
            monitor.track_transaction()
        
        # Perform backup
        backup_info = monitor.perform_backup({"test": "data"})
        assert backup_info.success is True
        
        # Check health
        health = monitor.get_system_health()
        assert health.total_operations == 20
        assert health.active_sessions == 1
        
        # Get report
        report = monitor.get_performance_report()
        assert report["meeting_targets"] is True
        
        # Cleanup
        monitor.unregister_session("user_session")
        monitor.stop_backup_service()
    
    def test_error_recovery_workflow(self, monitor):
        """Test error recovery workflow"""
        recovery_called = False
        
        def recovery_handler(context):
            nonlocal recovery_called
            recovery_called = True
        
        monitor.register_error_handler("data_error", recovery_handler)
        
        # Simulate error
        try:
            with monitor.measure_operation("failing_op"):
                raise ValueError("Data error")
        except ValueError:
            pass
        
        # Attempt recovery
        result = monitor.recover_from_error("data_error", {"error": "test"})
        
        assert result is True
        assert recovery_called is True
        
        # Check error was recorded
        health = monitor.get_system_health()
        assert health.error_rate > 0
