# -*- coding: utf-8 -*-
"""
测试氧化加工厂配置模块
"""

from oxidation_factory.config import get_config

def test_config():
    """测试配置加载和功能"""
    print("=" * 60)
    print("     氧化加工厂配置模块测试")
    print("=" * 60)
    
    # 获取配置实例
    config = get_config()
    
    # 测试计价单位
    print("\n📋 计价单位:")
    for unit in config.get_pricing_units():
        print(f"  - {unit}")
    
    # 测试外发工序
    print("\n🔧 外发工序:")
    for process in config.get_outsourced_processes():
        print(f"  - {process}")
    
    # 测试原材料类型
    print("\n📦 原材料类型:")
    for material in config.get_material_types():
        print(f"  - {material}")
    
    # 测试银行账户
    print("\n🏦 银行账户配置:")
    for bank_name, bank_info in config.get_bank_accounts().items():
        print(f"  - {bank_name}:")
        print(f"    类型: {bank_info['type']}")
        print(f"    有票: {'是' if bank_info['has_invoice'] else '否'}")
        print(f"    现金: {'是' if bank_info['is_cash'] else '否'}")
    
    # 测试费用分类
    print("\n💰 默认费用分类:")
    categories = config.get_default_categories()
    print(f"  收入类别 ({len(categories.get('收入', []))}个):")
    for cat in categories.get('收入', []):
        print(f"    - {cat}")
    print(f"  支出类别 ({len(categories.get('支出', []))}个):")
    for cat in categories.get('支出', []):
        print(f"    - {cat}")
    
    # 测试分类关键词
    print("\n🔍 分类关键词示例:")
    keywords = config.get_category_keywords()
    sample_categories = ["原材料-三酸", "外发加工-喷砂", "房租"]
    for cat in sample_categories:
        if cat in keywords:
            print(f"  {cat}: {', '.join(keywords[cat])}")
    
    # 测试AI配置
    print("\n🤖 AI分类配置:")
    print(f"  启用状态: {'启用' if config.is_ai_enabled() else '禁用'}")
    print(f"  置信度阈值: {config.get_ai_confidence_threshold()}")
    print(f"  行业上下文: {config.get_ai_context()[:50]}...")
    
    # 验证配置
    print("\n✅ 配置验证:")
    if config.validate():
        print("  配置完整性检查通过！")
    else:
        print("  配置存在问题，请检查！")
    
    print("\n" + "=" * 60)
    print("✅ 配置模块测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_config()
