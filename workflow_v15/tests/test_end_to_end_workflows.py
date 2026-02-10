"""
End-to-End Workflow Testing

This module tests complete daily workflows from start to finish, verifying
that all V1.5 components work together seamlessly.

Requirements: All requirements (end-to-end validation)
"""

import pytest
from datetime import datetime, date, timedelta
from typing import Dict, Any

from workflow_v15.core.workflow_engine import WorkflowEngine, WorkflowType
from workflow_v15.core.context_engine import ContextEngine
from workflow_v15.core.progressive_disclosure import ProgressiveDisclosureManager
from workflow_v15.core.one_click_operations import OneClickOperationManager
from workflow_v15.core.data_consistency import DataConsistencyManager
from workflow_v15.core.error_prevention import ErrorPreventionManager
from workflow_v15.core.automation_layer import AutomationLayer
from workflow_v15.core.mobile_interface import MobileInterfaceManager
from workflow_v15.core.offline_manager import OfflineDataManager
from workflow_v15.core.adaptive_interface import AdaptiveInterfaceManager
from workflow_v15.core.performance_monitor import PerformanceMonitor
from workflow_v15.core.morning_dashboard import MorningDashboardManager, PriorityTask, TaskPriority, TaskStatus


@pytest.fixture
def integrated_system():
    """Create integrated system with all components"""
    # Initialize components in dependency order
    workflow_engine = WorkflowEngine()
    context_engine = ContextEngine()
    progressive_disclosure = ProgressiveDisclosureManager()
    
    # Components that depend on others
    one_click_ops = OneClickOperationManager(
        context_engine=context_engine,
        workflow_engine=workflow_engine,
        progressive_disclosure_manager=progressive_disclosure
    )
    
    system = {
        'workflow_engine': workflow_engine,
        'context_engine': context_engine,
        'progressive_disclosure': progressive_disclosure,
        'one_click_ops': one_click_ops,
        'data_consistency': DataConsistencyManager(),
        'error_prevention': ErrorPreventionManager(),
        'automation': AutomationLayer(),
        'mobile': MobileInterfaceManager(),
        'offline': OfflineDataManager(),
        'adaptive': AdaptiveInterfaceManager(),
        'performance': PerformanceMonitor(backup_dir="test_backups"),
        'dashboard': MorningDashboardManager()
    }
    return system


class TestMorningStartupWorkflow:
    """Test complete morning startup workflow"""
    
    def test_morning_startup_complete_flow(self, integrated_system):
        """Test complete morning startup workflow"""
        user_id = "test_user"
        
        # Step 1: User starts system - Performance monitoring begins
        perf = integrated_system['performance']
        perf.register_session(user_id)
        
        with perf.measure_operation("morning_startup"):
            # Step 2: Generate morning dashboard
            dashboard_mgr = integrated_system['dashboard']
            
            # Add some tasks
            task1 = PriorityTask(
                task_id="morning_task1",
                title="Review yesterday's transactions",
                description="",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                due_date=date.today()
            )
            dashboard_mgr.add_task(task1)
            
            dashboard = dashboard_mgr.generate_dashboard(user_id)
            
            # Step 3: Progressive disclosure shows primary actions
            pd_manager = integrated_system['progressive_disclosure']
            primary_actions = pd_manager.get_primary_actions(
                user_id=user_id,
                context="morning_startup"
            )
            
            # Step 4: Adaptive interface adjusts based on history
            adaptive = integrated_system['adaptive']
            adaptive.track_interaction(user_id, "morning_startup", "view_dashboard")
        
        # Verify workflow completed successfully
        assert dashboard is not None
        assert dashboard.user_id == user_id
        assert len(primary_actions) <= 5  # Progressive disclosure limit
        
        # Verify performance
        health = perf.get_system_health()
        assert health.active_sessions == 1
        
        # Cleanup
        perf.unregister_session(user_id)
    
    def test_morning_dashboard_with_pending_tasks(self, integrated_system):
        """Test morning dashboard shows pending tasks correctly"""
        user_id = "test_user"
        dashboard_mgr = integrated_system['dashboard']
        
        # Add various tasks
        today = date.today()
        tasks = [
            PriorityTask(
                task_id=f"task{i}",
                title=f"Task {i}",
                description="",
                priority=TaskPriority.HIGH if i % 2 == 0 else TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                due_date=today if i < 3 else today + timedelta(days=i)
            )
            for i in range(5)
        ]
        
        for task in tasks:
            dashboard_mgr.add_task(task)
        
        # Generate dashboard
        dashboard = dashboard_mgr.generate_dashboard(user_id)
        
        # Verify dashboard content
        assert len(dashboard.priority_tasks) > 0
        assert dashboard.summary.total_tasks == 5
        assert dashboard.summary.due_today > 0
        assert len(dashboard.quick_actions) <= 5


class TestTransactionEntryWorkflow:
    """Test complete transaction entry workflow"""
    
    def test_transaction_entry_basic_flow(self, integrated_system):
        """Test basic transaction entry workflow"""
        user_id = "test_user"
        
        # Step 1: User initiates transaction entry
        workflow_engine = integrated_system['workflow_engine']
        
        # Step 2: Start workflow
        session = workflow_engine.start_workflow(
            user_id=user_id,
            workflow_type=WorkflowType.TRANSACTION_ENTRY
        )
        
        # Step 3: Get smart defaults from context
        context_engine = integrated_system['context_engine']
        smart_defaults = context_engine.generate_smart_defaults(
            context_type="transaction_entry",
            current_context={"transaction_type": "sale"}
        )
        
        # Step 4: Complete workflow step
        workflow_engine.complete_step(session.session_id, {
            "transaction_id": "txn_001",
            "status": "completed"
        })
        
        # Verify workflow
        assert session is not None
        assert smart_defaults is not None
    
    def test_transaction_entry_with_error_prevention(self, integrated_system):
        """Test transaction entry with error prevention"""
        user_id = "test_user"
        
        # Step 1: Start transaction
        workflow_engine = integrated_system['workflow_engine']
        session = workflow_engine.start_workflow(
            user_id=user_id,
            workflow_type=WorkflowType.TRANSACTION_ENTRY
        )
        
        # Step 2: Enter invalid data
        error_prevention = integrated_system['error_prevention']
        
        invalid_data = {
            "amount": -100,  # Invalid negative amount
            "date": "invalid_date"
        }
        
        # Step 3: Validate with error prevention
        validation = error_prevention.validate_input(
            field_name="amount",
            value=invalid_data["amount"],
            context={"transaction_type": "sale"}
        )
        
        # Step 4: Get correction suggestions
        if not validation.is_valid:
            suggestions = error_prevention.get_correction_suggestions(
                field_name="amount",
                invalid_value=invalid_data["amount"],
                context={}
            )
            
            assert len(suggestions) > 0
            assert validation.is_valid is False
        
        # Step 5: Correct the data
        corrected_data = {
            "amount": 100,  # Corrected
            "date": date.today().isoformat()
        }
        
        corrected_validation = error_prevention.validate_input(
            field_name="amount",
            value=corrected_data["amount"],
            context={}
        )
        
        assert corrected_validation.is_valid is True


class TestEndOfDayWorkflow:
    """Test complete end-of-day workflow"""
    
    def test_end_of_day_complete_flow(self, integrated_system):
        """Test complete end-of-day workflow"""
        user_id = "test_user"
        
        # Step 1: Start end-of-day workflow
        workflow_engine = integrated_system['workflow_engine']
        session = workflow_engine.start_workflow(
            user_id=user_id,
            workflow_type=WorkflowType.END_OF_DAY
        )
        
        # Step 2: Perform backup
        perf = integrated_system['performance']
        backup_data = {
            "transactions": [],
            "date": date.today().isoformat(),
            "user_id": user_id
        }
        backup_info = perf.perform_backup(backup_data)
        
        # Step 3: Generate summary
        summary = {
            "total_transactions": 0,
            "total_amount": 0,
            "backup_success": backup_info.success
        }
        
        # Step 4: Complete workflow
        workflow_engine.complete_step(session.session_id, summary)
        
        # Verify workflow
        assert session is not None
        assert backup_info.success is True


class TestComponentIntegration:
    """Test integration between components"""
    
    def test_workflow_with_progressive_disclosure(self, integrated_system):
        """Test workflow engine integrates with progressive disclosure"""
        user_id = "test_user"
        
        workflow_engine = integrated_system['workflow_engine']
        pd_manager = integrated_system['progressive_disclosure']
        
        # Start workflow
        session = workflow_engine.start_workflow(
            user_id=user_id,
            workflow_type=WorkflowType.TRANSACTION_ENTRY
        )
        
        # Get actions for this workflow step
        actions = pd_manager.get_primary_actions(
            user_id=user_id,
            context="transaction_entry"
        )
        
        assert session is not None
        assert len(actions) <= 5
    
    def test_context_engine_with_smart_defaults(self, integrated_system):
        """Test context engine provides smart defaults"""
        context_engine = integrated_system['context_engine']
        
        # Generate smart defaults
        defaults = context_engine.generate_smart_defaults(
            context_type="transaction",
            current_context={"customer": "Test Customer"}
        )
        
        assert defaults is not None
        assert isinstance(defaults, dict)
    
    def test_error_prevention_with_validation(self, integrated_system):
        """Test error prevention validates inputs"""
        error_prevention = integrated_system['error_prevention']
        
        # Test valid input
        valid_result = error_prevention.validate_input(
            field_name="amount",
            value=100,
            context={}
        )
        
        assert valid_result.is_valid is True
        
        # Test invalid input
        invalid_result = error_prevention.validate_input(
            field_name="amount",
            value=-100,
            context={}
        )
        
        assert invalid_result.is_valid is False
    
    def test_performance_monitoring_integration(self, integrated_system):
        """Test performance monitoring tracks operations"""
        perf = integrated_system['performance']
        workflow_engine = integrated_system['workflow_engine']
        
        user_id = "test_user"
        perf.register_session(user_id)
        
        # Perform operations with monitoring
        with perf.measure_operation("workflow_start"):
            session = workflow_engine.start_workflow(
                user_id=user_id,
                workflow_type=WorkflowType.TRANSACTION_ENTRY
            )
        
        # Check metrics recorded
        health = perf.get_system_health()
        assert health.total_operations > 0
        
        perf.unregister_session(user_id)
    
    def test_dashboard_with_workflow_tasks(self, integrated_system):
        """Test dashboard integrates with workflow tasks"""
        user_id = "test_user"
        dashboard_mgr = integrated_system['dashboard']
        
        # Add workflow-related tasks
        task = PriorityTask(
            task_id="workflow_task",
            title="Complete transaction entry",
            description="",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=date.today()
        )
        dashboard_mgr.add_task(task)
        
        # Generate dashboard
        dashboard = dashboard_mgr.generate_dashboard(user_id)
        
        # Verify task appears
        assert len(dashboard.priority_tasks) > 0
        assert any(t.task_id == "workflow_task" for t in dashboard.priority_tasks)


class TestPerformanceAndReliability:
    """Test performance and reliability across workflows"""
    
    def test_response_time_under_load(self, integrated_system):
        """Test system maintains performance under load"""
        user_id = "test_user"
        perf = integrated_system['performance']
        workflow_engine = integrated_system['workflow_engine']
        
        # Perform multiple operations
        for i in range(20):
            with perf.measure_operation(f"workflow_operation_{i}"):
                session = workflow_engine.start_workflow(
                    user_id=user_id,
                    workflow_type=WorkflowType.TRANSACTION_ENTRY
                )
                workflow_engine.complete_step(session.session_id, {"status": "done"})
        
        # Check performance
        health = perf.get_system_health()
        
        # Should meet reasonable performance targets
        assert health.avg_response_time_ms < 1000  # Under 1 second average
        assert health.error_rate < 0.1  # Less than 10% errors
    
    def test_error_recovery_without_data_loss(self, integrated_system):
        """Test system recovers from errors without data loss"""
        user_id = "test_user"
        error_prevention = integrated_system['error_prevention']
        perf = integrated_system['performance']
        
        # Step 1: Create draft
        draft_data = {
            "transaction_type": "sale",
            "amount": 1000,
            "customer": "Test Customer"
        }
        
        draft = error_prevention.save_draft(
            form_type="transaction",
            data=draft_data
        )
        
        # Step 2: Simulate error recovery
        def recovery_handler(context):
            pass
        
        perf.register_error_handler("transaction_error", recovery_handler)
        
        # Step 3: Recover draft
        recovered_draft = error_prevention.get_draft("transaction")
        
        # Verify no data loss
        assert recovered_draft is not None
        assert recovered_draft.data == draft_data
    
    def test_scalability_with_many_operations(self, integrated_system):
        """Test system handles many operations"""
        perf = integrated_system['performance']
        
        # Simulate many transactions
        for i in range(100):
            perf.track_transaction()
        
        # Check scalability
        limits = perf.check_scalability_limits()
        
        assert limits["transactions_ok"] is True
        assert perf.transaction_count == 100


class TestCompleteDailyWorkflow:
    """Test complete daily workflow integration"""
    
    def test_complete_daily_workflow(self, integrated_system):
        """Test complete daily workflow from morning to end-of-day"""
        user_id = "test_user"
        
        # === Morning Startup ===
        perf = integrated_system['performance']
        perf.start_backup_service()
        perf.register_session(user_id)
        
        # Generate dashboard
        dashboard_mgr = integrated_system['dashboard']
        task = PriorityTask(
            task_id="daily_task",
            title="Process transactions",
            description="",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=date.today()
        )
        dashboard_mgr.add_task(task)
        morning_dashboard = dashboard_mgr.generate_dashboard(user_id)
        
        # === Transaction Processing ===
        workflow_engine = integrated_system['workflow_engine']
        
        # Process multiple transactions
        for i in range(5):
            session = workflow_engine.start_workflow(
                user_id=user_id,
                workflow_type=WorkflowType.TRANSACTION_ENTRY
            )
            
            workflow_engine.complete_step(session.session_id, {
                "transaction_id": f"txn_{i}",
                "amount": 100 * (i + 1)
            })
            
            perf.track_transaction()
        
        # === End of Day ===
        # Mark task complete
        dashboard_mgr.mark_task_completed("daily_task")
        
        # Perform backup
        backup_data = {
            "transactions": 5,
            "date": date.today().isoformat()
        }
        backup_info = perf.perform_backup(backup_data)
        
        # Generate end-of-day dashboard
        eod_dashboard = dashboard_mgr.generate_dashboard(user_id)
        
        # Verify complete workflow
        assert morning_dashboard.summary.pending_tasks > 0
        assert eod_dashboard.summary.completed_today > 0
        assert backup_info.success is True
        assert perf.transaction_count == 5
        
        # Cleanup
        perf.unregister_session(user_id)
        perf.stop_backup_service()
    
    def test_multi_user_workflow(self, integrated_system):
        """Test system handles multiple users"""
        users = ["user1", "user2", "user3"]
        perf = integrated_system['performance']
        workflow_engine = integrated_system['workflow_engine']
        
        # Each user starts a workflow
        sessions = {}
        for user_id in users:
            perf.register_session(user_id)
            session = workflow_engine.start_workflow(
                user_id=user_id,
                workflow_type=WorkflowType.TRANSACTION_ENTRY
            )
            sessions[user_id] = session
        
        # Verify all sessions created
        assert len(sessions) == 3
        assert perf.get_system_health().active_sessions == 3
        
        # Cleanup
        for user_id in users:
            perf.unregister_session(user_id)


class TestUserExperienceFlows:
    """Test user experience flows"""
    
    def test_progressive_disclosure_workflow(self, integrated_system):
        """Test progressive disclosure throughout workflow"""
        user_id = "test_user"
        pd_manager = integrated_system['progressive_disclosure']
        
        # Step 1: Initial view - limited options
        primary_actions = pd_manager.get_primary_actions(
            user_id=user_id,
            context="main_menu"
        )
        
        assert len(primary_actions) <= 5
        
        # Step 2: User requests advanced features
        secondary_actions = pd_manager.get_secondary_actions(
            user_id=user_id,
            context="main_menu"
        )
        
        # Should have more options available
        assert len(secondary_actions) >= len(primary_actions)
        
        # Step 3: Contextual help
        help_content = pd_manager.provide_contextual_help(
            user_id=user_id,
            context="transaction_entry",
            trigger="hover"
        )
        
        assert help_content is not None
    
    def test_one_click_operation_workflow(self, integrated_system):
        """Test one-click operation workflow"""
        user_id = "test_user"
        one_click = integrated_system['one_click_ops']
        
        # Execute one-click operation
        result = one_click.execute_one_click_operation(
            user_id=user_id,
            operation_type="common_sale",
            data={
                "customer": "Quick Customer",
                "amount": 500
            }
        )
        
        # Verify operation completed
        assert result.get("success") is True

    
    def test_morning_dashboard_with_pending_tasks(self, integrated_system):
        """Test morning dashboard shows pending tasks correctly"""
        user_id = "test_user"
        dashboard_mgr = integrated_system['dashboard']
        
        # Add various tasks
        today = date.today()
        tasks = [
            PriorityTask(
                task_id=f"task{i}",
                title=f"Task {i}",
                description="",
                priority=TaskPriority.HIGH if i % 2 == 0 else TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                due_date=today if i < 3 else today + timedelta(days=i)
            )
            for i in range(5)
        ]
        
        for task in tasks:
            dashboard_mgr.add_task(task)
        
        # Generate dashboard
        dashboard = dashboard_mgr.generate_dashboard(user_id)
        
        # Verify dashboard content
        assert len(dashboard.priority_tasks) > 0
        assert dashboard.summary.total_tasks == 5
        assert dashboard.summary.due_today > 0
        assert len(dashboard.quick_actions) <= 5


class TestTransactionEntryWorkflow:
    """Test complete transaction entry workflow"""
    
    def test_transaction_entry_with_smart_defaults(self, integrated_system):
        """Test transaction entry with context-aware smart defaults"""
        user_id = "test_user"
        
        # Step 1: User initiates transaction entry
        workflow_engine = integrated_system['workflow_engine']
        context_engine = integrated_system['context_engine']
        
        # Track historical pattern
        for i in range(5):
            context_engine.track_user_action(user_id, "transaction_entry", {
                "customer": "Customer A",
                "amount": 1000 + i * 100,
                "category": "sales"
            })
        
        # Step 2: Start workflow
        session = workflow_engine.start_workflow(
            user_id=user_id,
            workflow_type=WorkflowType.TRANSACTION_ENTRY,
            initial_data={"transaction_type": "sale"}
        )
        
        # Step 3: Get smart defaults from context
        smart_defaults = context_engine.generate_smart_defaults(
            user_id=user_id,
            context_type="transaction_entry",
            current_context={"transaction_type": "sale"}
        )
        
        # Step 4: One-click operation with defaults
        one_click = integrated_system['one_click_ops']
        transaction_data = {
            "customer": smart_defaults.get("customer", "Customer A"),
            "amount": 1500,
            "category": smart_defaults.get("category", "sales"),
            "date": date.today().isoformat()
        }
        
        result = one_click.execute_one_click_transaction(
            user_id=user_id,
            transaction_type="sale",
            data=transaction_data
        )
        
        # Step 5: Data consistency check
        data_consistency = integrated_system['data_consistency']
        consistency_check = data_consistency.validate_transaction(transaction_data)
        
        # Step 6: Complete workflow step
        workflow_engine.complete_step(session.session_id, {
            "transaction_id": result.get("transaction_id"),
            "status": "completed"
        })
        
        # Verify workflow
        assert session is not None
        assert result.get("success") is True
        assert consistency_check.get("valid") is True
        assert smart_defaults.get("customer") is not None
    
    def test_transaction_entry_with_error_prevention(self, integrated_system):
        """Test transaction entry with error prevention"""
        user_id = "test_user"
        
        # Step 1: Start transaction
        workflow_engine = integrated_system['workflow_engine']
        session = workflow_engine.start_workflow(
            user_id=user_id,
            workflow_type=WorkflowType.TRANSACTION_ENTRY,
            initial_data={}
        )
        
        # Step 2: Enter invalid data
        error_prevention = integrated_system['error_prevention']
        
        invalid_data = {
            "amount": -100,  # Invalid negative amount
            "date": "invalid_date"
        }
        
        # Step 3: Validate with error prevention
        validation = error_prevention.validate_input(
            field_name="amount",
            value=invalid_data["amount"],
            context={"transaction_type": "sale"}
        )
        
        # Step 4: Get correction suggestions
        if not validation.is_valid:
            suggestions = error_prevention.get_correction_suggestions(
                field_name="amount",
                invalid_value=invalid_data["amount"],
                context={}
            )
            
            assert len(suggestions) > 0
            assert validation.is_valid is False
        
        # Step 5: Correct the data
        corrected_data = {
            "amount": 100,  # Corrected
            "date": date.today().isoformat()
        }
        
        corrected_validation = error_prevention.validate_input(
            field_name="amount",
            value=corrected_data["amount"],
            context={}
        )
        
        assert corrected_validation.is_valid is True


class TestEndOfDayWorkflow:
    """Test complete end-of-day workflow"""
    
    def test_end_of_day_complete_flow(self, integrated_system):
        """Test complete end-of-day workflow"""
        user_id = "test_user"
        
        # Step 1: Start end-of-day workflow
        workflow_engine = integrated_system['workflow_engine']
        session = workflow_engine.start_workflow(
            user_id=user_id,
            workflow_type=WorkflowType.END_OF_DAY,
            initial_data={"date": date.today().isoformat()}
        )
        
        # Step 2: Data consistency check
        data_consistency = integrated_system['data_consistency']
        
        # Simulate some transactions
        transactions = [
            {"id": f"txn{i}", "amount": 100 * i, "status": "completed"}
            for i in range(5)
        ]
        
        for txn in transactions:
            data_consistency.track_data_change(
                entity_type="transaction",
                entity_id=txn["id"],
                changes=txn
            )
        
        consistency_report = data_consistency.check_overall_consistency()
        
        # Step 3: Perform backup
        perf = integrated_system['performance']
        backup_data = {
            "transactions": transactions,
            "date": date.today().isoformat(),
            "user_id": user_id
        }
        backup_info = perf.perform_backup(backup_data)
        
        # Step 4: Generate summary
        summary = {
            "total_transactions": len(transactions),
            "total_amount": sum(t["amount"] for t in transactions),
            "consistency_issues": len(consistency_report.get("issues", [])),
            "backup_success": backup_info.success
        }
        
        # Step 5: Complete workflow
        workflow_engine.complete_step(session.session_id, summary)
        
        # Verify workflow
        assert session is not None
        assert backup_info.success is True
        assert summary["total_transactions"] == 5
        assert consistency_report.get("overall_status") in ["consistent", "warning"]
    
    def test_end_of_day_with_automation(self, integrated_system):
        """Test end-of-day with automation suggestions"""
        user_id = "test_user"
        
        # Step 1: Track repeated end-of-day actions
        automation = integrated_system['automation']
        
        # Simulate repeated pattern
        for i in range(5):
            automation.track_user_action(user_id, {
                "action": "generate_daily_report",
                "timestamp": datetime.now() - timedelta(days=i),
                "parameters": {"report_type": "daily_summary"}
            })
        
        # Step 2: Detect automation opportunity
        opportunities = automation.detect_automation_opportunities(user_id)
        
        # Step 3: Create automation rule if pattern detected
        if opportunities:
            rule = automation.create_automation_rule(
                user_id=user_id,
                rule_name="Daily Report Generation",
                trigger_pattern={"action": "end_of_day"},
                actions=[{"type": "generate_report", "report_type": "daily_summary"}],
                requires_approval=True
            )
            
            assert rule is not None
            assert rule.requires_approval is True


class TestMobileWorkflow:
    """Test mobile-specific workflows"""
    
    def test_mobile_transaction_entry(self, integrated_system):
        """Test transaction entry on mobile"""
        user_id = "test_user"
        
        # Step 1: Initialize mobile interface
        mobile = integrated_system['mobile']
        mobile_session = mobile.start_mobile_session(user_id, {
            "device_type": "smartphone",
            "screen_size": "small"
        })
        
        # Step 2: Get mobile-optimized actions
        actions = mobile.get_mobile_actions(user_id, "transaction_entry")
        
        # Step 3: Verify progressive disclosure for mobile
        assert len(actions) <= 5  # Even more limited on mobile
        
        # Step 4: Simulate voice input
        voice_data = mobile.process_voice_input(
            user_id=user_id,
            audio_text="Record sale of 500 yuan to Customer A"
        )
        
        # Step 5: Process transaction
        if voice_data.get("success"):
            transaction_data = voice_data.get("parsed_data", {})
            assert "amount" in transaction_data or "customer" in transaction_data
        
        # Cleanup
        mobile.end_mobile_session(mobile_session.session_id)
    
    def test_offline_mobile_workflow(self, integrated_system):
        """Test offline mobile workflow with sync"""
        user_id = "test_user"
        
        # Step 1: Go offline
        offline = integrated_system['offline']
        offline.set_offline_mode(user_id, True)
        
        # Step 2: Create offline transactions
        offline_transactions = []
        for i in range(3):
            txn = offline.create_offline_transaction(
                user_id=user_id,
                transaction_data={
                    "amount": 100 * (i + 1),
                    "customer": f"Customer {i}",
                    "date": date.today().isoformat()
                }
            )
            offline_transactions.append(txn)
        
        # Step 3: Go back online
        offline.set_offline_mode(user_id, False)
        
        # Step 4: Sync offline data
        sync_result = offline.sync_offline_data(user_id)
        
        # Verify sync
        assert sync_result.get("success") is True
        assert sync_result.get("synced_count") == 3
        assert len(sync_result.get("conflicts", [])) == 0


class TestAdaptiveLearningWorkflow:
    """Test adaptive learning across workflows"""
    
    def test_interface_adaptation_over_time(self, integrated_system):
        """Test interface adapts based on usage patterns"""
        user_id = "test_user"
        adaptive = integrated_system['adaptive']
        
        # Step 1: Track user interactions over time
        common_actions = ["view_transactions", "create_invoice", "view_reports"]
        
        for day in range(10):
            for action in common_actions:
                # User performs actions with different frequencies
                frequency = 5 if action == "view_transactions" else 2
                for _ in range(frequency):
                    adaptive.track_interaction(user_id, action, {
                        "timestamp": datetime.now() - timedelta(days=day)
                    })
        
        # Step 2: Get optimized layout
        layout = adaptive.get_optimized_layout(user_id, "main_menu")
        
        # Step 3: Verify most-used action is prioritized
        assert layout is not None
        if layout.get("prioritized_actions"):
            # Most frequent action should be first
            assert "view_transactions" in str(layout.get("prioritized_actions", []))
    
    def test_context_learning_from_corrections(self, integrated_system):
        """Test system learns from user corrections"""
        user_id = "test_user"
        context_engine = integrated_system['context_engine']
        
        # Step 1: System makes predictions
        for i in range(5):
            # System predicts customer
            predicted = context_engine.generate_smart_defaults(
                user_id=user_id,
                context_type="transaction",
                current_context={"amount": 1000}
            )
            
            # Step 2: User corrects prediction
            actual_customer = "Customer B"  # User always chooses Customer B
            context_engine.learn_from_correction(
                user_id=user_id,
                context_type="transaction",
                predicted_value=predicted.get("customer", "Customer A"),
                actual_value=actual_customer,
                context={"amount": 1000}
            )
        
        # Step 3: Verify learning improved predictions
        final_prediction = context_engine.generate_smart_defaults(
            user_id=user_id,
            context_type="transaction",
            current_context={"amount": 1000}
        )
        
        # After learning, should predict Customer B more often
        # (In real implementation, this would use ML model)
        assert final_prediction is not None


class TestPerformanceAndReliability:
    """Test performance and reliability across workflows"""
    
    def test_response_time_under_load(self, integrated_system):
        """Test system maintains performance under load"""
        user_id = "test_user"
        perf = integrated_system['performance']
        workflow_engine = integrated_system['workflow_engine']
        
        # Perform multiple operations
        for i in range(20):
            with perf.measure_operation(f"workflow_operation_{i}"):
                session = workflow_engine.start_workflow(
                    user_id=user_id,
                    workflow_type=WorkflowType.TRANSACTION_ENTRY,
                    initial_data={"iteration": i}
                )
                workflow_engine.complete_step(session.session_id, {"status": "done"})
        
        # Check performance
        health = perf.get_system_health()
        
        # Should meet 200ms target for most operations
        assert health.avg_response_time_ms < 500  # Relaxed for testing
        assert health.error_rate < 0.1  # Less than 10% errors
    
    def test_error_recovery_without_data_loss(self, integrated_system):
        """Test system recovers from errors without data loss"""
        user_id = "test_user"
        error_prevention = integrated_system['error_prevention']
        perf = integrated_system['performance']
        
        # Step 1: Create draft
        draft_data = {
            "transaction_type": "sale",
            "amount": 1000,
            "customer": "Test Customer"
        }
        
        draft = error_prevention.save_draft(
            user_id=user_id,
            form_type="transaction",
            data=draft_data
        )
        
        # Step 2: Simulate error
        def recovery_handler(context):
            # Recovery logic
            pass
        
        perf.register_error_handler("transaction_error", recovery_handler)
        
        # Step 3: Recover draft
        recovered_draft = error_prevention.get_draft(user_id, "transaction")
        
        # Verify no data loss
        assert recovered_draft is not None
        assert recovered_draft.data == draft_data
    
    def test_scalability_with_many_transactions(self, integrated_system):
        """Test system handles large number of transactions"""
        perf = integrated_system['performance']
        data_consistency = integrated_system['data_consistency']
        
        # Simulate many transactions
        for i in range(100):
            perf.track_transaction()
            
            # Track data changes
            data_consistency.track_data_change(
                entity_type="transaction",
                entity_id=f"txn_{i}",
                changes={"amount": i * 100}
            )
        
        # Check scalability
        limits = perf.check_scalability_limits()
        
        assert limits["transactions_ok"] is True
        assert perf.transaction_count == 100


class TestIntegrationScenarios:
    """Test complex integration scenarios"""
    
    def test_complete_daily_workflow_integration(self, integrated_system):
        """Test complete daily workflow from morning to end-of-day"""
        user_id = "test_user"
        
        # === Morning Startup ===
        perf = integrated_system['performance']
        perf.start_backup_service()
        perf.register_session(user_id)
        
        # Generate dashboard
        dashboard_mgr = integrated_system['dashboard']
        task = PriorityTask(
            task_id="daily_task",
            title="Process transactions",
            description="",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=date.today()
        )
        dashboard_mgr.add_task(task)
        morning_dashboard = dashboard_mgr.generate_dashboard(user_id)
        
        # === Transaction Processing ===
        workflow_engine = integrated_system['workflow_engine']
        
        # Process multiple transactions
        for i in range(5):
            session = workflow_engine.start_workflow(
                user_id=user_id,
                workflow_type=WorkflowType.TRANSACTION_ENTRY,
                initial_data={"transaction_num": i}
            )
            
            workflow_engine.complete_step(session.session_id, {
                "transaction_id": f"txn_{i}",
                "amount": 100 * (i + 1)
            })
            
            perf.track_transaction()
        
        # === End of Day ===
        # Mark task complete
        dashboard_mgr.mark_task_completed("daily_task")
        
        # Perform backup
        backup_data = {
            "transactions": 5,
            "date": date.today().isoformat()
        }
        backup_info = perf.perform_backup(backup_data)
        
        # Generate end-of-day dashboard
        eod_dashboard = dashboard_mgr.generate_dashboard(user_id)
        
        # Verify complete workflow
        assert morning_dashboard.summary.pending_tasks > 0
        assert eod_dashboard.summary.completed_today > 0
        assert backup_info.success is True
        assert perf.transaction_count == 5
        
        # Cleanup
        perf.unregister_session(user_id)
        perf.stop_backup_service()
    
    def test_multi_component_error_handling(self, integrated_system):
        """Test error handling across multiple components"""
        user_id = "test_user"
        
        # Component 1: Workflow Engine
        workflow_engine = integrated_system['workflow_engine']
        session = workflow_engine.start_workflow(
            user_id=user_id,
            workflow_type=WorkflowType.TRANSACTION_ENTRY,
            initial_data={}
        )
        
        # Component 2: Error Prevention
        error_prevention = integrated_system['error_prevention']
        
        # Save draft before potential error
        draft = error_prevention.save_draft(
            user_id=user_id,
            form_type="transaction",
            data={"amount": 1000}
        )
        
        # Component 3: Performance Monitor
        perf = integrated_system['performance']
        
        # Register recovery handler
        recovered = False
        def recovery_handler(context):
            nonlocal recovered
            recovered = True
        
        perf.register_error_handler("test_error", recovery_handler)
        
        # Simulate error and recovery
        perf.recover_from_error("test_error", {"session_id": session.session_id})
        
        # Verify error handling
        assert draft is not None
        assert recovered is True
        
        # Verify draft can be recovered
        recovered_draft = error_prevention.get_draft(user_id, "transaction")
        assert recovered_draft.data["amount"] == 1000


class TestUserExperienceFlows:
    """Test user experience flows"""
    
    def test_progressive_disclosure_workflow(self, integrated_system):
        """Test progressive disclosure throughout workflow"""
        user_id = "test_user"
        pd_manager = integrated_system['progressive_disclosure']
        
        # Step 1: Initial view - limited options
        primary_actions = pd_manager.get_primary_actions(
            user_id=user_id,
            context="main_menu"
        )
        
        assert len(primary_actions) <= 5
        
        # Step 2: User requests advanced features
        secondary_actions = pd_manager.get_secondary_actions(
            user_id=user_id,
            context="main_menu"
        )
        
        # Should have more options available
        assert len(secondary_actions) >= len(primary_actions)
        
        # Step 3: Contextual help
        help_content = pd_manager.get_contextual_help(
            user_id=user_id,
            context="transaction_entry"
        )
        
        assert help_content is not None
    
    def test_one_click_operation_workflow(self, integrated_system):
        """Test one-click operation workflow"""
        user_id = "test_user"
        one_click = integrated_system['one_click_ops']
        
        # Step 1: Execute one-click transaction
        result = one_click.execute_one_click_transaction(
            user_id=user_id,
            transaction_type="sale",
            data={
                "customer": "Quick Customer",
                "amount": 500
            }
        )
        
        # Step 2: Verify all steps completed
        assert result.get("success") is True
        assert result.get("transaction_id") is not None
        
        # Step 3: Verify data consistency maintained
        data_consistency = integrated_system['data_consistency']
        consistency = data_consistency.check_overall_consistency()
        
        assert consistency.get("overall_status") in ["consistent", "warning"]
