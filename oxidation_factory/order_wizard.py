# -*- coding: utf-8 -*-
"""
订单录入向导
提供分步向导式的订单录入界面
"""

from datetime import datetime
from .order_manager import Order
from .config import get_config

class OrderWizard:
    """订单录入向导"""
    
    def __init__(self):
        self.config = get_config()
        self.order = Order()
    
    def run(self) -> Order:
        """
        运行向导，返回创建的订单对象
        
        Returns:
            Order: 订单对象，如果用户取消则返回None
        """
        print("\n" + "=" * 60)
        print("     新建加工订单 - 分步向导")
        print("=" * 60)
        
        # 步骤1：基本信息
        if not self._step1_basic_info():
            return None
        
        # 步骤2：计价信息
        if not self._step2_pricing_info():
            return None
        
        # 步骤3：工序信息
        if not self._step3_process_info():
            return None
        
        # 步骤4：确认信息
        if not self._step4_confirm():
            return None
        
        return self.order
    
    def _step1_basic_info(self) -> bool:
        """步骤1：基本信息"""
        print("\n" + "-" * 60)
        print("步骤 1/4：基本信息")
        print("-" * 60)
        
        # 订单编号
        while True:
            order_no = input("订单编号（如 PO20260209001）: ").strip()
            if order_no:
                self.order.order_no = order_no
                break
            print("❌ 订单编号不能为空")
        
        # 客户名称
        while True:
            customer = input("客户名称: ").strip()
            if customer:
                self.order.customer = customer
                break
            print("❌ 客户名称不能为空")
        
        # 订单日期
        date_str = input("订单日期（回车使用今天，格式：2026-02-09）: ").strip()
        if date_str:
            try:
                self.order.order_date = datetime.strptime(date_str, "%Y-%m-%d")
            except:
                print("⚠️ 日期格式错误，使用今天")
                self.order.order_date = datetime.now()
        else:
            self.order.order_date = datetime.now()
        
        # 物品名称
        while True:
            item_name = input("物品名称（如：铝合金外壳）: ").strip()
            if item_name:
                self.order.item_name = item_name
                break
            print("❌ 物品名称不能为空")
        
        return True
    
    def _step2_pricing_info(self) -> bool:
        """步骤2：计价信息"""
        print("\n" + "-" * 60)
        print("步骤 2/4：计价信息")
        print("-" * 60)
        
        # 计价单位
        units = self.config.get_pricing_units()
        print("\n可选计价单位:")
        for i, unit in enumerate(units, 1):
            print(f"  {i}. {unit}")
        
        while True:
            choice = input(f"请选择计价单位 (1-{len(units)}): ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(units):
                    self.order.pricing_unit = units[idx]
                    break
            print("❌ 无效选择")
        
        # 数量
        while True:
            quantity_str = input(f"数量（{self.order.pricing_unit}）: ").strip()
            try:
                quantity = float(quantity_str)
                if quantity > 0:
                    self.order.quantity = quantity
                    break
                else:
                    print("❌ 数量必须大于0")
            except:
                print("❌ 请输入有效数字")
        
        # 单价
        while True:
            price_str = input(f"单价（元/{self.order.pricing_unit}）: ").strip()
            try:
                price = float(price_str)
                if price > 0:
                    self.order.unit_price = price
                    break
                else:
                    print("❌ 单价必须大于0")
            except:
                print("❌ 请输入有效数字")
        
        # 计算订单金额
        self.order.calculate_amount()
        print(f"\n💰 订单金额：{self.order.order_amount:.2f} 元")
        
        return True
    
    def _step3_process_info(self) -> bool:
        """步骤3：工序信息"""
        print("\n" + "-" * 60)
        print("步骤 3/4：工序信息")
        print("-" * 60)
        
        # 工序明细
        process_details = input("工序明细（如：喷砂、氧化、封孔）: ").strip()
        self.order.process_details = process_details if process_details else "氧化"
        
        # 外发工序
        processes = self.config.get_outsourced_processes()
        print("\n外发工序（可多选，用逗号分隔，回车跳过）:")
        for i, process in enumerate(processes, 1):
            print(f"  {i}. {process}")
        
        outsourced_input = input("请选择外发工序（如：1,2 或直接回车）: ").strip()
        if outsourced_input:
            try:
                indices = [int(x.strip()) - 1 for x in outsourced_input.split(',')]
                self.order.outsourced_processes = [processes[i] for i in indices if 0 <= i < len(processes)]
            except:
                print("⚠️ 输入格式错误，跳过外发工序")
        
        # 外发成本
        if self.order.outsourced_processes:
            cost_str = input("外发成本（元）: ").strip()
            try:
                self.order.outsourced_cost = float(cost_str) if cost_str else 0.0
            except:
                print("⚠️ 成本格式错误，设为0")
                self.order.outsourced_cost = 0.0
        
        # 备注
        remark = input("备注（可选）: ").strip()
        self.order.remark = remark
        
        return True
    
    def _step4_confirm(self) -> bool:
        """步骤4：确认信息"""
        print("\n" + "-" * 60)
        print("步骤 4/4：确认信息")
        print("-" * 60)
        
        # 显示订单信息
        print(f"\n订单编号：{self.order.order_no}")
        print(f"客户名称：{self.order.customer}")
        print(f"订单日期：{self.order.order_date.strftime('%Y-%m-%d')}")
        print(f"物品名称：{self.order.item_name}")
        print(f"计价方式：{self.order.quantity} {self.order.pricing_unit} × {self.order.unit_price} 元/{self.order.pricing_unit}")
        print(f"订单金额：{self.order.order_amount:.2f} 元")
        print(f"工序明细：{self.order.process_details}")
        if self.order.outsourced_processes:
            print(f"外发工序：{', '.join(self.order.outsourced_processes)}")
            print(f"外发成本：{self.order.outsourced_cost:.2f} 元")
            print(f"预计利润：{self.order.order_amount - self.order.outsourced_cost:.2f} 元")
        if self.order.remark:
            print(f"备注：{self.order.remark}")
        
        # 确认
        print("\n" + "-" * 60)
        confirm = input("确认创建订单？(Y/n): ").strip().lower()
        
        if confirm in ['', 'y', 'yes']:
            return True
        else:
            print("❌ 已取消创建")
            return False


def create_order_interactive():
    """交互式创建订单"""
    wizard = OrderWizard()
    order = wizard.run()
    return order
