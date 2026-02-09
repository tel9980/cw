# -*- coding: utf-8 -*-
"""
飞书多维表格初始化模块
负责创建和初始化氧化加工厂所需的所有表格
"""

import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
from .config import get_config

class TableInitializer:
    """表格初始化器"""
    
    def __init__(self, client, app_token):
        """
        初始化表格初始化器
        
        Args:
            client: 飞书客户端
            app_token: 多维表格的app_token
        """
        self.client = client
        self.app_token = app_token
        self.config = get_config()
    
    def create_processing_orders_table(self):
        """创建加工订单表"""
        print("\n📋 正在创建【加工订单表】...")
        
        # 定义表格字段
        fields = [
            {"field_name": "订单编号", "type": 1},  # 文本
            {"field_name": "客户名称", "type": 1},  # 文本
            {"field_name": "订单日期", "type": 5},  # 日期
            {"field_name": "物品名称", "type": 1},  # 文本
            {"field_name": "计价单位", "type": 3, "property": {"options": [
                {"name": unit} for unit in self.config.get_pricing_units()
            ]}},  # 单选
            {"field_name": "数量", "type": 2},  # 数字
            {"field_name": "单价", "type": 2},  # 数字
            {"field_name": "订单金额", "type": 20},  # 公式
            {"field_name": "已收款金额", "type": 2},  # 数字
            {"field_name": "未收款金额", "type": 20},  # 公式
            {"field_name": "工序明细", "type": 1},  # 多行文本
            {"field_name": "外发工序", "type": 4, "property": {"options": [
                {"name": process} for process in self.config.get_outsourced_processes()
            ]}},  # 多选
            {"field_name": "外发成本", "type": 2},  # 数字
            {"field_name": "订单状态", "type": 3, "property": {"options": [
                {"name": status} for status in self.config.get_order_status_list()
            ]}},  # 单选
            {"field_name": "备注", "type": 1},  # 多行文本
        ]
        
        try:
            # 创建表格
            req = CreateAppTableRequest.builder() \
                .app_token(self.app_token) \
                .request_body(AppTableCreateHeader.builder()
                    .table(AppTable.builder()
                        .name("加工订单表")
                        .build())
                    .build()) \
                .build()
            
            resp = self.client.bitable.v1.app_table.create(req)
            
            if resp.success():
                table_id = resp.data.table_id
                print(f"✅ 加工订单表创建成功！Table ID: {table_id}")
                return table_id
            else:
                print(f"❌ 创建失败: {resp.msg}")
                return None
                
        except Exception as e:
            print(f"❌ 创建异常: {str(e)}")
            return None
    
    def extend_daily_ledger_table(self, table_id):
        """
        扩展日常台账表
        添加对账相关字段
        
        Args:
            table_id: 日常台账表的table_id
        """
        print("\n📋 正在扩展【日常台账表】...")
        
        # 新增字段列表
        new_fields = [
            {
                "field_name": "关联订单号",
                "type": 1,  # 文本
                "description": "关联的加工订单编号"
            },
            {
                "field_name": "对账状态",
                "type": 3,  # 单选
                "property": {
                    "options": [{"name": status} for status in self.config.get_reconcile_status_list()]
                },
                "description": "对账状态：未对账/部分对账/已对账"
            },
            {
                "field_name": "对账金额",
                "type": 2,  # 数字
                "description": "本次对账的金额"
            },
            {
                "field_name": "对账时间",
                "type": 5,  # 日期时间
                "description": "对账操作的时间"
            },
            {
                "field_name": "对账备注",
                "type": 1,  # 文本
                "description": "对账说明"
            }
        ]
        
        try:
            for field_info in new_fields:
                # 创建字段
                req = CreateAppTableFieldRequest.builder() \
                    .app_token(self.app_token) \
                    .table_id(table_id) \
                    .request_body(AppTableField.builder()
                        .field_name(field_info["field_name"])
                        .type(field_info["type"])
                        .build()) \
                    .build()
                
                resp = self.client.bitable.v1.app_table_field.create(req)
                
                if resp.success():
                    print(f"  ✅ 字段【{field_info['field_name']}】添加成功")
                else:
                    print(f"  ⚠️ 字段【{field_info['field_name']}】添加失败: {resp.msg}")
            
            print("✅ 日常台账表扩展完成！")
            return True
            
        except Exception as e:
            print(f"❌ 扩展异常: {str(e)}")
            return False
    
    def create_business_partners_table(self):
        """创建往来单位表"""
        print("\n📋 正在创建【往来单位表】...")
        
        try:
            req = CreateAppTableRequest.builder() \
                .app_token(self.app_token) \
                .request_body(AppTableCreateHeader.builder()
                    .table(AppTable.builder()
                        .name("往来单位表")
                        .build())
                    .build()) \
                .build()
            
            resp = self.client.bitable.v1.app_table.create(req)
            
            if resp.success():
                table_id = resp.data.table_id
                print(f"✅ 往来单位表创建成功！Table ID: {table_id}")
                
                # 添加字段
                fields = [
                    {"field_name": "单位名称", "type": 1},
                    {"field_name": "单位类型", "type": 3, "options": ["客户", "供应商", "两者"]},
                    {"field_name": "别名列表", "type": 1},  # 多行文本，一行一个别名
                    {"field_name": "联系人", "type": 1},
                    {"field_name": "联系电话", "type": 13},
                    {"field_name": "应收余额", "type": 2},
                    {"field_name": "应付余额", "type": 2},
                    {"field_name": "备注", "type": 1},
                ]
                
                for field_info in fields:
                    self._create_field(table_id, field_info)
                
                return table_id
            else:
                print(f"❌ 创建失败: {resp.msg}")
                return None
                
        except Exception as e:
            print(f"❌ 创建异常: {str(e)}")
            return None
    
    def create_reconciliation_records_table(self):
        """创建对账记录表"""
        print("\n📋 正在创建【对账记录表】...")
        
        try:
            req = CreateAppTableRequest.builder() \
                .app_token(self.app_token) \
                .request_body(AppTableCreateHeader.builder()
                    .table(AppTable.builder()
                        .name("对账记录表")
                        .build())
                    .build()) \
                .build()
            
            resp = self.client.bitable.v1.app_table.create(req)
            
            if resp.success():
                table_id = resp.data.table_id
                print(f"✅ 对账记录表创建成功！Table ID: {table_id}")
                return table_id
            else:
                print(f"❌ 创建失败: {resp.msg}")
                return None
                
        except Exception as e:
            print(f"❌ 创建异常: {str(e)}")
            return None
    
    def create_category_rules_table(self):
        """创建费用分类规则表"""
        print("\n📋 正在创建【费用分类规则表】...")
        
        try:
            req = CreateAppTableRequest.builder() \
                .app_token(self.app_token) \
                .request_body(AppTableCreateHeader.builder()
                    .table(AppTable.builder()
                        .name("费用分类规则表")
                        .build())
                    .build()) \
                .build()
            
            resp = self.client.bitable.v1.app_table.create(req)
            
            if resp.success():
                table_id = resp.data.table_id
                print(f"✅ 费用分类规则表创建成功！Table ID: {table_id}")
                
                # 预填充分类规则
                self._populate_category_rules(table_id)
                
                return table_id
            else:
                print(f"❌ 创建失败: {resp.msg}")
                return None
                
        except Exception as e:
            print(f"❌ 创建异常: {str(e)}")
            return None
    
    def _create_field(self, table_id, field_info):
        """创建字段的辅助方法"""
        try:
            builder = AppTableField.builder() \
                .field_name(field_info["field_name"]) \
                .type(field_info["type"])
            
            # 如果有选项，添加选项
            if "options" in field_info:
                # 这里需要根据实际API调整
                pass
            
            req = CreateAppTableFieldRequest.builder() \
                .app_token(self.app_token) \
                .table_id(table_id) \
                .request_body(builder.build()) \
                .build()
            
            resp = self.client.bitable.v1.app_table_field.create(req)
            
            if resp.success():
                print(f"  ✅ 字段【{field_info['field_name']}】添加成功")
            else:
                print(f"  ⚠️ 字段【{field_info['field_name']}】添加失败: {resp.msg}")
                
        except Exception as e:
            print(f"  ❌ 字段【{field_info['field_name']}】创建异常: {str(e)}")
    
    def _populate_category_rules(self, table_id):
        """预填充分类规则"""
        print("  📝 正在预填充分类规则...")
        
        keywords = self.config.get_category_keywords()
        
        # 这里可以批量插入规则
        # 由于需要实际的飞书API调用，这里先打印提示
        print(f"  ℹ️ 共有 {len(keywords)} 条分类规则待填充")
        print("  💡 提示：可以通过导入Excel批量填充规则")
    
    def initialize_all_tables(self, daily_ledger_table_id=None):
        """
        初始化所有表格
        
        Args:
            daily_ledger_table_id: 现有的日常台账表ID（如果已存在）
        
        Returns:
            dict: 所有表格的ID映射
        """
        print("=" * 60)
        print("     氧化加工厂表格初始化")
        print("=" * 60)
        
        table_ids = {}
        
        # 1. 创建加工订单表
        orders_table_id = self.create_processing_orders_table()
        if orders_table_id:
            table_ids["加工订单表"] = orders_table_id
        
        # 2. 扩展日常台账表（如果提供了table_id）
        if daily_ledger_table_id:
            if self.extend_daily_ledger_table(daily_ledger_table_id):
                table_ids["日常台账表"] = daily_ledger_table_id
        
        # 3. 创建往来单位表
        partners_table_id = self.create_business_partners_table()
        if partners_table_id:
            table_ids["往来单位表"] = partners_table_id
        
        # 4. 创建对账记录表
        reconcile_table_id = self.create_reconciliation_records_table()
        if reconcile_table_id:
            table_ids["对账记录表"] = reconcile_table_id
        
        # 5. 创建费用分类规则表
        rules_table_id = self.create_category_rules_table()
        if rules_table_id:
            table_ids["费用分类规则表"] = rules_table_id
        
        print("\n" + "=" * 60)
        print("✅ 表格初始化完成！")
        print("=" * 60)
        print("\n📊 已创建的表格:")
        for table_name, table_id in table_ids.items():
            print(f"  - {table_name}: {table_id}")
        
        return table_ids


def init_oxidation_tables(client, app_token, daily_ledger_table_id=None):
    """
    便捷函数：初始化氧化加工厂所需的所有表格
    
    Args:
        client: 飞书客户端
        app_token: 多维表格的app_token
        daily_ledger_table_id: 现有的日常台账表ID（可选）
    
    Returns:
        dict: 所有表格的ID映射
    """
    initializer = TableInitializer(client, app_token)
    return initializer.initialize_all_tables(daily_ledger_table_id)
