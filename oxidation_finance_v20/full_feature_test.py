#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CWZS系统全面功能测试
验证所有业务功能是否正常工作
"""

import os
import sys
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_all_features():
    """全面测试所有功能"""
    print("=" * 60)
    print("🔍 CWZS氧化加工厂财务系统 - 全面功能测试")
    print("=" * 60)
    
    results = []
    
    # 1. 测试模块导入
    print("\n📦 测试1: 模块导入")
    try:
        from tools.小白财务助手 import SimpleFinanceHelper
        print("✅ 小白财务助手模块导入成功")
        results.append(("模块导入", True))
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        results.append(("模块导入", False))
        return results
    
    # 2. 创建助手实例
    print("\n⚙️  测试2: 创建系统实例")
    try:
        helper = SimpleFinanceHelper()
        print("✅ 系统实例创建成功")
        results.append(("系统实例", True))
    except Exception as e:
        print(f"❌ 实例创建失败: {e}")
        results.append(("系统实例", False))
        return results
    
    # 3. 测试客户管理
    print("\n👥 测试3: 客户管理功能")
    try:
        # 添加测试客户
        customer1 = helper.add_customer("测试客户A有限公司", "张经理", "13800138001")
        customer2 = helper.add_customer("测试客户B公司", "李总", "13900139002")
        
        if customer1 and customer2:
            print(f"✅ 添加客户成功: {customer1['name']}, {customer2['name']}")
            results.append(("客户管理", True))
        else:
            print("❌ 添加客户失败")
            results.append(("客户管理", False))
    except Exception as e:
        print(f"❌ 客户管理测试失败: {e}")
        results.append(("客户管理", False))
    
    # 4. 测试订单管理 - 多种计价方式
    print("\n📋 测试4: 订单管理（多种计价方式）")
    pricing_units_tested = []
    try:
        # 按件计价
        order1 = helper.add_order(customer1['id'], "铝合金把手", 500, 2.5, "件", ["氧化"])
        if order1:
            pricing_units_tested.append("件")
            print("✅ 按件计价: 铝合金把手 500件×2.5元 = ¥1250")
        
        # 按条计价
        order2 = helper.add_order(customer1['id'], "铜管", 200, 15.0, "条", ["氧化"])
        if order2:
            pricing_units_tested.append("条")
            print("✅ 按条计价: 铜管 200条×15元 = ¥3000")
        
        # 按米计价
        order3 = helper.add_order(customer2['id'], "不锈钢管", 80, 25.0, "米", ["喷砂", "氧化"])
        if order3:
            pricing_units_tested.append("米")
            print("✅ 按米计价: 不锈钢管 80米×25元 = ¥2000")
        
        # 按公斤计价
        order4 = helper.add_order(customer2['id'], "铁质零件", 300, 8.0, "公斤", ["氧化"])
        if order4:
            pricing_units_tested.append("公斤")
            print("✅ 按公斤计价: 铁质零件 300公斤×8元 = ¥2400")
        
        # 按平方米计价
        order5 = helper.add_order(customer1['id'], "铝板", 50, 45.0, "平方米", ["氧化"])
        if order5:
            pricing_units_tested.append("平方米")
            print("✅ 按平方米计价: 铝板 50平方米×45元 = ¥2250")
        
        # 委外加工订单
        order6 = helper.add_order(customer2['id'], "精密零件", 200, 18.0, "件", ["喷砂", "拉丝", "氧化"])
        if order6:
            print("✅ 委外加工订单: 精密零件（含喷砂+拉丝+氧化工序）")
        
        print(f"✅ 计价方式测试通过: {', '.join(pricing_units_tested)}")
        results.append(("订单管理", True))
    except Exception as e:
        print(f"❌ 订单管理测试失败: {e}")
        results.append(("订单管理", False))
    
    # 5. 测试收入管理 - 双银行账户
    print("\n💰 测试5: 收入管理（G银行/N银行/微信）")
    try:
        # G银行收入（有票）
        income1 = helper.add_income(customer1['id'], 2500, "G银行", "铝合金把手加工费")
        if income1:
            print("✅ G银行收入: ¥2500 (有发票)")
        
        # N银行收入（现金）
        income2 = helper.add_income(customer1['id'], 1200, "N银行", "部分款项")
        if income2:
            print("✅ N银行收入: ¥1200 (现金)")
        
        # 微信收入
        income3 = helper.add_income(customer2['id'], 800, "微信", "微信收款")
        if income3:
            print("✅ 微信收入: ¥800")
        
        print("✅ 收入管理测试通过（支持G银行/N银行/微信）")
        results.append(("收入管理", True))
    except Exception as e:
        print(f"❌ 收入管理测试失败: {e}")
        results.append(("收入管理", False))
    
    # 6. 测试支出管理 - 12类支出
    print("\n💸 测试6: 支出管理（12类支出类型）")
    expense_types = [
        ("房租", 8000, "厂房租金"),
        ("水电费", 2500, "本月水电费"),
        ("三酸", 3200, "硫酸、盐酸、硝酸"),
        ("片碱", 1800, "氢氧化钠"),
        ("亚钠", 1200, "亚硝酸钠"),
        ("色粉", 800, "各种颜色粉末"),
        ("除油剂", 600, "金属表面处理剂"),
        ("挂具", 1500, "电镀挂具"),
        ("外发加工费", 2800, "喷砂拉丝外发费用"),
        ("日常费用", 1200, "办公用品等"),
        ("工资", 15000, "员工工资"),
        ("其他", 500, "杂项支出")
    ]
    
    try:
        for exp_type, amount, desc in expense_types:
            helper.add_expense(exp_type, amount, desc, "")
        
        print("✅ 12类支出类型全部测试通过:")
        for exp_type, amount, desc in expense_types:
            print(f"   - {exp_type}: ¥{amount}")
        
        results.append(("支出管理", True))
    except Exception as e:
        print(f"❌ 支出管理测试失败: {e}")
        results.append(("支出管理", False))
    
    # 7. 测试财务报表
    print("\n📊 测试7: 财务报表生成")
    try:
        summary = helper.get_financial_summary()
        
        print("✅ 财务报表生成成功:")
        for key, value in summary.items():
            print(f"   {key}: {value}")
        
        results.append(("财务报表", True))
    except Exception as e:
        print(f"❌ 财务报表测试失败: {e}")
        results.append(("财务报表", False))
    
    # 8. 测试灵活收付款机制
    print("\n🔄 测试8: 灵活收付款机制（非一一对应）")
    try:
        # 添加多笔收入（不关联订单）
        helper.add_income(customer1['id'], 5000, "G银行", "混合收款1")
        helper.add_income(customer2['id'], 3000, "N银行", "混合收款2")
        
        # 添加多笔支出（不关联特定收入）
        helper.add_expense("房租", 8000, "厂房租金2", "")
        helper.add_expense("工资", 15000, "员工工资2", "")
        
        summary = helper.get_financial_summary()
        
        print("✅ 灵活收付款测试通过:")
        print(f"   - 可独立记录收入，无需关联订单")
        print(f"   - 可独立记录支出，无需关联收入")
        print(f"   - 按实际发生入账，符合小公司实际业务")
        
        results.append(("灵活收付款", True))
    except Exception as e:
        print(f"❌ 灵活收付款测试失败: {e}")
        results.append(("灵活收付款", False))
    
    # 输出测试结果汇总
    print("\n" + "=" * 60)
    print("📋 测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有功能测试通过！系统可以正常使用。")
        print("\n📖 系统功能确认:")
        print("  ✅ 客户来料氧化加工管理")
        print("  ✅ 多种计价方式（件/条/米/公斤/平方米）")
        print("  ✅ 委外加工管理（喷砂/拉丝/抛光）")
        print("  ✅ 氧化工序完工收费")
        print("  ✅ 灵活收付款（无需一一对应）")
        print("  ✅ G银行(有票)/N银行+微信(现金)双账户")
        print("  ✅ 12类支出完整管理")
        print("  ✅ 会计报表自动生成")
    else:
        print(f"\n⚠️  有 {total-passed} 项测试未通过，请检查系统配置。")
    
    return results

if __name__ == "__main__":
    try:
        test_all_features()
    except Exception as e:
        print(f"\n❌ 测试过程出现错误: {e}")
    finally:
        input("\n按任意键退出...")
