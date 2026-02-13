"""
Unit tests for Industry Chart Generator

Tests the generation of industry-specific charts:
- Processing income trend chart (by pricing unit)
- Outsourced processing cost structure pie chart
- Raw material consumption trend chart
"""

import pytest
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import tempfile
import os

from oxidation_complete_v17.reports.industry_chart_generator import IndustryChartGenerator


@pytest.fixture
def chart_generator():
    """创建图表生成器"""
    return IndustryChartGenerator()


@pytest.fixture
def income_trend_data():
    """创建收入趋势测试数据"""
    data = {
        '月份': ['2026-01', '2026-01', '2026-01', '2026-02', '2026-02', '2026-02'],
        '计价单位': ['件', '米长', '平方', '件', '米长', '平方'],
        '总金额': [5500, 6000, 5000, 6000, 6500, 5500]
    }
    return pd.DataFrame(data)


@pytest.fixture
def outsourced_cost_data():
    """创建外发成本测试数据"""
    data = {
        '工序类型': ['喷砂', '拉丝', '抛光'],
        '总成本': [500, 750, 400]
    }
    return pd.DataFrame(data)


@pytest.fixture
def material_consumption_data():
    """创建原材料消耗测试数据"""
    data = {
        '月份': ['2026-01', '2026-01', '2026-01', '2026-02', '2026-02', '2026-02'],
        '材料类型': ['三酸', '片碱', '色粉', '三酸', '片碱', '色粉'],
        '金额': [3000, 1500, 800, 3200, 1600, 900]
    }
    return pd.DataFrame(data)


class TestIndustryChartGenerator:
    """测试行业图表生成器"""
    
    def test_initialization(self, chart_generator):
        """测试初始化"""
        assert chart_generator is not None
        assert chart_generator.default_figsize == (12, 7)
        assert chart_generator.default_dpi == 100
        
        # 验证配色方案
        assert '件' in chart_generator.pricing_unit_colors
        assert '喷砂' in chart_generator.process_type_colors
        assert '三酸' in chart_generator.material_colors
    
    def test_create_income_trend_by_pricing_unit(
        self, chart_generator, income_trend_data
    ):
        """测试创建收入趋势图"""
        fig = chart_generator.create_income_trend_by_pricing_unit(income_trend_data)
        
        # 验证返回类型
        assert isinstance(fig, Figure)
        
        # 验证图表有内容
        axes = fig.get_axes()
        assert len(axes) > 0
        
        # 验证有折线
        ax = axes[0]
        lines = ax.get_lines()
        assert len(lines) > 0
        
        # 清理
        chart_generator.close_figure(fig)
    
    def test_create_income_trend_custom_title(
        self, chart_generator, income_trend_data
    ):
        """测试自定义标题的收入趋势图"""
        custom_title = "测试收入趋势图"
        fig = chart_generator.create_income_trend_by_pricing_unit(
            income_trend_data,
            title=custom_title
        )
        
        assert isinstance(fig, Figure)
        ax = fig.get_axes()[0]
        assert ax.get_title() == custom_title
        
        chart_generator.close_figure(fig)
    
    def test_create_income_trend_custom_figsize(
        self, chart_generator, income_trend_data
    ):
        """测试自定义尺寸的收入趋势图"""
        custom_size = (10, 6)
        fig = chart_generator.create_income_trend_by_pricing_unit(
            income_trend_data,
            figsize=custom_size
        )
        
        assert isinstance(fig, Figure)
        # 注意：figsize可能因DPI和其他因素略有不同
        assert fig.get_figwidth() == custom_size[0]
        assert fig.get_figheight() == custom_size[1]
        
        chart_generator.close_figure(fig)
    
    def test_create_outsourced_cost_pie_chart(
        self, chart_generator, outsourced_cost_data
    ):
        """测试创建外发成本饼图"""
        fig = chart_generator.create_outsourced_cost_pie_chart(outsourced_cost_data)
        
        # 验证返回类型
        assert isinstance(fig, Figure)
        
        # 验证图表有内容
        axes = fig.get_axes()
        assert len(axes) > 0
        
        # 验证有饼图扇区
        ax = axes[0]
        patches = ax.patches
        assert len(patches) > 0
        
        # 清理
        chart_generator.close_figure(fig)
    
    def test_create_outsourced_cost_pie_chart_custom_title(
        self, chart_generator, outsourced_cost_data
    ):
        """测试自定义标题的外发成本饼图"""
        custom_title = "测试成本结构图"
        fig = chart_generator.create_outsourced_cost_pie_chart(
            outsourced_cost_data,
            title=custom_title
        )
        
        assert isinstance(fig, Figure)
        ax = fig.get_axes()[0]
        # 饼图标题包含总成本信息，所以只检查是否包含自定义标题
        assert custom_title in ax.get_title()
        
        chart_generator.close_figure(fig)
    
    def test_create_material_consumption_trend(
        self, chart_generator, material_consumption_data
    ):
        """测试创建原材料消耗趋势图"""
        fig = chart_generator.create_material_consumption_trend(
            material_consumption_data
        )
        
        # 验证返回类型
        assert isinstance(fig, Figure)
        
        # 验证图表有内容
        axes = fig.get_axes()
        assert len(axes) > 0
        
        # 验证有堆叠面积图
        ax = axes[0]
        collections = ax.collections
        assert len(collections) > 0
        
        # 清理
        chart_generator.close_figure(fig)
    
    def test_create_material_consumption_trend_custom_title(
        self, chart_generator, material_consumption_data
    ):
        """测试自定义标题的原材料消耗趋势图"""
        custom_title = "测试材料消耗图"
        fig = chart_generator.create_material_consumption_trend(
            material_consumption_data,
            title=custom_title
        )
        
        assert isinstance(fig, Figure)
        ax = fig.get_axes()[0]
        assert ax.get_title() == custom_title
        
        chart_generator.close_figure(fig)
    
    def test_create_material_consumption_bar_chart(
        self, chart_generator, material_consumption_data
    ):
        """测试创建原材料消耗对比柱状图"""
        fig = chart_generator.create_material_consumption_bar_chart(
            material_consumption_data
        )
        
        # 验证返回类型
        assert isinstance(fig, Figure)
        
        # 验证图表有内容
        axes = fig.get_axes()
        assert len(axes) > 0
        
        # 验证有柱状图
        ax = axes[0]
        patches = ax.patches
        assert len(patches) > 0
        
        # 清理
        chart_generator.close_figure(fig)
    
    def test_create_material_consumption_bar_chart_custom_title(
        self, chart_generator, material_consumption_data
    ):
        """测试自定义标题的原材料消耗对比图"""
        custom_title = "测试材料对比图"
        fig = chart_generator.create_material_consumption_bar_chart(
            material_consumption_data,
            title=custom_title
        )
        
        assert isinstance(fig, Figure)
        ax = fig.get_axes()[0]
        assert ax.get_title() == custom_title
        
        chart_generator.close_figure(fig)
    
    def test_close_figure(self, chart_generator, income_trend_data):
        """测试关闭图表"""
        fig = chart_generator.create_income_trend_by_pricing_unit(income_trend_data)
        
        # 关闭图表不应抛出异常
        chart_generator.close_figure(fig)
        
        # 验证图表已关闭（通过检查是否还在pyplot的figure列表中）
        assert fig not in plt.get_fignums()
    
    def test_color_schemes(self, chart_generator):
        """测试配色方案完整性"""
        # 验证计价单位配色
        expected_units = ['件', '条', '只', '个', '米长', '米重', '平方']
        for unit in expected_units:
            assert unit in chart_generator.pricing_unit_colors
            assert chart_generator.pricing_unit_colors[unit].startswith('#')
        
        # 验证工序类型配色
        expected_processes = ['喷砂', '拉丝', '抛光']
        for process in expected_processes:
            assert process in chart_generator.process_type_colors
            assert chart_generator.process_type_colors[process].startswith('#')
        
        # 验证材料类型配色
        expected_materials = ['三酸', '片碱', '亚钠', '色粉', '除油剂', '挂具']
        for material in expected_materials:
            assert material in chart_generator.material_colors
            assert chart_generator.material_colors[material].startswith('#')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
