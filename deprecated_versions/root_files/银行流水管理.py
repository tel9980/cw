# -*- coding: utf-8 -*-
"""
银行流水管理模块
处理银行流水导入、对账、分析等功能
"""

import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from 财务数据管理器 import financial_manager

class BankStatementManager:
    """银行流水管理器"""
    
    def __init__(self):
        self.data_dir = "财务数据/银行流水"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def import_from_excel(self, file_path: str, bank_name: str) -> Tuple[bool, str]:
        """从Excel导入银行流水"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 标准化列名（根据不同银行的格式调整）
            column_mapping = {
                '交易日期': 'date',
                '日期': 'date', 
                '交易时间': 'time',
                '时间': 'time',
                '摘要': 'description',
                '交易摘要': 'description',
                '用途': 'description',
                '收入': 'income',
                '收入金额': 'income',
                '支出': 'expense', 
                '支出金额': 'expense',
                '余额': 'balance',
                '账户余额': 'balance',
                '对方账号': 'counterpart_account',
                '对方户名': 'counterpart_name'
            }
            
            # 重命名列
            df = df.rename(columns=column_mapping)
            
            # 数据清洗和转换
            statements = []
            for _, row in df.iterrows():
                statement = {
                    'bank_name': bank_name,
                    'date': self._parse_date(row.get('date')),
                    'time': str(row.get('time', '')),
                    'description': str(row.get('description', '')),
                    'income': self._parse_amount(row.get('income', 0)),
                    'expense': self._parse_amount(row.get('expense', 0)),
                    'balance': self._parse_amount(row.get('balance', 0)),
                    'counterpart_account': str(row.get('counterpart_account', '')),
                    'counterpart_name': str(row.get('counterpart_name', '')),
                    'imported_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'matched': False,  # 是否已对账
                    'category': '',   # 分类
                    'remark': ''      # 备注
                }
                
                # 计算交易金额和类型
                if statement['income'] > 0:
                    statement['amount'] = statement['income']
                    statement['type'] = '收入'
                elif statement['expense'] > 0:
                    statement['amount'] = statement['expense']
                    statement['type'] = '支出'
                else:
                    continue  # 跳过无金额的记录
                
                statements.append(statement)
            
            # 保存到文件
            if statements:
                existing_statements = financial_manager.load_bank_statements(bank_name)
                all_statements = existing_statements + statements
                
                if financial_manager.save_bank_statements(all_statements, bank_name):
                    return True, f"成功导入 {len(statements)} 条银行流水记录"
                else:
                    return False, "保存银行流水失败"
            else:
                return False, "未找到有效的银行流水数据"
                
        except Exception as e:
            return False, f"导入失败：{str(e)}"
    
    def _parse_date(self, date_value) -> str:
        """解析日期"""
        if pd.isna(date_value):
            return ""
        
        try:
            if isinstance(date_value, str):
                # 尝试不同的日期格式
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        dt = datetime.strptime(date_value, fmt)
                        return dt.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            elif hasattr(date_value, 'strftime'):
                return date_value.strftime('%Y-%m-%d')
        except:
            pass
        
        return str(date_value)
    
    def _parse_amount(self, amount_value) -> float:
        """解析金额"""
        if pd.isna(amount_value):
            return 0.0
        
        try:
            # 移除货币符号和逗号
            if isinstance(amount_value, str):
                amount_str = amount_value.replace('¥', '').replace(',', '').replace('￥', '')
                return float(amount_str)
            else:
                return float(amount_value)
        except:
            return 0.0
    
    def auto_match_transactions(self, bank_name: str) -> Dict:
        """自动对账 - 匹配银行流水和收支记录"""
        try:
            # 获取银行流水
            statements = financial_manager.load_bank_statements(bank_name)
            
            # 获取收支记录
            transactions = financial_manager.load_transactions()
            
            matched_count = 0
            unmatched_statements = []
            unmatched_transactions = []
            
            # 对账逻辑
            for statement in statements:
                if statement.get('matched'):
                    continue  # 已经对账的跳过
                
                matched = False
                statement_date = statement.get('date', '')
                statement_amount = statement.get('amount', 0)
                statement_type = statement.get('type', '')
                
                # 在收支记录中查找匹配项
                for transaction in transactions:
                    if transaction.get('matched'):
                        continue  # 已经对账的跳过
                    
                    trans_date = transaction.get('date', '')
                    trans_amount = transaction.get('amount', 0)
                    trans_type = transaction.get('type', '')
                    
                    # 匹配条件：日期相近、金额相等、类型相同
                    date_diff = abs((datetime.strptime(statement_date, '%Y-%m-%d') - 
                                   datetime.strptime(trans_date, '%Y-%m-%d')).days)
                    
                    if (date_diff <= 2 and  # 日期差不超过2天
                        abs(statement_amount - trans_amount) < 0.01 and  # 金额相等
                        statement_type == trans_type):  # 类型相同
                        
                        # 标记为已匹配
                        statement['matched'] = True
                        statement['matched_transaction_id'] = transaction.get('id')
                        transaction['matched'] = True
                        transaction['matched_statement_id'] = statement.get('id')
                        
                        matched = True
                        matched_count += 1
                        break
                
                if not matched:
                    unmatched_statements.append(statement)
            
            # 找出未匹配的收支记录
            for transaction in transactions:
                if not transaction.get('matched'):
                    unmatched_transactions.append(transaction)
            
            # 保存更新后的数据
            financial_manager.save_bank_statements(statements, bank_name)
            financial_manager.save_transactions(transactions)
            
            return {
                'matched_count': matched_count,
                'unmatched_statements': len(unmatched_statements),
                'unmatched_transactions': len(unmatched_transactions),
                'unmatched_statement_list': unmatched_statements[:10],  # 只返回前10条
                'unmatched_transaction_list': unmatched_transactions[:10]
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def generate_reconciliation_report(self, bank_name: str, start_date: str, end_date: str) -> Dict:
        """生成银行对账报告"""
        try:
            statements = financial_manager.load_bank_statements(bank_name)
            transactions = financial_manager.load_transactions()
            
            # 筛选期间内的数据
            period_statements = []
            for stmt in statements:
                stmt_date = stmt.get('date', '')
                if start_date <= stmt_date <= end_date:
                    period_statements.append(stmt)
            
            period_transactions = []
            for trans in transactions:
                trans_date = trans.get('date', '')
                if start_date <= trans_date <= end_date:
                    period_transactions.append(trans)
            
            # 统计对账情况
            matched_statements = [s for s in period_statements if s.get('matched')]
            unmatched_statements = [s for s in period_statements if not s.get('matched')]
            
            matched_transactions = [t for t in period_transactions if t.get('matched')]
            unmatched_transactions = [t for t in period_transactions if not t.get('matched')]
            
            # 计算金额
            bank_income = sum(s.get('amount', 0) for s in period_statements if s.get('type') == '收入')
            bank_expense = sum(s.get('amount', 0) for s in period_statements if s.get('type') == '支出')
            
            record_income = sum(t.get('amount', 0) for t in period_transactions if t.get('type') == '收入')
            record_expense = sum(t.get('amount', 0) for t in period_transactions if t.get('type') == '支出')
            
            return {
                'period': f"{start_date} 至 {end_date}",
                'bank_name': bank_name,
                'bank_summary': {
                    'total_statements': len(period_statements),
                    'income': bank_income,
                    'expense': bank_expense,
                    'net': bank_income - bank_expense
                },
                'record_summary': {
                    'total_transactions': len(period_transactions),
                    'income': record_income,
                    'expense': record_expense,
                    'net': record_income - record_expense
                },
                'reconciliation': {
                    'matched_statements': len(matched_statements),
                    'unmatched_statements': len(unmatched_statements),
                    'matched_transactions': len(matched_transactions),
                    'unmatched_transactions': len(unmatched_transactions),
                    'match_rate': len(matched_statements) / len(period_statements) * 100 if period_statements else 0
                },
                'differences': {
                    'income_diff': bank_income - record_income,
                    'expense_diff': bank_expense - record_expense,
                    'net_diff': (bank_income - bank_expense) - (record_income - record_expense)
                },
                'unmatched_details': {
                    'statements': unmatched_statements[:20],  # 最多显示20条
                    'transactions': unmatched_transactions[:20]
                }
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def export_reconciliation_report(self, report_data: Dict) -> str:
        """导出对账报告到Excel"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"银行对账报告_{report_data.get('bank_name', '')}_{timestamp}.xlsx"
            output_path = f"{self.data_dir}/{filename}"
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 汇总信息
                summary_data = {
                    '项目': ['银行流水笔数', '银行收入', '银行支出', '银行净额',
                           '记账笔数', '记账收入', '记账支出', '记账净额',
                           '已匹配笔数', '未匹配银行流水', '未匹配记账', '匹配率'],
                    '数值': [
                        report_data['bank_summary']['total_statements'],
                        report_data['bank_summary']['income'],
                        report_data['bank_summary']['expense'],
                        report_data['bank_summary']['net'],
                        report_data['record_summary']['total_transactions'],
                        report_data['record_summary']['income'],
                        report_data['record_summary']['expense'],
                        report_data['record_summary']['net'],
                        report_data['reconciliation']['matched_statements'],
                        report_data['reconciliation']['unmatched_statements'],
                        report_data['reconciliation']['unmatched_transactions'],
                        f"{report_data['reconciliation']['match_rate']:.1f}%"
                    ]
                }
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='对账汇总', index=False)
                
                # 未匹配银行流水
                if report_data['unmatched_details']['statements']:
                    unmatched_statements_df = pd.DataFrame(report_data['unmatched_details']['statements'])
                    unmatched_statements_df.to_excel(writer, sheet_name='未匹配银行流水', index=False)
                
                # 未匹配记账记录
                if report_data['unmatched_details']['transactions']:
                    unmatched_transactions_df = pd.DataFrame(report_data['unmatched_details']['transactions'])
                    unmatched_transactions_df.to_excel(writer, sheet_name='未匹配记账记录', index=False)
            
            return output_path
            
        except Exception as e:
            print(f"导出对账报告失败: {e}")
            return None
    
    def get_bank_balance_trend(self, bank_name: str, days: int = 30) -> Dict:
        """获取银行余额趋势"""
        try:
            statements = financial_manager.load_bank_statements(bank_name)
            
            # 按日期排序
            statements.sort(key=lambda x: x.get('date', ''))
            
            # 获取最近N天的数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            trend_data = []
            for stmt in statements:
                stmt_date = datetime.strptime(stmt.get('date', ''), '%Y-%m-%d')
                if start_date <= stmt_date <= end_date:
                    trend_data.append({
                        'date': stmt.get('date'),
                        'balance': stmt.get('balance', 0),
                        'amount': stmt.get('amount', 0),
                        'type': stmt.get('type', '')
                    })
            
            return {
                'bank_name': bank_name,
                'period': f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
                'trend_data': trend_data,
                'current_balance': trend_data[-1]['balance'] if trend_data else 0,
                'period_income': sum(d['amount'] for d in trend_data if d['type'] == '收入'),
                'period_expense': sum(d['amount'] for d in trend_data if d['type'] == '支出')
            }
            
        except Exception as e:
            return {'error': str(e)}

# 全局银行流水管理器实例
bank_manager = BankStatementManager()