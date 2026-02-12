#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支出管理属性测试
使用 Hypothesis 进行基于属性的测试
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from decimal import Decimal
from datetime import date, timedelta
from ..models.business_models import (
    Supplier, ExpenseType, BankType
)
from ..business.finance_manager import FinanceManager
from ..database.db_manager import DatabaseManager


# 测试策略定义
@st.composite
def expense_type_strategy(draw):
    """生成支出类型"""
    return draw(st.sampled_from(list(ExpenseType)))


@st.composite
def bank_type_strategy(draw):
    """生成银行类型"""
    return draw(st.sampled_from(list(BankType)))


@st.composite
def positive_decimal_strategy(draw, min_value=1, max_value=100000):
    """生成正数金额"""
    value = draw(st.integers(min_value=min_value, max_value=max_value))
    return Decimal(str(value))


@st.composite
def date_strategy(draw):
    """生成日期"""
    days_offset = draw(st.integers(min_value=-365, max_value=365))
    return date.today() + timedelta(days=days_offset)


@st.composite
def supplier_strategy(draw):
    """生成供应商"""
    return Supplier(
        name=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        contact=draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        phone=draw(st.text(min_size=11, max_size=11, alphabet='0123456789')),
        business_type=draw(st.sampled_from(["原料供应商", "委外加工商", "设备供应商"]))
    )


@pytest.fixture
def db_manager(tmp_path):
    """创建临时数据库管理器"""
    db_path = tmp_path / "test_expense_properties.db"
    db = DatabaseManager(str(db_path))
    db.connect()
    yield db
    db.close()


@pytest.fixture
def finance_manager(db_manager):
    """创建财务管理器"""
    return FinanceManager(db_manager)


class TestExpenseProperties:
    """支出管理属性测试"""
    
    @settings(max_examples=50)
    @given(
        expense_type=expense_type_strategy(),
        amount=positive_decimal_strategy(),
        bank_type=bank_type_strategy(),
        expense_date=date_strategy()
    )
    def test_property_10_expense_classification_integrity(
        self, db_manager, expense_type, amount, bank_type, expense_date
    ):
        """
        **属性 10: 支出分类管理完整性**
        
        对于任何支出记录，都应该能够正确分类到十种预定义支出类型中的一种，
        并且分类信息应该在查询时保持一致
        
        **验证: 需求 3.1**
        """
        finance_manager = FinanceManager(db_manager)
        
        # 记录支出
        expense = finance_manager.record_expense(
            expense_type=expense_type,
            amount=amount,
            bank_type=bank_type,
            expense_date=expense_date,
            description=f"测试支出-{expense_type.value}"
        )
        
        # 验证支出类型正确保存
        assert expense.expense_type == expense_type
        assert expense.amount == amount
        assert expense.bank_type == bank_type
        assert expense.expense_date == expense_date
        
        # 从数据库查询验证分类一致性
        retrieved_expenses = finance_manager.get_expenses_by_type(expense_type)
        assert len(retrieved_expenses) > 0
        
        # 找到刚创建的支出
        found = False
        for exp in retrieved_expenses:
            if exp.id == expense.id:
                found = True
                assert exp.expense_type == expense_type
                assert exp.amount == amount
                break
        
        assert found, "创建的支出应该能够通过类型查询找到"
    
    @settings(max_examples=50)
    @given(
        amount=positive_decimal_strategy(min_value=100, max_value=10000),
        expense_date=date_strategy()
    )
    def test_property_11_professional_materials_recognition(
        self, db_manager, amount, expense_date
    ):
        """
        **属性 11: 专业原料识别准确性**
        
        对于任何专业原料采购（三酸、片碱、亚钠、色粉、除油剂），
        系统应该正确识别原料类型并应用相应的管理规则
        
        **验证: 需求 3.2**
        """
        finance_manager = FinanceManager(db_manager)
        
        # 专业原料类型
        professional_materials = [
            ExpenseType.ACID_THREE,
            ExpenseType.CAUSTIC_SODA,
            ExpenseType.SODIUM_SULFITE,
            ExpenseType.COLOR_POWDER,
            ExpenseType.DEGREASER
        ]
        
        # 记录专业原料支出
        for material_type in professional_materials:
            expense = finance_manager.record_expense(
                expense_type=material_type,
                amount=amount,
                bank_type=BankType.G_BANK,
                expense_date=expense_date,
                description=f"{material_type.value}采购"
            )
            
            # 验证原料类型正确识别
            assert expense.expense_type == material_type
            assert expense.expense_type in professional_materials
        
        # 获取专业原料汇总
        materials_summary = finance_manager.get_professional_materials_expenses(
            start_date=expense_date,
            end_date=expense_date
        )
        
        # 验证所有专业原料都被正确识别和汇总
        assert materials_summary["total_amount"] == amount * len(professional_materials)
        
        for material_type in professional_materials:
            material_name = material_type.value
            assert material_name in materials_summary["materials"]
            assert materials_summary["materials"][material_name]["amount"] == amount
            assert materials_summary["materials"][material_name]["count"] == 1
    
    @settings(max_examples=30)
    @given(
        num_expenses=st.integers(min_value=2, max_value=5),
        payment_amount=positive_decimal_strategy(min_value=1000, max_value=10000)
    )
    def test_property_7_payment_allocation_consistency(
        self, db_manager, num_expenses, payment_amount
    ):
        """
        **属性 7: 付款灵活分配一致性**
        
        对于任何付款分配操作，分配到各个支出记录的金额总和应该等于原始付款金额，
        且不能超过各项的金额
        
        **验证: 需求 3.4**
        """
        finance_manager = FinanceManager(db_manager)
        
        # 创建供应商
        supplier = Supplier(
            name="测试供应商",
            contact="张三",
            business_type="原料供应商"
        )
        db_manager.save_supplier(supplier)
        
        # 创建多个支出记录
        expenses = []
        for i in range(num_expenses):
            expense = finance_manager.record_expense(
                expense_type=ExpenseType.ACID_THREE,
                amount=Decimal(str(payment_amount // num_expenses)),
                bank_type=BankType.G_BANK,
                expense_date=date.today(),
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                description=f"支出{i+1}"
            )
            expenses.append(expense)
        
        # 计算分配金额（确保总和不超过付款金额）
        allocations = {}
        remaining = payment_amount
        for i, expense in enumerate(expenses):
            if i == len(expenses) - 1:
                # 最后一个分配剩余金额
                allocations[expense.id] = remaining
            else:
                # 平均分配
                allocated = payment_amount // num_expenses
                allocations[expense.id] = allocated
                remaining -= allocated
        
        # 执行付款分配
        success, message = finance_manager.allocate_payment_to_expenses(
            payment_amount=payment_amount,
            allocations=allocations,
            bank_type=BankType.G_BANK,
            payment_date=date.today()
        )
        
        # 验证分配成功
        assert success is True, f"付款分配应该成功: {message}"
        
        # 验证分配金额总和等于付款金额
        total_allocated = sum(allocations.values())
        assert total_allocated == payment_amount, \
            f"分配金额总和 {total_allocated} 应该等于付款金额 {payment_amount}"
    
    @settings(max_examples=30)
    @given(
        expense_amount=positive_decimal_strategy(min_value=100, max_value=5000),
        payment_amount=positive_decimal_strategy(min_value=100, max_value=5000)
    )
    def test_property_payment_allocation_validation(
        self, db_manager, expense_amount, payment_amount
    ):
        """
        测试付款分配验证：分配金额不能超过付款金额
        """
        assume(payment_amount < expense_amount)  # 确保付款金额小于支出金额
        
        finance_manager = FinanceManager(db_manager)
        
        # 创建支出
        expense = finance_manager.record_expense(
            expense_type=ExpenseType.ACID_THREE,
            amount=expense_amount,
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            description="测试支出"
        )
        
        # 尝试分配超过付款金额
        success, message = finance_manager.allocate_payment_to_expenses(
            payment_amount=payment_amount,
            allocations={expense.id: expense_amount},  # 分配金额大于付款金额
            bank_type=BankType.G_BANK,
            payment_date=date.today()
        )
        
        # 验证分配失败
        assert success is False
        assert "超过付款金额" in message
    
    @settings(max_examples=30)
    @given(
        num_expenses=st.integers(min_value=3, max_value=10),
        expense_date=date_strategy()
    )
    def test_property_expense_summary_accuracy(
        self, db_manager, num_expenses, expense_date
    ):
        """
        测试支出汇总准确性：按类型汇总的金额应该等于各项支出的总和
        """
        finance_manager = FinanceManager(db_manager)
        
        # 记录多笔支出
        expense_types = [ExpenseType.RENT, ExpenseType.UTILITIES, ExpenseType.ACID_THREE]
        expected_totals = {et.value: Decimal("0") for et in expense_types}
        
        for i in range(num_expenses):
            expense_type = expense_types[i % len(expense_types)]
            amount = Decimal(str((i + 1) * 100))
            
            finance_manager.record_expense(
                expense_type=expense_type,
                amount=amount,
                bank_type=BankType.G_BANK,
                expense_date=expense_date,
                description=f"支出{i+1}"
            )
            
            expected_totals[expense_type.value] += amount
        
        # 获取汇总
        summary = finance_manager.get_expense_summary_by_type(
            start_date=expense_date,
            end_date=expense_date
        )
        
        # 验证汇总准确性
        for expense_type_name, expected_amount in expected_totals.items():
            if expected_amount > 0:
                assert expense_type_name in summary
                assert summary[expense_type_name] == expected_amount, \
                    f"{expense_type_name} 汇总金额应该为 {expected_amount}，实际为 {summary.get(expense_type_name, 0)}"
    
    @settings(max_examples=30)
    @given(
        supplier_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        num_expenses=st.integers(min_value=1, max_value=5)
    )
    def test_property_supplier_payables_accuracy(
        self, db_manager, supplier_name, num_expenses
    ):
        """
        测试供应商应付账款准确性：应付账款总额应该等于所有支出的总和
        """
        finance_manager = FinanceManager(db_manager)
        
        # 创建供应商
        supplier = Supplier(
            name=supplier_name,
            contact="测试联系人",
            business_type="原料供应商"
        )
        db_manager.save_supplier(supplier)
        
        # 记录多笔支出
        total_expected = Decimal("0")
        for i in range(num_expenses):
            amount = Decimal(str((i + 1) * 500))
            finance_manager.record_expense(
                expense_type=ExpenseType.ACID_THREE,
                amount=amount,
                bank_type=BankType.G_BANK,
                expense_date=date.today(),
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                description=f"支出{i+1}"
            )
            total_expected += amount
        
        # 获取应付账款
        payables = finance_manager.get_supplier_payables(supplier.id)
        
        # 验证应付账款准确性
        assert payables["total_amount"] == total_expected
        assert payables["expense_count"] == num_expenses
        assert len(payables["expense_details"]) == num_expenses
    
    @settings(max_examples=30)
    @given(
        start_offset=st.integers(min_value=-30, max_value=-1),
        end_offset=st.integers(min_value=0, max_value=30)
    )
    def test_property_date_filter_accuracy(
        self, db_manager, start_offset, end_offset
    ):
        """
        测试日期过滤准确性：按日期过滤的结果应该只包含指定日期范围内的支出
        """
        finance_manager = FinanceManager(db_manager)
        
        today = date.today()
        start_date = today + timedelta(days=start_offset)
        end_date = today + timedelta(days=end_offset)
        
        # 记录不同日期的支出
        in_range_amount = Decimal("0")
        out_range_amount = Decimal("0")
        
        # 范围内的支出
        for i in range(3):
            amount = Decimal(str((i + 1) * 100))
            expense_date = start_date + timedelta(days=i % (end_offset - start_offset + 1))
            finance_manager.record_expense(
                expense_type=ExpenseType.RENT,
                amount=amount,
                bank_type=BankType.G_BANK,
                expense_date=expense_date,
                description=f"范围内支出{i+1}"
            )
            in_range_amount += amount
        
        # 范围外的支出
        out_date = start_date - timedelta(days=10)
        out_amount = Decimal("500")
        finance_manager.record_expense(
            expense_type=ExpenseType.RENT,
            amount=out_amount,
            bank_type=BankType.G_BANK,
            expense_date=out_date,
            description="范围外支出"
        )
        out_range_amount += out_amount
        
        # 获取过滤后的汇总
        summary = finance_manager.get_expense_summary_by_type(
            start_date=start_date,
            end_date=end_date
        )
        
        # 验证只包含范围内的支出
        if "房租" in summary:
            assert summary["房租"] == in_range_amount, \
                f"日期过滤后的金额应该为 {in_range_amount}，不应包含范围外的 {out_range_amount}"
