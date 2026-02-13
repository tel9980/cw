"""
Unit tests for extended data models in V1.7

Tests the oxidation factory specific models:
- ProcessingOrder
- OutsourcedProcessing
- BankAccount
- ReconciliationMatch
- Extended TransactionRecord and Counterparty
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from oxidation_complete_v17.models.core_models import (
    ProcessingOrder,
    OutsourcedProcessing,
    BankAccount,
    ReconciliationMatch,
    TransactionRecord,
    Counterparty,
    PricingUnit,
    ProcessType,
    OrderStatus,
    AccountType,
    TransactionType,
    TransactionStatus,
    CounterpartyType,
)


class TestProcessingOrder:
    """测试加工订单模型"""
    
    def test_create_processing_order(self):
        """测试创建加工订单"""
        order = ProcessingOrder(
            id="PO001",
            order_number="2024-001",
            customer_id="C001",
            order_date=date(2024, 1, 15),
            product_name="铝型材氧化",
            pricing_unit=PricingUnit.METER_LENGTH,
            quantity=Decimal("100.5"),
            unit_price=Decimal("15.00"),
            total_amount=Decimal("1507.50"),
            status=OrderStatus.IN_PROGRESS,
            received_amount=Decimal("500.00"),
            outsourced_cost=Decimal("200.00"),
            notes="客户要求黑色氧化",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        assert order.id == "PO001"
        assert order.pricing_unit == PricingUnit.METER_LENGTH
        assert order.quantity == Decimal("100.5")
        assert order.unit_price == Decimal("15.00")
    
    def test_calculate_total(self):
        """测试计算订单总金额"""
        order = ProcessingOrder(
            id="PO002",
            order_number="2024-002",
            customer_id="C001",
            order_date=date(2024, 1, 15),
            product_name="铝板氧化",
            pricing_unit=PricingUnit.SQUARE_METER,
            quantity=Decimal("50"),
            unit_price=Decimal("20.00"),
            total_amount=Decimal("1000.00"),
            status=OrderStatus.PENDING,
            received_amount=Decimal("0"),
            outsourced_cost=Decimal("0"),
            notes="",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        calculated_total = order.calculate_total()
        assert calculated_total == Decimal("1000.00")
        assert calculated_total == order.total_amount
    
    def test_get_balance(self):
        """测试获取未收款余额"""
        order = ProcessingOrder(
            id="PO003",
            order_number="2024-003",
            customer_id="C001",
            order_date=date(2024, 1, 15),
            product_name="铝管氧化",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("1000"),
            unit_price=Decimal("2.50"),
            total_amount=Decimal("2500.00"),
            status=OrderStatus.IN_PROGRESS,
            received_amount=Decimal("1000.00"),
            outsourced_cost=Decimal("300.00"),
            notes="",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        balance = order.get_balance()
        assert balance == Decimal("1500.00")  # 2500 - 1000
    
    def test_get_profit(self):
        """测试获取订单利润"""
        order = ProcessingOrder(
            id="PO004",
            order_number="2024-004",
            customer_id="C001",
            order_date=date(2024, 1, 15),
            product_name="铝条氧化",
            pricing_unit=PricingUnit.STRIP,
            quantity=Decimal("500"),
            unit_price=Decimal("5.00"),
            total_amount=Decimal("2500.00"),
            status=OrderStatus.COMPLETED,
            received_amount=Decimal("2500.00"),
            outsourced_cost=Decimal("800.00"),
            notes="包含喷砂和拉丝",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        profit = order.get_profit()
        assert profit == Decimal("1700.00")  # 2500 - 800
    
    def test_order_to_dict_and_from_dict(self):
        """测试订单序列化和反序列化"""
        original_order = ProcessingOrder(
            id="PO005",
            order_number="2024-005",
            customer_id="C002",
            order_date=date(2024, 1, 20),
            product_name="铝件氧化",
            pricing_unit=PricingUnit.ITEM,
            quantity=Decimal("200"),
            unit_price=Decimal("3.50"),
            total_amount=Decimal("700.00"),
            status=OrderStatus.PENDING,
            received_amount=Decimal("0"),
            outsourced_cost=Decimal("0"),
            notes="急单",
            created_at=datetime(2024, 1, 20, 10, 0, 0),
            updated_at=datetime(2024, 1, 20, 10, 0, 0),
        )
        
        # 序列化
        order_dict = original_order.to_dict()
        
        # 反序列化
        restored_order = ProcessingOrder.from_dict(order_dict)
        
        # 验证
        assert restored_order.id == original_order.id
        assert restored_order.order_number == original_order.order_number
        assert restored_order.pricing_unit == original_order.pricing_unit
        assert restored_order.quantity == original_order.quantity
        assert restored_order.total_amount == original_order.total_amount


class TestOutsourcedProcessing:
    """测试外发加工模型"""
    
    def test_create_outsourced_processing(self):
        """测试创建外发加工记录"""
        processing = OutsourcedProcessing(
            id="OP001",
            order_id="PO001",
            supplier_id="S001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("100"),
            unit_price=Decimal("1.50"),
            total_cost=Decimal("150.00"),
            notes="喷砂处理",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        assert processing.id == "OP001"
        assert processing.process_type == ProcessType.SANDBLASTING
        assert processing.quantity == Decimal("100")
    
    def test_calculate_total_cost(self):
        """测试计算外发加工总成本"""
        processing = OutsourcedProcessing(
            id="OP002",
            order_id="PO002",
            supplier_id="S002",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("50"),
            unit_price=Decimal("2.00"),
            total_cost=Decimal("100.00"),
            notes="拉丝处理",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        calculated_cost = processing.calculate_total()
        assert calculated_cost == Decimal("100.00")
        assert calculated_cost == processing.total_cost
    
    def test_processing_to_dict_and_from_dict(self):
        """测试外发加工序列化和反序列化"""
        original_processing = OutsourcedProcessing(
            id="OP003",
            order_id="PO003",
            supplier_id="S003",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 18),
            quantity=Decimal("75"),
            unit_price=Decimal("3.00"),
            total_cost=Decimal("225.00"),
            notes="抛光处理",
            created_at=datetime(2024, 1, 18, 14, 0, 0),
            updated_at=datetime(2024, 1, 18, 14, 0, 0),
        )
        
        # 序列化
        processing_dict = original_processing.to_dict()
        
        # 反序列化
        restored_processing = OutsourcedProcessing.from_dict(processing_dict)
        
        # 验证
        assert restored_processing.id == original_processing.id
        assert restored_processing.process_type == original_processing.process_type
        assert restored_processing.total_cost == original_processing.total_cost


class TestBankAccount:
    """测试银行账户模型"""
    
    def test_create_business_account_with_invoice(self):
        """测试创建有票据的对公账户"""
        account = BankAccount(
            id="BA001",
            name="G银行",
            account_number="1234567890",
            account_type=AccountType.BUSINESS,
            has_invoice=True,
            balance=Decimal("50000.00"),
            description="对公账户,有票据",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        assert account.name == "G银行"
        assert account.account_type == AccountType.BUSINESS
        assert account.has_invoice is True
    
    def test_create_cash_account_without_invoice(self):
        """测试创建无票据的现金账户"""
        account = BankAccount(
            id="BA002",
            name="N银行",
            account_number="9876543210",
            account_type=AccountType.CASH,
            has_invoice=False,
            balance=Decimal("10000.00"),
            description="现金账户,无票据",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        assert account.name == "N银行"
        assert account.account_type == AccountType.CASH
        assert account.has_invoice is False
    
    def test_account_to_dict_and_from_dict(self):
        """测试银行账户序列化和反序列化"""
        original_account = BankAccount(
            id="BA003",
            name="微信",
            account_number="WX123456",
            account_type=AccountType.CASH,
            has_invoice=False,
            balance=Decimal("5000.00"),
            description="微信支付账户",
            created_at=datetime(2024, 1, 1, 0, 0, 0),
            updated_at=datetime(2024, 1, 1, 0, 0, 0),
        )
        
        # 序列化
        account_dict = original_account.to_dict()
        
        # 反序列化
        restored_account = BankAccount.from_dict(account_dict)
        
        # 验证
        assert restored_account.id == original_account.id
        assert restored_account.account_type == original_account.account_type
        assert restored_account.has_invoice == original_account.has_invoice


class TestReconciliationMatch:
    """测试对账匹配模型"""
    
    def test_one_to_many_match(self):
        """测试一对多匹配（一笔银行流水对多个订单）"""
        match = ReconciliationMatch(
            id="RM001",
            match_date=datetime.now(),
            bank_record_ids=["BR001"],
            order_ids=["PO001", "PO002", "PO003"],
            total_bank_amount=Decimal("5000.00"),
            total_order_amount=Decimal("5000.00"),
            difference=Decimal("0"),
            notes="客户合并付款",
            created_by="admin",
            created_at=datetime.now(),
        )
        
        assert match.is_one_to_many() is True
        assert match.is_many_to_one() is False
        assert len(match.bank_record_ids) == 1
        assert len(match.order_ids) == 3
    
    def test_many_to_one_match(self):
        """测试多对一匹配（多笔银行流水对一个订单）"""
        match = ReconciliationMatch(
            id="RM002",
            match_date=datetime.now(),
            bank_record_ids=["BR001", "BR002", "BR003"],
            order_ids=["PO001"],
            total_bank_amount=Decimal("3000.00"),
            total_order_amount=Decimal("3000.00"),
            difference=Decimal("0"),
            notes="客户分批付款",
            created_by="admin",
            created_at=datetime.now(),
        )
        
        assert match.is_one_to_many() is False
        assert match.is_many_to_one() is True
        assert len(match.bank_record_ids) == 3
        assert len(match.order_ids) == 1
    
    def test_match_with_difference(self):
        """测试有差额的对账匹配"""
        match = ReconciliationMatch(
            id="RM003",
            match_date=datetime.now(),
            bank_record_ids=["BR001"],
            order_ids=["PO001"],
            total_bank_amount=Decimal("1000.00"),
            total_order_amount=Decimal("1005.00"),
            difference=Decimal("5.00"),
            notes="有5元差额",
            created_by="admin",
            created_at=datetime.now(),
        )
        
        assert match.difference == Decimal("5.00")
        assert match.total_bank_amount < match.total_order_amount
    
    def test_match_to_dict_and_from_dict(self):
        """测试对账匹配序列化和反序列化"""
        original_match = ReconciliationMatch(
            id="RM004",
            match_date=datetime(2024, 1, 20, 15, 30, 0),
            bank_record_ids=["BR001", "BR002"],
            order_ids=["PO001", "PO002"],
            total_bank_amount=Decimal("2500.00"),
            total_order_amount=Decimal("2500.00"),
            difference=Decimal("0"),
            notes="完全匹配",
            created_by="admin",
            created_at=datetime(2024, 1, 20, 15, 30, 0),
        )
        
        # 序列化
        match_dict = original_match.to_dict()
        
        # 反序列化
        restored_match = ReconciliationMatch.from_dict(match_dict)
        
        # 验证
        assert restored_match.id == original_match.id
        assert restored_match.bank_record_ids == original_match.bank_record_ids
        assert restored_match.order_ids == original_match.order_ids
        assert restored_match.difference == original_match.difference


class TestExtendedTransactionRecord:
    """测试扩展的交易记录模型"""
    
    def test_transaction_with_pricing_unit(self):
        """测试带计价单位的交易记录"""
        transaction = TransactionRecord(
            id="TR001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("1500.00"),
            counterparty_id="C001",
            description="铝型材氧化加工费",
            category="加工费收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            pricing_unit=PricingUnit.METER_LENGTH,
            quantity=Decimal("100"),
            unit_price=Decimal("15.00"),
            bank_account_id="BA001",
        )
        
        assert transaction.pricing_unit == PricingUnit.METER_LENGTH
        assert transaction.quantity == Decimal("100")
        assert transaction.unit_price == Decimal("15.00")
        assert transaction.bank_account_id == "BA001"
    
    def test_transaction_to_dict_with_extensions(self):
        """测试扩展字段的序列化"""
        transaction = TransactionRecord(
            id="TR002",
            date=date(2024, 1, 16),
            type=TransactionType.EXPENSE,
            amount=Decimal("500.00"),
            counterparty_id="S001",
            description="喷砂加工费",
            category="外发加工费",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("200"),
            unit_price=Decimal("2.50"),
            bank_account_id="BA002",
        )
        
        transaction_dict = transaction.to_dict()
        
        assert transaction_dict["pricing_unit"] == "piece"
        assert transaction_dict["quantity"] == "200"
        assert transaction_dict["unit_price"] == "2.50"
        assert transaction_dict["bank_account_id"] == "BA002"


class TestExtendedCounterparty:
    """测试扩展的往来单位模型"""
    
    def test_counterparty_with_aliases(self):
        """测试带别名的往来单位"""
        counterparty = Counterparty(
            id="C001",
            name="深圳市XX铝业有限公司",
            type=CounterpartyType.CUSTOMER,
            contact_person="张三",
            phone="13800138000",
            email="zhangsan@example.com",
            address="深圳市南山区",
            tax_id="91440300XXXXXXXXXX",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            aliases=["XX铝业", "深圳XX", "XX公司"],
        )
        
        assert len(counterparty.aliases) == 3
        assert "XX铝业" in counterparty.aliases
        assert "深圳XX" in counterparty.aliases
    
    def test_counterparty_to_dict_with_aliases(self):
        """测试别名的序列化"""
        counterparty = Counterparty(
            id="S001",
            name="东莞市YY表面处理厂",
            type=CounterpartyType.SUPPLIER,
            contact_person="李四",
            phone="13900139000",
            email="lisi@example.com",
            address="东莞市长安镇",
            tax_id="91441900XXXXXXXXXX",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            aliases=["YY表面处理", "东莞YY", "YY厂"],
        )
        
        counterparty_dict = counterparty.to_dict()
        
        assert "aliases" in counterparty_dict
        assert len(counterparty_dict["aliases"]) == 3
        assert "YY表面处理" in counterparty_dict["aliases"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
