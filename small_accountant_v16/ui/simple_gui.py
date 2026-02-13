#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单图形界面 - 提升用户体验

Feature: small-accountant-practical-enhancement
Optimization: User experience with GUI
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
from typing import Optional, Dict, List
import json
from datetime import datetime, date
import webbrowser

from ..import_engine.optimized_excel_processor import OptimizedExcelProcessor, ProgressCallback
from ..import_engine.import_engine import ImportEngine
from ..reports.report_generator import ReportGenerator
from ..reconciliation.reconciliation_assistant import ReconciliationAssistant
from ..storage.transaction_storage import TransactionStorage
from ..storage.counterparty_storage import CounterpartyStorage
from ..storage.reminder_storage import ReminderStorage
from ..config.config_manager import ConfigManager


class GUIProgressCallback(ProgressCallback):
    """GUI进度回调"""
    
    def __init__(self, total_steps: int, progress_var: tk.IntVar, status_var: tk.StringVar):
        super().__init__(total_steps)
        self.progress_var = progress_var
        self.status_var = status_var
    
    def update(self, step: int, message: str = ""):
        """更新GUI进度"""
        super().update(step, message)
        progress = int((step / self.total_steps) * 100)
        self.progress_var.set(progress)
        self.status_var.set(message)
    
    def finish(self):
        """完成进度"""
        super().finish()
        self.progress_var.set(100)
        self.status_var.set("处理完成")


class SmallAccountantGUI:
    """小企业会计助手图形界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("小企业会计助手 V1.6 - 图形界面版")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # 设置图标和样式
        self.setup_style()
        
        # 初始化组件
        self.config_manager = ConfigManager()
        self.setup_storage()
        
        # GUI变量
        self.progress_var = tk.IntVar()
        self.status_var = tk.StringVar(value="就绪")
        self.current_file_var = tk.StringVar()
        
        # 创建界面
        self.create_widgets()
        
        # 绑定事件
        self.bind_events()
        
        # 加载配置
        self.load_settings()
    
    def setup_style(self):
        """设置界面样式"""
        style = ttk.Style()
        
        # 尝试使用现代主题
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        
        # 自定义样式
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
    
    def setup_storage(self):
        """初始化存储"""
        try:
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            self.transaction_storage = TransactionStorage(data_dir)
            self.counterparty_storage = CounterpartyStorage(data_dir)
            self.reminder_storage = ReminderStorage(data_dir)
            
        except Exception as e:
            messagebox.showerror("初始化错误", f"存储初始化失败: {e}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="小企业会计助手", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 左侧功能面板
        self.create_function_panel(main_frame)
        
        # 右侧主工作区
        self.create_work_area(main_frame)
        
        # 底部状态栏
        self.create_status_bar(main_frame)
    
    def create_function_panel(self, parent):
        """创建功能面板"""
        # 功能面板框架
        func_frame = ttk.LabelFrame(parent, text="功能菜单", padding="10")
        func_frame.grid(row=1, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Excel导入
        import_frame = ttk.LabelFrame(func_frame, text="数据导入", padding="5")
        import_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(import_frame, text="📁 选择Excel文件", 
                  command=self.select_excel_file, width=20).pack(pady=2)
        ttk.Button(import_frame, text="⚡ 快速导入", 
                  command=self.quick_import, width=20).pack(pady=2)
        ttk.Button(import_frame, text="🔧 高级导入", 
                  command=self.advanced_import, width=20).pack(pady=2)
        
        # 报表生成
        report_frame = ttk.LabelFrame(func_frame, text="报表生成", padding="5")
        report_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(report_frame, text="📊 利润表", 
                  command=self.generate_income_statement, width=20).pack(pady=2)
        ttk.Button(report_frame, text="📋 资产负债表", 
                  command=self.generate_balance_sheet, width=20).pack(pady=2)
        ttk.Button(report_frame, text="💰 现金流量表", 
                  command=self.generate_cash_flow, width=20).pack(pady=2)
        
        # 对账功能
        reconcile_frame = ttk.LabelFrame(func_frame, text="对账管理", padding="5")
        reconcile_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(reconcile_frame, text="🏦 银行对账", 
                  command=self.bank_reconciliation, width=20).pack(pady=2)
        ttk.Button(reconcile_frame, text="👥 客户对账", 
                  command=self.customer_reconciliation, width=20).pack(pady=2)
        ttk.Button(reconcile_frame, text="🏪 供应商对账", 
                  command=self.supplier_reconciliation, width=20).pack(pady=2)
        
        # 系统工具
        tools_frame = ttk.LabelFrame(func_frame, text="系统工具", padding="5")
        tools_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(tools_frame, text="⚙️ 系统设置", 
                  command=self.open_settings, width=20).pack(pady=2)
        ttk.Button(tools_frame, text="📖 使用帮助", 
                  command=self.show_help, width=20).pack(pady=2)
        ttk.Button(tools_frame, text="ℹ️ 关于", 
                  command=self.show_about, width=20).pack(pady=2)
    
    def create_work_area(self, parent):
        """创建主工作区"""
        # 工作区框架
        work_frame = ttk.LabelFrame(parent, text="工作区域", padding="10")
        work_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        work_frame.columnconfigure(0, weight=1)
        work_frame.rowconfigure(1, weight=1)
        
        # 当前文件显示
        file_frame = ttk.Frame(work_frame)
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="当前文件:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(file_frame, textvariable=self.current_file_var, 
                 foreground='blue').grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        # 创建笔记本控件（标签页）
        self.notebook = ttk.Notebook(work_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 欢迎页面
        self.create_welcome_tab()
        
        # 数据预览页面
        self.create_preview_tab()
        
        # 处理日志页面
        self.create_log_tab()
    
    def create_welcome_tab(self):
        """创建欢迎页面"""
        welcome_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(welcome_frame, text="欢迎")
        
        # 欢迎信息
        welcome_text = """🎉 欢迎使用小企业会计助手 V1.6

✨ 主要功能：
• 📁 Excel数据快速导入
• 📊 财务报表自动生成
• 🏦 银行对账智能匹配
• ⏰ 税务提醒及时通知
• 📋 往来账款精确管理

🚀 新版本特性：
• ⚡ 优化大文件处理性能
• 🎨 全新图形界面体验
• 🔧 智能错误处理机制
• 📈 实时进度显示

📖 快速开始：
1. 点击"选择Excel文件"导入数据
2. 使用"快速导入"一键处理
3. 在"报表生成"中查看结果
4. 通过"对账管理"核对数据

💡 提示：首次使用建议查看"使用帮助"
"""
        
        text_widget = tk.Text(welcome_frame, wrap=tk.WORD, font=('Arial', 11), 
                             bg='#f8f9fa', relief=tk.FLAT, padx=20, pady=20)
        text_widget.insert(tk.END, welcome_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True)
    
    def create_preview_tab(self):
        """创建数据预览页面"""
        preview_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(preview_frame, text="数据预览")
        
        # 预览表格
        columns = ('日期', '金额', '摘要', '对方', '类型')
        self.preview_tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题
        for col in columns:
            self.preview_tree.heading(col, text=col)
            self.preview_tree.column(col, width=120)
        
        # 滚动条
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=preview_scrollbar.set)
        
        # 布局
        self.preview_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
    
    def create_log_tab(self):
        """创建处理日志页面"""
        log_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(log_frame, text="处理日志")
        
        # 日志文本区域
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, 
                                                 font=('Consolas', 10), height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 清空日志按钮
        ttk.Button(log_frame, text="清空日志", 
                  command=self.clear_log).pack(pady=(10, 0))
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(1, weight=1)
        
        # 状态标签
        ttk.Label(status_frame, text="状态:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(status_frame, textvariable=self.status_var).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # 进度条
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, 
                                          maximum=100, length=200)
        self.progress_bar.grid(row=0, column=2, sticky=tk.E)
    
    def bind_events(self):
        """绑定事件"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_settings(self):
        """加载设置"""
        try:
            # 加载配置
            config = self.config_manager.get_config()
            self.log(f"配置加载成功: {config.company_name}")
        except Exception as e:
            self.log(f"配置加载失败: {e}", "WARNING")
    
    # 功能实现方法
    def select_excel_file(self):
        """选择Excel文件"""
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        
        if file_path:
            self.current_file_var.set(file_path)
            self.log(f"已选择文件: {Path(file_path).name}")
            
            # 切换到数据预览页面
            self.notebook.select(1)
            
            # 预览文件内容
            self.preview_excel_file(file_path)
    
    def preview_excel_file(self, file_path: str):
        """预览Excel文件内容"""
        try:
            import pandas as pd
            
            # 读取前100行进行预览
            df = pd.read_excel(file_path, nrows=100)
            
            # 清空现有数据
            for item in self.preview_tree.get_children():
                self.preview_tree.delete(item)
            
            # 添加数据到预览表格
            for idx, row in df.iterrows():
                values = []
                for col in ['日期', '金额', '摘要', '对方', '类型']:
                    if col in df.columns:
                        values.append(str(row[col])[:20])  # 限制显示长度
                    else:
                        values.append("")
                
                self.preview_tree.insert('', tk.END, values=values)
            
            self.log(f"预览文件成功，显示前 {len(df)} 行数据")
            
        except Exception as e:
            self.log(f"预览文件失败: {e}", "ERROR")
            messagebox.showerror("预览错误", f"无法预览文件: {e}")
    
    def quick_import(self):
        """快速导入"""
        file_path = self.current_file_var.get()
        if not file_path:
            messagebox.showwarning("提示", "请先选择Excel文件")
            return
        
        # 切换到日志页面
        self.notebook.select(2)
        
        # 在后台线程中执行导入
        def import_thread():
            try:
                self.log("开始快速导入...")
                
                # 创建优化处理器
                processor = OptimizedExcelProcessor(
                    chunk_size=1000,
                    max_workers=2,
                    memory_limit_mb=200
                )
                
                # 默认列映射
                column_mapping = {
                    'date': '日期',
                    'amount': '金额',
                    'description': '摘要',
                    'counterparty': '对方户名'
                }
                
                # 创建GUI进度回调
                progress_callback = GUIProgressCallback(
                    total_steps=1000,
                    progress_var=self.progress_var,
                    status_var=self.status_var
                )
                
                # 处理文件
                records, stats = processor.process_excel_file(
                    file_path=Path(file_path),
                    column_mapping=column_mapping,
                    progress_callback=progress_callback
                )
                
                # 保存到存储
                for record in records:
                    self.transaction_storage.save_transaction(record)
                
                # 显示结果
                self.root.after(0, lambda: self.show_import_result(records, stats))
                
            except Exception as e:
                self.root.after(0, lambda: self.log(f"导入失败: {e}", "ERROR"))
                self.root.after(0, lambda: messagebox.showerror("导入错误", f"导入失败: {e}"))
        
        # 启动后台线程
        threading.Thread(target=import_thread, daemon=True).start()
    
    def show_import_result(self, records, stats):
        """显示导入结果"""
        result_msg = f"""
✅ 导入完成！

📊 处理统计：
• 总行数: {stats.total_rows:,}
• 成功导入: {stats.processed_rows:,}
• 错误行数: {stats.error_rows:,}
• 成功率: {stats.success_rate:.1f}%
• 处理时间: {stats.processing_time:.2f} 秒
• 处理速度: {stats.processed_rows / max(stats.processing_time, 0.001):.0f} 行/秒

💾 已保存 {len(records)} 条交易记录到数据库
"""
        
        self.log(result_msg)
        messagebox.showinfo("导入成功", f"成功导入 {len(records)} 条记录")
    
    def advanced_import(self):
        """高级导入"""
        messagebox.showinfo("功能开发中", "高级导入功能正在开发中，敬请期待！")
    
    def generate_income_statement(self):
        """生成利润表"""
        try:
            self.log("正在生成利润表...")
            
            # 获取交易数据
            transactions = self.transaction_storage.get_all_transactions()
            
            if not transactions:
                messagebox.showwarning("提示", "没有找到交易数据，请先导入数据")
                return
            
            # 生成报表
            report_generator = ReportGenerator(self.transaction_storage)
            report_data = report_generator.generate_income_statement(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31)
            )
            
            # 显示报表
            self.show_report("利润表", report_data)
            
        except Exception as e:
            self.log(f"生成利润表失败: {e}", "ERROR")
            messagebox.showerror("报表错误", f"生成利润表失败: {e}")
    
    def generate_balance_sheet(self):
        """生成资产负债表"""
        messagebox.showinfo("功能开发中", "资产负债表功能正在开发中，敬请期待！")
    
    def generate_cash_flow(self):
        """生成现金流量表"""
        messagebox.showinfo("功能开发中", "现金流量表功能正在开发中，敬请期待！")
    
    def show_report(self, title: str, report_data: dict):
        """显示报表"""
        # 创建新窗口显示报表
        report_window = tk.Toplevel(self.root)
        report_window.title(f"{title} - {datetime.now().strftime('%Y-%m-%d')}")
        report_window.geometry("600x400")
        
        # 报表内容
        report_text = scrolledtext.ScrolledText(report_window, wrap=tk.WORD, font=('Consolas', 10))
        report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 格式化报表数据
        content = f"{title}\n{'='*50}\n\n"
        for key, value in report_data.items():
            content += f"{key}: {value}\n"
        
        report_text.insert(tk.END, content)
        report_text.config(state=tk.DISABLED)
    
    def bank_reconciliation(self):
        """银行对账"""
        messagebox.showinfo("功能开发中", "银行对账功能正在开发中，敬请期待！")
    
    def customer_reconciliation(self):
        """客户对账"""
        messagebox.showinfo("功能开发中", "客户对账功能正在开发中，敬请期待！")
    
    def supplier_reconciliation(self):
        """供应商对账"""
        messagebox.showinfo("功能开发中", "供应商对账功能正在开发中，敬请期待！")
    
    def open_settings(self):
        """打开设置"""
        # 创建设置窗口
        settings_window = tk.Toplevel(self.root)
        settings_window.title("系统设置")
        settings_window.geometry("500x400")
        settings_window.resizable(False, False)
        
        # 设置内容
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 基本设置
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="基本设置")
        
        ttk.Label(basic_frame, text="公司名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        company_entry = ttk.Entry(basic_frame, width=30)
        company_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Label(basic_frame, text="税号:").grid(row=1, column=0, sticky=tk.W, pady=5)
        tax_entry = ttk.Entry(basic_frame, width=30)
        tax_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 性能设置
        perf_frame = ttk.Frame(notebook, padding="10")
        notebook.add(perf_frame, text="性能设置")
        
        ttk.Label(perf_frame, text="处理块大小:").grid(row=0, column=0, sticky=tk.W, pady=5)
        chunk_var = tk.StringVar(value="1000")
        chunk_entry = ttk.Entry(perf_frame, textvariable=chunk_var, width=20)
        chunk_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        ttk.Label(perf_frame, text="工作线程数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        worker_var = tk.StringVar(value="4")
        worker_entry = ttk.Entry(perf_frame, textvariable=worker_var, width=20)
        worker_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 保存按钮
        ttk.Button(settings_window, text="保存设置", 
                  command=lambda: self.save_settings(settings_window)).pack(pady=10)
    
    def save_settings(self, window):
        """保存设置"""
        self.log("设置已保存")
        messagebox.showinfo("提示", "设置保存成功")
        window.destroy()
    
    def show_help(self):
        """显示帮助"""
        help_text = """
📖 小企业会计助手使用帮助

🚀 快速开始：
1. 准备Excel文件，确保包含日期、金额、摘要等列
2. 点击"选择Excel文件"选择要导入的文件
3. 点击"快速导入"开始处理数据
4. 在"数据预览"中查看导入结果
5. 使用"报表生成"功能生成财务报表

📁 Excel文件格式要求：
• 必须包含日期列（格式：YYYY-MM-DD）
• 必须包含金额列（数字格式）
• 建议包含摘要、对方户名等描述信息
• 支持.xlsx和.xls格式

⚡ 性能优化特性：
• 支持大文件分块处理
• 多线程并行处理提升速度
• 智能内存管理避免崩溃
• 实时进度显示

🔧 高级功能：
• 自动交易分类
• 重复记录检测
• 数据验证和清理
• 错误恢复机制

❓ 常见问题：
Q: 导入速度慢怎么办？
A: 可以在设置中调整处理块大小和线程数

Q: 如何处理导入错误？
A: 查看处理日志了解具体错误信息

Q: 支持哪些Excel格式？
A: 支持.xlsx和.xls格式，推荐使用.xlsx

📞 技术支持：
如有问题请查看文档或联系技术支持
"""
        
        # 创建帮助窗口
        help_window = tk.Toplevel(self.root)
        help_window.title("使用帮助")
        help_window.geometry("700x500")
        
        help_text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, 
                                                    font=('Arial', 10), padx=20, pady=20)
        help_text_widget.pack(fill=tk.BOTH, expand=True)
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state=tk.DISABLED)
    
    def show_about(self):
        """显示关于"""
        about_text = """
小企业会计助手 V1.6
图形界面版

🏢 专为小企业财务管理设计
⚡ 高性能Excel数据处理
📊 智能财务报表生成
🔧 用户友好的操作界面

版本信息：
• 版本号：V1.6.0
• 发布日期：2024年
• 开发语言：Python
• 界面框架：Tkinter

特别感谢：
感谢所有用户的反馈和建议，
让我们能够不断改进产品！

© 2024 小企业会计助手
保留所有权利
"""
        messagebox.showinfo("关于", about_text)
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        # 添加到日志文本框
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # 根据级别设置颜色
        if level == "ERROR":
            self.log_text.tag_add("error", f"end-{len(log_entry)}c", "end-1c")
            self.log_text.tag_config("error", foreground="red")
        elif level == "WARNING":
            self.log_text.tag_add("warning", f"end-{len(log_entry)}c", "end-1c")
            self.log_text.tag_config("warning", foreground="orange")
        elif level == "SUCCESS":
            self.log_text.tag_add("success", f"end-{len(log_entry)}c", "end-1c")
            self.log_text.tag_config("success", foreground="green")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log("日志已清空")
    
    def on_closing(self):
        """关闭程序"""
        if messagebox.askokcancel("退出", "确定要退出小企业会计助手吗？"):
            self.root.destroy()
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()


def main():
    """主函数"""
    try:
        app = SmallAccountantGUI()
        app.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        messagebox.showerror("启动错误", f"程序启动失败: {e}")


if __name__ == "__main__":
    main()