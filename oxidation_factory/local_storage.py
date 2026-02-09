# -*- coding: utf-8 -*-
"""
本地存储模块
用于在没有飞书配置时，将订单保存到本地JSON文件
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from .order_manager import Order


class LocalStorage:
    """本地存储管理器"""
    
    def __init__(self, storage_dir: str = "财务数据/本地订单"):
        """
        初始化本地存储
        
        Args:
            storage_dir: 存储目录路径
        """
        self.storage_dir = storage_dir
        self.orders_file = os.path.join(storage_dir, "orders.json")
        
        # 确保目录存在
        os.makedirs(storage_dir, exist_ok=True)
        
        # 如果文件不存在，创建空文件
        if not os.path.exists(self.orders_file):
            self._save_orders([])
    
    def _save_orders(self, orders: List[Dict]):
        """保存订单列表到文件"""
        with open(self.orders_file, 'w', encoding='utf-8') as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
    
    def _load_orders(self) -> List[Dict]:
        """从文件加载订单列表"""
        try:
            with open(self.orders_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 加载订单失败：{e}")
            return []
    
    def save_order(self, order: Order) -> bool:
        """
        保存订单到本地
        
        Args:
            order: 订单对象
        
        Returns:
            bool: 是否保存成功
        """
        try:
            orders = self._load_orders()
            
            # 转换订单为字典
            order_dict = {
                "order_no": order.order_no,
                "customer": order.customer,
                "order_date": order.order_date.strftime("%Y-%m-%d"),
                "item_name": order.item_name,
                "pricing_unit": order.pricing_unit,
                "quantity": order.quantity,
                "unit_price": order.unit_price,
                "order_amount": order.order_amount,
                "paid_amount": order.paid_amount,
                "unpaid_amount": order.unpaid_amount,
                "process_details": order.process_details,
                "outsourced_processes": order.outsourced_processes,
                "outsourced_cost": order.outsourced_cost,
                "status": order.status,
                "remark": order.remark,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 检查订单号是否已存在
            existing_index = None
            for i, existing_order in enumerate(orders):
                if existing_order["order_no"] == order.order_no:
                    existing_index = i
                    break
            
            if existing_index is not None:
                # 更新现有订单
                orders[existing_index] = order_dict
                print(f"✅ 订单已更新：{order.order_no}")
            else:
                # 添加新订单
                orders.append(order_dict)
                print(f"✅ 订单已保存：{order.order_no}")
            
            self._save_orders(orders)
            return True
            
        except Exception as e:
            print(f"❌ 保存订单失败：{e}")
            return False
    
    def get_all_orders(self) -> List[Dict]:
        """获取所有订单"""
        return self._load_orders()
    
    def get_order_by_no(self, order_no: str) -> Optional[Dict]:
        """
        根据订单号获取订单
        
        Args:
            order_no: 订单编号
        
        Returns:
            订单字典或None
        """
        orders = self._load_orders()
        for order in orders:
            if order["order_no"] == order_no:
                return order
        return None
    
    def search_orders(self, 
                     customer: str = None,
                     status: str = None,
                     date_from: str = None,
                     date_to: str = None) -> List[Dict]:
        """
        搜索订单
        
        Args:
            customer: 客户名称（可选）
            status: 订单状态（可选）
            date_from: 开始日期（可选，格式：YYYY-MM-DD）
            date_to: 结束日期（可选，格式：YYYY-MM-DD）
        
        Returns:
            符合条件的订单列表
        """
        orders = self._load_orders()
        results = []
        
        for order in orders:
            # 客户名称过滤
            if customer and customer not in order["customer"]:
                continue
            
            # 订单状态过滤
            if status and order["status"] != status:
                continue
            
            # 日期范围过滤
            if date_from and order["order_date"] < date_from:
                continue
            
            if date_to and order["order_date"] > date_to:
                continue
            
            results.append(order)
        
        return results
    
    def get_statistics(self) -> Dict:
        """
        获取订单统计信息
        
        Returns:
            统计信息字典
        """
        orders = self._load_orders()
        
        if not orders:
            return {
                "total_orders": 0,
                "total_amount": 0.0,
                "total_paid": 0.0,
                "total_unpaid": 0.0,
                "by_status": {},
                "by_customer": {},
                "by_unit": {}
            }
        
        total_amount = sum(o["order_amount"] for o in orders)
        total_paid = sum(o["paid_amount"] for o in orders)
        total_unpaid = sum(o["unpaid_amount"] for o in orders)
        
        # 按状态统计
        by_status = {}
        for order in orders:
            status = order["status"]
            if status not in by_status:
                by_status[status] = {"count": 0, "amount": 0.0}
            by_status[status]["count"] += 1
            by_status[status]["amount"] += order["order_amount"]
        
        # 按客户统计
        by_customer = {}
        for order in orders:
            customer = order["customer"]
            if customer not in by_customer:
                by_customer[customer] = {"count": 0, "amount": 0.0, "unpaid": 0.0}
            by_customer[customer]["count"] += 1
            by_customer[customer]["amount"] += order["order_amount"]
            by_customer[customer]["unpaid"] += order["unpaid_amount"]
        
        # 按计价单位统计
        by_unit = {}
        for order in orders:
            unit = order["pricing_unit"]
            if unit not in by_unit:
                by_unit[unit] = {"count": 0, "quantity": 0, "amount": 0.0}
            by_unit[unit]["count"] += 1
            by_unit[unit]["quantity"] += order["quantity"]
            by_unit[unit]["amount"] += order["order_amount"]
        
        return {
            "total_orders": len(orders),
            "total_amount": total_amount,
            "total_paid": total_paid,
            "total_unpaid": total_unpaid,
            "by_status": by_status,
            "by_customer": by_customer,
            "by_unit": by_unit
        }
    
    def delete_order(self, order_no: str) -> bool:
        """
        删除订单
        
        Args:
            order_no: 订单编号
        
        Returns:
            bool: 是否删除成功
        """
        try:
            orders = self._load_orders()
            original_count = len(orders)
            
            orders = [o for o in orders if o["order_no"] != order_no]
            
            if len(orders) < original_count:
                self._save_orders(orders)
                print(f"✅ 订单已删除：{order_no}")
                return True
            else:
                print(f"⚠️ 未找到订单：{order_no}")
                return False
                
        except Exception as e:
            print(f"❌ 删除订单失败：{e}")
            return False
    
    def export_to_excel(self, output_file: str = None) -> bool:
        """
        导出订单到Excel
        
        Args:
            output_file: 输出文件路径（可选）
        
        Returns:
            bool: 是否导出成功
        """
        try:
            import pandas as pd
            
            orders = self._load_orders()
            
            if not orders:
                print("⚠️ 没有订单可导出")
                return False
            
            # 转换为DataFrame
            df = pd.DataFrame(orders)
            
            # 重新排列列顺序
            columns = [
                "order_no", "customer", "order_date", "item_name",
                "pricing_unit", "quantity", "unit_price", "order_amount",
                "paid_amount", "unpaid_amount", "process_details",
                "outsourced_processes", "outsourced_cost", "status",
                "remark", "created_at"
            ]
            
            # 只保留存在的列
            columns = [col for col in columns if col in df.columns]
            df = df[columns]
            
            # 设置中文列名
            df.columns = [
                "订单编号", "客户名称", "订单日期", "物品名称",
                "计价单位", "数量", "单价", "订单金额",
                "已收款", "未收款", "工序明细",
                "外发工序", "外发成本", "订单状态",
                "备注", "创建时间"
            ][:len(columns)]
            
            # 生成文件名
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"财务数据/本地订单/订单导出_{timestamp}.xlsx"
            
            # 导出到Excel
            df.to_excel(output_file, index=False, engine='openpyxl')
            
            print(f"✅ 订单已导出：{output_file}")
            return True
            
        except ImportError:
            print("❌ 导出失败：需要安装 pandas 和 openpyxl")
            print("💡 运行：pip install pandas openpyxl")
            return False
        except Exception as e:
            print(f"❌ 导出失败：{e}")
            return False


# 全局存储实例
_storage = None

def get_storage() -> LocalStorage:
    """获取本地存储实例"""
    global _storage
    if _storage is None:
        _storage = LocalStorage()
    return _storage
