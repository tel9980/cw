"""
Unit tests for Industry Report Generator

Tests the generation of industry-specific reports:
- Processing income detail report
- Outsourced processing cost report
- Raw material consumption report
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
import os
import tempfile
import shutil
from pathlib import Path

from oxidation_complete_v17.models.core_models import (
    ProcessingOrder, OutsourcedProcessing, TransactionRecord,
    PricingUnit, ProcessType, OrderStatus, TransactionType,
    TransactionStatus, Counterparty, CounterpartyType
)
from oxidation_complete_v17.industry.processing_order_manager import ProcessingOrderManager
from oxidation_complete_v17.industry.outsourced_processing_manager import OutsourcedProcessingManager
from oxidation_complete_v17.storage.transaction_storage import TransactionStorage
from oxidation_complete_v17.storage.counterparty_storage import CounterpartyStorage
from oxidation_complete_v17.reports.industry_report_generator import IndustryReportGenerator


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def data_dir(temp_dir):
    """创建数据目录"""
    data_path = os.path.join(temp_dir, "data")
    os.makedirs(data_path, exist_ok=True)
    return data_path


@pytest.fixture
def output_dir(temp_dir):
    """创建报表输出目录"""
    output_path = os.path.join(temp_dir, "reports")
    os.makedirs(output_path, exist_ok=True)
    return output_path


@pytest.fixture
def counterparty_storage(data_dir):
    """创建往来单位存储"""
    return CounterpartyStorage(data_dir)


@pytest.fixture
def transaction_storage(data_dir):
    """创建交易记录存储"""
    return TransactionStorage(data_dir)


@pytest.fixture
def order_manager(data_dir):
    """创建订单管理器"""
    return ProcessingOrderManager(data_dir)


@pytest.fixture
def outsourced_manager(data_dir):
    """创建外发加工管理器"""
    return OutsourcedProcessingManager(data_dir)


@pytest.fixture
def report_generator(order_manager, outsourced_manager, transaction_storage, 
                     counterparty_storage, output_dir):
    """创建报表生成器"""
    return IndustryReportGenerator(
        order_manager=order_manager,
        outsourced_manager=outsourced_manager,
        transaction_storage=transaction_storage,
        counterparty_storage=counterparty_storage,
        output_dir=output_dir
    )


@pytest.fixture
def sample_customer(counterparty_storage):
    """创建示例客户"""
    customer = Counterparty(
        id="customer_001",
        name="优质客户有限公司",
        type=CounterpartyType.CUSTOMER,
        contact_person="张经理",
        phone="13800138000",
        email="zhang@customer.com",
        address="上海市浦东新区",
        tax_id="91310000MA1234567X",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        aliases=["优质客户", "优质公司"]
    )
    counterparty_storage.add(customer)
    return customer


@pytest.fixture
def sample_supplier(counterparty_storage):
    """创建示例供应商"""
    supplier = Counterparty(
        id="supplier_001",
        name="专业喷砂加工厂",
        type=CounterpartyType.SUPPLIER,
        contact_person="李师傅",
        phone="13900139000",
        email="li@supplier.com",
        address="江苏省苏州市",
        tax_id="91320000MA7654321Y",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        aliases=["喷砂厂"]
    )
    counterparty_storage.add(supplier)
    return supplier


@pytest.fixture
def sample_orders(order_manager, sample_customer):
    """创建示例订单"""
    orders = []
    
    # 订单1: 按件计价
    order1 = order_manager.create_order(
        order_number="PO202601001",
        customer_id=sample_customer.id,
        order_date=date(2026, 1, 15),
        product_name="铝型材氧化",
        pricing_unit=PricingUnit.PIECE,
        quantity=Decimal("1000"),
        unit_price=Decimal("5.50"),
        notes="常规订单"
    )
    order_manager.update_received_amount(order1.id, Decimal("3000"), add=False)
    order_manager.update_outsourced_cost(order1.id, Decimal("800"), add=False)
    orders.append(order1)
    
    # 订单2: 按米长计价
    order2 = order_manager.create_order(
        order_number="PO202601002",
        customer_id=sample_customer.id,
        order_date=date(2026, 1, 20),
        product_name="铝管氧化",
        pricing_unit=PricingUnit.METER_LENGTH,
        quantity=Decimal("500"),
        unit_price=Decimal("12.00"),
        notes="加急订单"
    )
    order_manager.update_received_amount(order2.id, Decimal("6000"), add=False)
    order_manager.update_outsourced_cost(order2.id, Decimal("1200"), add=False)
    orders.append(order2)
    
    # 订单3: 按平方计价
    order3 = order_manager.create_order(
        order_number="PO202602001",
        customer_id=sample_customer.id,
        order_date=date(2026, 2, 5),
        product_name="铝板氧化",
        pricing_unit=PricingUnit.SQUARE_METER,
        quantity=Decimal("200"),
        unit_price=Decimal("25.00"),
        notes="大面积订单"
    )
    order_manager.update_received_amount(order3.id, Decimal("2500"), add=False)
    order_manager.update_outsourced_cost(order3.id, Decimal("600"), add=False)
    orders.append(order3)
    
    return orders


@pytest.fixture
def sample_outsourced(outsourced_manager, sample_orders, sample_supplier):
    """创建示例外发加工记录"""
    outsourced_list = []
    
    # 外发1: 喷砂
    op1 = outsourced_manager.create_processing(
        order_id=sample_orders[0].id,
        supplier_id=sample_supplier.id,
        process_type=ProcessType.SANDBLASTING,
        process_date=date(2026, 1, 16),
        quantity=Decimal("1000"),
        unit_price=Decimal("0.50"),
        notes="喷砂处理"
    )
    outsourced_list.append(op1)
    
    # 外发2: 拉丝
    op2 = outsourced_manager.create_processing(
        order_id=sample_orders[1].id,
        supplier_id=sample_supplier.id,
        process_type=ProcessType.WIRE_DRAWING,
        process_date=date(2026, 1, 21),
        quantity=Decimal("500"),
        unit_price=Decimal("1.50"),
        notes="拉丝处理"
    )
    outsourced_list.append(op2)
    
    # 外发3: 抛光
    op3 = outsourced_manager.create_processing(
        order_id=sample_orders[2].id,
        supplier_id=sample_supplier.id,
        process_type=ProcessType.POLISHING,
        process_date=date(2026, 2, 6),
        quantity=Decimal("200"),
        unit_price=Decimal("2.00"),
        notes="抛光处理"
    )
    outsourced_list.append(op3)
    
    return outsourced_list


@pytest.fixture
def sample_materials(transaction_storage, sample_supplier):
    """创建示例原材料交易"""
    materials = []
    
    # 三酸采购
    trans1 = TransactionRecord(
        id="trans_001",
        date=date(2026, 1, 10),
        type=TransactionType.EXPENSE,
        amount=Decimal("3000"),
        counterparty_id=sample_supplier.id,
        description="采购三酸（硫酸、硝酸、盐酸）",
        category="原材料-三酸",
        status=TransactionStatus.COMPLETED,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    transaction_storage.add(trans1)
    materials.append(trans1)
    
    # 片碱采购
    trans2 = TransactionRecord(
        id="trans_002",
        date=date(2026, 1, 15),
        type=TransactionType.EXPENSE,
        amount=Decimal("1500"),
        counterparty_id=sample_supplier.id,
        description="采购片碱（氢氧化钠）",
        category="原材料-片碱",
        status=TransactionStatus.COMPLETED,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    transaction_storage.add(trans2)
    materials.append(trans2)
    
    # 色粉采购
    trans3 = TransactionRecord(
        id="trans_003",
        date=date(2026, 2, 1),
        type=TransactionType.EXPENSE,
        amount=Decimal("800"),
        counterparty_id=sample_supplier.id,
        description="采购色粉（染料）",
        category="原材料-色粉",
        status=TransactionStatus.COMPLETED,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    transaction_storage.add(trans3)
    materials.append(trans3)
    
    return materials


class TestIndustryReportGenerator:
    """测试行业报表生成器"""
    
    def test_initialization(self, report_generator, output_dir):
        """测试初始化"""
        assert report_generator is not None
        assert report_generator.output_dir == Path(output_dir)
        assert os.path.exists(output_dir)
    
    def test_generate_processing_income_report(
        self, report_generator, sample_orders, sample_customer
    ):
        """测试生成加工费收入明细表"""
        # 生成报表
        output_file = report_generator.generate_processing_income_report(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 28),
            group_by="all"
        )
        
        # 验证文件生成
        assert output_file != ""
        assert os.path.exists(output_file)
        assert output_file.endswith(".xlsx")
        
        # 验证文件名格式
        assert "加工费收入明细表" in output_file
        assert "20260101" in output_file
        assert "20260228" in output_file
    
    def test_generate_processing_income_report_by_customer(
        self, report_generator, sample_orders
    ):
        """测试按客户分组的加工费收入明细表"""
        output_file = report_generator.generate_processing_income_report(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 28),
            group_by="customer"
        )
        
        assert output_file != ""
        assert os.path.exists(output_file)
    
    def test_generate_processing_income_report_by_pricing_unit(
        self, report_generator, sample_orders
    ):
        """测试按计价单位分组的加工费收入明细表"""
        output_file = report_generator.generate_processing_income_report(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 28),
            group_by="pricing_unit"
        )
        
        assert output_file != ""
        assert os.path.exists(output_file)
    
    def test_generate_processing_income_report_by_month(
        self, report_generator, sample_orders
    ):
        """测试按月份分组的加工费收入明细表"""
        output_file = report_generator.generate_processing_income_report(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 28),
            group_by="month"
        )
        
        assert output_file != ""
        assert os.path.exists(output_file)
    
    def test_generate_processing_income_report_no_data(self, report_generator):
        """测试无数据时的加工费收入明细表"""
        output_file = report_generator.generate_processing_income_report(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            group_by="all"
        )
        
        # 无数据时返回空字符串
        assert output_file == ""
    
    def test_generate_outsourced_cost_report(
        self, report_generator, sample_outsourced, sample_supplier
    ):
        """测试生成外发加工成本统计表"""
        output_file = report_generator.generate_outsourced_cost_report(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 28)
        )
        
        # 验证文件生成
        assert output_file != ""
        assert os.path.exists(output_file)
        assert output_file.endswith(".xlsx")
        
        # 验证文件名格式
        assert "外发加工成本统计表" in output_file
        assert "20260101" in output_file
        assert "20260228" in output_file
    
    def test_generate_outsourced_cost_report_no_data(self, report_generator):
        """测试无数据时的外发加工成本统计表"""
        output_file = report_generator.generate_outsourced_cost_report(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31)
        )
        
        # 无数据时返回空字符串
        assert output_file == ""
    
    def test_generate_raw_material_report(
        self, report_generator, sample_materials, sample_supplier
    ):
        """测试生成原材料消耗统计表"""
        output_file = report_generator.generate_raw_material_report(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 28)
        )
        
        # 验证文件生成
        assert output_file != ""
        assert os.path.exists(output_file)
        assert output_file.endswith(".xlsx")
        
        # 验证文件名格式
        assert "原材料消耗统计表" in output_file
        assert "20260101" in output_file
        assert "20260228" in output_file
    
    def test_generate_raw_material_report_no_data(self, report_generator):
        """测试无数据时的原材料消耗统计表"""
        output_file = report_generator.generate_raw_material_report(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31)
        )
        
        # 无数据时返回空字符串
        assert output_file == ""
    
    def test_generate_all_industry_reports(
        self, report_generator, sample_orders, sample_outsourced, sample_materials
    ):
        """测试生成所有行业报表"""
        results = report_generator.generate_all_industry_reports(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 28)
        )
        
        # 验证返回结果
        assert isinstance(results, dict)
        assert len(results) == 3
        
        # 验证报表名称
        assert "加工费收入明细表" in results
        assert "外发加工成本统计表" in results
        assert "原材料消耗统计表" in results
        
        # 验证所有文件都存在
        for report_name, file_path in results.items():
            assert os.path.exists(file_path)
            assert file_path.endswith(".xlsx")
    
    def test_generate_all_industry_reports_partial_data(
        self, report_generator, sample_orders
    ):
        """测试部分数据时生成所有行业报表"""
        results = report_generator.generate_all_industry_reports(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 28)
        )
        
        # 至少应该有加工费收入明细表
        assert "加工费收入明细表" in results
        assert os.path.exists(results["加工费收入明细表"])
    
    def test_status_name_mapping(self, report_generator):
        """测试订单状态中文名称映射"""
        assert report_generator._get_status_name(OrderStatus.PENDING) == "待处理"
        assert report_generator._get_status_name(OrderStatus.IN_PROGRESS) == "进行中"
        assert report_generator._get_status_name(OrderStatus.COMPLETED) == "已完成"
        assert report_generator._get_status_name(OrderStatus.CANCELLED) == "已取消"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
