#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
氧化加工厂财务系统 V2.0 - 统一启动器
提供图形化菜单选择不同启动方式
"""

import os
import sys
import subprocess
from pathlib import Path


class Launcher:
    """启动器主类"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.main_project = self.project_root / "oxidation_finance_v20"

    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """打印标题"""
        print("\n" + "=" * 70)
        print("  🏭 氧化加工厂财务系统 V2.0 - 启动器")
        print("=" * 70)
        print()

    def print_menu(self):
        """打印菜单"""
        print("请选择启动方式：\n")
        print("  1. 🌐 启动 Web 界面")
        print("  2. 📊 启动演示数据生成器")
        print("  3. 🧪 运行测试套件")
        print("  4. 📦 运行数据库迁移")
        print("  5. 🔧 系统设置向导")
        print("  6. 📈 快速面板")
        print("  7. 💾 备份与恢复")
        print("  8. 🚪 退出")
        print()

    def launch_web_interface(self):
        """启动Web界面"""
        print("\n🚀 正在启动 Web 界面...")

        try:
            os.chdir(self.main_project)
            subprocess.run([sys.executable, "web_app.py"], check=True)
        except subprocess.CalledProcessError:
            print("❌ Web界面启动失败")
        except FileNotFoundError:
            print("❌ 找不到 web_app.py 文件")
        except Exception as e:
            print(f"❌ 启动失败: {e}")

    def launch_demo_generator(self):
        """启动演示数据生成器"""
        print("\n🚀 正在启动演示数据生成器...")

        try:
            demo_script = self.main_project / "examples" / "generate_comprehensive_demo.py"
            os.chdir(self.main_project)
            subprocess.run([sys.executable, str(demo_script)], check=True)
        except subprocess.CalledProcessError:
            print("❌ 演示数据生成失败")
        except FileNotFoundError:
            print("❌ 找不到演示数据生成脚本")
        except Exception as e:
            print(f"❌ 启动失败: {e}")

    def launch_tests(self):
        """运行测试套件"""
        print("\n🧪 正在运行测试套件...")

        try:
            os.chdir(self.main_project)
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
                capture_output=False
            )

            if result.returncode == 0:
                print("\n✅ 所有测试通过！")
            else:
                print("\n⚠️ 部分测试失败，请检查输出")
        except Exception as e:
            print(f"❌ 测试运行失败: {e}")

    def launch_setup_wizard(self):
        """启动设置向导"""
        print("\n🔧 正在启动系统设置向导...")

        try:
            wizard_script = self.main_project / "tools" / "setup_wizard.py"
            os.chdir(self.main_project)
            subprocess.run([sys.executable, str(wizard_script)], check=True)
        except subprocess.CalledProcessError:
            print("❌ 设置向导运行失败")
        except FileNotFoundError:
            print("❌ 找不到设置向导脚本")
        except Exception as e:
            print(f"❌ 启动失败: {e}")

    def launch_quick_panel(self):
        """启动快速面板"""
        print("\n📈 正在启动快速面板...")

        try:
            panel_script = self.main_project / "tools" / "quick_panel.py"
            os.chdir(self.main_project)
            subprocess.run([sys.executable, str(panel_script)], check=True)
        except subprocess.CalledProcessError:
            print("❌ 快速面板启动失败")
        except FileNotFoundError:
            print("❌ 找不到快速面板脚本")
        except Exception as e:
            print(f"❌ 启动失败: {e}")

    def launch_backup_restore(self):
        """启动备份恢复工具"""
        print("\n💾 正在启动备份恢复工具...")

        try:
            backup_script = self.main_project / "tools" / "backup_restore.py"
            os.chdir(self.main_project)
            subprocess.run([sys.executable, str(backup_script)], check=True)
        except subprocess.CalledProcessError:
            print("❌ 备份恢复工具运行失败")
        except FileNotFoundError:
            print("❌ 找不到备份恢复脚本")
        except Exception as e:
            print(f"❌ 启动失败: {e}")

    def run(self):
        """运行启动器"""
        while True:
            self.clear_screen()
            self.print_header()
            self.print_menu()

            try:
                choice = input("请输入选项 (1-8): ").strip()

                if choice == '1':
                    self.launch_web_interface()
                elif choice == '2':
                    self.launch_demo_generator()
                elif choice == '3':
                    self.launch_tests()
                elif choice == '4':
                    self.run_migration()
                elif choice == '5':
                    self.launch_setup_wizard()
                elif choice == '6':
                    self.launch_quick_panel()
                elif choice == '7':
                    self.launch_backup_restore()
                elif choice == '8':
                    print("\n👋 感谢使用，再见！\n")
                    break
                else:
                    print("\n⚠️ 无效的选项，请重新选择")
                    input("\n按回车键继续...")

            except KeyboardInterrupt:
                print("\n\n👋 退出启动器")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                input("\n按回车键继续...")

    def run_migration(self):
        """运行数据库迁移"""
        print("\n📦 正在运行数据库迁移...")

        try:
            migration_script = self.main_project / "tools" / "migrate_to_text_amounts.py"
            os.chdir(self.main_project)
            subprocess.run([sys.executable, str(migration_script)], check=True)
        except subprocess.CalledProcessError:
            print("❌ 数据库迁移失败")
        except FileNotFoundError:
            print("❌ 找不到迁移脚本")
        except Exception as e:
            print(f"❌ 迁移失败: {e}")


def main():
    """主函数"""
    launcher = Launcher()
    launcher.run()


if __name__ == "__main__":
    main()
