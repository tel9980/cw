# -*- coding: utf-8 -*-
"""
财务数据管理器
专门处理收支记录、银行流水、税务计算等财务数据
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

class FinancialDataManager:
    """财务数据管理器"""
    
    def __init__(self):
        self.base_dir = "财务数据"
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保所有必要目录存在"""
        dirs = [
            f"{self.base_dir}/收支记录",
            f"{self.base_dir}/银行流水", 
            f"{self.base_dir}/税务资料",
            f"{self.base_dir}/月度报表",
            f"{self.base_dir}/年度报表",
            f"{self.base_dir}/凭证档案",
            f"{self.base_dir}/合同档案",
            f"{self.base_dir}/客户档案",
            f"{self.base_dir}/供应商档案",
            f"{self.base_dir}/自动备份",
            f"{self.base_dir}/运行日志"
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    # 收支记录管理
    def load_transactions(self) -> List[Dict]:
        """加载收支记录"""
        file_path = f"{self.base_dir}/收支记录/transactions.json"
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载收支记录失败: {e}")
        return []
    
    def save_transactions(self, transactions: List[Dict]) -> bool:
        """保存收支记录"""
        file_path = f"{self.base_dir}/收支记录/transactions.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(transactions, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存收支记录失败: {e}")
            return False
    
    def add_transaction(self, transaction: Dict) -> bool:
        """添加收支记录"""
        transactions = self.load_transactions()
        transaction['id'] = len(transactions) + 1
        transaction['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        transactions.append(transaction)
        return self.save_transactions(transactions)
    
    def get_transactions_by_period(self, start_date: str, end_date: str) -> List[Dict]:
        """获取指定期间的收支记录"""
        transactions = self.load_transactions()
        result = []
        
        for trans in transactions:
            trans_date = trans.get('date', '')
            if start_date <= trans_date <= end_date:
                result.append(trans)
        
        return result
    
    def get_transaction_statistics(self, start_date: str = None, end_date: str = None) -> Dict:
        """获取收支统计"""
        if start_date and end_date:
            transactions = self.get_transactions_by_period(start_date, end_date)
        else:
            transactions = self.load_transactions()
        
        stats = {
            'total_income': 0,
            'total_expense': 0,
            'net_profit': 0,
            'income_by_category': {},
            'expense_by_category': {},
            'by_payment_method': {},
            'transaction_count': len(transactions)
        }
        
        for trans in transactions:
            amount = trans.get('amount', 0)
            category = trans.get('category', '未分类')
            payment_method = trans.get('payment_method', '未知')
            
            # 按收支类型统计
            if trans.get('type') == '收入':
                stats['total_income'] += amount
                if category not in stats['income_by_category']:
                    stats['income_by_category'][category] = 0
                stats['income_by_category'][category] += amount
            else:
                stats['total_expense'] += amount
                if category not in stats['expense_by_category']:
                    stats['expense_by_category'][category] = 0
                stats['expense_by_category'][category] += amount
            
            # 按支付方式统计
            if payment_method not in stats['by_payment_method']:
                stats['by_payment_method'][payment_method] = {'income': 0, 'expense': 0}
            
            if trans.get('type') == '收入':
                stats['by_payment_method'][payment_method]['income'] += amount
            else:
                stats['by_payment_method'][payment_method]['expense'] += amount
        
        stats['net_profit'] = stats['total_income'] - stats['total_expense']
        
        return stats
    
    # 银行流水管理
    def load_bank_statements(self, bank_name: str = None) -> List[Dict]:
        """加载银行流水"""
        if bank_name:
            file_path = f"{self.base_dir}/银行流水/{bank_name}_statements.json"
        else:
            file_path = f"{self.base_dir}/银行流水/all_statements.json"
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载银行流水失败: {e}")
        return []
    
    def save_bank_statements(self, statements: List[Dict], bank_name: str = None) -> bool:
        """保存银行流水"""
        if bank_name:
            file_path = f"{self.base_dir}/银行流水/{bank_name}_statements.json"
        else:
            file_path = f"{self.base_dir}/银行流水/all_statements.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(statements, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存银行流水失败: {e}")
            return False
    
    def add_bank_statement(self, statement: Dict, bank_name: str = None) -> bool:
        """添加银行流水记录"""
        statements = self.load_bank_statements(bank_name)
        statement['id'] = len(statements) + 1
        statement['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        statements.append(statement)
        return self.save_bank_statements(statements, bank_name)
    
    # 客户档案管理
    def load_customers(self) -> List[Dict]:
        """加载客户档案"""
        file_path = f"{self.base_dir}/客户档案/customers.json"
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载客户档案失败: {e}")
        return []
    
    def save_customers(self, customers: List[Dict]) -> bool:
        """保存客户档案"""
        file_path = f"{self.base_dir}/客户档案/customers.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(customers, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存客户档案失败: {e}")
            return False
    
    def add_customer(self, customer: Dict) -> bool:
        """添加客户档案"""
        customers = self.load_customers()
        
        # 检查客户是否已存在
        for existing in customers:
            if existing.get('name') == customer.get('name'):
                return False  # 客户已存在
        
        customer['id'] = len(customers) + 1
        customer['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        customers.append(customer)
        return self.save_customers(customers)
    
    def update_customer(self, customer_id: int, updates: Dict) -> bool:
        """更新客户档案"""
        customers = self.load_customers()
        
        for i, customer in enumerate(customers):
            if customer.get('id') == customer_id:
                customer.update(updates)
                customer['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                customers[i] = customer
                return self.save_customers(customers)
        
        return False
    
    def get_customer_statistics(self) -> Dict:
        """获取客户统计信息"""
        customers = self.load_customers()
        transactions = self.load_transactions()
        
        # 从订单系统获取数据
        try:
            from oxidation_factory import get_storage
            orders = get_storage().get_all_orders()
        except:
            orders = []
        
        customer_stats = {}
        
        # 统计交易记录中的客户
        for trans in transactions:
            if trans.get('type') == '收入' and trans.get('customer'):
                customer = trans['customer']
                if customer not in customer_stats:
                    customer_stats[customer] = {
                        'income': 0,
                        'orders': 0,
                        'last_transaction': None
                    }
                customer_stats[customer]['income'] += trans.get('amount', 0)
                customer_stats[customer]['last_transaction'] = trans.get('date')
        
        # 统计订单中的客户
        for order in orders:
            customer = order.get('customer')
            if customer:
                if customer not in customer_stats:
                    customer_stats[customer] = {
                        'income': 0,
                        'orders': 0,
                        'last_transaction': None
                    }
                customer_stats[customer]['orders'] += 1
        
        return customer_stats
    
    # 税务计算
    def calculate_vat(self, start_date: str, end_date: str) -> Dict:
        """计算增值税"""
        transactions = self.get_transactions_by_period(start_date, end_date)
        
        taxable_income = 0  # 应税收入
        tax_free_income = 0  # 免税收入
        
        for trans in transactions:
            if trans.get('type') == '收入':
                if trans.get('has_invoice', False):
                    taxable_income += trans.get('amount', 0)
                else:
                    tax_free_income += trans.get('amount', 0)
        
        total_income = taxable_income + tax_free_income
        
        # 增值税计算（小规模纳税人3%征收率）
        vat_rate = 0.03
        income_without_tax = taxable_income / (1 + vat_rate) if taxable_income > 0 else 0
        vat_amount = taxable_income - income_without_tax
        
        # 小规模纳税人月销售额15万以下免征增值税
        monthly_limit = 150000
        period_days = (datetime.strptime(end_date, '%Y-%m-%d') - 
                      datetime.strptime(start_date, '%Y-%m-%d')).days + 1
        
        if period_days <= 31:  # 月度期间
            if income_without_tax <= monthly_limit:
                actual_vat = 0
                exempt_reason = "月销售额未超过15万元，享受小规模纳税人免税政策"
            else:
                actual_vat = vat_amount
                exempt_reason = None
        else:
            actual_vat = vat_amount
            exempt_reason = None
        
        return {
            'period': f"{start_date} 至 {end_date}",
            'taxable_income': taxable_income,
            'tax_free_income': tax_free_income,
            'total_income': total_income,
            'income_without_tax': income_without_tax,
            'vat_rate': vat_rate,
            'vat_amount': vat_amount,
            'actual_vat': actual_vat,
            'exempt_reason': exempt_reason
        }
    
    # 报表生成
    def generate_profit_statement(self, start_date: str, end_date: str) -> Dict:
        """生成利润表"""
        stats = self.get_transaction_statistics(start_date, end_date)
        
        return {
            'period': f"{start_date} 至 {end_date}",
            'operating_income': stats['total_income'],
            'operating_costs': stats['total_expense'],
            'gross_profit': stats['net_profit'],
            'profit_rate': (stats['net_profit'] / stats['total_income'] * 100) if stats['total_income'] > 0 else 0,
            'income_breakdown': stats['income_by_category'],
            'expense_breakdown': stats['expense_by_category']
        }
    
    def generate_monthly_summary(self, year: int, month: int) -> Dict:
        """生成月度汇总"""
        start_date = f"{year}-{month:02d}-01"
        
        # 计算月末日期
        if month == 12:
            end_date = f"{year}-12-31"
        else:
            next_month = datetime(year, month + 1, 1)
            last_day = next_month - timedelta(days=1)
            end_date = last_day.strftime("%Y-%m-%d")
        
        # 获取收支统计
        financial_stats = self.get_transaction_statistics(start_date, end_date)
        
        # 获取订单统计
        try:
            from oxidation_factory import get_storage
            orders = get_storage().get_all_orders()
            monthly_orders = []
            
            for order in orders:
                order_date = order.get('order_date', '')
                if start_date <= order_date <= end_date:
                    monthly_orders.append(order)
            
            order_stats = {
                'total_orders': len(monthly_orders),
                'total_amount': sum(o.get('order_amount', 0) for o in monthly_orders),
                'total_paid': sum(o.get('paid_amount', 0) for o in monthly_orders),
                'total_unpaid': sum(o.get('unpaid_amount', 0) for o in monthly_orders)
            }
        except:
            order_stats = {
                'total_orders': 0,
                'total_amount': 0,
                'total_paid': 0,
                'total_unpaid': 0
            }
        
        # 获取税务信息
        vat_info = self.calculate_vat(start_date, end_date)
        
        return {
            'period': f"{year}年{month}月",
            'start_date': start_date,
            'end_date': end_date,
            'financial_stats': financial_stats,
            'order_stats': order_stats,
            'vat_info': vat_info,
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    # 数据导出
    def export_transactions_to_excel(self, start_date: str = None, end_date: str = None) -> str:
        """导出收支记录到Excel"""
        try:
            if start_date and end_date:
                transactions = self.get_transactions_by_period(start_date, end_date)
                filename = f"收支明细_{start_date}至{end_date}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            else:
                transactions = self.load_transactions()
                filename = f"收支明细_全部_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            if not transactions:
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(transactions)
            
            # 重新排列列顺序
            columns = ['date', 'type', 'amount', 'category', 'description', 
                      'customer', 'payment_method', 'has_invoice', 'invoice_no', 'status']
            
            # 只保留存在的列
            columns = [col for col in columns if col in df.columns]
            df = df[columns]
            
            # 设置中文列名
            column_names = {
                'date': '日期',
                'type': '类型', 
                'amount': '金额',
                'category': '分类',
                'description': '说明',
                'customer': '客户',
                'payment_method': '支付方式',
                'has_invoice': '是否开票',
                'invoice_no': '发票号码',
                'status': '状态'
            }
            
            df.columns = [column_names.get(col, col) for col in df.columns]
            
            # 导出路径
            output_path = f"{self.base_dir}/月度报表/{filename}"
            
            # 导出到Excel
            df.to_excel(output_path, index=False, engine='openpyxl')
            
            return output_path
            
        except Exception as e:
            print(f"导出Excel失败: {e}")
            return None
    
    # 数据备份
    def backup_all_data(self) -> str:
        """备份所有财务数据"""
        try:
            import shutil
            from pathlib import Path
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"财务数据备份_{timestamp}"
            backup_path = f"{self.base_dir}/自动备份/{backup_name}"
            
            # 创建备份目录
            os.makedirs(backup_path, exist_ok=True)
            
            # 备份各个数据文件
            data_files = [
                "收支记录/transactions.json",
                "客户档案/customers.json", 
                "本地订单/orders.json"
            ]
            
            for file_path in data_files:
                source = f"{self.base_dir}/{file_path}"
                if os.path.exists(source):
                    dest_dir = f"{backup_path}/{os.path.dirname(file_path)}"
                    os.makedirs(dest_dir, exist_ok=True)
                    shutil.copy2(source, f"{backup_path}/{file_path}")
            
            # 创建备份说明文件
            with open(f"{backup_path}/备份说明.txt", 'w', encoding='utf-8') as f:
                f.write(f"财务数据备份\n")
                f.write(f"备份时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"备份内容：收支记录、客户档案、订单数据\n")
            
            return backup_path
            
        except Exception as e:
            print(f"数据备份失败: {e}")
            return None

# 全局财务数据管理器实例
financial_manager = FinancialDataManager()