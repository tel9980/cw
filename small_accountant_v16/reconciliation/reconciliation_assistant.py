"""
Reconciliation Assistant for V1.6 Small Accountant Practical Enhancement

This module implements the ReconciliationAssistant class that provides a unified
interface for bank reconciliation, customer statements, and supplier reconciliation.
It integrates BankStatementMatcher and ReconciliationReportGenerator to provide
a simple, easy-to-use interface for small accountants.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pathlib import Path
import logging

import pandas as pd
from openpyxl import load_workbook

from small_accountant_v16.models.core_models import (
    BankRecord,
    TransactionRecord,
    ReconciliationResult,
    Counterparty,
    CounterpartyType,
    TransactionType,
    Discrepancy
)
from small_accountant_v16.reconciliation.bank_statement_matcher import (
    BankStatementMatcher,
    MatchConfig
)
from small_accountant_v16.reconciliation.reconciliation_report_generator import (
    ReconciliationReportGenerator,
    CustomerAccountData
)
from small_accountant_v16.storage.transaction_storage import TransactionStorage
from small_accountant_v16.storage.counterparty_storage import CounterpartyStorage

logger = logging.getLogger(__name__)


class ReconciliationAssistant:
    """
    快速对账助手
    
    提供简单易用的对账功能，包括：
    1. 银行对账：导入银行流水并自动匹配系统记录
    2. 客户对账单：生成专业的客户对账单Excel文件
    3. 供应商对账：核对采购订单和付款记录
    
    设计原则：
    - 简单易用：不需要专业IT知识
    - 自动化：自动匹配和识别差异
    - 专业输出：生成格式化的Excel报表
    """
    
    def __init__(
        self,
        transaction_storage: Optional[TransactionStorage] = None,
        counterparty_storage: Optional[CounterpartyStorage] = None,
        output_dir: Optional[str] = None,
        match_config: Optional[MatchConfig] = None
    ):
        """
        初始化对账助手
        
        Args:
            transaction_storage: 交易记录存储，如果为None则创建新实例
            counterparty_storage: 往来单位存储，如果为None则创建新实例
            output_dir: 报表输出目录，如果为None则使用当前目录
            match_config: 匹配配置，如果为None则使用默认配置
        """
        self.transaction_storage = transaction_storage or TransactionStorage()
        self.counterparty_storage = counterparty_storage or CounterpartyStorage()
        self.output_dir = Path(output_dir) if output_dir else Path(".")
        
        # 初始化匹配器和报告生成器
        self.matcher = BankStatementMatcher(match_config)
        self.report_generator = ReconciliationReportGenerator(str(self.output_dir))
        
        logger.info("对账助手初始化完成")
    
    def reconcile_bank_statement(
        self,
        bank_statement_file: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> ReconciliationResult:
        """
        银行对账
        
        导入银行流水Excel文件，自动匹配系统交易记录，识别差异并生成报告。
        
        Args:
            bank_statement_file: 银行流水Excel文件路径
            start_date: 对账开始日期（可选，用于过滤系统记录）
            end_date: 对账结束日期（可选，用于过滤系统记录）
        
        Returns:
            ReconciliationResult: 对账结果，包含匹配信息和差异列表
        
        Raises:
            FileNotFoundError: 如果银行流水文件不存在
            ValueError: 如果文件格式不正确
        """
        logger.info(f"开始银行对账: {bank_statement_file}")
        
        # 1. 读取银行流水
        bank_records = self._load_bank_statement(bank_statement_file)
        logger.info(f"读取银行流水记录: {len(bank_records)} 条")
        
        # 2. 获取系统交易记录
        if start_date and end_date:
            system_records = self.transaction_storage.get_by_date_range(
                start_date, end_date
            )
        else:
            # 如果没有指定日期范围，使用银行流水的日期范围
            if bank_records:
                min_date = min(r.transaction_date for r in bank_records)
                max_date = max(r.transaction_date for r in bank_records)
                system_records = self.transaction_storage.get_by_date_range(
                    min_date, max_date
                )
            else:
                system_records = []
        
        logger.info(f"获取系统交易记录: {len(system_records)} 条")
        
        # 3. 执行匹配
        match_result = self.matcher.match_transactions(bank_records, system_records)
        logger.info(
            f"匹配完成: 匹配 {match_result.matched_count} 条, "
            f"未匹配银行流水 {len(match_result.unmatched_bank_records)} 条, "
            f"未匹配系统记录 {len(match_result.unmatched_system_records)} 条"
        )
        
        # 4. 识别差异
        discrepancies = self.matcher.identify_discrepancies(match_result)
        logger.info(f"识别差异: {len(discrepancies)} 条")
        
        # 5. 生成差异报告
        report_path = self.report_generator.save_discrepancy_report(discrepancies)
        logger.info(f"差异报告已生成: {report_path}")
        
        # 6. 构建对账结果
        result = ReconciliationResult(
            matched_count=match_result.matched_count,
            unmatched_bank_records=match_result.unmatched_bank_records,
            unmatched_system_records=match_result.unmatched_system_records,
            discrepancies=discrepancies,
            reconciliation_date=datetime.now()
        )
        
        logger.info("银行对账完成")
        return result
    
    def generate_customer_statement(
        self,
        customer_id: str,
        start_date: date,
        end_date: date,
        opening_balance: Optional[Decimal] = None
    ) -> str:
        """
        生成客户对账单
        
        生成指定客户在指定期间的对账单Excel文件，可直接发送给客户。
        
        Args:
            customer_id: 客户ID
            start_date: 对账开始日期
            end_date: 对账结束日期
            opening_balance: 期初余额（可选，如果为None则默认为0）
        
        Returns:
            str: 生成的对账单文件路径
        
        Raises:
            ValueError: 如果客户不存在或不是客户类型
        """
        logger.info(f"开始生成客户对账单: {customer_id}")
        
        # 1. 获取客户信息
        customer = self.counterparty_storage.get(customer_id)
        if not customer:
            raise ValueError(f"客户不存在: {customer_id}")
        
        if customer.type != CounterpartyType.CUSTOMER:
            raise ValueError(f"往来单位不是客户类型: {customer_id}")
        
        # 2. 获取客户交易记录
        all_transactions = self.transaction_storage.get_by_counterparty(customer_id)
        
        # 过滤日期范围
        transactions = [
            t for t in all_transactions
            if start_date <= t.date <= end_date
        ]
        
        # 按日期排序
        transactions.sort(key=lambda t: t.date)
        
        logger.info(f"获取客户交易记录: {len(transactions)} 条")
        
        # 3. 计算期初余额和期末余额
        if opening_balance is None:
            opening_balance = Decimal('0')
        
        closing_balance = opening_balance
        for transaction in transactions:
            if transaction.type == TransactionType.INCOME:
                closing_balance += transaction.amount
            else:  # EXPENSE
                closing_balance -= transaction.amount
        
        # 4. 构建客户对账数据
        customer_data = CustomerAccountData(
            customer=customer,
            transactions=transactions,
            start_date=start_date,
            end_date=end_date,
            opening_balance=opening_balance,
            closing_balance=closing_balance
        )
        
        # 5. 生成对账单
        report_path = self.report_generator.save_customer_statement(customer_data)
        logger.info(f"客户对账单已生成: {report_path}")
        
        return report_path
    
    def reconcile_supplier_accounts(
        self,
        supplier_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> ReconciliationResult:
        """
        供应商对账
        
        核对指定供应商的采购订单和付款记录，识别未付款订单和差异。
        
        Args:
            supplier_id: 供应商ID
            start_date: 对账开始日期（可选）
            end_date: 对账结束日期（可选）
        
        Returns:
            ReconciliationResult: 对账结果，包含匹配信息和差异列表
        
        Raises:
            ValueError: 如果供应商不存在或不是供应商类型
        """
        logger.info(f"开始供应商对账: {supplier_id}")
        
        # 1. 获取供应商信息
        supplier = self.counterparty_storage.get(supplier_id)
        if not supplier:
            raise ValueError(f"供应商不存在: {supplier_id}")
        
        if supplier.type != CounterpartyType.SUPPLIER:
            raise ValueError(f"往来单位不是供应商类型: {supplier_id}")
        
        # 2. 获取供应商相关交易记录
        all_transactions = self.transaction_storage.get_by_counterparty(supplier_id)
        
        # 过滤日期范围
        if start_date and end_date:
            transactions = [
                t for t in all_transactions
                if start_date <= t.date <= end_date
            ]
        else:
            transactions = all_transactions
        
        # 3. 分离订单和付款记录
        orders = [t for t in transactions if t.type == TransactionType.ORDER]
        payments = [t for t in transactions if t.type == TransactionType.EXPENSE]
        
        logger.info(f"订单记录: {len(orders)} 条, 付款记录: {len(payments)} 条")
        
        # 4. 匹配订单和付款
        # 将订单转换为类似银行记录的格式，付款转换为系统记录格式
        # 这样可以复用银行对账的匹配逻辑
        order_records = [
            BankRecord(
                id=order.id,
                transaction_date=order.date,
                description=order.description,
                amount=order.amount,
                balance=Decimal('0'),  # 不使用余额字段
                transaction_type='DEBIT',
                counterparty=supplier.name
            )
            for order in orders
        ]
        
        payment_records = payments  # 付款记录直接使用
        
        # 5. 执行匹配
        match_result = self.matcher.match_transactions(order_records, payment_records)
        logger.info(
            f"匹配完成: 匹配 {match_result.matched_count} 条, "
            f"未付款订单 {len(match_result.unmatched_bank_records)} 条, "
            f"未匹配付款 {len(match_result.unmatched_system_records)} 条"
        )
        
        # 6. 识别差异
        discrepancies = self.matcher.identify_discrepancies(match_result)
        
        # 修改差异描述，使其更适合供应商对账
        for disc in discrepancies:
            if disc.bank_record:  # 未付款订单
                disc.description = (
                    f"未付款订单：订单日期 {disc.bank_record.transaction_date} "
                    f"{disc.bank_record.description} {disc.bank_record.amount}，"
                    f"尚未找到对应付款记录"
                )
            elif disc.system_record:  # 未匹配订单的付款
                disc.description = (
                    f"未匹配订单的付款：付款日期 {disc.system_record.date} "
                    f"{disc.system_record.description} {disc.system_record.amount}，"
                    f"未找到对应订单记录"
                )
        
        logger.info(f"识别差异: {len(discrepancies)} 条")
        
        # 7. 生成差异报告
        if discrepancies:
            report_path = self.report_generator.save_discrepancy_report(
                discrepancies,
                filename=f'供应商对账报告_{supplier.name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
            logger.info(f"供应商对账报告已生成: {report_path}")
        
        # 8. 构建对账结果
        result = ReconciliationResult(
            matched_count=match_result.matched_count,
            unmatched_bank_records=match_result.unmatched_bank_records,
            unmatched_system_records=match_result.unmatched_system_records,
            discrepancies=discrepancies,
            reconciliation_date=datetime.now()
        )
        
        logger.info("供应商对账完成")
        return result
    
    def _load_bank_statement(self, file_path: str) -> List[BankRecord]:
        """
        从Excel文件加载银行流水
        
        支持常见的银行流水格式，自动识别列名。
        
        Args:
            file_path: Excel文件路径
        
        Returns:
            List[BankRecord]: 银行流水记录列表
        
        Raises:
            FileNotFoundError: 如果文件不存在
            ValueError: 如果文件格式不正确
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"银行流水文件不存在: {file_path}")
        
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 识别列名（支持常见的列名变体）
            column_mapping = self._recognize_bank_statement_columns(df.columns.tolist())
            
            # 验证必需列
            required_fields = ['date', 'amount', 'counterparty']
            missing_fields = [f for f in required_fields if f not in column_mapping]
            if missing_fields:
                raise ValueError(
                    f"银行流水文件缺少必需列: {missing_fields}。"
                    f"请确保文件包含日期、金额和往来单位列。"
                )
            
            # 转换为BankRecord对象
            bank_records = []
            for idx, row in df.iterrows():
                try:
                    # 提取字段
                    transaction_date = pd.to_datetime(
                        row[column_mapping['date']]
                    ).date()
                    
                    amount = Decimal(str(row[column_mapping['amount']]))
                    
                    counterparty = str(row[column_mapping['counterparty']])
                    
                    # 可选字段
                    description = str(row[column_mapping.get('description', column_mapping['counterparty'])])
                    
                    balance = Decimal('0')
                    if 'balance' in column_mapping:
                        balance = Decimal(str(row[column_mapping['balance']]))
                    
                    transaction_type = 'DEBIT'
                    if 'type' in column_mapping:
                        type_value = str(row[column_mapping['type']]).upper()
                        if '收入' in type_value or 'CREDIT' in type_value:
                            transaction_type = 'CREDIT'
                    
                    # 创建BankRecord
                    bank_record = BankRecord(
                        id=f"BANK-{idx+1:06d}",
                        transaction_date=transaction_date,
                        description=description,
                        amount=amount,
                        balance=balance,
                        transaction_type=transaction_type,
                        counterparty=counterparty
                    )
                    
                    bank_records.append(bank_record)
                    
                except Exception as e:
                    logger.warning(f"跳过第 {idx+2} 行（解析错误）: {e}")
                    continue
            
            if not bank_records:
                raise ValueError("银行流水文件中没有有效的记录")
            
            return bank_records
            
        except Exception as e:
            raise ValueError(f"读取银行流水文件失败: {e}")
    
    def _recognize_bank_statement_columns(self, columns: List[str]) -> dict:
        """
        识别银行流水Excel的列名
        
        支持常见的列名变体，如"日期"、"交易日期"、"时间"等。
        
        Args:
            columns: Excel列名列表
        
        Returns:
            dict: 列名映射 {标准字段名: Excel列名}
        """
        mapping = {}
        
        # 标准化列名（转小写，去空格）
        normalized_columns = {col: col.strip().lower() for col in columns}
        
        # 日期列的可能名称
        date_patterns = ['日期', '交易日期', '时间', 'date', 'transaction_date', 'trans_date']
        for pattern in date_patterns:
            for col, norm_col in normalized_columns.items():
                if pattern in norm_col:
                    mapping['date'] = col
                    break
            if 'date' in mapping:
                break
        
        # 金额列的可能名称
        amount_patterns = ['金额', '交易金额', '发生额', 'amount', 'transaction_amount']
        for pattern in amount_patterns:
            for col, norm_col in normalized_columns.items():
                if pattern in norm_col:
                    mapping['amount'] = col
                    break
            if 'amount' in mapping:
                break
        
        # 往来单位列的可能名称
        counterparty_patterns = ['往来单位', '对方户名', '对方账户', '交易对手', 'counterparty', 'payee', 'payer']
        for pattern in counterparty_patterns:
            for col, norm_col in normalized_columns.items():
                if pattern in norm_col:
                    mapping['counterparty'] = col
                    break
            if 'counterparty' in mapping:
                break
        
        # 描述列的可能名称
        description_patterns = ['摘要', '备注', '说明', 'description', 'memo', 'remark']
        for pattern in description_patterns:
            for col, norm_col in normalized_columns.items():
                if pattern in norm_col:
                    mapping['description'] = col
                    break
            if 'description' in mapping:
                break
        
        # 余额列的可能名称
        balance_patterns = ['余额', '账户余额', 'balance', 'account_balance']
        for pattern in balance_patterns:
            for col, norm_col in normalized_columns.items():
                if pattern in norm_col:
                    mapping['balance'] = col
                    break
            if 'balance' in mapping:
                break
        
        # 交易类型列的可能名称
        type_patterns = ['类型', '交易类型', '收支', 'type', 'transaction_type']
        for pattern in type_patterns:
            for col, norm_col in normalized_columns.items():
                if pattern in norm_col:
                    mapping['type'] = col
                    break
            if 'type' in mapping:
                break
        
        return mapping
