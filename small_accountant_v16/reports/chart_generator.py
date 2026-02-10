"""
图表生成器模块

使用matplotlib生成各类财务图表并嵌入Excel文件。
"""

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from typing import Optional, Tuple
import numpy as np

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class ChartGenerator:
    """图表生成器
    
    生成各类财务图表并支持嵌入Excel文件。
    """
    
    def __init__(self):
        """初始化图表生成器"""
        self.default_figsize = (10, 6)
        self.default_dpi = 100
    
    def create_revenue_comparison_chart(
        self,
        data: pd.DataFrame,
        title: str = "收支对比图",
        figsize: Optional[Tuple[int, int]] = None
    ) -> Figure:
        """创建收支对比图
        
        Args:
            data: 数据DataFrame，需要包含以下列：
                - period: 期间（如"2024年1月"）
                - income: 收入金额
                - expense: 支出金额
            title: 图表标题
            figsize: 图表尺寸 (width, height)
            
        Returns:
            matplotlib Figure对象
        """
        if figsize is None:
            figsize = self.default_figsize
        
        # 创建图表
        fig, ax = plt.subplots(figsize=figsize, dpi=self.default_dpi)
        
        # 准备数据
        periods = data['period'].tolist()
        income = data['income'].tolist()
        expense = data['expense'].tolist()
        
        # 设置柱状图位置
        x = np.arange(len(periods))
        width = 0.35
        
        # 绘制柱状图
        bars1 = ax.bar(x - width/2, income, width, label='收入', color='#4CAF50', alpha=0.8)
        bars2 = ax.bar(x + width/2, expense, width, label='支出', color='#F44336', alpha=0.8)
        
        # 添加数值标签
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:,.0f}',
                       ha='center', va='bottom', fontsize=9)
        
        # 设置标题和标签
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('期间', fontsize=12)
        ax.set_ylabel('金额（元）', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(periods, rotation=45, ha='right')
        ax.legend(fontsize=10)
        
        # 添加网格线
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # 调整布局
        plt.tight_layout()
        
        return fig
    
    def create_profit_trend_chart(
        self,
        data: pd.DataFrame,
        title: str = "利润趋势图",
        figsize: Optional[Tuple[int, int]] = None
    ) -> Figure:
        """创建利润趋势图
        
        Args:
            data: 数据DataFrame，需要包含以下列：
                - month: 月份（如"2024-01"）
                - revenue: 营业收入
                - cost: 营业成本
                - gross_profit: 毛利润
                - net_profit: 净利润
            title: 图表标题
            figsize: 图表尺寸 (width, height)
            
        Returns:
            matplotlib Figure对象
        """
        if figsize is None:
            figsize = self.default_figsize
        
        # 创建图表
        fig, ax = plt.subplots(figsize=figsize, dpi=self.default_dpi)
        
        # 准备数据
        months = data['month'].tolist()
        revenue = data['revenue'].tolist()
        cost = data['cost'].tolist()
        gross_profit = data['gross_profit'].tolist()
        net_profit = data['net_profit'].tolist()
        
        # 绘制折线图
        x = np.arange(len(months))
        ax.plot(x, revenue, marker='o', linewidth=2, label='营业收入', color='#2196F3')
        ax.plot(x, cost, marker='s', linewidth=2, label='营业成本', color='#FF9800')
        ax.plot(x, gross_profit, marker='^', linewidth=2, label='毛利润', color='#4CAF50')
        ax.plot(x, net_profit, marker='D', linewidth=2, label='净利润', color='#9C27B0')
        
        # 设置标题和标签
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('月份', fontsize=12)
        ax.set_ylabel('金额（元）', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45, ha='right')
        ax.legend(fontsize=10, loc='best')
        
        # 添加网格线
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # 调整布局
        plt.tight_layout()
        
        return fig
    
    def create_customer_ranking_chart(
        self,
        data: pd.DataFrame,
        title: str = "客户排名图",
        top_n: int = 10,
        figsize: Optional[Tuple[int, int]] = None
    ) -> Figure:
        """创建客户排名图
        
        Args:
            data: 数据DataFrame，需要包含以下列：
                - customer_name: 客户名称
                - sales_amount: 销售金额
            title: 图表标题
            top_n: 显示前N名客户
            figsize: 图表尺寸 (width, height)
            
        Returns:
            matplotlib Figure对象
        """
        if figsize is None:
            figsize = (10, 8)
        
        # 取前N名客户
        top_data = data.head(top_n).copy()
        
        # 创建图表
        fig, ax = plt.subplots(figsize=figsize, dpi=self.default_dpi)
        
        # 准备数据
        customers = top_data['customer_name'].tolist()
        sales = top_data['sales_amount'].tolist()
        
        # 创建颜色渐变
        colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(customers)))
        
        # 绘制水平柱状图
        y_pos = np.arange(len(customers))
        bars = ax.barh(y_pos, sales, color=colors, alpha=0.8)
        
        # 添加数值标签
        for i, (bar, value) in enumerate(zip(bars, sales)):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{value:,.0f}',
                   ha='left', va='center', fontsize=9, 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
        
        # 设置标题和标签
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('销售金额（元）', fontsize=12)
        ax.set_ylabel('客户名称', fontsize=12)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(customers)
        
        # 反转Y轴，使第一名在顶部
        ax.invert_yaxis()
        
        # 添加网格线
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # 调整布局
        plt.tight_layout()
        
        return fig
    
    def save_chart_to_excel(
        self,
        workbook: Workbook,
        sheet_name: str,
        figure: Figure,
        cell: str = 'H4',
        scale: float = 1.0
    ) -> None:
        """将图表保存到Excel工作表
        
        Args:
            workbook: openpyxl工作簿对象
            sheet_name: 工作表名称
            figure: matplotlib Figure对象
            cell: 图表插入位置（如'H4'）
            scale: 图表缩放比例
        """
        # 将图表保存到BytesIO
        img_buffer = BytesIO()
        figure.savefig(img_buffer, format='png', bbox_inches='tight', dpi=self.default_dpi)
        img_buffer.seek(0)
        
        # 创建Excel图片对象
        img = XLImage(img_buffer)
        
        # 调整图片大小
        if scale != 1.0:
            img.width = int(img.width * scale)
            img.height = int(img.height * scale)
        
        # 获取工作表
        if sheet_name in workbook.sheetnames:
            ws = workbook[sheet_name]
        else:
            ws = workbook.create_sheet(sheet_name)
        
        # 插入图片
        ws.add_image(img, cell)
        
        # 关闭图表以释放内存
        plt.close(figure)
    
    def create_and_embed_revenue_comparison(
        self,
        workbook: Workbook,
        sheet_name: str,
        data: pd.DataFrame,
        cell: str = 'H4',
        title: str = "收支对比图"
    ) -> None:
        """创建收支对比图并嵌入Excel
        
        Args:
            workbook: openpyxl工作簿对象
            sheet_name: 工作表名称
            data: 数据DataFrame
            cell: 图表插入位置
            title: 图表标题
        """
        fig = self.create_revenue_comparison_chart(data, title)
        self.save_chart_to_excel(workbook, sheet_name, fig, cell)
    
    def create_and_embed_profit_trend(
        self,
        workbook: Workbook,
        sheet_name: str,
        data: pd.DataFrame,
        cell: str = 'H4',
        title: str = "利润趋势图"
    ) -> None:
        """创建利润趋势图并嵌入Excel
        
        Args:
            workbook: openpyxl工作簿对象
            sheet_name: 工作表名称
            data: 数据DataFrame
            cell: 图表插入位置
            title: 图表标题
        """
        fig = self.create_profit_trend_chart(data, title)
        self.save_chart_to_excel(workbook, sheet_name, fig, cell)
    
    def create_and_embed_customer_ranking(
        self,
        workbook: Workbook,
        sheet_name: str,
        data: pd.DataFrame,
        cell: str = 'H4',
        title: str = "客户排名图",
        top_n: int = 10
    ) -> None:
        """创建客户排名图并嵌入Excel
        
        Args:
            workbook: openpyxl工作簿对象
            sheet_name: 工作表名称
            data: 数据DataFrame
            cell: 图表插入位置
            title: 图表标题
            top_n: 显示前N名客户
        """
        fig = self.create_customer_ranking_chart(data, title, top_n)
        self.save_chart_to_excel(workbook, sheet_name, fig, cell)
