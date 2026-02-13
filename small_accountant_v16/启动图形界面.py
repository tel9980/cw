#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小企业会计助手 - 图形界面启动器

一键启动图形界面版本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from ui.simple_gui import SmallAccountantGUI
    
    def main():
        """启动图形界面"""
        print("🚀 正在启动小企业会计助手图形界面...")
        print("📋 版本: V1.6 - 优化版")
        print("⚡ 特性: 高性能Excel处理 + 友好GUI界面")
        print("-" * 50)
        
        try:
            app = SmallAccountantGUI()
            app.run()
        except KeyboardInterrupt:
            print("\n👋 用户取消，程序退出")
        except Exception as e:
            print(f"❌ 程序运行错误: {e}")
            input("按回车键退出...")
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("💡 请确保已安装所有依赖包:")
    print("   pip install -r requirements.txt")
    input("按回车键退出...")
except Exception as e:
    print(f"❌ 启动失败: {e}")
    input("按回车键退出...")