"""
Main entry point for Oxidation Workflow System.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxidation_workflow_v18.config import get_config


def main():
    """Main application entry point."""
    print("=" * 60)
    print("氧化加工厂工作流程优化系统 V1.8")
    print("Oxidation Factory Workflow Optimization System")
    print("=" * 60)
    print()
    
    # Initialize configuration
    config = get_config()
    print(f"✓ 配置加载成功")
    print(f"  数据路径: {config.get('storage.data_path')}")
    print(f"  备份路径: {config.get('storage.backup_path')}")
    print(f"  演示模式: {'开启' if config.get('system.demo_mode') else '关闭'}")
    print()
    
    print("系统初始化完成！")
    print()
    print("注意：完整的用户界面将在后续任务中实现。")
    print("当前版本仅包含项目结构和配置管理功能。")
    print()


if __name__ == "__main__":
    main()
