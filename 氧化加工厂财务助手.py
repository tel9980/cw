# -*- coding: utf-8 -*-
"""
氧化加工厂财务助手 V1.0
专为氧化加工行业定制的财务管理工具
"""

import os
import sys
from datetime import datetime

# 导入氧化加工厂模块
try:
    from oxidation_factory import get_config
    from oxidation_factory.order_wizard import create_order_interactive
    print("✅ 氧化加工厂模块加载成功")
except Exception as e:
    print(f"⚠️ 模块加载失败: {e}")
    print("💡 提示：请确保 oxidation_factory 模块在当前目录")

class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def show_main_menu():
    """显示主菜单"""
    print("\n" + "=" * 70)
    print(f"{Color.HEADER}             氧化加工厂财务助手 V1.0{Color.ENDC}")
    print("=" * 70)
    
    print(f"\n{Color.CYAN}【快捷操作】{Color.ENDC}")
    print("  01. 📋 新建加工订单")
    print("  02. 💰 查看订单统计")
    print("  03. 📊 生成示例数据")
    
    print(f"\n{Color.CYAN}【系统设置】{Color.ENDC}")
    print("  10. ⚙️  查看系统配置")
    print("  11. 📖 使用教程")
    
    print(f"\n{Color.CYAN}【其他功能】{Color.ENDC}")
    print("  99. 🚪 退出系统")
    
    print("\n" + "=" * 70)

def create_order_demo():
    """创建订单演示"""
    print("\n" + "=" * 70)
    print("     新建加工订单")
    print("=" * 70)
    
    print("\n💡 提示：这是订单录入演示，实际使用需要配置飞书")
    print("   当前版本展示订单管理的核心功能\n")
    
    # 使用向导创建订单
    order = create_order_interactive()
    
    if order:
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
        print("\n💡 提示：配置飞书后，订单将自动保存到云端")
    else:
        print("\n⚠️ 订单创建已取消")

def show_statistics_demo():
    """显示统计演示"""
    print("\n" + "=" * 70)
    print("     订单统计演示")
    print("=" * 70)
    
    print("\n📊 统计功能包括:")
    print("  - 订单总额统计")
    print("  - 已收款/未收款统计")
    print("  - 按客户统计")
    print("  - 按计价单位统计")
    print("  - 按订单状态统计")
    
    print("\n💡 提示：配置飞书后可查看实时统计数据")

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
    print("1. 首次使用：生成示例数据（选项03）")
    print("2. 学习操作：新建加工订单（选项01）")
    print("3. 查看配置：系统配置（选项10）")
    
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
    print("  查看：.kiro/specs/oxidation-factory-optimization/QUICKSTART.md")
    print("  包含：6个典型业务场景 + 10个常见问题解答")

def main():
    """主函数"""
    print(f"\n{Color.GREEN}{'=' * 70}{Color.ENDC}")
    print(f"{Color.GREEN}     欢迎使用氧化加工厂财务助手！{Color.ENDC}")
    print(f"{Color.GREEN}{'=' * 70}{Color.ENDC}")
    
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
            create_order_demo()
        elif choice == "02":
            show_statistics_demo()
        elif choice == "03":
            generate_demo_data()
        elif choice == "10":
            show_config()
        elif choice == "11":
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
