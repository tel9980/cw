"""
Unit tests for industry-specific features

Tests for:
- ProcessingOrderManager
- OutsourcedProcessingManager
- IndustryClassifier
"""

import pytest
import os
import json
import tempfile
import shutil
from datetime import date, datetime
from decimal import Decimal

from oxidation_complete_v17.models.core_models import (
    ProcessingOrder,
    OutsourcedProcessing,
    OrderStatus,
    PricingUnit,
    ProcessType
)
from oxidation_complete_v17.industry import (
    ProcessingOrderManager,
    OutsourcedProcessingManager,
    IndustryClassifier
)


class TestProcessingOrderManager:
    """测试加工订单管理器"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_dir):
        """创建订单管理器实例"""
        return ProcessingOrderManager(data_dir=temp_dir)
    
    def test_create_order(self, manager):
        """测试创建订单"""
        order = manager.create_order(
            order_number="ORD001",
            customer_id="CUST001",
            order_date=date(2024, 1, 15),
            product_name="铝型材氧化",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("100"),
            unit_price=Decimal("5.50"),
            notes="测试订单"
        )
        
        assert order is not None
        assert order.order_number == "ORD001"
        assert order.customer_id == "CUST001"
        assert order.product_name == "铝型材氧化"
        assert order.pricing_unit == PricingUnit.PIECE
        assert order.quantity == Decimal("100")
        assert order.unit_price == Decimal("5.50")
        assert order.total_amount == Decimal("550.00")
        assert order.status == OrderStatus.PENDING
        assert order.received_amount == Decimal("0")
        assert order.outsourced_cost == Decimal("0")
    
    def test_auto_calculate_total(self, manager):
        """测试自动计算订单总金额"""
        order = manager.create_order(
            order_number="ORD002",
            customer_id="CUST001",
            order_date=date(2024, 1, 15),
            product_name="不锈钢拉丝",
            pricing_unit=PricingUnit.METER_LENGTH,
            quantity=Decimal("50.5"),
            unit_price=Decimal("12.80"),
            notes=""
        )
        
        expected_total = Decimal("50.5") * Decimal("12.80")
        assert order.total_amount == expected_total
        assert order.calculate_total() == expected_total
    
    def test_get_order(self, manager):
        """测试获取订单"""
        order = manager.create_order(
            order_number="ORD003",
            customer_id="CUST001",
            order_date=date(2024, 1, 15),
            product_name="测试产品",
            pricing_unit=PricingUnit.UNIT,
            quantity=Decimal("10"),
            unit_price=Decimal("20"),
            notes=""
        )
        
        retrieved_order = manager.get_order(order.id)
        assert retrieved_order is not None
        assert retrieved_order.id == order.id
        assert retrieved_order.order_number == "ORD003"
    
    def test_get_order_by_number(self, manager):
        """测试根据订单编号获取订单"""
        order = manager.create_order(
            order_number="ORD004",
            customer_id="CUST001",
            order_date=date(2024, 1, 15),
            product_name="测试产品",
            pricing_unit=PricingUnit.UNIT,
            quantity=Decimal("10"),
            unit_price=Decimal("20"),
            notes=""
        )
        
        retrieved_order = manager.get_order_by_number("ORD004")
        assert retrieved_order is not None
        assert retrieved_order.id == order.id
    
    def test_query_orders_by_customer(self, manager):
        """测试按客户查询订单"""
        # 创建多个订单
        manager.create_order(
            order_number="ORD005",
            customer_id="CUST001",
            order_date=date(2024, 1, 15),
            product_name="产品A",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("10"),
            unit_price=Decimal("5"),
            notes=""
        )
        manager.create_order(
            order_number="ORD006",
            customer_id="CUST002",
            order_date=date(2024, 1, 16),
            product_name="产品B",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("20"),
            unit_price=Decimal("10"),
            notes=""
        )
        manager.create_order(
            order_number="ORD007",
            customer_id="CUST001",
            order_date=date(2024, 1, 17),
            product_name="产品C",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("15"),
            unit_price=Decimal("8"),
            notes=""
        )
        
        # 查询CUST001的订单
        orders = manager.query_orders(customer_id="CUST001")
        assert len(orders) == 2
        assert all(o.customer_id == "CUST001" for o in orders)
    
    def test_query_orders_by_date_range(self, manager):
        """测试按日期范围查询订单"""
        manager.create_order(
            order_number="ORD008",
            customer_id="CUST001",
            order_date=date(2024, 1, 10),
            product_name="产品A",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("10"),
            unit_price=Decimal("5"),
            notes=""
        )
        manager.create_order(
            order_number="ORD009",
            customer_id="CUST001",
            order_date=date(2024, 1, 20),
            product_name="产品B",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("20"),
            unit_price=Decimal("10"),
            notes=""
        )
        manager.create_order(
            order_number="ORD010",
            customer_id="CUST001",
            order_date=date(2024, 1, 30),
            product_name="产品C",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("15"),
            unit_price=Decimal("8"),
            notes=""
        )
        
        # 查询1月15日到1月25日的订单
        orders = manager.query_orders(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 25)
        )
        assert len(orders) == 1
        assert orders[0].order_number == "ORD009"
    
    def test_query_orders_by_pricing_unit(self, manager):
        """测试按计价单位查询订单"""
        manager.create_order(
            order_number="ORD011",
            customer_id="CUST001",
            order_date=date(2024, 1, 15),
            product_name="产品A",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("10"),
            unit_price=Decimal("5"),
            notes=""
        )
        manager.create_order(
            order_number="ORD012",
            customer_id="CUST001",
            order_date=date(2024, 1, 16),
            product_name="产品B",
            pricing_unit=PricingUnit.METER_LENGTH,
            quantity=Decimal("20"),
            unit_price=Decimal("10"),
            notes=""
        )
        
        # 查询按件计价的订单
        orders = manager.query_orders(pricing_unit=PricingUnit.PIECE)
        assert len(orders) == 1
        assert orders[0].pricing_unit == PricingUnit.PIECE
    
    def test_update_order_status(self, manager):
        """测试更新订单状态"""
        order = manager.create_order(
            order_number="ORD013",
            customer_id="CUST001",
            order_date=date(2024, 1, 15),
            product_name="测试产品",
            pricing_unit=PricingUnit.UNIT,
            quantity=Decimal("10"),
            unit_price=Decimal("20"),
            notes=""
        )
        
        # 更新状态
        success = manager.update_order_status(order.id, OrderStatus.IN_PROGRESS)
        assert success is True
        
        # 验证状态已更新
        updated_order = manager.get_order(order.id)
        assert updated_order.status == OrderStatus.IN_PROGRESS
    
    def test_update_received_amount(self, manager):
        """测试更新已收款金额"""
        order = manager.create_order(
            order_number="ORD014",
            customer_id="CUST001",
            order_date=date(2024, 1, 15),
            product_name="测试产品",
            pricing_unit=PricingUnit.UNIT,
            quantity=Decimal("10"),
            unit_price=Decimal("20"),
            notes=""
        )
        
        # 增加收款
        success = manager.update_received_amount(order.id, Decimal("100"), add=True)
        assert success is True
        
        updated_order = manager.get_order(order.id)
        assert updated_order.received_amount == Decimal("100")
        
        # 再次增加
        manager.update_received_amount(order.id, Decimal("50"), add=True)
        updated_order = manager.get_order(order.id)
        assert updated_order.received_amount == Decimal("150")
    
    def test_update_outsourced_cost(self, manager):
        """测试更新外发加工成本"""
        order = manager.create_order(
            order_number="ORD015",
            customer_id="CUST001",
            order_date=date(2024, 1, 15),
            product_name="测试产品",
            pricing_unit=PricingUnit.UNIT,
            quantity=Decimal("10"),
            unit_price=Decimal("20"),
            notes=""
        )
        
        # 增加成本
        success = manager.update_outsourced_cost(order.id, Decimal("30"), add=True)
        assert success is True
        
        updated_order = manager.get_order(order.id)
        assert updated_order.outsourced_cost == Decimal("30")
    
    def test_get_order_balance(self, manager):
        """测试获取订单未收款余额"""
        order = manager.create_order(
            order_number="ORD016",
            customer_id="CUST001",
            order_date=date(2024, 1, 15),
            product_name="测试产品",
            pricing_unit=PricingUnit.UNIT,
            quantity=Decimal("10"),
            unit_price=Decimal("20"),  # 总金额200
            notes=""
        )
        
        # 收款100
        manager.update_received_amount(order.id, Decimal("100"), add=True)
        
        # 余额应该是100
        balance = manager.get_order_balance(order.id)
        assert balance == Decimal("100")
    
    def test_get_order_profit(self, manager):
        """测试获取订单利润"""
        order = manager.create_order(
            order_number="ORD017",
            customer_id="CUST001",
            order_date=date(2024, 1, 15),
            product_name="测试产品",
            pricing_unit=PricingUnit.UNIT,
            quantity=Decimal("10"),
            unit_price=Decimal("20"),  # 总金额200
            notes=""
        )
        
        # 外发成本50
        manager.update_outsourced_cost(order.id, Decimal("50"), add=True)
        
        # 利润应该是150
        profit = manager.get_order_profit(order.id)
        assert profit == Decimal("150")
    
    def test_get_statistics(self, manager):
        """测试获取订单统计信息"""
        # 创建多个订单
        manager.create_order(
            order_number="ORD018",
            customer_id="CUST001",
            order_date=date(2024, 1, 15),
            product_name="产品A",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("10"),
            unit_price=Decimal("10"),  # 100
            notes=""
        )
        order2 = manager.create_order(
            order_number="ORD019",
            customer_id="CUST001",
            order_date=date(2024, 1, 16),
            product_name="产品B",
            pricing_unit=PricingUnit.METER_LENGTH,
            quantity=Decimal("20"),
            unit_price=Decimal("5"),  # 100
            notes=""
        )
        
        # 更新第二个订单
        manager.update_received_amount(order2.id, Decimal("50"), add=True)
        manager.update_outsourced_cost(order2.id, Decimal("20"), add=True)
        
        # 获取统计
        stats = manager.get_statistics()
        
        assert stats["total_orders"] == 2
        assert Decimal(stats["total_amount"]) == Decimal("200")
        assert Decimal(stats["total_received"]) == Decimal("50")
        assert Decimal(stats["total_outsourced_cost"]) == Decimal("20")
        assert Decimal(stats["total_balance"]) == Decimal("150")
        assert Decimal(stats["total_profit"]) == Decimal("180")


class TestOutsourcedProcessingManager:
    """测试外发加工管理器"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_dir):
        """创建外发加工管理器实例"""
        return OutsourcedProcessingManager(data_dir=temp_dir)
    
    def test_create_processing(self, manager):
        """测试创建外发加工记录"""
        processing = manager.create_processing(
            order_id="ORDER001",
            supplier_id="SUPP001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("0.50"),
            notes="喷砂处理"
        )
        
        assert processing is not None
        assert processing.order_id == "ORDER001"
        assert processing.supplier_id == "SUPP001"
        assert processing.process_type == ProcessType.SANDBLASTING
        assert processing.quantity == Decimal("100")
        assert processing.unit_price == Decimal("0.50")
        assert processing.total_cost == Decimal("50.00")
    
    def test_get_processing_by_order(self, manager):
        """测试获取订单的所有外发加工记录"""
        # 创建多个外发加工记录
        manager.create_processing(
            order_id="ORDER001",
            supplier_id="SUPP001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("0.50"),
            notes=""
        )
        manager.create_processing(
            order_id="ORDER001",
            supplier_id="SUPP002",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("100"),
            unit_price=Decimal("0.80"),
            notes=""
        )
        manager.create_processing(
            order_id="ORDER002",
            supplier_id="SUPP001",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("50"),
            unit_price=Decimal("1.00"),
            notes=""
        )
        
        # 查询ORDER001的外发加工
        processing_list = manager.get_processing_by_order("ORDER001")
        assert len(processing_list) == 2
        assert all(p.order_id == "ORDER001" for p in processing_list)
    
    def test_query_processing_by_process_type(self, manager):
        """测试按工序类型查询外发加工"""
        manager.create_processing(
            order_id="ORDER001",
            supplier_id="SUPP001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("0.50"),
            notes=""
        )
        manager.create_processing(
            order_id="ORDER002",
            supplier_id="SUPP001",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("100"),
            unit_price=Decimal("0.80"),
            notes=""
        )
        
        # 查询喷砂工序
        processing_list = manager.query_processing(process_type=ProcessType.SANDBLASTING)
        assert len(processing_list) == 1
        assert processing_list[0].process_type == ProcessType.SANDBLASTING
    
    def test_get_order_total_cost(self, manager):
        """测试获取订单的外发加工总成本"""
        manager.create_processing(
            order_id="ORDER001",
            supplier_id="SUPP001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("0.50"),  # 50
            notes=""
        )
        manager.create_processing(
            order_id="ORDER001",
            supplier_id="SUPP002",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("100"),
            unit_price=Decimal("0.80"),  # 80
            notes=""
        )
        
        total_cost = manager.get_order_total_cost("ORDER001")
        assert total_cost == Decimal("130")
    
    def test_get_statistics_by_process_type(self, manager):
        """测试按工序类型统计"""
        manager.create_processing(
            order_id="ORDER001",
            supplier_id="SUPP001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("0.50"),
            notes=""
        )
        manager.create_processing(
            order_id="ORDER002",
            supplier_id="SUPP001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("200"),
            unit_price=Decimal("0.60"),
            notes=""
        )
        manager.create_processing(
            order_id="ORDER003",
            supplier_id="SUPP002",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("150"),
            unit_price=Decimal("0.80"),
            notes=""
        )
        
        stats = manager.get_statistics_by_process_type()
        
        # 喷砂统计
        sandblasting_stats = stats["sandblasting"]
        assert sandblasting_stats["count"] == 2
        assert Decimal(sandblasting_stats["total_cost"]) == Decimal("170")  # 50 + 120
        
        # 抛光统计
        polishing_stats = stats["polishing"]
        assert polishing_stats["count"] == 1
        assert Decimal(polishing_stats["total_cost"]) == Decimal("120")
    
    def test_get_statistics_by_supplier(self, manager):
        """测试按供应商统计"""
        manager.create_processing(
            order_id="ORDER001",
            supplier_id="SUPP001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 15),
            quantity=Decimal("100"),
            unit_price=Decimal("0.50"),
            notes=""
        )
        manager.create_processing(
            order_id="ORDER002",
            supplier_id="SUPP001",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("100"),
            unit_price=Decimal("0.80"),
            notes=""
        )
        manager.create_processing(
            order_id="ORDER003",
            supplier_id="SUPP002",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("50"),
            unit_price=Decimal("1.00"),
            notes=""
        )
        
        stats = manager.get_statistics_by_supplier()
        
        # SUPP001统计
        supp001_stats = stats["SUPP001"]
        assert supp001_stats["total_records"] == 2
        assert Decimal(supp001_stats["total_cost"]) == Decimal("130")  # 50 + 80
        
        # SUPP002统计
        supp002_stats = stats["SUPP002"]
        assert supp002_stats["total_records"] == 1
        assert Decimal(supp002_stats["total_cost"]) == Decimal("50")


class TestIndustryClassifier:
    """测试行业费用分类器"""
    
    @pytest.fixture
    def classifier(self):
        """创建分类器实例"""
        return IndustryClassifier()
    
    def test_classify_raw_materials(self, classifier):
        """测试原材料分类"""
        # 测试三酸
        code, name, confidence = classifier.classify_expense("购买三酸", "化工原料公司")
        assert code == "raw_materials"
        assert name == "原材料"
        assert confidence >= 0.7
        
        # 测试片碱
        code, name, confidence = classifier.classify_expense("片碱采购", "化学品供应商")
        assert code == "raw_materials"
        assert confidence >= 0.7
        
        # 测试色粉
        code, name, confidence = classifier.classify_expense("色粉", "染料供应商")
        assert code == "raw_materials"
        assert confidence >= 0.7
    
    def test_classify_outsourced_processing(self, classifier):
        """测试外发加工分类"""
        # 测试喷砂
        code, name, confidence = classifier.classify_expense("喷砂加工费", "A喷砂厂")
        assert code == "outsourced_processing"
        assert name == "外发加工费"
        assert confidence >= 0.7
        
        # 测试拉丝
        code, name, confidence = classifier.classify_expense("拉丝处理", "C拉丝加工")
        assert code == "outsourced_processing"
        assert confidence >= 0.7
        
        # 测试抛光
        code, name, confidence = classifier.classify_expense("抛光费用", "E抛光厂")
        assert code == "outsourced_processing"
        assert confidence >= 0.7
    
    def test_classify_fixtures(self, classifier):
        """测试挂具分类"""
        code, name, confidence = classifier.classify_expense("购买挂具", "五金工具店")
        assert code == "fixtures"
        assert name == "挂具"
        assert confidence >= 0.7
    
    def test_classify_rent(self, classifier):
        """测试房租分类"""
        code, name, confidence = classifier.classify_expense("厂房租金", "房东")
        assert code == "rent"
        assert name == "房租"
        assert confidence >= 0.9
    
    def test_classify_utilities(self, classifier):
        """测试水电费分类"""
        # 测试电费
        code, name, confidence = classifier.classify_expense("电费", "供电局")
        assert code == "utilities"
        assert name == "水电费"
        assert confidence >= 0.7
        
        # 测试水费
        code, name, confidence = classifier.classify_expense("水费", "自来水公司")
        assert code == "utilities"
        assert confidence >= 0.7
    
    def test_classify_salary(self, classifier):
        """测试工资分类"""
        code, name, confidence = classifier.classify_expense("员工工资", "")
        assert code == "salary"
        assert name == "工资"
        assert confidence >= 0.7
    
    def test_classify_daily_expenses(self, classifier):
        """测试日常费用分类"""
        code, name, confidence = classifier.classify_expense("办公用品", "文具店")
        assert code == "daily_expenses"
        assert name == "日常费用"
        assert confidence >= 0.7
    
    def test_classify_processing_income(self, classifier):
        """测试加工费收入分类"""
        code, name, confidence = classifier.classify_income("加工费收入", "客户A")
        assert code == "processing_income"
        assert name == "加工费收入"
        assert confidence >= 0.7
    
    def test_classify_transaction(self, classifier):
        """测试分类交易"""
        result = classifier.classify_transaction(
            transaction_type="expense",
            description="购买三酸",
            counterparty="化工原料公司"
        )
        
        assert result["category_code"] == "raw_materials"
        assert result["category_name"] == "原材料"
        assert result["confidence"] >= 0.7
        assert result["is_low_confidence"] is False
    
    def test_low_confidence_detection(self, classifier):
        """测试低置信度检测"""
        result = classifier.classify_transaction(
            transaction_type="expense",
            description="未知费用",
            counterparty="某公司"
        )
        
        assert result["is_low_confidence"] is True
        assert result["confidence"] < 0.7
    
    def test_batch_classify(self, classifier):
        """测试批量分类"""
        transactions = [
            {"type": "expense", "description": "购买三酸", "counterparty": "化工公司"},
            {"type": "expense", "description": "喷砂加工", "counterparty": "喷砂厂"},
            {"type": "income", "description": "加工费", "counterparty": "客户A"}
        ]
        
        results = classifier.batch_classify(transactions)
        
        assert len(results) == 3
        assert results[0]["category_code"] == "raw_materials"
        assert results[1]["category_code"] == "outsourced_processing"
        assert results[2]["category_code"] == "processing_income"
    
    def test_get_low_confidence_items(self, classifier):
        """测试获取低置信度项"""
        transactions = [
            {"type": "expense", "description": "购买三酸", "counterparty": "化工公司"},
            {"type": "expense", "description": "未知费用", "counterparty": "某公司"}
        ]
        
        results = classifier.batch_classify(transactions)
        low_confidence = classifier.get_low_confidence_items(results)
        
        assert len(low_confidence) >= 1
        assert all(item["is_low_confidence"] for item in low_confidence)
    
    def test_get_all_categories(self, classifier):
        """测试获取所有分类"""
        expense_categories = classifier.get_all_categories("expense")
        income_categories = classifier.get_all_categories("income")
        
        assert len(expense_categories) > 0
        assert len(income_categories) > 0
        
        # 验证包含预期的分类
        expense_codes = [c["code"] for c in expense_categories]
        assert "raw_materials" in expense_codes
        assert "outsourced_processing" in expense_codes
        assert "fixtures" in expense_codes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
