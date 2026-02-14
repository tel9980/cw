#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
氧化加工厂财务系统 - 统一启动入口
直接运行此文件即可启动系统
"""
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
oxi_path = os.path.join(project_root, "oxidation_finance_v20")
sys.path.insert(0, oxi_path)

def main():
    """主入口"""
    print("="*60)
    print("🏭 氧化加工厂财务系统 V2.0")
    print("="*60)
    print()
    print("请选择启动方式:")
    print("  1. 启动菜单式界面（推荐新手）")
    print("  2. 启动Web浏览器界面")
    print("  3. 运行功能测试")
    print("  4. 生成示例数据")
    print("  0. 退出")
    print("="*60)
    
    choice = input("\n请选择 [0-4]: ").strip()
    
    if choice == "1":
        # 启动菜单式界面
        from tools.小白财务助手 import main as小白助手
        小白助手()
        
    elif choice == "2":
        # 启动Web界面
        print("\n正在启动Web服务...")
        print("请在浏览器中访问: http://localhost:5000")
        print("按 Ctrl+C 停止服务\n")
        import web_app
        web_app.app.run(debug=True, host='0.0.0.0', port=5000)
        
    elif choice == "3":
        # 运行测试
        print("\n运行功能测试...")
        os.chdir(oxi_path)
        import pytest
        sys.exit(pytest.main(["-xvs", "tests/", "-k", "test_customer"]))
        
    elif choice == "4":
        # 生成示例数据
        print("\n生成示例数据...")
        from tools.小白财务助手 import SimpleFinanceHelper, create_sample_data
        helper = SimpleFinanceHelper()
        create_sample_data(helper)
        print("\n✅ 示例数据生成完成！")
        
    else:
        print("\n👋 再见！")

if __name__ == "__main__":
    main()
