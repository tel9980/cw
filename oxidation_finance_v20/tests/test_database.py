#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库功能测试
"""

import pytest
from decimal import Decimal
from datetime import date

from oxidation_finance_v20.models.business_models import (
    PricingUnit, ProcessType, OrderStatus, ExpenseType, BankType
)


class TestDatabaseBasics:
    """数据库基础功能测试"""
    
    def test_database_connection(self, temp_db):
        """测试数据库连接"""
        assert temp_db.conn is not None
        assert temp_db.conn.row_factory is not None
    
    def test_customer_crud(self, temp_db, sample_customer):
        """测试客户的增删改查"""
        # 保存客户
        customer_id = temp_db.save_customer(sample_customer)
        assert customer_id == sample_customer.id
        
        # 读取客户
        retrieved = temp_db.get_customer(customer_id)
        assert retrieved is not None
        assert retrieved.name == sample_customer.name
        assert retrieved.contact == sample_customer.contact
        assert retrieved.credit_limit == sample_customer.credit_limit
        
        # 列出所有客户
        customers = temp_db.list_customers()
        assert len(customers) == 1
        assert customers[0].id == customer_id
    
    def test_supplier_crud(self, temp_db, sample_supplier):
        """测试供应商的增删改查"""
        # 保存供应商
        supplier_id = temp_db.save_supplier(sample_supplier)
        assert supplier_id == sample_supplier.id
        
        # 读取供应商
        retrieved = temp_db.get_supplier(supplier_id)
        assert retrieved is not None
        assert retrieved.name == sample_supplier.name
        assert retrieved.business_type == sample_supplier.business_type
        
        # 列出所有供应商
        suppliers = temp_db.list_suppliers()
        assert len(suppliers) == 1
        assert suppliers[0].id == supplier_id
    
    def test_order_crud(self, temp_db, sample_customer, sample_order):
        """测试订单的增删改查"""
        # 先保存客户
        temp_db.save_customer(sample_customer)
        
        # 保存订单
        order_id = temp_db.save_order(sample_order)
        assert order_id == sample_order.id
        
        # 读取订单
        retrieved = temp_db.get_order(order_id)
        assert retrieved is not None
        assert retrieved.order_no == sample_order.order_no
        assert retrieved.customer_name == sample_order.customer_name
        assert retrieved.item_description == sample_order.item_description
        assert retrieved.quantity == sample_order.quantity
        assert retrieved.pricing_unit == sample_order.pricing_unit
        assert retrieved.total_amount == sample_order.total_amount
        assert len(retrieved.processes) == len(sample_order.processes)
        
        # 列出订单
        orders = temp_db.list_orders()
        assert len(orders) == 1
        assert orders[0].id == order_id
        
        # 按客户筛选
        customer_orders = temp_db.list_orders(customer_id=sample_customer.id)
        assert len(customer_orders) == 1
        
        # 按状态筛选
        pending_orders = temp_db.list_orders(status=OrderStatus.PENDING)
        assert len(pending_orders) == 1
    
    def test_income_crud(self, temp_db, sample_customer, sample_income):
        """测试收入的增删改查"""
        # 先保存客户
        temp_db.save_customer(sample_customer)
        
        # 保存收入
        income_id = temp_db.save_income(sample_income)
        assert income_id == sample_income.id
        
        # 读取收入
        retrieved = temp_db.get_income(income_id)
        assert retrieved is not None
        assert retrieved.customer_name == sample_income.customer_name
        assert retrieved.amount == sample_income.amount
        assert retrieved.bank_type == sample_income.bank_type
        assert retrieved.has_invoice == sample_income.has_invoice
        
        # 列出收入
        incomes = temp_db.list_incomes()
        assert len(incomes) == 1
        assert incomes[0].id == income_id
    
    def test_expense_crud(self, temp_db, sample_supplier, sample_expense):
        """测试支出的增删改查"""
        # 先保存供应商
        temp_db.save_supplier(sample_supplier)
        
        # 保存支出
        expense_id = temp_db.save_expense(sample_expense)
        assert expense_id == sample_expense.id
        
        # 读取支出
        retrieved = temp_db.get_expense(expense_id)
        assert retrieved is not None
        assert retrieved.expense_type == sample_expense.expense_type
        assert retrieved.supplier_name == sample_expense.supplier_name
        assert retrieved.amount == sample_expense.amount
        assert retrieved.bank_type == sample_expense.bank_type
        
        # 列出支出
        expenses = temp_db.list_expenses()
        assert len(expenses) == 1
        assert expenses[0].id == expense_id
        
        # 按类型筛选
        acid_expenses = temp_db.list_expenses(expense_type=ExpenseType.ACID_THREE)
        assert len(acid_expenses) == 1
    
    def test_bank_account_crud(self, temp_db, sample_bank_account):
        """测试银行账户的增删改查"""
        # 保存账户
        account_id = temp_db.save_bank_account(sample_bank_account)
        assert account_id == sample_bank_account.id
        
        # 读取账户
        retrieved = temp_db.get_bank_account(account_id)
        assert retrieved is not None
        assert retrieved.bank_type == sample_bank_account.bank_type
        assert retrieved.account_name == sample_bank_account.account_name
        assert retrieved.balance == sample_bank_account.balance
        
        # 列出账户
        accounts = temp_db.list_bank_accounts()
        assert len(accounts) == 1
        assert accounts[0].id == account_id
    
    def test_bank_transaction_crud(self, temp_db, sample_bank_transaction):
        """测试银行交易的增删改查"""
        # 保存交易
        transaction_id = temp_db.save_bank_transaction(sample_bank_transaction)
        assert transaction_id == sample_bank_transaction.id
        
        # 读取交易
        retrieved = temp_db.get_bank_transaction(transaction_id)
        assert retrieved is not None
        assert retrieved.bank_type == sample_bank_transaction.bank_type
        assert retrieved.amount == sample_bank_transaction.amount
        assert retrieved.counterparty == sample_bank_transaction.counterparty
        assert retrieved.matched == sample_bank_transaction.matched
        
        # 列出交易
        transactions = temp_db.list_bank_transactions()
        assert len(transactions) == 1
        assert transactions[0].id == transaction_id
        
        # 按银行类型筛选
        g_bank_transactions = temp_db.list_bank_transactions(bank_type=BankType.G_BANK)
        assert len(g_bank_transactions) == 1


class TestDatabaseIntegration:
    """数据库集成测试"""
    
    def test_order_with_income_allocation(self, temp_db, sample_customer, sample_order):
        """测试订单与收入分配的集成"""
        # 保存客户和订单
        temp_db.save_customer(sample_customer)
        temp_db.save_order(sample_order)
        
        # 创建收入并分配到订单
        from oxidation_finance_v20.models.business_models import Income
        income = Income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("550.00"),
            bank_type=BankType.G_BANK,
            has_invoice=True,
            related_orders=[sample_order.id],
            allocation={sample_order.id: Decimal("550.00")},
            income_date=date.today(),
            notes="订单收款"
        )
        
        income_id = temp_db.save_income(income)
        
        # 验证收入保存成功
        retrieved_income = temp_db.get_income(income_id)
        assert retrieved_income is not None
        assert sample_order.id in retrieved_income.related_orders
        assert retrieved_income.allocation[sample_order.id] == Decimal("550.00")
    
    def test_order_with_outsourcing_expense(self, temp_db, sample_customer, 
                                           sample_supplier, sample_order):
        """测试订单与委外费用的集成"""
        # 保存客户、供应商和订单
        temp_db.save_customer(sample_customer)
        temp_db.save_supplier(sample_supplier)
        temp_db.save_order(sample_order)
        
        # 创建委外费用
        from oxidation_finance_v20.models.business_models import Expense
        expense = Expense(
            expense_type=ExpenseType.OUTSOURCING,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            amount=sample_order.outsourcing_cost,
            bank_type=BankType.G_BANK,
            has_invoice=True,
            related_order_id=sample_order.id,
            expense_date=date.today(),
            description="委外加工费",
            notes="喷砂加工"
        )
        
        expense_id = temp_db.save_expense(expense)
        
        # 验证支出保存成功
        retrieved_expense = temp_db.get_expense(expense_id)
        assert retrieved_expense is not None
        assert retrieved_expense.related_order_id == sample_order.id
        assert retrieved_expense.amount == sample_order.outsourcing_cost
