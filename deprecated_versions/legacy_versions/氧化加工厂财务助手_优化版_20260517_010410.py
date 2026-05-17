# -*- coding: utf-8 -*-
"""
氧化加工厂财务助手 V1.1 - 优化版
专为氧化加工行业定制的财务管理工具
"""

import os
import sys
from datetime import datetime

# 导入氧化加工厂模块
try:
    from oxidation_factory import get_config, get_storage
    from oxidation_factory.order_wizard import create_order_interactive
    from oxidation_factory.order_manager import Order
    print("✅ 氧化加工厂模块加载成功")
except Exception as e:
    print(f"⚠️ 模块加载失败: {e}")
    print("💡 提示：请确保 oxidation_factory 模块在当前目录")
    sys.exit(1)

class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_main_menu():
    """显示主菜单"""
    print("\n" + "=" * 70)
    print(f"{Color.HEADER}             氧化加工厂财务助手 V1.1{Color.ENDC}")
    print("=" * 70)
    
    print(f"\n{Color.CYAN}【订单管理】{Color.ENDC}")
    print("  01. 📋 新建加工订单")
    print("  02. 📖 查看订单列表")
    print("  03. 🔍 搜索订单")
    print("  04. 💰 订单统计分析")
    print("  05. 📤 导出订单到Excel")
    
    print(f"\n{Color.CYAN}【示例数据】{Color.ENDC}")
    print("  10. 📊 生成示例数据")
    
    print(f"\n{Color.CYAN}【系统设置】{Color.ENDC}")
    print("  20. ⚙️  查看系统配置")
    print("  21. 📖 使用教程")
    
    print(f"\n{Color.CYAN}【其他功能】{Color.ENDC}")
    print("  99. 🚪 退出系统")
    
    print("\n" + "=" * 70)

def create_order():
    """创建订单"""
    print("\n" + "=" * 70)
    print("     新建加工订单")
    print("=" * 70)
    
    print("\n💡 提示：订单将自动保存到本地")
    print("   位置：财务数据/本地订单/orders.json\n")
    
    # 使用向导创建订单
    order = create_order_interactive()
    
    if order:
        # 保存到本地
        storage = get_storage()
        if storage.save_order(order):
            print("\n" + "=" * 70)
            print("✅ 订单创建成功！")
            print("=" * 70)
            print("\n📋 订单详情:")
            print(f"  订单编号: {order.order_no}")
            print(f"  客户名称: {order.customer}")
            print(f"  物品名称: {order.item_name}")
            print(f"  计价方式: {order.quantity} {order.pricing_unit} × {order.unit_price} 元")
            print(f"  订单金额: {order.order_amount:.2f} 元")
            if order.outsourced_cost > 0:
                print(f"  外发成本: {order.outsourced_cost:.2f} 元")
                print(f"  预计利润: {order.order_amount - order.outsourced_cost:.2f} 元")
            print(f"\n📁 订单已保存到：财务数据/本地订单/orders.json")
        else:
            print("\n⚠️ 订单保存失败")
    else:
        print("\n⚠️ 订单创建已取消")

def list_orders():
    """查看订单列表"""
    print("\n" + "=" * 70)
    print("     订单列表")
    print("=" * 70)
    
    storage = get_storage()
    orders = storage.get_all_orders()
    
    if not orders:
        print("\n⚠️ 暂无订单数据")
        print("💡 提示：请先创建订单（功能01）或生成示例数据（功能10）")
        return
    
    print(f"\n📊 共有 {len(orders)} 个订单\n")
    
    # 按日期排序（最新的在前）
    orders.sort(key=lambda x: x.get("order_date", ""), reverse=True)
    
    # 显示订单列表
    for i, order in enumerate(orders, 1):
        print(f"{i}. {order['order_no']} - {order['customer']}")
        print(f"   物品：{order['item_name']}")
        print(f"   金额：{order['order_amount']:.2f}元 | 状态：{order['status']}")
        print(f"   日期：{order['order_date']}")
        
        if i < len(orders):
            print()
    
    # 询问是否查看详情
    print("\n" + "-" * 70)
    choice = input("\n是否查看订单详情？(输入订单编号，直接回车返回): ").strip()
    
    if choice:
        show_order_detail(choice)

def show_order_detail(order_no: str):
    """显示订单详情"""
    storage = get_storage()
    order = storage.get_order_by_no(order_no)
    
    if not order:
        print(f"\n❌ 未找到订单：{order_no}")
        return
    
    print("\n" + "=" * 70)
    print(f"     订单详情 - {order_no}")
    print("=" * 70)
    
    print(f"\n📋 基本信息:")
    print(f"  订单编号: {order['order_no']}")
    print(f"  客户名称: {order['customer']}")
    print(f"  订单日期: {order['order_date']}")
    print(f"  物品名称: {order['item_name']}")
    print(f"  订单状态: {order['status']}")
    
    print(f"\n💰 计价信息:")
    print(f"  计价单位: {order['pricing_unit']}")
    print(f"  数量: {order['quantity']}")
    print(f"  单价: {order['unit_price']} 元")
    print(f"  订单金额: {order['order_amount']:.2f} 元")
    
    print(f"\n💵 收款信息:")
    print(f"  已收款: {order['paid_amount']:.2f} 元")
    print(f"  未收款: {order['unpaid_amount']:.2f} 元")
    
    print(f"\n🔧 工序信息:")
    print(f"  工序明细: {order['process_details']}")
    if order['outsourced_processes']:
        print(f"  外发工序: {', '.join(order['outsourced_processes'])}")
        print(f"  外发成本: {order['outsourced_cost']:.2f} 元")
        print(f"  预计利润: {order['order_amount'] - order['outsourced_cost']:.2f} 元")
    
    if order.get('remark'):
        print(f"\n📝 备注: {order['remark']}")
    
    print(f"\n⏰ 创建时间: {order.get('created_at', '未知')}")

def search_orders():
    """搜索订单"""
    print("\n" + "=" * 70)
    print("     搜索订单")
    print("=" * 70)
    
    print("\n💡 提示：直接回车跳过该条件\n")
    
    # 输入搜索条件
    customer = input("客户名称（支持模糊搜索）: ").strip()
    
    print("\n可选状态：待生产、生产中、已完工、已结算")
    status = input("订单状态: ").strip()
    
    date_from = input("开始日期（格式：2026-01-01）: ").strip()
    date_to = input("结束日期（格式：2026-12-31）: ").strip()
    
    # 执行搜索
    storage = get_storage()
    results = storage.search_orders(
        customer=customer if customer else None,
        status=status if status else None,
        date_from=date_from if date_from else None,
        date_to=date_to if date_to else None
    )
    
    if not results:
        print("\n⚠️ 未找到符合条件的订单")
        return
    
    print(f"\n📊 找到 {len(results)} 个订单\n")
    
    # 显示搜索结果
    for i, order in enumerate(results, 1):
        print(f"{i}. {order['order_no']} - {order['customer']}")
        print(f"   物品：{order['item_name']}")
        print(f"   金额：{order['order_amount']:.2f}元 | 状态：{order['status']}")
        print(f"   日期：{order['order_date']}")
        
        if i < len(results):
            print()
    
    # 询问是否查看详情
    print("\n" + "-" * 70)
    choice = input("\n是否查看订单详情？(输入订单编号，直接回车返回): ").strip()
    
    if choice:
        show_order_detail(choice)

def show_statistics():
    """显示订单统计"""
    print("\n" + "=" * 70)
    print("     订单统计分析")
    print("=" * 70)
    
    storage = get_storage()
    stats = storage.get_statistics()
    
    if stats["total_orders"] == 0:
        print("\n⚠️ 暂无订单数据")
        print("💡 提示：请先创建订单（功能01）或生成示例数据（功能10）")
        return
    
    print(f"\n📊 总体统计:")
    print(f"  订单总数: {stats['total_orders']} 个")
    print(f"  订单总额: {stats['total_amount']:.2f} 元")
    print(f"  已收款: {stats['total_paid']:.2f} 元")
    print(f"  未收款: {stats['total_unpaid']:.2f} 元")
    print(f"  收款率: {(stats['total_paid'] / stats['total_amount'] * 100):.1f}%")
    
    print(f"\n📋 按状态统计:")
    for status, data in stats['by_status'].items():
        print(f"  {status}: {data['count']}个订单，金额 {data['amount']:.2f}元")
    
    print(f"\n👥 按客户统计:")
    # 按金额排序
    customers = sorted(stats['by_customer'].items(), 
                      key=lambda x: x[1]['amount'], reverse=True)
    for customer, data in customers[:10]:  # 只显示前10个
        print(f"  {customer}: {data['count']}个订单，金额 {data['amount']:.2f}元，未收款 {data['unpaid']:.2f}元")
    
    if len(customers) > 10:
        print(f"  ... 还有 {len(customers) - 10} 个客户")
    
    print(f"\n📏 按计价单位统计:")
    for unit, data in stats['by_unit'].items():
        print(f"  {unit}: {data['count']}个订单，数量 {data['quantity']}，金额 {data['amount']:.2f}元")

def export_orders():
    """导出订单到Excel"""
    print("\n" + "=" * 70)
    print("     导出订单到Excel")
    print("=" * 70)
    
    storage = get_storage()
    orders = storage.get_all_orders()
    
    if not orders:
        print("\n⚠️ 暂无订单数据")
        return
    
    print(f"\n📊 准备导出 {len(orders)} 个订单...")
    
    if storage.export_to_excel():
        print("\n✅ 导出成功！")
        print("📁 文件位置：财务数据/本地订单/")
    else:
        print("\n❌ 导出失败")

def generate_demo_data():
    """生成示例数据"""
    print("\n" + "=" * 70)
    print("     生成示例数据")
    print("=" * 70)
    
    print("\n正在生成示例数据...")
    
    try:
        # 运行示例数据生成脚本
        import subprocess
        result = subprocess.run([sys.executable, "create_oxidation_demo_data.py"], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print(result.stdout)
            print("\n✅ 示例数据生成成功！")
            print(f"📁 文件位置：财务数据/示例数据/")
        else:
            print(f"\n❌ 生成失败：{result.stderr}")
    except Exception as e:
        print(f"\n❌ 生成异常：{str(e)}")

def show_config():
    """显示系统配置"""
    print("\n" + "=" * 70)
    print("     系统配置")
    print("=" * 70)
    
    try:
        config = get_config()
        
        print(f"\n📋 计价单位 ({len(config.get_pricing_units())}种):")
        for unit in config.get_pricing_units():
            print(f"  - {unit}")
        
        print(f"\n🔧 外发工序 ({len(config.get_outsourced_processes())}种):")
        for process in config.get_outsourced_processes():
            print(f"  - {process}")
        
        print(f"\n📦 原材料类型 ({len(config.get_material_types())}种):")
        for material in config.get_material_types():
            print(f"  - {material}")
        
        print(f"\n🏦 银行账户:")
        for bank_name, bank_info in config.get_bank_accounts().items():
            print(f"  - {bank_name} ({bank_info['type']})")
        
        print(f"\n💰 费用分类:")
        categories = config.get_default_categories()
        print(f"  收入: {len(categories.get('收入', []))}类")
        print(f"  支出: {len(categories.get('支出', []))}类")
        
        print(f"\n🤖 AI分类:")
        print(f"  状态: {'启用' if config.is_ai_enabled() else '禁用'}")
        print(f"  置信度阈值: {config.get_ai_confidence_threshold()}")
        
    except Exception as e:
        print(f"\n❌ 配置加载失败：{str(e)}")

def show_tutorial():
    """显示使用教程"""
    print("\n" + "=" * 70)
    print("     使用教程")
    print("=" * 70)
    
    print(f"\n{Color.CYAN}📖 快速开始{Color.ENDC}")
    print("1. 首次使用：生成示例数据（功能10）")
    print("2. 学习操作：新建加工订单（功能01）")
    print("3. 查看订单：订单列表（功能02）")
    print("4. 搜索订单：搜索功能（功能03）")
    print("5. 查看统计：统计分析（功能04）")
    print("6. 导出数据：导出Excel（功能05）")
    
    print(f"\n{Color.CYAN}📋 订单录入流程{Color.ENDC}")
    print("步骤1：输入基本信息（订单编号、客户、日期、物品）")
    print("步骤2：输入计价信息（单位、数量、单价）")
    print("步骤3：输入工序信息（工序明细、外发工序、成本）")
    print("步骤4：确认信息并创建")
    
    print(f"\n{Color.CYAN}💡 计价单位说明{Color.ENDC}")
    print("  件 - 按件数计价（如：1000件 × 2.5元/件）")
    print("  条 - 按条数计价（如：300条 × 12元/条）")
    print("  只 - 按只数计价（如：5000只 × 0.8元/只）")
    print("  个 - 按个数计价（如：10000个 × 0.5元/个）")
    print("  米长 - 按长度计价（如：500米 × 8元/米）")
    print("  米重 - 按重量计价（如：200公斤 × 15元/公斤）")
    print("  平方 - 按面积计价（如：50平方 × 80元/平方）")
    
    print(f"\n{Color.CYAN}🔧 外发工序说明{Color.ENDC}")
    print("  喷砂 - 表面喷砂处理")
    print("  拉丝 - 表面拉丝处理")
    print("  抛光 - 表面抛光处理")
    print("  💡 外发工序可多选，系统会自动计算预计利润")
    
    print(f"\n{Color.CYAN}📚 详细文档{Color.ENDC}")
    print("  查看：快速使用指南.txt")
    print("  包含：4个典型业务场景 + 常见问题解答")

def main():
    """主函数"""
    print(f"\n{Color.GREEN}{'=' * 70}{Color.ENDC}")
    print(f"{Color.GREEN}     欢迎使用氧化加工厂财务助手！{Color.ENDC}")
    print(f"{Color.GREEN}{'=' * 70}{Color.ENDC}")
    
    print(f"\n{Color.CYAN}💡 V1.1 新功能：{Color.ENDC}")
    print("  ✅ 订单自动保存到本地（无需飞书）")
    print("  ✅ 查看订单列表和详情")
    print("  ✅ 搜索订单（按客户、状态、日期）")
    print("  ✅ 订单统计分析（总额、收款率、客户排名）")
    print("  ✅ 导出订单到Excel")
    
    print(f"\n{Color.CYAN}💡 系统特色：{Color.ENDC}")
    print("  ✅ 支持7种计价单位（件/条/只/个/米长/米重/平方）")
    print("  ✅ 支持外发工序管理（喷砂/拉丝/抛光）")
    print("  ✅ 自动计算订单金额和预计利润")
    print("  ✅ 分步向导，简单易用")
    print("  ✅ 完整示例数据，依葫芦画瓢")
    
    while True:
        show_main_menu()
        
        choice = input(f"\n{Color.BOLD}请选择功能编号：{Color.ENDC}").strip()
        
        if choice == "01":
            create_order()
        elif choice == "02":
            list_orders()
        elif choice == "03":
            search_orders()
        elif choice == "04":
            show_statistics()
        elif choice == "05":
            export_orders()
        elif choice == "10":
            generate_demo_data()
        elif choice == "20":
            show_config()
        elif choice == "21":
            show_tutorial()
        elif choice == "99":
            print(f"\n{Color.GREEN}👋 感谢使用，再见！{Color.ENDC}\n")
            break
        else:
            print(f"\n{Color.FAIL}❌ 无效选择，请重新输入{Color.ENDC}")
        
        input(f"\n{Color.CYAN}按回车键继续...{Color.ENDC}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Color.WARNING}⚠️ 用户中断操作{Color.ENDC}")
        print(f"{Color.GREEN}👋 感谢使用，再见！{Color.ENDC}\n")
    except Exception as e:
        print(f"\n{Color.FAIL}❌ 程序异常：{str(e)}{Color.ENDC}\n")
        import traceback
        traceback.print_exc()
