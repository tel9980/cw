"""
Unit tests for Outsourced Processing Manager

Tests CRUD operations, cost calculations, and statistics for outsourced processing.

Requirements: 5.1, 5.2, 5.3, 5.5
"""

import pytest
import os
import tempfile
import shutil
from datetime import date, datetime
from decimal import Decimal

from oxidation_workflow_v18.models.core_models import (
    OutsourcedProcessing,
    ProcessType
)
from oxidation_workflow_v18.business.outsourced_processing_manager import (
    OutsourcedProcessingManager
)


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def manager(temp_data_dir):
    """创建外发加工管理器实例"""
    return OutsourcedProcessingManager(data_dir=temp_data_dir)


class TestOutsourcedProcessingCreation:
    """测试外发加工记录创建"""
    
    def test_create_sandblasting_processing(self, manager):
        """测试创建喷砂加工记录
        
        Requirements: 5.1, 5.2, 5.3
        """
        processing = manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5"),
            notes="喷砂加工"
        )
        
        assert processing.id is not None
        assert processing.order_id == "order-001"
        assert processing.supplier_id == "supplier-001"
        assert processing.process_type == ProcessType.SANDBLASTING
        assert processing.process_date == date(2024, 1, 15)
        assert processing.quantity == Decimal("100")
        assert processing.unit_price == Decimal("2.5")
        assert processing.total_cost == Decimal("250")  # 100 * 2.5
        assert processing.notes == "喷砂加工"
    
    def test_create_wire_drawing_processing(self, manager):
        """测试创建拉丝加工记录
        
        Requirements: 5.1, 5.2, 5.3
        """
        processing = manager.create_processing(
            order_id="order-002",
            supplier_id="supplier-002",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("50"),
            unit_price=Decimal("3.0"),
            notes="拉丝加工"
        )
        
        assert processing.process_type == ProcessType.WIRE_DRAWING
        assert processing.total_cost == Decimal("150")  # 50 * 3.0
    
    def test_create_polishing_processing(self, manager):
        """测试创建抛光加工记录
        
        Requirements: 5.1, 5.2, 5.3
        """
        processing = manager.create_processing(
            order_id="order-003",
            supplier_id="supplier-003",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("75"),
            unit_price=Decimal("4.0"),
            notes="抛光加工"
        )
        
        assert processing.process_type == ProcessType.POLISHING
        assert processing.total_cost == Decimal("300")  # 75 * 4.0
    
    def test_create_processing_auto_calculates_cost(self, manager):
        """测试创建记录时自动计算总成本
        
        Requirements: 5.3
        """
        processing = manager.create_processing(
            order_id="order-004",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 18),
            quantity=Decimal("123.45"),
            unit_price=Decimal("6.78")
        )
        
        expected_cost = Decimal("123.45") * Decimal("6.78")
        assert processing.total_cost == expected_cost
    
    def test_create_processing_persists_to_file(self, manager, temp_data_dir):
        """测试创建记录后持久化到文件
        
        Requirements: 5.1
        """
        manager.create_processing(
            order_id="order-005",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 19),
            quantity=Decimal("100"),
            unit_price=Decimal("2.0")
        )
        
        # 验证文件存在
        file_path = os.path.join(temp_data_dir, "outsourced_processing.json")
        assert os.path.exists(file_path)
        
        # 创建新管理器实例，验证数据已加载
        new_manager = OutsourcedProcessingManager(data_dir=temp_data_dir)
        assert len(new_manager.processing_records) == 1


class TestOutsourcedProcessingRetrieval:
    """测试外发加工记录查询"""
    
    def test_get_processing_by_id(self, manager):
        """测试根据ID获取记录"""
        processing = manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        
        retrieved = manager.get_processing(processing.id)
        assert retrieved is not None
        assert retrieved.id == processing.id
        assert retrieved.order_id == "order-001"
    
    def test_get_processing_nonexistent_returns_none(self, manager):
        """测试获取不存在的记录返回None"""
        result = manager.get_processing("nonexistent-id")
        assert result is None
    
    def test_get_processing_by_order(self, manager):
        """测试获取订单的所有外发加工记录
        
        Requirements: 5.5
        """
        # 创建多个外发加工记录
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-002",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("50"),
            unit_price=Decimal("3.0")
        )
        manager.create_processing(
            order_id="order-002",
            supplier_id="supplier-001",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("75"),
            unit_price=Decimal("4.0")
        )
        
        # 获取order-001的记录
        order_001_records = manager.get_processing_by_order("order-001")
        assert len(order_001_records) == 2
        assert all(r.order_id == "order-001" for r in order_001_records)
        
        # 验证按日期排序
        assert order_001_records[0].process_date <= order_001_records[1].process_date
    
    def test_query_processing_by_supplier(self, manager):
        """测试按供应商查询"""
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        manager.create_processing(
            order_id="order-002",
            supplier_id="supplier-001",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("50"),
            unit_price=Decimal("3.0")
        )
        manager.create_processing(
            order_id="order-003",
            supplier_id="supplier-002",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("75"),
            unit_price=Decimal("4.0")
        )
        
        supplier_001_records = manager.query_processing(supplier_id="supplier-001")
        assert len(supplier_001_records) == 2
        assert all(r.supplier_id == "supplier-001" for r in supplier_001_records)
    
    def test_query_processing_by_process_type(self, manager):
        """测试按工序类型查询"""
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        manager.create_processing(
            order_id="order-002",
            supplier_id="supplier-002",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("50"),
            unit_price=Decimal("3.0")
        )
        manager.create_processing(
            order_id="order-003",
            supplier_id="supplier-003",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("75"),
            unit_price=Decimal("4.0")
        )
        
        sandblasting_records = manager.query_processing(process_type=ProcessType.SANDBLASTING)
        assert len(sandblasting_records) == 2
        assert all(r.process_type == ProcessType.SANDBLASTING for r in sandblasting_records)
    
    def test_query_processing_by_date_range(self, manager):
        """测试按日期范围查询"""
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 10),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        manager.create_processing(
            order_id="order-002",
            supplier_id="supplier-002",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("50"),
            unit_price=Decimal("3.0")
        )
        manager.create_processing(
            order_id="order-003",
            supplier_id="supplier-003",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 20),
            quantity=Decimal("75"),
            unit_price=Decimal("4.0")
        )
        
        records = manager.query_processing(
            start_date=date(2024, 1, 12),
            end_date=date(2024, 1, 18)
        )
        assert len(records) == 1
        assert records[0].process_date == date(2024, 1, 15)
    
    def test_query_processing_multiple_filters(self, manager):
        """测试多条件组合查询"""
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-002",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("50"),
            unit_price=Decimal("3.0")
        )
        manager.create_processing(
            order_id="order-002",
            supplier_id="supplier-001",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("75"),
            unit_price=Decimal("4.0")
        )
        
        records = manager.query_processing(
            order_id="order-001",
            process_type=ProcessType.SANDBLASTING
        )
        assert len(records) == 2
        assert all(r.order_id == "order-001" and r.process_type == ProcessType.SANDBLASTING for r in records)


class TestOutsourcedProcessingUpdate:
    """测试外发加工记录更新"""
    
    def test_update_processing_quantity(self, manager):
        """测试更新数量"""
        processing = manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        
        success = manager.update_processing(
            processing.id,
            quantity=Decimal("150")
        )
        
        assert success is True
        updated = manager.get_processing(processing.id)
        assert updated.quantity == Decimal("150")
        assert updated.total_cost == Decimal("375")  # 150 * 2.5
    
    def test_update_processing_unit_price(self, manager):
        """测试更新单价"""
        processing = manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        
        success = manager.update_processing(
            processing.id,
            unit_price=Decimal("3.0")
        )
        
        assert success is True
        updated = manager.get_processing(processing.id)
        assert updated.unit_price == Decimal("3.0")
        assert updated.total_cost == Decimal("300")  # 100 * 3.0
    
    def test_update_processing_notes(self, manager):
        """测试更新备注"""
        processing = manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5"),
            notes="原始备注"
        )
        
        success = manager.update_processing(
            processing.id,
            notes="更新后的备注"
        )
        
        assert success is True
        updated = manager.get_processing(processing.id)
        assert updated.notes == "更新后的备注"
    
    def test_update_processing_multiple_fields(self, manager):
        """测试同时更新多个字段"""
        processing = manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        
        success = manager.update_processing(
            processing.id,
            quantity=Decimal("200"),
            unit_price=Decimal("3.5"),
            notes="批量更新"
        )
        
        assert success is True
        updated = manager.get_processing(processing.id)
        assert updated.quantity == Decimal("200")
        assert updated.unit_price == Decimal("3.5")
        assert updated.total_cost == Decimal("700")  # 200 * 3.5
        assert updated.notes == "批量更新"
    
    def test_update_nonexistent_processing_returns_false(self, manager):
        """测试更新不存在的记录返回False"""
        success = manager.update_processing(
            "nonexistent-id",
            quantity=Decimal("100")
        )
        assert success is False


class TestOutsourcedProcessingCostCalculation:
    """测试外发加工成本计算"""
    
    def test_get_order_total_cost_single_processing(self, manager):
        """测试获取订单的外发加工总成本（单个记录）
        
        Requirements: 5.5
        """
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        
        total_cost = manager.get_order_total_cost("order-001")
        assert total_cost == Decimal("250")
    
    def test_get_order_total_cost_multiple_processing(self, manager):
        """测试获取订单的外发加工总成本（多个记录）
        
        Requirements: 5.5
        """
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-002",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("50"),
            unit_price=Decimal("3.0")
        )
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-003",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("75"),
            unit_price=Decimal("4.0")
        )
        
        total_cost = manager.get_order_total_cost("order-001")
        # 250 + 150 + 300 = 700
        assert total_cost == Decimal("700")
    
    def test_get_order_total_cost_no_processing(self, manager):
        """测试获取没有外发加工的订单成本"""
        total_cost = manager.get_order_total_cost("order-999")
        assert total_cost == Decimal("0")


class TestOutsourcedProcessingStatistics:
    """测试外发加工统计功能"""
    
    def test_statistics_by_process_type(self, manager):
        """测试按工序类型统计"""
        # 创建不同工序类型的记录
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        manager.create_processing(
            order_id="order-002",
            supplier_id="supplier-002",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("50"),
            unit_price=Decimal("3.0")
        )
        manager.create_processing(
            order_id="order-003",
            supplier_id="supplier-003",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("75"),
            unit_price=Decimal("4.0")
        )
        
        stats = manager.get_statistics_by_process_type()
        
        # 验证喷砂统计
        sandblasting_stats = stats[ProcessType.SANDBLASTING.value]
        assert sandblasting_stats["count"] == 2
        assert Decimal(sandblasting_stats["total_cost"]) == Decimal("400")  # 250 + 150
        assert Decimal(sandblasting_stats["total_quantity"]) == Decimal("150")  # 100 + 50
        
        # 验证拉丝统计
        wire_drawing_stats = stats[ProcessType.WIRE_DRAWING.value]
        assert wire_drawing_stats["count"] == 1
        assert Decimal(wire_drawing_stats["total_cost"]) == Decimal("300")
        
        # 验证抛光统计（无记录）
        polishing_stats = stats[ProcessType.POLISHING.value]
        assert polishing_stats["count"] == 0
    
    def test_statistics_by_supplier(self, manager):
        """测试按供应商统计"""
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        manager.create_processing(
            order_id="order-002",
            supplier_id="supplier-001",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("50"),
            unit_price=Decimal("3.0")
        )
        manager.create_processing(
            order_id="order-003",
            supplier_id="supplier-002",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("75"),
            unit_price=Decimal("4.0")
        )
        
        stats = manager.get_statistics_by_supplier()
        
        # 验证supplier-001统计
        supplier_001_stats = stats["supplier-001"]
        assert supplier_001_stats["total_records"] == 2
        assert Decimal(supplier_001_stats["total_cost"]) == Decimal("400")  # 250 + 150
        assert ProcessType.SANDBLASTING.value in supplier_001_stats["process_type_breakdown"]
        assert ProcessType.WIRE_DRAWING.value in supplier_001_stats["process_type_breakdown"]
        
        # 验证supplier-002统计
        supplier_002_stats = stats["supplier-002"]
        assert supplier_002_stats["total_records"] == 1
        assert Decimal(supplier_002_stats["total_cost"]) == Decimal("300")
    
    def test_overall_statistics(self, manager):
        """测试总体统计"""
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        manager.create_processing(
            order_id="order-002",
            supplier_id="supplier-002",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("50"),
            unit_price=Decimal("3.0")
        )
        
        stats = manager.get_overall_statistics()
        
        assert stats["total_records"] == 2
        assert Decimal(stats["total_cost"]) == Decimal("400")  # 250 + 150
        assert Decimal(stats["total_quantity"]) == Decimal("150")  # 100 + 50
        assert "by_process_type" in stats
        assert "by_supplier" in stats
    
    def test_statistics_with_date_range(self, manager):
        """测试带日期范围的统计"""
        manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 10),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        manager.create_processing(
            order_id="order-002",
            supplier_id="supplier-002",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("50"),
            unit_price=Decimal("3.0")
        )
        manager.create_processing(
            order_id="order-003",
            supplier_id="supplier-003",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 20),
            quantity=Decimal("75"),
            unit_price=Decimal("4.0")
        )
        
        stats = manager.get_overall_statistics(
            start_date=date(2024, 1, 12),
            end_date=date(2024, 1, 18)
        )
        
        # 只有1月15日的记录在范围内
        assert stats["total_records"] == 1
        assert Decimal(stats["total_cost"]) == Decimal("150")


class TestOutsourcedProcessingIntegration:
    """测试外发加工管理器集成场景"""
    
    def test_complete_workflow(self, manager):
        """测试完整的外发加工工作流
        
        Requirements: 5.1, 5.2, 5.3, 5.5
        """
        # 1. 创建订单的多个外发加工记录
        processing1 = manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5"),
            notes="喷砂加工"
        )
        
        processing2 = manager.create_processing(
            order_id="order-001",
            supplier_id="supplier-002",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("50"),
            unit_price=Decimal("3.0"),
            notes="拉丝加工"
        )
        
        # 2. 查询订单的所有外发加工
        order_processing = manager.get_processing_by_order("order-001")
        assert len(order_processing) == 2
        
        # 3. 计算订单的外发加工总成本
        total_cost = manager.get_order_total_cost("order-001")
        assert total_cost == Decimal("400")  # 250 + 150
        
        # 4. 更新其中一个记录
        manager.update_processing(
            processing1.id,
            quantity=Decimal("120"),
            notes="喷砂加工（已更新）"
        )
        
        # 5. 重新计算总成本
        new_total_cost = manager.get_order_total_cost("order-001")
        assert new_total_cost == Decimal("450")  # 300 + 150
        
        # 6. 获取统计信息
        stats = manager.get_overall_statistics()
        assert stats["total_records"] == 2
        assert Decimal(stats["total_cost"]) == Decimal("450")
