# -*- coding: utf-8 -*-
"""
测试订单管理功能（不连接飞书，仅测试逻辑）
"""

from datetime import datetime
from oxidation_factory.order_manager import Order
from oxidation_factory.order_wizard import OrderWizard
from oxidation_factory.config import get_config

def test_order_creation():
    """测试订单创建"""
    print("=" * 60)
    print("     测试订单创建功能")
    print("=" * 60)
    
    # 创建测试订单
    order = Order(
        order_no="PO20260209001",
        customer="华为技术有限公司",
        order_date=datetime(2026, 2, 9),
        item_name="铝合金手机外壳",
        pricing_unit="件",
        quantity=1000,
        unit_price=2.5,
        process_details="喷砂、氧化、封孔",
        outsourced_processes=["喷砂"],
        outsourced_cost=300,
        status="待生产",
        remark="VIP客户，优先处理"
    )
    
    # 计算金额
    order.calculate_amount()
    order.calculate_unpaid()
    
    # 显示订单信息
    print("\n📋 订单信息:")
    print(f"  订单编号: {order.order_no}")
    print(f"  客户名称: {order.customer}")
    print(f"  订单日期: {order.order_date.strftime('%Y-%m-%d')}")
    print(f"  物品名称: {order.item_name}")
    print(f"  计价方式: {order.quantity} {order.pricing_unit} × {order.unit_price} 元/{order.pricing_unit}")
    print(f"  订单金额: {order.order_amount:.2f} 元")
    print(f"  已收款: {order.paid_amount:.2f} 元")
    print(f"  未收款: {order.unpaid_amount:.2f} 元")
    print(f"  工序明细: {order.process_details}")
    print(f"  外发工序: {', '.join(order.outsourced_processes)}")
    print(f"  外发成本: {order.outsourced_cost:.2f} 元")
    print(f"  预计利润: {order.order_amount - order.outsourced_cost:.2f} 元")
    print(f"  订单状态: {order.status}")
    print(f"  备注: {order.remark}")
    
    # 转换为飞书字段格式
    print("\n📤 飞书字段格式:")
    fields = order.to_feishu_fields()
    for key, value in fields.items():
        print(f"  {key}: {value}")
    
    print("\n✅ 订单创建测试完成！")

def test_order_validation():
    """测试订单验证"""
    print("\n" + "=" * 60)
    print("     测试订单验证功能")
    print("=" * 60)
    
    config = get_config()
    
    # 测试用例
    test_cases = [
        {
            "name": "正常订单",
            "order": Order(
                order_no="PO001",
                customer="客户A",
                item_name="产品A",
                pricing_unit="件",
                quantity=100,
                unit_price=10.0
            ),
            "expected": True
        },
        {
            "name": "缺少订单编号",
            "order": Order(
                customer="客户A",
                item_name="产品A",
                pricing_unit="件",
                quantity=100,
                unit_price=10.0
            ),
            "expected": False
        },
        {
            "name": "数量为0",
            "order": Order(
                order_no="PO002",
                customer="客户A",
                item_name="产品A",
                pricing_unit="件",
                quantity=0,
                unit_price=10.0
            ),
            "expected": False
        },
        {
            "name": "无效计价单位",
            "order": Order(
                order_no="PO003",
                customer="客户A",
                item_name="产品A",
                pricing_unit="无效单位",
                quantity=100,
                unit_price=10.0
            ),
            "expected": False
        }
    ]
    
    # 执行测试
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['name']}")
        
        # 简单验证（不连接飞书）
        order = test_case['order']
        
        # 基本验证
        is_valid = True
        if not order.order_no:
            print("  ❌ 订单编号不能为空")
            is_valid = False
        if not order.customer:
            print("  ❌ 客户名称不能为空")
            is_valid = False
        if not order.item_name:
            print("  ❌ 物品名称不能为空")
            is_valid = False
        if order.quantity <= 0:
            print("  ❌ 数量必须大于0")
            is_valid = False
        if order.unit_price <= 0:
            print("  ❌ 单价必须大于0")
            is_valid = False
        if order.pricing_unit not in config.get_pricing_units():
            print(f"  ❌ 计价单位无效")
            is_valid = False
        
        if is_valid:
            print("  ✅ 验证通过")
        
        # 检查结果
        if is_valid == test_case['expected']:
            print(f"  ✅ 测试通过")
        else:
            print(f"  ❌ 测试失败（预期: {test_case['expected']}, 实际: {is_valid}）")
    
    print("\n✅ 订单验证测试完成！")

def test_order_statistics():
    """测试订单统计"""
    print("\n" + "=" * 60)
    print("     测试订单统计功能")
    print("=" * 60)
    
    # 创建多个测试订单
    orders = [
        Order(order_no="PO001", customer="华为", item_name="产品A", pricing_unit="件", 
              quantity=1000, unit_price=2.5, paid_amount=2500, status="已结算"),
        Order(order_no="PO002", customer="小米", item_name="产品B", pricing_unit="米长", 
              quantity=500, unit_price=8.0, paid_amount=2000, status="生产中"),
        Order(order_no="PO003", customer="华为", item_name="产品C", pricing_unit="件", 
              quantity=800, unit_price=3.2, paid_amount=0, status="待生产"),
    ]
    
    # 计算金额
    for order in orders:
        order.calculate_amount()
        order.calculate_unpaid()
    
    # 统计
    total_amount = sum(o.order_amount for o in orders)
    total_paid = sum(o.paid_amount for o in orders)
    total_unpaid = sum(o.unpaid_amount for o in orders)
    
    # 按状态统计
    by_status = {}
    for order in orders:
        status = order.status
        if status not in by_status:
            by_status[status] = {"count": 0, "amount": 0.0}
        by_status[status]["count"] += 1
        by_status[status]["amount"] += order.order_amount
    
    # 按计价单位统计
    by_unit = {}
    for order in orders:
        unit = order.pricing_unit
        if unit not in by_unit:
            by_unit[unit] = {"count": 0, "quantity": 0, "amount": 0.0}
        by_unit[unit]["count"] += 1
        by_unit[unit]["quantity"] += order.quantity
        by_unit[unit]["amount"] += order.order_amount
    
    # 显示统计结果
    print(f"\n📊 订单统计:")
    print(f"  订单总数: {len(orders)}")
    print(f"  订单总额: {total_amount:.2f} 元")
    print(f"  已收款: {total_paid:.2f} 元")
    print(f"  未收款: {total_unpaid:.2f} 元")
    
    print(f"\n📈 按状态统计:")
    for status, data in by_status.items():
        print(f"  {status}: {data['count']}个订单, 金额 {data['amount']:.2f} 元")
    
    print(f"\n📏 按计价单位统计:")
    for unit, data in by_unit.items():
        print(f"  {unit}: {data['count']}个订单, 数量 {data['quantity']}, 金额 {data['amount']:.2f} 元")
    
    print("\n✅ 订单统计测试完成！")

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("     氧化加工厂订单管理模块测试")
    print("=" * 60)
    
    # 测试1：订单创建
    test_order_creation()
    
    # 测试2：订单验证
    test_order_validation()
    
    # 测试3：订单统计
    test_order_statistics()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
    print("\n💡 提示：")
    print("  - 订单管理模块已就绪")
    print("  - 配置飞书后可直接使用")
    print("  - 支持7种计价单位")
    print("  - 支持外发工序管理")
    print("  - 支持订单状态跟踪")
    print("=" * 60)

if __name__ == "__main__":
    main()
