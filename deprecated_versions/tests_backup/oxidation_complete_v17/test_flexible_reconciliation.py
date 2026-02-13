"""
Unit tests for flexible reconciliation features

Tests for:
- FlexibleReconciliationMatcher (one-to-many, many-to-one matching)
- CounterpartyAliasManager (alias management and matching)
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
import tempfile
import shutil
import os

from oxidation_complete_v17.models.core_models import (
    BankRecord,
    TransactionRecord,
    TransactionType,
    TransactionStatus,
    ProcessingOrder,
    OrderStatus,
    PricingUnit
)
from oxidation_complete_v17.reconciliation.flexible_matcher import (
    FlexibleReconciliationMatcher,
    FlexibleMatchType,
    CounterpartyBalance
)
from oxidation_complete_v17.reconciliation.alias_manager import (
    CounterpartyAliasManager,
    AliasMatchResult
)


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_bank_records():
    """示例银行流水记录"""
    return [
        BankRecord(
            id="BR001",
            transaction_date=date(2026, 2, 1),
            description="收到客户A付款",
            amount=Decimal("15000.00"),
            balance=Decimal("100000.00"),
            transaction_type="CREDIT",
            counterparty="客户A有限公司"
        ),
        BankRecord(
            id="BR002",
            transaction_date=date(2026, 2, 5),
            description="收到客户B付款",
            amount=Decimal("5000.00"),
            balance=Decimal("105000.00"),
            transaction_type="CREDIT",
            counterparty="客户B公司"
        ),
        BankRecord(
            id="BR003",
            transaction_date=date(2026, 2, 10),
            description="收到客户B付款",
            amount=Decimal("3000.00"),
            balance=Decimal("108000.00"),
            transaction_type="CREDIT",
            counterparty="客户B公司"
        ),
    ]


@pytest.fixture
def sample_orders():
    """示例加工订单"""
    return [
        ProcessingOrder(
            id="ORD001",
            order_number="2026020001",
            customer_id="CUST001",
            order_date=date(2026, 1, 25),
            product_name="铝型材氧化",
            quantity=Decimal("1000"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10.00"),
            total_amount=Decimal("10000.00"),
            status=OrderStatus.PENDING,
            received_amount=Decimal("0"),
            outsourced_cost=Decimal("0"),
            notes="",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        ProcessingOrder(
            id="ORD002",
            order_number="2026020002",
            customer_id="CUST001",
            order_date=date(2026, 1, 28),
            product_name="不锈钢拉丝",
            quantity=Decimal("500"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("8.00"),
            total_amount=Decimal("4000.00"),
            status=OrderStatus.PENDING,
            received_amount=Decimal("0"),
            outsourced_cost=Decimal("0"),
            notes="",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        ProcessingOrder(
            id="ORD003",
            order_number="2026020003",
            customer_id="CUST002",
            order_date=date(2026, 2, 1),
            product_name="铜件抛光",
            quantity=Decimal("800"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("12.00"),
            total_amount=Decimal("9600.00"),
            status=OrderStatus.PENDING,
            received_amount=Decimal("0"),
            outsourced_cost=Decimal("0"),
            notes="",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
    ]


class TestFlexibleReconciliationMatcher:
    """测试灵活对账匹配器"""
    
    def test_create_one_to_many_match(self, temp_data_dir, sample_bank_records, sample_orders):
        """测试创建一对多匹配(一笔银行流水对应多个订单)"""
        matcher = FlexibleReconciliationMatcher(data_dir=temp_data_dir)
        
        # 客户A合并付款,一次性支付两个订单
        bank_record = sample_bank_records[0]  # 15000元
        orders = [sample_orders[0], sample_orders[1]]  # 10000 + 4000 = 14000元
        
        match = matcher.create_one_to_many_match(
            bank_record=bank_record,
            orders=orders,
            notes="客户A合并付款",
            performed_by="test_user"
        )
        
        assert match.match_type == FlexibleMatchType.ONE_TO_MANY
        assert len(match.bank_records) == 1
        assert len(match.orders) == 2
        assert match.total_bank_amount == Decimal("15000.00")
        assert match.total_system_amount == Decimal("14000.00")
        assert match.balance == Decimal("1000.00")  # 多付了1000元
        assert match.notes == "客户A合并付款"
    
    def test_create_many_to_one_match(self, temp_data_dir, sample_bank_records, sample_orders):
        """测试创建多对一匹配(多笔银行流水对应一个订单)"""
        matcher = FlexibleReconciliationMatcher(data_dir=temp_data_dir)
        
        # 客户B分批付款,分两次支付一个订单
        bank_records = [sample_bank_records[1], sample_bank_records[2]]  # 5000 + 3000 = 8000元
        order = sample_orders[2]  # 9600元
        
        match = matcher.create_many_to_one_match(
            bank_records=bank_records,
            order=order,
            notes="客户B分批付款",
            performed_by="test_user"
        )
        
        assert match.match_type == FlexibleMatchType.MANY_TO_ONE
        assert len(match.bank_records) == 2
        assert len(match.orders) == 1
        assert match.total_bank_amount == Decimal("8000.00")
        assert match.total_system_amount == Decimal("9600.00")
        assert match.balance == Decimal("-1600.00")  # 还欠1600元
        assert match.notes == "客户B分批付款"
    
    def test_update_match_balance(self, temp_data_dir, sample_bank_records, sample_orders):
        """测试更新匹配记录的余额"""
        matcher = FlexibleReconciliationMatcher(data_dir=temp_data_dir)
        
        # 创建初始匹配
        bank_records = [sample_bank_records[1]]  # 5000元
        order = sample_orders[2]  # 9600元
        
        match = matcher.create_many_to_one_match(
            bank_records=bank_records,
            order=order,
            notes="客户B首次付款",
            performed_by="test_user"
        )
        
        assert match.balance == Decimal("-4600.00")  # 还欠4600元
        
        # 客户B再次付款
        new_bank_record = sample_bank_records[2]  # 3000元
        updated_match = matcher.update_match_balance(
            match_id=match.id,
            new_bank_records=[new_bank_record],
            performed_by="test_user"
        )
        
        assert len(updated_match.bank_records) == 2
        assert updated_match.total_bank_amount == Decimal("8000.00")
        assert updated_match.balance == Decimal("-1600.00")  # 还欠1600元
    
    def test_undo_match(self, temp_data_dir, sample_bank_records, sample_orders):
        """测试撤销对账操作"""
        matcher = FlexibleReconciliationMatcher(data_dir=temp_data_dir)
        
        # 创建匹配
        bank_record = sample_bank_records[0]
        orders = [sample_orders[0], sample_orders[1]]
        
        match = matcher.create_one_to_many_match(
            bank_record=bank_record,
            orders=orders,
            performed_by="test_user"
        )
        
        match_id = match.id
        
        # 撤销匹配
        result = matcher.undo_match(match_id, performed_by="test_user")
        
        assert result is True
        assert match_id not in matcher.matches
        
        # 再次撤销应该失败
        result = matcher.undo_match(match_id, performed_by="test_user")
        assert result is False
    
    def test_get_counterparty_balance(self, temp_data_dir, sample_bank_records, sample_orders):
        """测试获取往来单位未对账余额"""
        matcher = FlexibleReconciliationMatcher(data_dir=temp_data_dir)
        
        # 创建匹配:客户A付款15000元,订单总额14000元
        bank_record = sample_bank_records[0]
        orders = [sample_orders[0], sample_orders[1]]
        
        matcher.create_one_to_many_match(
            bank_record=bank_record,
            orders=orders,
            performed_by="test_user"
        )
        
        # 获取客户A的余额
        balance = matcher.get_counterparty_balance(
            counterparty_id="CUST001",
            counterparty_name="客户A有限公司",
            all_orders=orders
        )
        
        assert balance.counterparty_id == "CUST001"
        assert balance.total_orders_amount == Decimal("14000.00")
        assert balance.total_received_amount == Decimal("15000.00")
        assert balance.unreconciled_balance == Decimal("-1000.00")  # 多付了1000元
    
    def test_get_match_history(self, temp_data_dir, sample_bank_records, sample_orders):
        """测试获取对账历史"""
        matcher = FlexibleReconciliationMatcher(data_dir=temp_data_dir)
        
        # 创建匹配
        bank_record = sample_bank_records[0]
        orders = [sample_orders[0]]
        
        match = matcher.create_one_to_many_match(
            bank_record=bank_record,
            orders=orders,
            performed_by="test_user"
        )
        
        # 更新匹配
        matcher.update_match_balance(
            match_id=match.id,
            new_orders=[sample_orders[1]],
            performed_by="test_user"
        )
        
        # 获取历史
        history = matcher.get_match_history(match.id)
        
        assert len(history) == 2
        assert history[0].action == "create"
        assert history[1].action == "update"
    
    def test_get_all_matches_with_filters(self, temp_data_dir, sample_bank_records, sample_orders):
        """测试获取所有匹配记录(带过滤)"""
        matcher = FlexibleReconciliationMatcher(data_dir=temp_data_dir)
        
        # 创建一对多匹配
        matcher.create_one_to_many_match(
            bank_record=sample_bank_records[0],
            orders=[sample_orders[0], sample_orders[1]],
            performed_by="test_user"
        )
        
        # 创建多对一匹配
        matcher.create_many_to_one_match(
            bank_records=[sample_bank_records[1], sample_bank_records[2]],
            order=sample_orders[2],
            performed_by="test_user"
        )
        
        # 获取所有匹配
        all_matches = matcher.get_all_matches()
        assert len(all_matches) == 2
        
        # 按类型过滤
        one_to_many = matcher.get_all_matches(match_type=FlexibleMatchType.ONE_TO_MANY)
        assert len(one_to_many) == 1
        assert one_to_many[0].match_type == FlexibleMatchType.ONE_TO_MANY
        
        many_to_one = matcher.get_all_matches(match_type=FlexibleMatchType.MANY_TO_ONE)
        assert len(many_to_one) == 1
        assert many_to_one[0].match_type == FlexibleMatchType.MANY_TO_ONE
    
    def test_persistence(self, temp_data_dir, sample_bank_records, sample_orders):
        """测试数据持久化"""
        # 创建匹配器并添加数据
        matcher1 = FlexibleReconciliationMatcher(data_dir=temp_data_dir)
        match = matcher1.create_one_to_many_match(
            bank_record=sample_bank_records[0],
            orders=[sample_orders[0]],
            performed_by="test_user"
        )
        match_id = match.id
        
        # 创建新的匹配器实例,应该能加载之前的数据
        matcher2 = FlexibleReconciliationMatcher(data_dir=temp_data_dir)
        assert match_id in matcher2.matches
        loaded_match = matcher2.matches[match_id]
        assert loaded_match.total_bank_amount == match.total_bank_amount


class TestCounterpartyAliasManager:
    """测试往来单位别名管理器"""
    
    def test_add_alias(self, temp_data_dir):
        """测试添加别名"""
        manager = CounterpartyAliasManager(data_dir=temp_data_dir)
        
        alias = manager.add_alias(
            counterparty_id="CUST001",
            counterparty_name="客户A有限公司",
            alias="客户A",
            created_by="test_user"
        )
        
        assert alias.counterparty_id == "CUST001"
        assert alias.alias == "客户A"
        assert alias.created_by == "test_user"
    
    def test_add_duplicate_alias(self, temp_data_dir):
        """测试添加重复别名"""
        manager = CounterpartyAliasManager(data_dir=temp_data_dir)
        
        manager.add_alias(
            counterparty_id="CUST001",
            counterparty_name="客户A有限公司",
            alias="客户A",
            created_by="test_user"
        )
        
        # 尝试添加相同别名应该失败
        with pytest.raises(ValueError, match="别名已存在"):
            manager.add_alias(
                counterparty_id="CUST001",
                counterparty_name="客户A有限公司",
                alias="客户A",
                created_by="test_user"
            )
    
    def test_add_conflicting_alias(self, temp_data_dir):
        """测试添加冲突别名"""
        manager = CounterpartyAliasManager(data_dir=temp_data_dir)
        
        manager.add_alias(
            counterparty_id="CUST001",
            counterparty_name="客户A有限公司",
            alias="客户A",
            created_by="test_user"
        )
        
        # 尝试为不同往来单位添加相同别名应该失败
        with pytest.raises(ValueError, match="别名冲突"):
            manager.add_alias(
                counterparty_id="CUST002",
                counterparty_name="客户B公司",
                alias="客户A",
                created_by="test_user"
            )
    
    def test_add_aliases_batch(self, temp_data_dir):
        """测试批量添加别名"""
        manager = CounterpartyAliasManager(data_dir=temp_data_dir)
        
        aliases_data = [
            {
                "counterparty_id": "CUST001",
                "counterparty_name": "客户A有限公司",
                "alias": "客户A"
            },
            {
                "counterparty_id": "CUST001",
                "counterparty_name": "客户A有限公司",
                "alias": "A公司"
            },
            {
                "counterparty_id": "CUST002",
                "counterparty_name": "客户B公司",
                "alias": "客户B"
            },
        ]
        
        result = manager.add_aliases_batch(aliases_data, created_by="test_user")
        
        assert result["total"] == 3
        assert result["success"] == 3
        assert result["failed"] == 0
    
    def test_remove_alias(self, temp_data_dir):
        """测试删除别名"""
        manager = CounterpartyAliasManager(data_dir=temp_data_dir)
        
        manager.add_alias(
            counterparty_id="CUST001",
            counterparty_name="客户A有限公司",
            alias="客户A",
            created_by="test_user"
        )
        
        result = manager.remove_alias("CUST001", "客户A")
        assert result is True
        
        # 再次删除应该失败
        result = manager.remove_alias("CUST001", "客户A")
        assert result is False
    
    def test_get_aliases(self, temp_data_dir):
        """测试获取往来单位的所有别名"""
        manager = CounterpartyAliasManager(data_dir=temp_data_dir)
        
        manager.add_alias("CUST001", "客户A有限公司", "客户A", "test_user")
        manager.add_alias("CUST001", "客户A有限公司", "A公司", "test_user")
        manager.add_alias("CUST002", "客户B公司", "客户B", "test_user")
        
        aliases = manager.get_aliases("CUST001")
        assert len(aliases) == 2
        assert "客户A" in aliases
        assert "A公司" in aliases
    
    def test_match_counterparty_exact_alias(self, temp_data_dir):
        """测试精确匹配别名"""
        manager = CounterpartyAliasManager(data_dir=temp_data_dir)
        
        manager.add_alias("CUST001", "客户A有限公司", "客户A", "test_user")
        
        result = manager.match_counterparty("客户A")
        
        assert result is not None
        assert result.counterparty_id == "CUST001"
        assert result.matched_alias == "客户A"
        assert result.confidence == 1.0
        assert result.match_type == "alias"
    
    def test_match_counterparty_exact_name(self, temp_data_dir):
        """测试精确匹配往来单位名称"""
        manager = CounterpartyAliasManager(data_dir=temp_data_dir)
        
        manager.add_alias("CUST001", "客户A有限公司", "客户A", "test_user")
        
        result = manager.match_counterparty("客户A有限公司")
        
        assert result is not None
        assert result.counterparty_id == "CUST001"
        assert result.confidence == 1.0
        assert result.match_type == "exact"
    
    def test_match_counterparty_fuzzy(self, temp_data_dir):
        """测试模糊匹配"""
        manager = CounterpartyAliasManager(data_dir=temp_data_dir)
        
        manager.add_alias("CUST001", "客户A有限公司", "客户A", "test_user")
        
        result = manager.match_counterparty("客户A有限责任公司", similarity_threshold=0.7)
        
        assert result is not None
        assert result.counterparty_id == "CUST001"
        assert result.confidence >= 0.7
        assert result.match_type == "fuzzy"
    
    def test_match_counterparty_no_match(self, temp_data_dir):
        """测试无匹配"""
        manager = CounterpartyAliasManager(data_dir=temp_data_dir)
        
        manager.add_alias("CUST001", "客户A有限公司", "客户A", "test_user")
        
        result = manager.match_counterparty("完全不相关的公司")
        
        assert result is None
    
    def test_detect_conflicts(self, temp_data_dir):
        """测试检测别名冲突"""
        manager = CounterpartyAliasManager(data_dir=temp_data_dir)
        
        # 正常情况:不同往来单位使用不同别名
        manager.add_alias("CUST001", "客户A有限公司", "客户A", "test_user")
        manager.add_alias("CUST002", "客户B公司", "客户B", "test_user")
        
        conflicts = manager.detect_conflicts()
        assert len(conflicts) == 0
        
        # 注意:由于add_alias会检查冲突,我们无法直接创建冲突
        # 这个测试主要验证detect_conflicts方法的逻辑
    
    def test_suggest_aliases(self, temp_data_dir):
        """测试智能建议别名"""
        manager = CounterpartyAliasManager(data_dir=temp_data_dir)
        
        bank_statement_names = [
            "客户A有限责任公司",
            "客户A公司",
            "A有限公司",
            "完全不相关的公司",
        ]
        
        suggestions = manager.suggest_aliases(
            counterparty_name="客户A有限公司",
            bank_statement_names=bank_statement_names,
            similarity_threshold=0.7
        )
        
        assert len(suggestions) > 0
        assert "客户A有限责任公司" in suggestions or "客户A公司" in suggestions
        assert "完全不相关的公司" not in suggestions
    
    def test_export_aliases(self, temp_data_dir):
        """测试导出别名数据"""
        manager = CounterpartyAliasManager(data_dir=temp_data_dir)
        
        manager.add_alias("CUST001", "客户A有限公司", "客户A", "test_user")
        manager.add_alias("CUST002", "客户B公司", "客户B", "test_user")
        
        exported = manager.export_aliases()
        
        assert len(exported) == 2
        assert all("往来单位ID" in item for item in exported)
        assert all("别名" in item for item in exported)
    
    def test_persistence(self, temp_data_dir):
        """测试数据持久化"""
        # 创建管理器并添加别名
        manager1 = CounterpartyAliasManager(data_dir=temp_data_dir)
        manager1.add_alias("CUST001", "客户A有限公司", "客户A", "test_user")
        
        # 创建新的管理器实例,应该能加载之前的数据
        manager2 = CounterpartyAliasManager(data_dir=temp_data_dir)
        aliases = manager2.get_aliases("CUST001")
        assert len(aliases) == 1
        assert "客户A" in aliases
