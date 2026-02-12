#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器 - 管理系统配置和基础数据
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from decimal import Decimal

from ..models.business_models import (
    Customer, Supplier, PricingUnit, ProcessType, ExpenseType
)


class ConfigManager:
    """配置管理器 - 支持客户、供应商、计价方式、工序类型、会计科目和报表格式配置"""
    
    def __init__(self, db_path: str, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            db_path: 数据库路径
            config_dir: 配置文件目录，默认为 config_data/
        """
        self.db_path = db_path
        self.config_dir = Path(config_dir) if config_dir else Path("config_data")
        self.config_dir.mkdir(exist_ok=True)
        
        # 配置文件路径
        self.pricing_config_file = self.config_dir / "pricing_methods.json"
        self.process_config_file = self.config_dir / "process_types.json"
        self.account_config_file = self.config_dir / "account_structure.json"
        self.report_config_file = self.config_dir / "report_formats.json"
        
        # 初始化默认配置
        self._init_default_configs()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def _init_default_configs(self):
        """初始化默认配置文件"""
        # 默认计价方式配置
        if not self.pricing_config_file.exists():
            default_pricing = {
                "pricing_methods": [
                    {"code": "PIECE", "name": "件", "description": "按件计价，例如：螺丝、螺母等小零件"},
                    {"code": "STRIP", "name": "条", "description": "按条计价，例如：铝条、钢条等长条形物品"},
                    {"code": "UNIT", "name": "只", "description": "按只计价，例如：把手、拉手等单个物品"},
                    {"code": "ITEM", "name": "个", "description": "按个计价，例如：配件、组件等"},
                    {"code": "METER", "name": "米", "description": "按米长计价，例如：铝型材、管材等"},
                    {"code": "KILOGRAM", "name": "公斤", "description": "按重量计价，例如：板材、型材等"},
                    {"code": "SQUARE_METER", "name": "平方米", "description": "按面积计价，例如：铝板、钢板等"}
                ]
            }
            self._save_json(self.pricing_config_file, default_pricing)
        
        # 默认工序类型配置
        if not self.process_config_file.exists():
            default_process = {
                "process_types": [
                    {"code": "SANDBLASTING", "name": "喷砂", "description": "用砂粒喷射表面，去除氧化层和杂质", "order": 1},
                    {"code": "WIRE_DRAWING", "name": "拉丝", "description": "用砂带或砂轮拉出丝纹效果", "order": 2},
                    {"code": "POLISHING", "name": "抛光", "description": "用抛光轮打磨至光亮", "order": 3},
                    {"code": "OXIDATION", "name": "氧化", "description": "最后工序，在酸液中形成氧化膜", "order": 4}
                ]
            }
            self._save_json(self.process_config_file, default_process)
        
        # 默认会计科目配置
        if not self.account_config_file.exists():
            default_accounts = {
                "assets": [
                    {"code": "1001", "name": "库存现金", "category": "流动资产"},
                    {"code": "1002", "name": "银行存款", "category": "流动资产"},
                    {"code": "1122", "name": "应收账款", "category": "流动资产"},
                    {"code": "1123", "name": "预付账款", "category": "流动资产"},
                    {"code": "1601", "name": "固定资产", "category": "非流动资产"}
                ],
                "liabilities": [
                    {"code": "2202", "name": "应付账款", "category": "流动负债"},
                    {"code": "2203", "name": "预收账款", "category": "流动负债"}
                ],
                "equity": [
                    {"code": "4001", "name": "实收资本", "category": "所有者权益"},
                    {"code": "4103", "name": "本年利润", "category": "所有者权益"}
                ],
                "income": [
                    {"code": "6001", "name": "主营业务收入", "category": "收入"},
                    {"code": "6051", "name": "其他业务收入", "category": "收入"}
                ],
                "expenses": [
                    {"code": "6401", "name": "主营业务成本", "category": "成本"},
                    {"code": "6601", "name": "销售费用", "category": "期间费用"},
                    {"code": "6602", "name": "管理费用", "category": "期间费用"}
                ]
            }
            self._save_json(self.account_config_file, default_accounts)
        
        # 默认报表格式配置
        if not self.report_config_file.exists():
            default_reports = {
                "balance_sheet": {
                    "name": "资产负债表",
                    "sections": ["资产", "负债", "所有者权益"],
                    "format": "standard"
                },
                "income_statement": {
                    "name": "利润表",
                    "sections": ["营业收入", "营业成本", "期间费用", "利润"],
                    "format": "standard"
                },
                "cash_flow_statement": {
                    "name": "现金流量表",
                    "sections": ["经营活动", "投资活动", "筹资活动"],
                    "format": "standard"
                }
            }
            self._save_json(self.report_config_file, default_reports)
    
    def _save_json(self, file_path: Path, data: Dict):
        """保存JSON配置文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_json(self, file_path: Path) -> Dict:
        """加载JSON配置文件"""
        if not file_path.exists():
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # ==================== 客户管理 ====================
    
    def add_customer(self, customer: Customer) -> bool:
        """添加客户"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO customers (id, name, contact, phone, address, credit_limit, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer.id, customer.name, customer.contact, customer.phone,
                customer.address, float(customer.credit_limit), customer.notes,
                customer.created_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加客户失败: {e}")
            return False
    
    def update_customer(self, customer: Customer) -> bool:
        """更新客户信息"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE customers
                SET name=?, contact=?, phone=?, address=?, credit_limit=?, notes=?
                WHERE id=?
            """, (
                customer.name, customer.contact, customer.phone,
                customer.address, float(customer.credit_limit), customer.notes,
                customer.id
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"更新客户失败: {e}")
            return False
    
    def delete_customer(self, customer_id: str) -> bool:
        """删除客户"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM customers WHERE id=?", (customer_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"删除客户失败: {e}")
            return False
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """获取客户信息"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM customers WHERE id=?", (customer_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return Customer(
                    id=row[0], name=row[1], contact=row[2], phone=row[3],
                    address=row[4], credit_limit=Decimal(str(row[5])),
                    notes=row[6], created_at=datetime.fromisoformat(row[7])
                )
            return None
        except Exception as e:
            print(f"获取客户失败: {e}")
            return None
    
    def list_customers(self) -> List[Customer]:
        """列出所有客户"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM customers ORDER BY name")
            rows = cursor.fetchall()
            conn.close()
            
            customers = []
            for row in rows:
                customers.append(Customer(
                    id=row[0], name=row[1], contact=row[2], phone=row[3],
                    address=row[4], credit_limit=Decimal(str(row[5])),
                    notes=row[6], created_at=datetime.fromisoformat(row[7])
                ))
            return customers
        except Exception as e:
            print(f"列出客户失败: {e}")
            return []
    
    # ==================== 供应商管理 ====================
    
    def add_supplier(self, supplier: Supplier) -> bool:
        """添加供应商"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO suppliers (id, name, contact, phone, address, business_type, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                supplier.id, supplier.name, supplier.contact, supplier.phone,
                supplier.address, supplier.business_type, supplier.notes,
                supplier.created_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加供应商失败: {e}")
            return False
    
    def update_supplier(self, supplier: Supplier) -> bool:
        """更新供应商信息"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE suppliers
                SET name=?, contact=?, phone=?, address=?, business_type=?, notes=?
                WHERE id=?
            """, (
                supplier.name, supplier.contact, supplier.phone,
                supplier.address, supplier.business_type, supplier.notes,
                supplier.id
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"更新供应商失败: {e}")
            return False
    
    def delete_supplier(self, supplier_id: str) -> bool:
        """删除供应商"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM suppliers WHERE id=?", (supplier_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"删除供应商失败: {e}")
            return False
    
    def get_supplier(self, supplier_id: str) -> Optional[Supplier]:
        """获取供应商信息"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM suppliers WHERE id=?", (supplier_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return Supplier(
                    id=row[0], name=row[1], contact=row[2], phone=row[3],
                    address=row[4], business_type=row[5],
                    notes=row[6], created_at=datetime.fromisoformat(row[7])
                )
            return None
        except Exception as e:
            print(f"获取供应商失败: {e}")
            return None
    
    def list_suppliers(self) -> List[Supplier]:
        """列出所有供应商"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM suppliers ORDER BY name")
            rows = cursor.fetchall()
            conn.close()
            
            suppliers = []
            for row in rows:
                suppliers.append(Supplier(
                    id=row[0], name=row[1], contact=row[2], phone=row[3],
                    address=row[4], business_type=row[5],
                    notes=row[6], created_at=datetime.fromisoformat(row[7])
                ))
            return suppliers
        except Exception as e:
            print(f"列出供应商失败: {e}")
            return []
    
    # ==================== 计价方式配置 ====================
    
    def get_pricing_methods(self) -> List[Dict[str, str]]:
        """获取所有计价方式"""
        config = self._load_json(self.pricing_config_file)
        return config.get("pricing_methods", [])
    
    def add_pricing_method(self, code: str, name: str, description: str) -> bool:
        """添加计价方式"""
        try:
            config = self._load_json(self.pricing_config_file)
            methods = config.get("pricing_methods", [])
            
            # 检查是否已存在
            if any(m["code"] == code for m in methods):
                print(f"计价方式 {code} 已存在")
                return False
            
            methods.append({"code": code, "name": name, "description": description})
            config["pricing_methods"] = methods
            self._save_json(self.pricing_config_file, config)
            return True
        except Exception as e:
            print(f"添加计价方式失败: {e}")
            return False
    
    def update_pricing_method(self, code: str, name: str, description: str) -> bool:
        """更新计价方式"""
        try:
            config = self._load_json(self.pricing_config_file)
            methods = config.get("pricing_methods", [])
            
            for method in methods:
                if method["code"] == code:
                    method["name"] = name
                    method["description"] = description
                    self._save_json(self.pricing_config_file, config)
                    return True
            
            print(f"计价方式 {code} 不存在")
            return False
        except Exception as e:
            print(f"更新计价方式失败: {e}")
            return False
    
    def delete_pricing_method(self, code: str) -> bool:
        """删除计价方式"""
        try:
            config = self._load_json(self.pricing_config_file)
            methods = config.get("pricing_methods", [])
            
            original_len = len(methods)
            methods = [m for m in methods if m["code"] != code]
            
            if len(methods) == original_len:
                print(f"计价方式 {code} 不存在")
                return False
            
            config["pricing_methods"] = methods
            self._save_json(self.pricing_config_file, config)
            return True
        except Exception as e:
            print(f"删除计价方式失败: {e}")
            return False
    
    # ==================== 工序类型配置 ====================
    
    def get_process_types(self) -> List[Dict[str, Any]]:
        """获取所有工序类型"""
        config = self._load_json(self.process_config_file)
        return config.get("process_types", [])
    
    def add_process_type(self, code: str, name: str, description: str, order: int) -> bool:
        """添加工序类型"""
        try:
            config = self._load_json(self.process_config_file)
            types = config.get("process_types", [])
            
            # 检查是否已存在
            if any(t["code"] == code for t in types):
                print(f"工序类型 {code} 已存在")
                return False
            
            types.append({"code": code, "name": name, "description": description, "order": order})
            # 按顺序排序
            types.sort(key=lambda x: x["order"])
            config["process_types"] = types
            self._save_json(self.process_config_file, config)
            return True
        except Exception as e:
            print(f"添加工序类型失败: {e}")
            return False
    
    def update_process_type(self, code: str, name: str, description: str, order: int) -> bool:
        """更新工序类型"""
        try:
            config = self._load_json(self.process_config_file)
            types = config.get("process_types", [])
            
            for ptype in types:
                if ptype["code"] == code:
                    ptype["name"] = name
                    ptype["description"] = description
                    ptype["order"] = order
                    # 按顺序排序
                    types.sort(key=lambda x: x["order"])
                    self._save_json(self.process_config_file, config)
                    return True
            
            print(f"工序类型 {code} 不存在")
            return False
        except Exception as e:
            print(f"更新工序类型失败: {e}")
            return False
    
    def delete_process_type(self, code: str) -> bool:
        """删除工序类型"""
        try:
            config = self._load_json(self.process_config_file)
            types = config.get("process_types", [])
            
            original_len = len(types)
            types = [t for t in types if t["code"] != code]
            
            if len(types) == original_len:
                print(f"工序类型 {code} 不存在")
                return False
            
            config["process_types"] = types
            self._save_json(self.process_config_file, config)
            return True
        except Exception as e:
            print(f"删除工序类型失败: {e}")
            return False
    
    # ==================== 会计科目配置 ====================
    
    def get_account_structure(self) -> Dict[str, List[Dict[str, str]]]:
        """获取会计科目结构"""
        return self._load_json(self.account_config_file)
    
    def add_account(self, category: str, code: str, name: str, account_category: str) -> bool:
        """添加会计科目"""
        try:
            config = self._load_json(self.account_config_file)
            
            if category not in config:
                config[category] = []
            
            accounts = config[category]
            
            # 检查是否已存在
            if any(a["code"] == code for a in accounts):
                print(f"会计科目 {code} 已存在")
                return False
            
            accounts.append({"code": code, "name": name, "category": account_category})
            # 按科目代码排序
            accounts.sort(key=lambda x: x["code"])
            self._save_json(self.account_config_file, config)
            return True
        except Exception as e:
            print(f"添加会计科目失败: {e}")
            return False
    
    def update_account(self, category: str, code: str, name: str, account_category: str) -> bool:
        """更新会计科目"""
        try:
            config = self._load_json(self.account_config_file)
            
            if category not in config:
                print(f"科目类别 {category} 不存在")
                return False
            
            accounts = config[category]
            
            for account in accounts:
                if account["code"] == code:
                    account["name"] = name
                    account["category"] = account_category
                    self._save_json(self.account_config_file, config)
                    return True
            
            print(f"会计科目 {code} 不存在")
            return False
        except Exception as e:
            print(f"更新会计科目失败: {e}")
            return False
    
    def delete_account(self, category: str, code: str) -> bool:
        """删除会计科目"""
        try:
            config = self._load_json(self.account_config_file)
            
            if category not in config:
                print(f"科目类别 {category} 不存在")
                return False
            
            accounts = config[category]
            original_len = len(accounts)
            accounts = [a for a in accounts if a["code"] != code]
            
            if len(accounts) == original_len:
                print(f"会计科目 {code} 不存在")
                return False
            
            config[category] = accounts
            self._save_json(self.account_config_file, config)
            return True
        except Exception as e:
            print(f"删除会计科目失败: {e}")
            return False
    
    # ==================== 报表格式配置 ====================
    
    def get_report_formats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有报表格式"""
        return self._load_json(self.report_config_file)
    
    def update_report_format(self, report_type: str, name: str, sections: List[str], format_type: str) -> bool:
        """更新报表格式"""
        try:
            config = self._load_json(self.report_config_file)
            
            config[report_type] = {
                "name": name,
                "sections": sections,
                "format": format_type
            }
            
            self._save_json(self.report_config_file, config)
            return True
        except Exception as e:
            print(f"更新报表格式失败: {e}")
            return False
    
    def get_report_format(self, report_type: str) -> Optional[Dict[str, Any]]:
        """获取指定报表格式"""
        config = self._load_json(self.report_config_file)
        return config.get(report_type)
    
    # ==================== 配置导出导入 ====================
    
    def export_all_configs(self, export_path: str) -> bool:
        """导出所有配置到指定目录"""
        try:
            export_dir = Path(export_path)
            export_dir.mkdir(exist_ok=True)
            
            # 导出各类配置文件
            import shutil
            shutil.copy(self.pricing_config_file, export_dir / "pricing_methods.json")
            shutil.copy(self.process_config_file, export_dir / "process_types.json")
            shutil.copy(self.account_config_file, export_dir / "account_structure.json")
            shutil.copy(self.report_config_file, export_dir / "report_formats.json")
            
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_all_configs(self, import_path: str) -> bool:
        """从指定目录导入所有配置"""
        try:
            import_dir = Path(import_path)
            
            if not import_dir.exists():
                print(f"导入目录不存在: {import_path}")
                return False
            
            # 导入各类配置文件
            import shutil
            if (import_dir / "pricing_methods.json").exists():
                shutil.copy(import_dir / "pricing_methods.json", self.pricing_config_file)
            if (import_dir / "process_types.json").exists():
                shutil.copy(import_dir / "process_types.json", self.process_config_file)
            if (import_dir / "account_structure.json").exists():
                shutil.copy(import_dir / "account_structure.json", self.account_config_file)
            if (import_dir / "report_formats.json").exists():
                shutil.copy(import_dir / "report_formats.json", self.report_config_file)
            
            return True
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False
