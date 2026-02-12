#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据管理器 - 处理Excel数据导入导出和数据备份恢复
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, date
from decimal import Decimal
import re
import shutil
import json
import sqlite3

from ..models.business_models import (
    BankTransaction, BankType, Customer, Supplier
)
from ..database.db_manager import DatabaseManager


class DataValidationError(Exception):
    """数据验证错误"""
    pass


class DataManager:
    """数据管理器 - 负责Excel数据导入导出和数据验证"""
    
    def __init__(self, db_manager: DatabaseManager):
        """初始化数据管理器"""
        self.db = db_manager
        self.validation_errors: List[str] = []
    
    def import_bank_statement(
        self,
        file_path: str,
        bank_type: BankType,
        date_column: str = "交易日期",
        amount_column: str = "金额",
        counterparty_column: str = "交易对手",
        description_column: str = "摘要"
    ) -> Tuple[int, List[str]]:
        """
        导入银行流水Excel文件
        
        Args:
            file_path: Excel文件路径
            bank_type: 银行类型（G银行或N银行）
            date_column: 日期列名
            amount_column: 金额列名
            counterparty_column: 交易对手列名
            description_column: 摘要列名
        
        Returns:
            (成功导入的记录数, 错误信息列表)
        """
        self.validation_errors = []
        
        # 1. 读取Excel文件
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            raise DataValidationError(f"无法读取Excel文件: {str(e)}")
        
        # 2. 验证必需列是否存在
        required_columns = [date_column, amount_column]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise DataValidationError(f"缺少必需列: {', '.join(missing_columns)}")
        
        # 3. 获取历史交易对手数据用于匹配
        customers = self.db.list_customers()
        suppliers = self.db.list_suppliers()
        
        # 4. 逐行处理数据
        imported_count = 0
        transactions = []
        
        for idx, row in df.iterrows():
            try:
                # 验证和解析数据
                transaction_data = self._parse_transaction_row(
                    row, idx, date_column, amount_column,
                    counterparty_column, description_column,
                    bank_type, customers, suppliers
                )
                
                if transaction_data:
                    transactions.append(transaction_data)
                    imported_count += 1
                    
            except Exception as e:
                self.validation_errors.append(f"第{idx+2}行错误: {str(e)}")
        
        # 5. 批量保存到数据库
        for transaction in transactions:
            self.db.save_bank_transaction(transaction)
        
        return imported_count, self.validation_errors
    
    def _parse_transaction_row(
        self,
        row: pd.Series,
        row_index: int,
        date_column: str,
        amount_column: str,
        counterparty_column: str,
        description_column: str,
        bank_type: BankType,
        customers: List[Customer],
        suppliers: List[Supplier]
    ) -> Optional[BankTransaction]:
        """解析单行交易数据"""
        
        # 1. 解析日期
        transaction_date = self._parse_date(row[date_column], row_index)
        if not transaction_date:
            return None
        
        # 2. 解析金额
        amount = self._parse_amount(row[amount_column], row_index)
        if amount is None:
            return None
        
        # 3. 获取交易对手和描述
        counterparty = ""
        if counterparty_column in row.index and pd.notna(row[counterparty_column]):
            counterparty = str(row[counterparty_column]).strip()
        
        description = ""
        if description_column in row.index and pd.notna(row[description_column]):
            description = str(row[description_column]).strip()
        
        # 4. 自动识别和匹配交易对手
        if counterparty:
            matched_counterparty = self._match_counterparty(
                counterparty, customers, suppliers
            )
            if matched_counterparty:
                counterparty = matched_counterparty
        
        # 5. 创建交易记录
        transaction = BankTransaction(
            bank_type=bank_type,
            transaction_date=transaction_date,
            amount=amount,
            counterparty=counterparty,
            description=description,
            matched=False
        )
        
        return transaction
    
    def _parse_date(self, date_value: Any, row_index: int) -> Optional[date]:
        """解析日期值"""
        if pd.isna(date_value):
            self.validation_errors.append(f"第{row_index+2}行: 日期为空")
            return None
        
        try:
            # 处理多种日期格式
            if isinstance(date_value, (datetime, pd.Timestamp)):
                return date_value.date()
            elif isinstance(date_value, date):
                return date_value
            elif isinstance(date_value, str):
                # 尝试多种日期格式
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%Y.%m.%d"]:
                    try:
                        return datetime.strptime(date_value, fmt).date()
                    except ValueError:
                        continue
                raise ValueError(f"无法解析日期格式: {date_value}")
            else:
                raise ValueError(f"不支持的日期类型: {type(date_value)}")
        except Exception as e:
            self.validation_errors.append(f"第{row_index+2}行: 日期解析错误 - {str(e)}")
            return None
    
    def _parse_amount(self, amount_value: Any, row_index: int) -> Optional[Decimal]:
        """解析金额值"""
        if pd.isna(amount_value):
            self.validation_errors.append(f"第{row_index+2}行: 金额为空")
            return None
        
        try:
            # 处理字符串格式的金额（可能包含逗号、货币符号等）
            if isinstance(amount_value, str):
                # 移除常见的非数字字符
                amount_str = re.sub(r'[,¥$￥\s]', '', amount_value)
                amount = Decimal(amount_str)
            else:
                amount = Decimal(str(amount_value))
            
            # 验证金额范围（防止异常值）
            if abs(amount) > Decimal("999999999.99"):
                raise ValueError("金额超出合理范围")
            
            return amount
            
        except Exception as e:
            self.validation_errors.append(f"第{row_index+2}行: 金额解析错误 - {str(e)}")
            return None
    
    def _match_counterparty(
        self,
        counterparty: str,
        customers: List[Customer],
        suppliers: List[Supplier]
    ) -> str:
        """
        自动识别和匹配交易对手
        
        使用模糊匹配算法，基于历史客户和供应商数据
        """
        if not counterparty:
            return counterparty
        
        # 清理交易对手名称
        clean_name = counterparty.strip()
        
        # 1. 精确匹配客户
        for customer in customers:
            if customer.name == clean_name:
                return customer.name
        
        # 2. 精确匹配供应商
        for supplier in suppliers:
            if supplier.name == clean_name:
                return supplier.name
        
        # 3. 模糊匹配客户（包含关系）
        for customer in customers:
            if customer.name in clean_name or clean_name in customer.name:
                return customer.name
        
        # 4. 模糊匹配供应商（包含关系）
        for supplier in suppliers:
            if supplier.name in clean_name or clean_name in supplier.name:
                return supplier.name
        
        # 5. 如果没有匹配，返回原始名称
        return counterparty
    
    def validate_import_data(
        self,
        file_path: str,
        date_column: str = "交易日期",
        amount_column: str = "金额"
    ) -> Tuple[bool, List[str]]:
        """
        验证导入数据的完整性和准确性
        
        Args:
            file_path: Excel文件路径
            date_column: 日期列名
            amount_column: 金额列名
        
        Returns:
            (是否通过验证, 错误信息列表)
        """
        errors = []
        
        # 1. 检查文件是否存在
        if not Path(file_path).exists():
            errors.append(f"文件不存在: {file_path}")
            return False, errors
        
        # 2. 尝试读取文件
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            errors.append(f"无法读取Excel文件: {str(e)}")
            return False, errors
        
        # 3. 检查是否为空
        if df.empty:
            errors.append("Excel文件为空，没有数据")
            return False, errors
        
        # 4. 检查必需列
        required_columns = [date_column, amount_column]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"缺少必需列: {', '.join(missing_columns)}")
        
        # 5. 检查数据完整性
        if date_column in df.columns:
            null_dates = df[date_column].isna().sum()
            if null_dates > 0:
                errors.append(f"发现{null_dates}行日期为空")
        
        if amount_column in df.columns:
            null_amounts = df[amount_column].isna().sum()
            if null_amounts > 0:
                errors.append(f"发现{null_amounts}行金额为空")
        
        # 6. 检查数据类型
        if amount_column in df.columns:
            for idx, value in enumerate(df[amount_column]):
                if pd.notna(value):
                    try:
                        if isinstance(value, str):
                            amount_str = re.sub(r'[,¥$￥\s]', '', value)
                            Decimal(amount_str)
                        else:
                            Decimal(str(value))
                    except:
                        errors.append(f"第{idx+2}行: 金额格式不正确 - {value}")
        
        # 7. 检查日期格式
        if date_column in df.columns:
            for idx, value in enumerate(df[date_column]):
                if pd.notna(value):
                    if not isinstance(value, (datetime, pd.Timestamp, date)):
                        if isinstance(value, str):
                            valid_format = False
                            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%Y.%m.%d"]:
                                try:
                                    datetime.strptime(value, fmt)
                                    valid_format = True
                                    break
                                except ValueError:
                                    continue
                            if not valid_format:
                                errors.append(f"第{idx+2}行: 日期格式不正确 - {value}")
        
        return len(errors) == 0, errors
    
    def get_import_summary(
        self,
        file_path: str,
        date_column: str = "交易日期",
        amount_column: str = "金额"
    ) -> Dict[str, Any]:
        """
        获取导入数据的摘要信息
        
        Returns:
            包含总行数、日期范围、金额范围等信息的字典
        """
        try:
            df = pd.read_excel(file_path)
            
            summary = {
                "total_rows": len(df),
                "columns": list(df.columns),
                "has_required_columns": all(col in df.columns for col in [date_column, amount_column])
            }
            
            if date_column in df.columns:
                valid_dates = df[date_column].dropna()
                if len(valid_dates) > 0:
                    summary["date_range"] = {
                        "start": str(valid_dates.min()),
                        "end": str(valid_dates.max())
                    }
            
            if amount_column in df.columns:
                valid_amounts = df[amount_column].dropna()
                if len(valid_amounts) > 0:
                    summary["amount_stats"] = {
                        "min": float(valid_amounts.min()),
                        "max": float(valid_amounts.max()),
                        "sum": float(valid_amounts.sum()),
                        "count": int(len(valid_amounts))
                    }
            
            return summary
            
        except Exception as e:
            return {"error": str(e)}
    
    # ==================== 数据备份和恢复 ====================
    
    def backup_system_data(
        self,
        backup_dir: str = "backups",
        include_config: bool = True
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        备份系统数据
        
        Args:
            backup_dir: 备份目录路径
            include_config: 是否包含系统配置参数
        
        Returns:
            (是否成功, 备份文件路径, 备份信息字典)
        """
        try:
            # 1. 创建备份目录
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 2. 生成备份文件名（带时间戳）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            backup_file = backup_path / f"{backup_name}.db"
            
            # 3. 备份SQLite数据库
            if not Path(self.db.db_path).exists():
                return False, "", {"error": "数据库文件不存在"}
            
            # 使用SQLite的备份API进行完整备份
            source_conn = sqlite3.connect(self.db.db_path)
            backup_conn = sqlite3.connect(str(backup_file))
            
            with backup_conn:
                source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            # 4. 收集备份统计信息
            backup_info = self._collect_backup_statistics()
            backup_info["backup_time"] = datetime.now().isoformat()
            backup_info["backup_file"] = str(backup_file)
            backup_info["database_size"] = Path(self.db.db_path).stat().st_size
            backup_info["backup_size"] = backup_file.stat().st_size
            
            # 5. 备份系统配置参数（如果需要）
            if include_config:
                config_file = backup_path / f"{backup_name}_config.json"
                config_data = self._export_system_config()
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                
                backup_info["config_file"] = str(config_file)
                backup_info["config_included"] = True
            else:
                backup_info["config_included"] = False
            
            # 6. 保存备份元数据
            metadata_file = backup_path / f"{backup_name}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            backup_info["metadata_file"] = str(metadata_file)
            
            return True, str(backup_file), backup_info
            
        except Exception as e:
            return False, "", {"error": f"备份失败: {str(e)}"}
    
    def restore_system_data(
        self,
        backup_file: str,
        restore_config: bool = True,
        validate_before_restore: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        恢复系统数据
        
        Args:
            backup_file: 备份文件路径
            restore_config: 是否恢复系统配置参数
            validate_before_restore: 恢复前是否验证备份文件
        
        Returns:
            (是否成功, 错误或警告信息列表)
        """
        messages = []
        
        try:
            backup_path = Path(backup_file)
            
            # 1. 验证备份文件是否存在
            if not backup_path.exists():
                return False, [f"备份文件不存在: {backup_file}"]
            
            # 2. 验证备份文件（如果需要）
            if validate_before_restore:
                is_valid, validation_errors = self._validate_backup_file(backup_file)
                if not is_valid:
                    return False, [f"备份文件验证失败: {', '.join(validation_errors)}"]
                messages.append("备份文件验证通过")
            
            # 3. 创建当前数据库的安全备份
            safety_backup = f"{self.db.db_path}.before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if Path(self.db.db_path).exists():
                shutil.copy2(self.db.db_path, safety_backup)
                messages.append(f"已创建安全备份: {safety_backup}")
            
            # 4. 关闭当前数据库连接
            if self.db.conn:
                self.db.close()
            
            # 5. 恢复数据库文件
            try:
                shutil.copy2(backup_file, self.db.db_path)
                messages.append("数据库文件恢复成功")
            except Exception as e:
                # 如果恢复失败，尝试还原安全备份
                if Path(safety_backup).exists():
                    shutil.copy2(safety_backup, self.db.db_path)
                    messages.append("恢复失败，已还原到恢复前状态")
                return False, [f"数据库恢复失败: {str(e)}"] + messages
            
            # 6. 重新连接数据库
            self.db.connect()
            messages.append("数据库连接已重新建立")
            
            # 7. 验证恢复后的数据完整性
            integrity_ok, integrity_errors = self._verify_database_integrity()
            if not integrity_ok:
                messages.append(f"警告: 数据完整性检查发现问题: {', '.join(integrity_errors)}")
            else:
                messages.append("数据完整性检查通过")
            
            # 8. 恢复系统配置参数（如果需要）
            if restore_config:
                config_file = backup_path.parent / f"{backup_path.stem}_config.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                        
                        self._import_system_config(config_data)
                        messages.append("系统配置参数恢复成功")
                    except Exception as e:
                        messages.append(f"警告: 配置参数恢复失败: {str(e)}")
                else:
                    messages.append("未找到配置文件，跳过配置恢复")
            
            # 9. 清理安全备份（可选，保留以防万一）
            # Path(safety_backup).unlink()
            
            return True, messages
            
        except Exception as e:
            return False, [f"恢复过程出错: {str(e)}"] + messages
    
    def _collect_backup_statistics(self) -> Dict[str, Any]:
        """收集备份统计信息"""
        stats = {}
        
        try:
            cursor = self.db.conn.cursor()
            
            # 统计各表的记录数
            tables = [
                'customers', 'suppliers', 'processing_orders', 'incomes',
                'expenses', 'bank_accounts', 'bank_transactions',
                'outsourced_processing', 'audit_logs', 'accounting_periods'
            ]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[f"{table}_count"] = count
            
            # 计算总记录数
            stats["total_records"] = sum(v for k, v in stats.items() if k.endswith('_count'))
            
        except Exception as e:
            stats["error"] = f"统计信息收集失败: {str(e)}"
        
        return stats
    
    def _export_system_config(self) -> Dict[str, Any]:
        """导出系统配置参数"""
        config = {
            "version": "1.0",
            "export_time": datetime.now().isoformat(),
            "database_path": self.db.db_path
        }
        
        try:
            # 导出客户列表（作为配置的一部分）
            customers = self.db.list_customers()
            config["customers"] = [
                {
                    "id": c.id,
                    "name": c.name,
                    "contact": c.contact,
                    "phone": c.phone,
                    "address": c.address,
                    "credit_limit": str(c.credit_limit),
                    "notes": c.notes
                }
                for c in customers
            ]
            
            # 导出供应商列表
            suppliers = self.db.list_suppliers()
            config["suppliers"] = [
                {
                    "id": s.id,
                    "name": s.name,
                    "contact": s.contact,
                    "phone": s.phone,
                    "address": s.address,
                    "business_type": s.business_type,
                    "notes": s.notes
                }
                for s in suppliers
            ]
            
            # 导出银行账户配置
            accounts = self.db.list_bank_accounts()
            config["bank_accounts"] = [
                {
                    "id": a.id,
                    "bank_type": a.bank_type.value,
                    "account_name": a.account_name,
                    "account_number": a.account_number,
                    "notes": a.notes
                }
                for a in accounts
            ]
            
        except Exception as e:
            config["export_error"] = str(e)
        
        return config
    
    def _import_system_config(self, config_data: Dict[str, Any]) -> None:
        """导入系统配置参数"""
        # 注意：这里只导入配置信息，不导入实际的业务数据
        # 业务数据已经通过数据库恢复完成
        
        # 可以在这里添加额外的配置导入逻辑
        # 例如：系统设置、用户偏好等
        pass
    
    def _validate_backup_file(self, backup_file: str) -> Tuple[bool, List[str]]:
        """验证备份文件的完整性和有效性"""
        errors = []
        
        try:
            backup_path = Path(backup_file)
            
            # 1. 检查文件大小
            if backup_path.stat().st_size == 0:
                errors.append("备份文件为空")
                return False, errors
            
            # 2. 尝试打开SQLite数据库
            try:
                conn = sqlite3.connect(str(backup_path))
                cursor = conn.cursor()
                
                # 3. 检查数据库完整性
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                if result[0] != "ok":
                    errors.append(f"数据库完整性检查失败: {result[0]}")
                
                # 4. 验证必需的表是否存在
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = [
                    'customers', 'suppliers', 'processing_orders',
                    'incomes', 'expenses', 'bank_accounts', 'bank_transactions'
                ]
                
                missing_tables = [t for t in required_tables if t not in tables]
                if missing_tables:
                    errors.append(f"缺少必需的表: {', '.join(missing_tables)}")
                
                conn.close()
                
            except sqlite3.Error as e:
                errors.append(f"无法打开备份文件作为SQLite数据库: {str(e)}")
                return False, errors
            
        except Exception as e:
            errors.append(f"验证过程出错: {str(e)}")
            return False, errors
        
        return len(errors) == 0, errors
    
    def _verify_database_integrity(self) -> Tuple[bool, List[str]]:
        """验证数据库完整性"""
        errors = []
        
        try:
            cursor = self.db.conn.cursor()
            
            # 1. SQLite完整性检查
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            if result[0] != "ok":
                errors.append(f"SQLite完整性检查失败: {result[0]}")
            
            # 2. 外键约束检查
            cursor.execute("PRAGMA foreign_key_check")
            fk_errors = cursor.fetchall()
            if fk_errors:
                errors.append(f"发现{len(fk_errors)}个外键约束违反")
            
            # 3. 基本数据一致性检查
            # 检查订单的客户ID是否都存在
            cursor.execute("""
                SELECT COUNT(*) FROM processing_orders 
                WHERE customer_id NOT IN (SELECT id FROM customers)
            """)
            orphan_orders = cursor.fetchone()[0]
            if orphan_orders > 0:
                errors.append(f"发现{orphan_orders}个订单的客户不存在")
            
            # 检查收入记录的客户ID是否都存在
            cursor.execute("""
                SELECT COUNT(*) FROM incomes 
                WHERE customer_id NOT IN (SELECT id FROM customers)
            """)
            orphan_incomes = cursor.fetchone()[0]
            if orphan_incomes > 0:
                errors.append(f"发现{orphan_incomes}个收入记录的客户不存在")
            
        except Exception as e:
            errors.append(f"完整性验证出错: {str(e)}")
        
        return len(errors) == 0, errors
    
    def list_backups(self, backup_dir: str = "backups") -> List[Dict[str, Any]]:
        """
        列出所有可用的备份
        
        Args:
            backup_dir: 备份目录路径
        
        Returns:
            备份信息列表
        """
        backups = []
        
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                return backups
            
            # 查找所有备份文件
            for db_file in backup_path.glob("backup_*.db"):
                backup_info = {
                    "backup_file": str(db_file),
                    "backup_name": db_file.stem,
                    "backup_size": db_file.stat().st_size,
                    "backup_time": datetime.fromtimestamp(db_file.stat().st_mtime).isoformat()
                }
                
                # 尝试读取元数据文件
                metadata_file = db_file.parent / f"{db_file.stem}_metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        backup_info.update(metadata)
                    except:
                        pass
                
                # 检查是否有配置文件
                config_file = db_file.parent / f"{db_file.stem}_config.json"
                backup_info["has_config"] = config_file.exists()
                
                backups.append(backup_info)
            
            # 按时间倒序排列
            backups.sort(key=lambda x: x["backup_time"], reverse=True)
            
        except Exception as e:
            pass
        
        return backups

