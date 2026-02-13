"""
Unit tests for core data models

Tests the basic functionality of ProcessingOrder, OutsourcedProcessing,
BankAccount, ReconciliationMatch, and related models.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from oxidation_workflow_v18.models.core_models import (
    ProcessingOrder,
    OutsourcedProcessing,
    BankAccount,
    ReconciliationMatch,
    TransactionRecord,
    Counterparty,
    BankRecord,
    PricingUnit,
    ProcessType,
    OrderStatus,
    AccountType,
    TransactionType,
    TransactionStatus,
    CounterpartyType,
)


class TestPricingUnit:
    """测试计价单位枚举"""
    
    def test_all_pricing_units_exist(self):
        """验证所有计价单位枚举值存在 - Requirements 1.1, 1.2, 1.3, 1.4"""
        # 验证所有7种计价单位
        assert PricingUnit.PIECE.value == "piece"  # 件
        assert PricingUnit.STRIP.value == "strip"  # 条
        assert PricingUnit.ITEM.value == "item"  # 只
        assert PricingUnit.UNIT.value == "unit"  # 个
        assert PricingUnit.METER_LENGTH.value == "meter_length"  # 米长
        assert PricingUnit.METER_WEIGHT.value == "meter_weight"  # 米重
        assert PricingUnit.SQUARE_METER.value == "square_meter"  # 平方
    
    def test_pricing_unit_count(self):
        """验证计价单位数量正确"""
        assert len(PricingUnit) == 7


class TestProcessingOrder:
    """测试加工订单模型"""
    
    def test_create_order_with_piece_unit(self):
        """测试创建按件计价的订单 - Requirement 1.1"""
        order = ProcessingOrder(
            id="order_001",
            order_number="ORD-2024-001",
            customer_id="cust_001",
            order_date=date(2024, 1, 15),
            product_name="铝型材氧化",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("100"),
            unit_price=Decimal("5.50"),
            total_amount=Decimal("550.00"),
            status=OrderStatus.PENDING,
            received_amount=Decimal("0"),
            outsourced_cost=Decimal("0"),
            notes="测试订单",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        assert order.pricing_unit == PricingUnit.PIECE
        assert order.quantity == Decimal("100")
        assert order.unit_price == Decimal("5.50")
        assert order.total_amount == Decimal("550.00")
    
    def test_create_order_with_meter_length_unit(self):
        """测试创建按米长计价的订单 - Requirement 1.2"""
        order = ProcessingOrder(
            id="order_002",
            order_number="ORD-2024-002",
            customer_id="cust_001",
            order_date=date(2024, 1, 15),
            product_name="长条型材",
            pricing_unit=PricingUnit.METER_LENGTH,
            quantity=Decimal("50.5"),
            unit_price=Decimal("12.00"),
            total_amount=Decimal("606.00"),
            status=OrderStatus.PENDING,
            received_amount=Decimal("0"),
            outsourced_cost=Decimal("0"),
            notes="",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        assert order.pricing_unit == PricingUnit.METER_LENGTH
        assert order.quantity == Decimal("50.5")
    
    def test_create_order_with_square_meter_unit(self):
        """测试创建按平方计价的订单 - Requirement 1.4"""
        order = ProcessingOrder(
            id="order_003",
            order_number="ORD-2024-003",
            customer_id="cust_001",
            order_date=date(2024, 1, 15),
            product_name="铝板氧化",
            pricing_unit=PricingUnit.SQUARE_METER,
            quantity=Decimal("25.8"),
            unit_price=Decimal("80.00"),
            total_amount=Decimal("2064.00"),
            status=OrderStatus.PENDING,
            received_amount=Decimal("0"),
            outsourced_cost=Decimal("0"),
            notes="",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        assert order.pricing_unit == PricingUnit.SQUARE_METER
        assert order.quantity == Decimal("25.8")
    
    def test_calculate_total(self):
        """测试订单金额计算 - Requirement 1.5"""
        order = ProcessingOrder(
            id="order_004",
            order_number="ORD-2024-004",
            customer_id="cust_001",
            order_date=date(2024, 1, 15),
            product_name="测试产品",
            pricing_unit=PricingUnit.UNIT,
            quantity=Decimal("100"),
            unit_price=Decimal("5.50"),
            total_amount=Decimal("550.00"),
            status=OrderStatus.PENDING,
            received_amount=Decimal("0"),
            outsourced_cost=Decimal("0"),
            notes="",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        calculated_total = order.calculate_total()
        assert calculated_total == Decimal("550.00")
        assert calculated_total == order.quantity * order.unit_price
    
    def test_calculate_total_with_decimals(self):
        """测试小数金额计算 - Requirement 1.5"""
        order = ProcessingOrder(
            id="order_005",
            order_number="ORD-2024-005",
            customer_id="cust_001",
            order_date=date(2024, 1, 15),
            product_name="测试产品",
            pricing_unit=PricingUnit.METER_WEIGHT,
            quantity=Decimal("12.345"),
            unit_price=Decimal("8.88"),
            total_amount=Decimal("109.6236"),
            status=OrderStatus.PENDING,
            received_amount=Decimal("0"),
            outsourced_cost=Decimal("0"),
            notes="",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        calculated_total = order.calculate_total()
        assert calculated_total == Decimal("109.6236")
    
    def test_get_balance(self):
        """测试未收款余额计算 - Requirement 2.2"""
        order = ProcessingOrder(
            id="order_006",
            order_number="ORD-2024-006",
            customer_id="cust_001",
            order_date=date(2024, 1, 15),
            product_name="测试产品",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("100"),
            unit_price=Decimal("10.00"),
            total_amount=Decimal("1000.00"),
            status=OrderStatus.IN_PROGRESS,
            received_amount=Decimal("300.00"),
            outsourced_cost=Decimal("0"),
            notes="",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        balance = order.get_balance()
        assert balance == Decimal("700.00")
        assert balance == order.total_amount - order.received_amount
    
    def test_get_profit(self):
        """测试订单利润计算"""
        order = ProcessingOrder(
            id="order_007",
            order_number="ORD-2024-007",
            customer_id="cust_001",
            order_date=date(2024, 1, 15),
            product_name="测试产品",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("100"),
            unit_price=Decimal("10.00"),
            total_amount=Decimal("1000.00"),
            status=OrderStatus.COMPLETED,
            received_amount=Decimal("1000.00"),
            outsourced_cost=Decimal("200.00"),
            notes="",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        profit = order.get_profit()
        assert profit == Decimal("800.00")
        assert profit == order.total_amount - order.outsourced_cost
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        original_order = ProcessingOrder(
            id="order_008",
            order_number="ORD-2024-008",
            customer_id="cust_001",
            order_date=date(2024, 1, 15),
            product_name="测试产品",
            pricing_unit=PricingUnit.STRIP,
            quantity=Decimal("50"),
            unit_price=Decimal("3.50"),
            total_amount=Decimal("175.00"),
            status=OrderStatus.PENDING,
            received_amount=Decimal("0"),
            outsourced_cost=Decimal("0"),
            notes="测试备注",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            updated_at=datetime(2024, 1, 15, 10, 30, 0),
        )
        
        # 转换为字典
        order_dict = original_order.to_dict()
        
        # 从字典恢复
        restored_order = ProcessingOrder.from_dict(order_dict)
        
        # 验证所有字段
        assert restored_order.id == original_order.id
        assert restored_order.order_number == original_order.order_number
        assert restored_order.customer_id == original_order.customer_id
        assert restored_order.order_date == original_order.order_date
        assert restored_order.product_name == original_order.product_name
        assert restored_order.pricing_unit == original_order.pricing_unit
        assert restored_order.quantity == original_order.quantity
        assert restored_order.unit_price == original_order.unit_price
        assert restored_order.total_amount == original_order.total_amount
        assert restored_order.status == original_order.status


class TestOutsourcedProcessing:
    """测试外发加工模型"""
    
    def test_create_outsourced_processing(self):
        """测试创建外发加工记录 - Requirements 5.1, 5.2, 5.3"""
        processing = OutsourcedProcessing(
            id="proc_001",
            order_id="order_001",
            supplier_id="supp_001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("100"),
            unit_price=Decimal("1.50"),
            total_cost=Decimal("150.00"),
            notes="喷砂处理",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        assert processing.process_type == ProcessType.SANDBLASTING
        assert processing.quantity == Decimal("100")
        assert processing.unit_price == Decimal("1.50")
        assert processing.total_cost == Decimal("150.00")
    
    def test_calculate_total(self):
        """测试外发加工成本计算"""
        processing = OutsourcedProcessing(
            id="proc_002",
            order_id="order_001",
            supplier_id="supp_001",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("50"),
            unit_price=Decimal("2.80"),
            total_cost=Decimal("140.00"),
            notes="",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        calculated_total = processing.calculate_total()
        assert calculated_total == Decimal("140.00")
        assert calculated_total == processing.quantity * processing.unit_price


class TestBankAccount:
    """测试银行账户模型"""
    
    def test_create_business_account_with_invoice(self):
        """测试创建有票对公账户 - Requirement 3.1"""
        account = BankAccount(
            id="acc_001",
            name="G银行",
            account_number="1234567890",
            account_type=AccountType.BUSINESS,
            has_invoice=True,
            balance=Decimal("50000.00"),
            description="对公账户，有票据",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        assert account.name == "G银行"
        assert account.account_type == AccountType.BUSINESS
        assert account.has_invoice is True
    
    def test_create_cash_account_without_invoice(self):
        """测试创建无票现金账户 - Requirements 3.2, 3.3"""
        account = BankAccount(
            id="acc_002",
            name="N银行",
            account_number="9876543210",
            account_type=AccountType.CASH,
            has_invoice=False,
            balance=Decimal("20000.00"),
            description="现金账户，无票据",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        assert account.name == "N银行"
        assert account.account_type == AccountType.CASH
        assert account.has_invoice is False
    
    def test_create_wechat_account(self):
        """测试创建微信账户 - Requirement 3.3"""
        account = BankAccount(
            id="acc_003",
            name="微信",
            account_number="wx_123456",
            account_type=AccountType.CASH,
            has_invoice=False,
            balance=Decimal("5000.00"),
            description="微信支付账户",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        assert account.name == "微信"
        assert account.account_type == AccountType.CASH
        assert account.has_invoice is False
    
    def test_update_balance_credit(self):
        """测试更新余额（收入）- Requirement 3.5"""
        account = BankAccount(
            id="acc_004",
            name="G银行",
            account_number="1234567890",
            account_type=AccountType.BUSINESS,
            has_invoice=True,
            balance=Decimal("10000.00"),
            description="测试账户",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # 收入1000元
        new_balance = account.update_balance(Decimal("1000.00"), is_credit=True)
        
        assert new_balance == Decimal("11000.00")
        assert account.balance == Decimal("11000.00")
    
    def test_update_balance_debit(self):
        """测试更新余额（支出）- Requirement 3.5"""
        account = BankAccount(
            id="acc_005",
            name="N银行",
            account_number="9876543210",
            account_type=AccountType.CASH,
            has_invoice=False,
            balance=Decimal("10000.00"),
            description="测试账户",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # 支出500元
        new_balance = account.update_balance(Decimal("500.00"), is_credit=False)
        
        assert new_balance == Decimal("9500.00")
        assert account.balance == Decimal("9500.00")
    
    def test_update_balance_multiple_transactions(self):
        """测试多次交易后的余额 - Requirement 3.5"""
        account = BankAccount(
            id="acc_006",
            name="微信",
            account_number="wx_123456",
            account_type=AccountType.CASH,
            has_invoice=False,
            balance=Decimal("5000.00"),
            description="测试账户",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # 收入2000元
        account.update_balance(Decimal("2000.00"), is_credit=True)
        assert account.balance == Decimal("7000.00")
        
        # 支出1500元
        account.update_balance(Decimal("1500.00"), is_credit=False)
        assert account.balance == Decimal("5500.00")
        
        # 收入800元
        account.update_balance(Decimal("800.00"), is_credit=True)
        assert account.balance == Decimal("6300.00")
    
    def test_calculate_balance_from_transactions(self):
        """测试从交易记录计算余额 - Requirement 3.5"""
        account = BankAccount(
            id="acc_007",
            name="G银行",
            account_number="1234567890",
            account_type=AccountType.BUSINESS,
            has_invoice=True,
            balance=Decimal("0"),
            description="测试账户",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # 创建交易记录
        transactions = [
            TransactionRecord(
                id="trans_001",
                date=date(2024, 1, 15),
                type=TransactionType.INCOME,
                amount=Decimal("5000.00"),
                counterparty_id="cust_001",
                description="客户付款1",
                category="加工费收入",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                bank_account_id="acc_007",
            ),
            TransactionRecord(
                id="trans_002",
                date=date(2024, 1, 16),
                type=TransactionType.INCOME,
                amount=Decimal("3000.00"),
                counterparty_id="cust_002",
                description="客户付款2",
                category="加工费收入",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                bank_account_id="acc_007",
            ),
            TransactionRecord(
                id="trans_003",
                date=date(2024, 1, 17),
                type=TransactionType.EXPENSE,
                amount=Decimal("1200.00"),
                counterparty_id="supp_001",
                description="支付供应商",
                category="外发加工费用",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                bank_account_id="acc_007",
            ),
            TransactionRecord(
                id="trans_004",
                date=date(2024, 1, 18),
                type=TransactionType.EXPENSE,
                amount=Decimal("800.00"),
                counterparty_id="supp_002",
                description="支付房租",
                category="房租",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                bank_account_id="acc_007",
            ),
        ]
        
        # 计算余额：5000 + 3000 - 1200 - 800 = 6000
        calculated_balance = account.calculate_balance_from_transactions(transactions)
        
        assert calculated_balance == Decimal("6000.00")
    
    def test_calculate_balance_from_transactions_with_other_accounts(self):
        """测试计算余额时排除其他账户的交易 - Requirement 3.5"""
        account = BankAccount(
            id="acc_008",
            name="N银行",
            account_number="9876543210",
            account_type=AccountType.CASH,
            has_invoice=False,
            balance=Decimal("0"),
            description="测试账户",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # 创建交易记录，包含其他账户的交易
        transactions = [
            TransactionRecord(
                id="trans_005",
                date=date(2024, 1, 15),
                type=TransactionType.INCOME,
                amount=Decimal("2000.00"),
                counterparty_id="cust_001",
                description="acc_008的收入",
                category="加工费收入",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                bank_account_id="acc_008",
            ),
            TransactionRecord(
                id="trans_006",
                date=date(2024, 1, 16),
                type=TransactionType.INCOME,
                amount=Decimal("5000.00"),
                counterparty_id="cust_002",
                description="其他账户的收入",
                category="加工费收入",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                bank_account_id="acc_999",  # 不同账户
            ),
            TransactionRecord(
                id="trans_007",
                date=date(2024, 1, 17),
                type=TransactionType.EXPENSE,
                amount=Decimal("500.00"),
                counterparty_id="supp_001",
                description="acc_008的支出",
                category="日常费用",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                bank_account_id="acc_008",
            ),
        ]
        
        # 计算余额：只计算acc_008的交易 2000 - 500 = 1500
        calculated_balance = account.calculate_balance_from_transactions(transactions)
        
        assert calculated_balance == Decimal("1500.00")
    
    def test_calculate_balance_from_empty_transactions(self):
        """测试从空交易列表计算余额 - Requirement 3.5"""
        account = BankAccount(
            id="acc_009",
            name="微信",
            account_number="wx_123456",
            account_type=AccountType.CASH,
            has_invoice=False,
            balance=Decimal("1000.00"),
            description="测试账户",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # 空交易列表
        transactions = []
        
        calculated_balance = account.calculate_balance_from_transactions(transactions)
        
        assert calculated_balance == Decimal("0")
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        original_account = BankAccount(
            id="acc_010",
            name="G银行",
            account_number="1234567890",
            account_type=AccountType.BUSINESS,
            has_invoice=True,
            balance=Decimal("50000.00"),
            description="测试账户",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            updated_at=datetime(2024, 1, 15, 10, 30, 0),
        )
        
        # 转换为字典
        account_dict = original_account.to_dict()
        
        # 从字典恢复
        restored_account = BankAccount.from_dict(account_dict)
        
        # 验证所有字段
        assert restored_account.id == original_account.id
        assert restored_account.name == original_account.name
        assert restored_account.account_number == original_account.account_number
        assert restored_account.account_type == original_account.account_type
        assert restored_account.has_invoice == original_account.has_invoice
        assert restored_account.balance == original_account.balance
        assert restored_account.description == original_account.description


class TestReconciliationMatch:
    """测试对账匹配模型"""
    
    def test_one_to_many_match(self):
        """测试一对多匹配（一笔付款对多个订单）- Requirement 2.1"""
        match = ReconciliationMatch(
            id="match_001",
            match_date=datetime.now(),
            bank_record_ids=["bank_001"],
            order_ids=["order_001", "order_002", "order_003"],
            total_bank_amount=Decimal("1500.00"),
            total_order_amount=Decimal("1500.00"),
            difference=Decimal("0"),
            notes="一笔付款对应三个订单",
            created_by="user_001",
            created_at=datetime.now(),
        )
        
        assert match.is_one_to_many() is True
        assert match.is_many_to_one() is False
        assert len(match.bank_record_ids) == 1
        assert len(match.order_ids) == 3
    
    def test_many_to_one_match(self):
        """测试多对一匹配（多笔付款对一个订单）- Requirement 2.2"""
        match = ReconciliationMatch(
            id="match_002",
            match_date=datetime.now(),
            bank_record_ids=["bank_001", "bank_002", "bank_003"],
            order_ids=["order_001"],
            total_bank_amount=Decimal("2000.00"),
            total_order_amount=Decimal("2000.00"),
            difference=Decimal("0"),
            notes="三笔付款对应一个订单",
            created_by="user_001",
            created_at=datetime.now(),
        )
        
        assert match.is_one_to_many() is False
        assert match.is_many_to_one() is True
        assert len(match.bank_record_ids) == 3
        assert len(match.order_ids) == 1
    
    def test_one_to_one_match(self):
        """测试一对一匹配"""
        match = ReconciliationMatch(
            id="match_003",
            match_date=datetime.now(),
            bank_record_ids=["bank_001"],
            order_ids=["order_001"],
            total_bank_amount=Decimal("1000.00"),
            total_order_amount=Decimal("1000.00"),
            difference=Decimal("0"),
            notes="一对一匹配",
            created_by="user_001",
            created_at=datetime.now(),
        )
        
        assert match.is_one_to_many() is False
        assert match.is_many_to_one() is False
    
    def test_match_with_difference(self):
        """测试有差额的匹配 - Requirement 2.5"""
        match = ReconciliationMatch(
            id="match_004",
            match_date=datetime.now(),
            bank_record_ids=["bank_001"],
            order_ids=["order_001"],
            total_bank_amount=Decimal("1000.00"),
            total_order_amount=Decimal("1050.00"),
            difference=Decimal("-50.00"),
            notes="存在50元差额",
            created_by="user_001",
            created_at=datetime.now(),
        )
        
        assert match.difference == Decimal("-50.00")
    
    def test_is_one_to_one(self):
        """测试一对一匹配识别"""
        match = ReconciliationMatch(
            id="match_005",
            match_date=datetime.now(),
            bank_record_ids=["bank_001"],
            order_ids=["order_001"],
            total_bank_amount=Decimal("1000.00"),
            total_order_amount=Decimal("1000.00"),
            difference=Decimal("0"),
            notes="一对一匹配",
            created_by="user_001",
            created_at=datetime.now(),
        )
        
        assert match.is_one_to_one() is True
        assert match.is_one_to_many() is False
        assert match.is_many_to_one() is False
        assert match.is_many_to_many() is False
    
    def test_is_many_to_many(self):
        """测试多对多匹配识别"""
        match = ReconciliationMatch(
            id="match_006",
            match_date=datetime.now(),
            bank_record_ids=["bank_001", "bank_002"],
            order_ids=["order_001", "order_002"],
            total_bank_amount=Decimal("3000.00"),
            total_order_amount=Decimal("3000.00"),
            difference=Decimal("0"),
            notes="多对多匹配",
            created_by="user_001",
            created_at=datetime.now(),
        )
        
        assert match.is_many_to_many() is True
        assert match.is_one_to_one() is False
        assert match.is_one_to_many() is False
        assert match.is_many_to_one() is False
    
    def test_validate_match_success(self):
        """测试有效匹配的验证 - Requirements 2.1, 2.2, 2.3, 2.4"""
        match = ReconciliationMatch(
            id="match_007",
            match_date=datetime.now(),
            bank_record_ids=["bank_001"],
            order_ids=["order_001"],
            total_bank_amount=Decimal("1000.00"),
            total_order_amount=Decimal("1000.00"),
            difference=Decimal("0"),
            notes="有效匹配",
            created_by="user_001",
            created_at=datetime.now(),
        )
        
        is_valid, error_msg = match.validate_match()
        assert is_valid is True
        assert error_msg == ""
    
    def test_validate_match_with_small_difference(self):
        """测试小额差异的匹配验证 - Requirement 2.5"""
        match = ReconciliationMatch(
            id="match_008",
            match_date=datetime.now(),
            bank_record_ids=["bank_001"],
            order_ids=["order_001"],
            total_bank_amount=Decimal("1000.00"),
            total_order_amount=Decimal("1000.01"),
            difference=Decimal("-0.01"),
            notes="小额差异",
            created_by="user_001",
            created_at=datetime.now(),
        )
        
        is_valid, error_msg = match.validate_match()
        assert is_valid is True
        assert error_msg == ""
    
    def test_validate_match_with_large_difference(self):
        """测试大额差异的匹配验证 - Requirement 2.5"""
        match = ReconciliationMatch(
            id="match_009",
            match_date=datetime.now(),
            bank_record_ids=["bank_001"],
            order_ids=["order_001"],
            total_bank_amount=Decimal("1000.00"),
            total_order_amount=Decimal("1050.00"),
            difference=Decimal("-50.00"),
            notes="大额差异",
            created_by="user_001",
            created_at=datetime.now(),
        )
        
        is_valid, error_msg = match.validate_match()
        assert is_valid is True  # 仍然有效，但有警告
        assert "存在金额差异" in error_msg
        assert "-50.00" in error_msg
    
    def test_validate_match_no_bank_records(self):
        """测试没有银行流水的匹配验证"""
        match = ReconciliationMatch(
            id="match_010",
            match_date=datetime.now(),
            bank_record_ids=[],
            order_ids=["order_001"],
            total_bank_amount=Decimal("0"),
            total_order_amount=Decimal("1000.00"),
            difference=Decimal("-1000.00"),
            notes="无银行流水",
            created_by="user_001",
            created_at=datetime.now(),
        )
        
        is_valid, error_msg = match.validate_match()
        assert is_valid is False
        assert error_msg == "至少需要一笔银行流水"
    
    def test_validate_match_no_orders(self):
        """测试没有订单的匹配验证"""
        match = ReconciliationMatch(
            id="match_011",
            match_date=datetime.now(),
            bank_record_ids=["bank_001"],
            order_ids=[],
            total_bank_amount=Decimal("1000.00"),
            total_order_amount=Decimal("0"),
            difference=Decimal("1000.00"),
            notes="无订单",
            created_by="user_001",
            created_at=datetime.now(),
        )
        
        is_valid, error_msg = match.validate_match()
        assert is_valid is False
        assert error_msg == "至少需要一个订单"
    
    def test_validate_match_empty_bank_record_id(self):
        """测试空银行流水ID的匹配验证"""
        match = ReconciliationMatch(
            id="match_012",
            match_date=datetime.now(),
            bank_record_ids=["bank_001", "", "bank_003"],
            order_ids=["order_001"],
            total_bank_amount=Decimal("1000.00"),
            total_order_amount=Decimal("1000.00"),
            difference=Decimal("0"),
            notes="包含空ID",
            created_by="user_001",
            created_at=datetime.now(),
        )
        
        is_valid, error_msg = match.validate_match()
        assert is_valid is False
        assert error_msg == "银行流水ID不能为空"
    
    def test_validate_match_empty_order_id(self):
        """测试空订单ID的匹配验证"""
        match = ReconciliationMatch(
            id="match_013",
            match_date=datetime.now(),
            bank_record_ids=["bank_001"],
            order_ids=["order_001", "  ", "order_003"],
            total_bank_amount=Decimal("1000.00"),
            total_order_amount=Decimal("1000.00"),
            difference=Decimal("0"),
            notes="包含空ID",
            created_by="user_001",
            created_at=datetime.now(),
        )
        
        is_valid, error_msg = match.validate_match()
        assert is_valid is False
        assert error_msg == "订单ID不能为空"
    
    def test_calculate_difference(self):
        """测试差额计算 - Requirement 2.5"""
        match = ReconciliationMatch(
            id="match_014",
            match_date=datetime.now(),
            bank_record_ids=["bank_001"],
            order_ids=["order_001"],
            total_bank_amount=Decimal("1200.00"),
            total_order_amount=Decimal("1000.00"),
            difference=Decimal("0"),  # 初始值
            notes="测试差额计算",
            created_by="user_001",
            created_at=datetime.now(),
        )
        
        calculated_diff = match.calculate_difference()
        assert calculated_diff == Decimal("200.00")
    
    def test_get_match_type(self):
        """测试获取匹配类型描述"""
        # 一对一
        match_1to1 = ReconciliationMatch(
            id="match_015",
            match_date=datetime.now(),
            bank_record_ids=["bank_001"],
            order_ids=["order_001"],
            total_bank_amount=Decimal("1000.00"),
            total_order_amount=Decimal("1000.00"),
            difference=Decimal("0"),
            notes="",
            created_by="user_001",
            created_at=datetime.now(),
        )
        assert match_1to1.get_match_type() == "一对一"
        
        # 一对多
        match_1toN = ReconciliationMatch(
            id="match_016",
            match_date=datetime.now(),
            bank_record_ids=["bank_001"],
            order_ids=["order_001", "order_002"],
            total_bank_amount=Decimal("2000.00"),
            total_order_amount=Decimal("2000.00"),
            difference=Decimal("0"),
            notes="",
            created_by="user_001",
            created_at=datetime.now(),
        )
        assert match_1toN.get_match_type() == "一对多"
        
        # 多对一
        match_Nto1 = ReconciliationMatch(
            id="match_017",
            match_date=datetime.now(),
            bank_record_ids=["bank_001", "bank_002"],
            order_ids=["order_001"],
            total_bank_amount=Decimal("2000.00"),
            total_order_amount=Decimal("2000.00"),
            difference=Decimal("0"),
            notes="",
            created_by="user_001",
            created_at=datetime.now(),
        )
        assert match_Nto1.get_match_type() == "多对一"
        
        # 多对多
        match_NtoN = ReconciliationMatch(
            id="match_018",
            match_date=datetime.now(),
            bank_record_ids=["bank_001", "bank_002"],
            order_ids=["order_001", "order_002"],
            total_bank_amount=Decimal("3000.00"),
            total_order_amount=Decimal("3000.00"),
            difference=Decimal("0"),
            notes="",
            created_by="user_001",
            created_at=datetime.now(),
        )
        assert match_NtoN.get_match_type() == "多对多"
    
    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化 - Requirement 2.6"""
        original_match = ReconciliationMatch(
            id="match_019",
            match_date=datetime(2024, 1, 15, 14, 30, 0),
            bank_record_ids=["bank_001", "bank_002"],
            order_ids=["order_001"],
            total_bank_amount=Decimal("2000.00"),
            total_order_amount=Decimal("2000.00"),
            difference=Decimal("0"),
            notes="测试序列化",
            created_by="user_001",
            created_at=datetime(2024, 1, 15, 14, 30, 0),
        )
        
        # 转换为字典
        match_dict = original_match.to_dict()
        
        # 从字典恢复
        restored_match = ReconciliationMatch.from_dict(match_dict)
        
        # 验证所有字段
        assert restored_match.id == original_match.id
        assert restored_match.match_date == original_match.match_date
        assert restored_match.bank_record_ids == original_match.bank_record_ids
        assert restored_match.order_ids == original_match.order_ids
        assert restored_match.total_bank_amount == original_match.total_bank_amount
        assert restored_match.total_order_amount == original_match.total_order_amount
        assert restored_match.difference == original_match.difference
        assert restored_match.notes == original_match.notes
        assert restored_match.created_by == original_match.created_by
        assert restored_match.created_at == original_match.created_at


class TestTransactionRecord:
    """测试交易记录模型"""
    
    def test_create_income_transaction(self):
        """测试创建收入交易"""
        transaction = TransactionRecord(
            id="trans_001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="cust_001",
            description="客户付款",
            category="加工费收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            bank_account_id="acc_001",
        )
        
        assert transaction.type == TransactionType.INCOME
        assert transaction.amount == Decimal("1000.00")
        assert transaction.bank_account_id == "acc_001"
    
    def test_create_expense_transaction(self):
        """测试创建支出交易"""
        transaction = TransactionRecord(
            id="trans_002",
            date=date(2024, 1, 15),
            type=TransactionType.EXPENSE,
            amount=Decimal("500.00"),
            counterparty_id="supp_001",
            description="外发加工费",
            category="外发加工费用",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            bank_account_id="acc_002",
        )
        
        assert transaction.type == TransactionType.EXPENSE
        assert transaction.amount == Decimal("500.00")
        assert transaction.category == "外发加工费用"


class TestCounterparty:
    """测试往来单位模型"""
    
    def test_create_customer(self):
        """测试创建客户"""
        customer = Counterparty(
            id="cust_001",
            name="测试客户",
            type=CounterpartyType.CUSTOMER,
            contact_person="张三",
            phone="13800138000",
            email="test@example.com",
            address="测试地址",
            tax_id="123456789",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            aliases=["客户A", "测试公司"],
        )
        
        assert customer.type == CounterpartyType.CUSTOMER
        assert len(customer.aliases) == 2
    
    def test_create_supplier(self):
        """测试创建供应商"""
        supplier = Counterparty(
            id="supp_001",
            name="测试供应商",
            type=CounterpartyType.SUPPLIER,
            contact_person="李四",
            phone="13900139000",
            email="supplier@example.com",
            address="供应商地址",
            tax_id="987654321",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        assert supplier.type == CounterpartyType.SUPPLIER
        assert len(supplier.aliases) == 0


class TestBankRecord:
    """测试银行流水模型"""
    
    def test_create_credit_record(self):
        """测试创建收入流水"""
        record = BankRecord(
            id="bank_001",
            transaction_date=date(2024, 1, 15),
            description="客户付款",
            amount=Decimal("1000.00"),
            balance=Decimal("51000.00"),
            transaction_type="CREDIT",
            counterparty="测试客户",
            bank_account_id="acc_001",
        )
        
        assert record.transaction_type == "CREDIT"
        assert record.amount == Decimal("1000.00")
    
    def test_create_debit_record(self):
        """测试创建支出流水"""
        record = BankRecord(
            id="bank_002",
            transaction_date=date(2024, 1, 15),
            description="支付供应商",
            amount=Decimal("500.00"),
            balance=Decimal("50500.00"),
            transaction_type="DEBIT",
            counterparty="测试供应商",
            bank_account_id="acc_001",
        )
        
        assert record.transaction_type == "DEBIT"
        assert record.amount == Decimal("500.00")
