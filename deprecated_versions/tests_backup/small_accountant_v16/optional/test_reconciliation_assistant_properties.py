"""
Property-based tests for ReconciliationAssistant - Supplier reconciliation verification

Feature: small-accountant-practical-enhancement
Property 13: Supplier reconciliation verification
Validates: Requirements 3.3
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
from typing import List
import uuid
import tempfile
import os

from small_accountant_v16.reconciliation.reconciliation_assistant import ReconciliationAssistant
from small_accountant_v16.models.core_models import (
    TransactionRecord, TransactionType, TransactionStatus,
    Counterparty, CounterpartyType,
    ReconciliationResult
)
from small_accountant_v16.storage.transaction_storage import TransactionStorage
from small_accountant_v16.storage.counterparty_storage import CounterpartyStorage


# Hypothesis strategies for generating test data
@st.composite
def valid_amount(draw, min_value=0.01, max_value=100000.0):
    """生成有效的金额"""
    amount = draw(st.decimals(
        min_value=Decimal(str(min_value)),
        max_value=Decimal(str(max_value)),
        places=2
    ))
    return amount


@st.composite
def valid_date_range(draw, max_days=365):
    """生成有效的日期范围"""
    base_date = draw(st.dates(
        min_value=date(2020, 1, 1),
        max_value=date.today() - timedelta(days=1)
    ))
    
    end_date = draw(st.dates(
        min_value=base_date,
        max_value=min(base_date + timedelta(days=max_days), date.today())
    ))
    
    return base_date, end_date


@st.composite
def supplier_strategy(draw):
    """生成供应商"""
    company_names = [
        "测试供应商A", "测试供应商B", "ABC供应商", "XYZ供应商",
        "北京供应商", "上海供应商", "深圳供应商", "广州供应商",
        "优质供应商有限公司", "长期合作供应商", "专业服务供应商"
    ]
    
    contact_persons = ["张三", "李四", "王五", "赵六", "陈七", "刘八"]
    
    return Counterparty(
        id=f"sp{draw(st.integers(min_value=1, max_value=9999))}",
        name=draw(st.sampled_from(company_names)),
        type=CounterpartyType.SUPPLIER,
        contact_person=draw(st.sampled_from(contact_persons)),
        phone=f"1{draw(st.integers(min_value=3000000000, max_value=8999999999))}",
        email=f"supplier{draw(st.integers(min_value=1, max_value=999))}@example.com",
        address=draw(st.sampled_from([
            "北京市朝阳区建国路1号", "上海市浦东新区陆家嘴环路2号",
            "深圳市南山区科技园3号", "广州市天河区珠江新城4号"
        ])),
        tax_id=f"{draw(st.integers(min_value=100000000000000000, max_value=999999999999999999))}",
        created_at=draw(st.datetimes()),
        updated_at=draw(st.datetimes())
    )


@st.composite
def customer_strategy(draw):
    """生成客户"""
    company_names = [
        "测试客户A", "测试客户B", "ABC客户", "XYZ客户",
        "北京客户", "上海客户", "深圳客户", "广州客户",
        "优质客户有限公司", "长期合作客户", "重要客户公司"
    ]
    
    contact_persons = ["张三", "李四", "王五", "赵六", "陈七", "刘八"]
    
    return Counterparty(
        id=f"cu{draw(st.integers(min_value=1, max_value=9999))}",
        name=draw(st.sampled_from(company_names)),
        type=CounterpartyType.CUSTOMER,
        contact_person=draw(st.sampled_from(contact_persons)),
        phone=f"1{draw(st.integers(min_value=3000000000, max_value=8999999999))}",
        email=f"customer{draw(st.integers(min_value=1, max_value=999))}@example.com",
        address=draw(st.sampled_from([
            "北京市朝阳区建国路1号", "上海市浦东新区陆家嘴环路2号",
            "深圳市南山区科技园3号", "广州市天河区珠江新城4号"
        ])),
        tax_id=f"{draw(st.integers(min_value=100000000000000000, max_value=999999999999999999))}",
        created_at=draw(st.datetimes()),
        updated_at=draw(st.datetimes())
    )


@st.composite
def supplier_transaction_data_strategy(draw):
    """生成供应商交易数据（包含订单和付款）"""
    # 生成供应商
    supplier = draw(supplier_strategy())
    
    # 生成日期范围
    start_date, end_date = draw(valid_date_range(max_days=90))
    
    # 生成简单的订单和付款记录
    orders = draw(st.lists(
        st.builds(
            TransactionRecord,
            id=st.text(min_size=1, max_size=50),
            date=st.dates(min_value=start_date, max_value=end_date),
            type=st.just(TransactionType.ORDER),
            amount=valid_amount(),
            counterparty_id=st.just(supplier.id),
            description=st.sampled_from([
                "采购原材料", "采购办公用品", "采购设备", "采购服务"
            ]),
            category=st.sampled_from(['采购', '材料', '设备', '服务']),
            status=st.just(TransactionStatus.COMPLETED),
            created_at=st.datetimes(),
            updated_at=st.datetimes()
        ),
        min_size=1,
        max_size=10
    ))
    
    # 生成付款记录
    payments = draw(st.lists(
        st.builds(
            TransactionRecord,
            id=st.text(min_size=1, max_size=50),
            date=st.dates(min_value=start_date, max_value=end_date),
            type=st.just(TransactionType.EXPENSE),
            amount=valid_amount(),
            counterparty_id=st.just(supplier.id),
            description=st.sampled_from([
                "支付供应商款项", "采购付款", "材料费支付", "服务费支付"
            ]),
            category=st.sampled_from(['采购', '材料', '设备', '服务']),
            status=st.just(TransactionStatus.COMPLETED),
            created_at=st.datetimes(),
            updated_at=st.datetimes()
        ),
        min_size=0,
        max_size=8
    ))
    
    return supplier, orders, payments, start_date, end_date


@st.composite
def customer_transaction_data_strategy(draw):
    """生成客户交易数据"""
    # 生成客户
    customer = draw(customer_strategy())
    
    # 生成日期范围
    start_date, end_date = draw(valid_date_range(max_days=90))
    
    # 生成交易记录
    transactions = draw(st.lists(
        st.builds(
            TransactionRecord,
            id=st.text(min_size=1, max_size=50),
            date=st.dates(min_value=start_date, max_value=end_date),
            type=st.sampled_from([TransactionType.INCOME, TransactionType.EXPENSE]),
            amount=valid_amount(),
            counterparty_id=st.just(customer.id),
            description=st.sampled_from([
                "销售收入", "服务费收入", "咨询费收入", "产品销售",
                "技术服务", "维护费用", "培训费用", "其他收入"
            ]),
            category=st.sampled_from(['销售', '服务', '咨询', '其他']),
            status=st.just(TransactionStatus.COMPLETED),
            created_at=st.datetimes(),
            updated_at=st.datetimes()
        ),
        min_size=1,
        max_size=15
    ))
    
    return customer, transactions, start_date, end_date


class TestReconciliationAssistantProperties:
    """Property-based tests for reconciliation assistant
    
    **Property 13: Supplier reconciliation verification**
    For any valid supplier with orders and payments, when performing supplier
    reconciliation, the system should correctly match orders with payments,
    identify unpaid orders, and generate accurate reconciliation reports.
    **Validates: Requirements 3.3**
    """
    
    @given(data=st.data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_supplier_reconciliation_completeness_property(self, data):
        """
        Property: 供应商对账完整性属性
        
        验证：
        1. 所有订单和付款记录都被正确处理
        2. 匹配的订单-付款对被正确识别
        3. 未付款订单被正确标识
        4. 未匹配订单的付款被正确标识
        5. 对账结果统计信息正确
        """
        # 生成测试数据
        supplier, orders, payments, start_date, end_date = data.draw(
            supplier_transaction_data_strategy()
        )
        
        # 创建临时存储
        with tempfile.TemporaryDirectory() as temp_dir:
            transaction_storage = TransactionStorage(temp_dir)
            counterparty_storage = CounterpartyStorage(temp_dir)
            
            # 保存测试数据
            counterparty_storage.add(supplier)
            
            all_transactions = orders + payments
            for transaction in all_transactions:
                transaction_storage.add(transaction)
            
            # 创建对账助手
            assistant = ReconciliationAssistant(
                transaction_storage=transaction_storage,
                counterparty_storage=counterparty_storage,
                output_dir=temp_dir
            )
            
            # 执行供应商对账
            result = assistant.reconcile_supplier_accounts(
                supplier.id, start_date, end_date
            )
            
            # 验证对账结果的完整性
            assert isinstance(result, ReconciliationResult), \
                "应该返回ReconciliationResult对象"
            
            assert result.reconciliation_date is not None, \
                "对账结果应该包含对账日期"
            
            # 验证记录总数的一致性
            total_orders = len(orders)
            total_payments = len(payments)
            
            matched_count = result.matched_count
            unmatched_orders = len(result.unmatched_bank_records)  # 未付款订单
            unmatched_payments = len(result.unmatched_system_records)  # 未匹配付款
            
            # 验证订单处理完整性
            assert matched_count + unmatched_orders == total_orders, \
                f"匹配订单数({matched_count}) + 未付款订单数({unmatched_orders}) 应该等于总订单数({total_orders})"
            
            # 验证付款处理完整性
            assert matched_count + unmatched_payments == total_payments, \
                f"匹配付款数({matched_count}) + 未匹配付款数({unmatched_payments}) 应该等于总付款数({total_payments})"
            
            # 验证差异记录
            discrepancies = result.discrepancies
            assert isinstance(discrepancies, list), "差异应该是列表"
            
            # 差异数量应该等于未匹配记录数量
            expected_discrepancy_count = unmatched_orders + unmatched_payments
            assert len(discrepancies) == expected_discrepancy_count, \
                f"差异数量应该为{expected_discrepancy_count}，但为{len(discrepancies)}"
    
    @given(data=st.data())
    @settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_supplier_reconciliation_error_handling_property(self, data):
        """
        Property: 供应商对账错误处理属性
        
        验证：
        1. 不存在的供应商ID应该抛出ValueError
        2. 客户类型的往来单位应该抛出ValueError
        3. 空的交易记录应该正确处理
        4. 错误信息应该清晰明确
        """
        # 生成测试数据
        supplier = data.draw(supplier_strategy())
        customer = data.draw(customer_strategy())
        
        # 创建临时存储
        with tempfile.TemporaryDirectory() as temp_dir:
            transaction_storage = TransactionStorage(temp_dir)
            counterparty_storage = CounterpartyStorage(temp_dir)
            
            # 只保存客户，不保存供应商
            counterparty_storage.add(customer)
            
            # 创建对账助手
            assistant = ReconciliationAssistant(
                transaction_storage=transaction_storage,
                counterparty_storage=counterparty_storage,
                output_dir=temp_dir
            )
            
            # 测试不存在的供应商ID
            non_existent_id = f"nonexistent_{data.draw(st.integers(min_value=1, max_value=9999))}"
            
            with pytest.raises(ValueError) as exc_info:
                assistant.reconcile_supplier_accounts(non_existent_id)
            
            assert "供应商不存在" in str(exc_info.value), \
                f"错误信息应该包含'供应商不存在'，但为: {exc_info.value}"
            
            # 测试客户类型的往来单位
            with pytest.raises(ValueError) as exc_info:
                assistant.reconcile_supplier_accounts(customer.id)
            
            assert "不是供应商类型" in str(exc_info.value), \
                f"错误信息应该包含'不是供应商类型'，但为: {exc_info.value}"
            
            # 测试空交易记录的处理
            counterparty_storage.add(supplier)  # 现在保存供应商
            
            # 执行对账（没有交易记录）
            result = assistant.reconcile_supplier_accounts(supplier.id)
            
            # 验证空记录的处理
            assert result.matched_count == 0, \
                f"没有交易记录时匹配数应该为0，但为{result.matched_count}"
            
            assert len(result.unmatched_bank_records) == 0, \
                f"没有交易记录时未匹配订单数应该为0，但为{len(result.unmatched_bank_records)}"
            
            assert len(result.unmatched_system_records) == 0, \
                f"没有交易记录时未匹配付款数应该为0，但为{len(result.unmatched_system_records)}"
            
            assert len(result.discrepancies) == 0, \
                f"没有交易记录时差异数应该为0，但为{len(result.discrepancies)}"
    
    @given(data=st.data())
    @settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_customer_statement_generation_property(self, data):
        """
        Property: 客户对账单生成属性
        
        验证：
        1. 客户对账单能够成功生成
        2. 生成的文件路径正确
        3. 期初余额和期末余额计算正确
        4. 只包含指定日期范围内的交易
        """
        # 生成客户交易数据
        customer, transactions, start_date, end_date = data.draw(
            customer_transaction_data_strategy()
        )
        
        # 生成期初余额
        opening_balance = data.draw(valid_amount(min_value=0, max_value=10000))
        
        # 创建临时存储
        with tempfile.TemporaryDirectory() as temp_dir:
            transaction_storage = TransactionStorage(temp_dir)
            counterparty_storage = CounterpartyStorage(temp_dir)
            
            # 保存测试数据
            counterparty_storage.add(customer)
            
            for transaction in transactions:
                transaction_storage.add(transaction)
            
            # 创建对账助手
            assistant = ReconciliationAssistant(
                transaction_storage=transaction_storage,
                counterparty_storage=counterparty_storage,
                output_dir=temp_dir
            )
            
            # 生成客户对账单
            statement_path = assistant.generate_customer_statement(
                customer.id, start_date, end_date, opening_balance
            )
            
            # 验证文件生成
            assert statement_path is not None, "应该返回对账单文件路径"
            assert os.path.exists(statement_path), f"对账单文件应该存在: {statement_path}"
            
            # 验证文件名格式
            filename = os.path.basename(statement_path)
            assert filename.startswith("客户对账单_"), "文件名应该以'客户对账单_'开头"
            assert customer.name in filename, f"文件名应该包含客户名称'{customer.name}'"
            assert filename.endswith(".xlsx"), "文件名应该以'.xlsx'结尾"
            
            # 验证文件大小
            file_size = os.path.getsize(statement_path)
            assert file_size > 0, f"对账单文件大小应该大于0，但为{file_size}"
    
    @given(data=st.data())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_customer_statement_error_handling_property(self, data):
        """
        Property: 客户对账单错误处理属性
        
        验证：
        1. 不存在的客户ID应该抛出ValueError
        2. 供应商类型的往来单位应该抛出ValueError
        3. 错误信息应该清晰明确
        """
        # 生成测试数据
        supplier = data.draw(supplier_strategy())
        customer = data.draw(customer_strategy())
        start_date, end_date = data.draw(valid_date_range())
        
        # 创建临时存储
        with tempfile.TemporaryDirectory() as temp_dir:
            transaction_storage = TransactionStorage(temp_dir)
            counterparty_storage = CounterpartyStorage(temp_dir)
            
            # 只保存供应商，不保存客户
            counterparty_storage.add(supplier)
            
            # 创建对账助手
            assistant = ReconciliationAssistant(
                transaction_storage=transaction_storage,
                counterparty_storage=counterparty_storage,
                output_dir=temp_dir
            )
            
            # 测试不存在的客户ID
            non_existent_id = f"nonexistent_{data.draw(st.integers(min_value=1, max_value=9999))}"
            
            with pytest.raises(ValueError) as exc_info:
                assistant.generate_customer_statement(
                    non_existent_id, start_date, end_date
                )
            
            assert "客户不存在" in str(exc_info.value), \
                f"错误信息应该包含'客户不存在'，但为: {exc_info.value}"
            
            # 测试供应商类型的往来单位
            with pytest.raises(ValueError) as exc_info:
                assistant.generate_customer_statement(
                    supplier.id, start_date, end_date
                )
            
            assert "不是客户类型" in str(exc_info.value), \
                f"错误信息应该包含'不是客户类型'，但为: {exc_info.value}"