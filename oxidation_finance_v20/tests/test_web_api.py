#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web API 端点测试示例

测试范围：
- 首页和仪表盘
- 订单管理 API
- 收入/支出录入
- 客户管理
- 报表功能
- 搜索和统计 API

使用方法：
    pytest tests/test_web_api.py -v
"""

import pytest
import json
from decimal import Decimal
from datetime import date, datetime

from oxidation_finance_v20.web_app import app
from oxidation_finance_v20.database.db_manager import DatabaseManager


@pytest.fixture
def client():
    """创建 Flask 测试客户端"""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.test_client() as client:
        yield client


@pytest.fixture
def client_with_db(client, tmp_path):
    """带有临时数据库的测试客户端"""
    # 创建临时数据库
    db_path = tmp_path / "test.db"

    with app.app_context():
        # 使用临时数据库
        app.config["DB_PATH"] = str(db_path)
        yield client


class TestHomePage:
    """测试首页和仪表盘"""

    def test_homepage_status(self, client):
        """测试首页返回状态 200"""
        response = client.get("/")
        assert response.status_code == 200

    def test_homepage_content(self, client):
        """测试首页包含关键内容"""
        response = client.get("/")
        html = response.data.decode("utf-8")
        assert "氧化加工厂财务系统" in html or "财务系统" in html

    def test_homepage_stats_section(self, client):
        """测试首页包含统计区域"""
        response = client.get("/")
        html = response.data.decode("utf-8")
        # 检查是否包含统计数据的关键元素
        assert "今日收入" in html or "今日" in html


class TestOrdersAPI:
    """测试订单管理 API"""

    def test_orders_list_page(self, client):
        """测试订单列表页"""
        response = client.get("/orders")
        assert response.status_code == 200

    def test_order_new_page_get(self, client):
        """测试新建订单页面 GET 请求"""
        response = client.get("/order/new")
        assert response.status_code == 200

    def test_order_new_page_post_success(self, client_with_db):
        """测试新建订单 POST 成功"""
        data = {
            "order_no": "TEST001",
            "customer_id": "test-customer-001",
            "customer_name": "测试客户",
            "item_description": "测试产品",
            "quantity": "100",
            "unit_price": "10.00",
            "pricing_unit": "米",
            "processes": ["OXIDATION"],
        }
        response = client_with_db.post("/order/new", data=data, follow_redirects=True)
        assert response.status_code == 200

    def test_order_new_page_post_validation_error(self, client):
        """测试新建订单 POST 验证失败"""
        # 提交空数据
        data = {}
        response = client.post("/order/new", data=data)
        # 应该返回表单页面或错误信息
        assert response.status_code in [200, 400]


class TestIncomeAPI:
    """测试收入录入 API"""

    def test_income_new_page_get(self, client):
        """测试收入录入页面 GET"""
        response = client.get("/income/new")
        assert response.status_code == 200

    def test_income_new_post(self, client_with_db):
        """测试收入录入 POST"""
        data = {
            "amount": "5000.00",
            "bank_type": "G银行",
            "customer_name": "测试客户",
            "description": "测试收入",
        }
        response = client_with_db.post("/income/new", data=data, follow_redirects=True)
        assert response.status_code == 200


class TestExpenseAPI:
    """测试支出录入 API"""

    def test_expense_new_page_get(self, client):
        """测试支出录入页面 GET"""
        response = client.get("/expense/new")
        assert response.status_code == 200

    def test_expense_new_post(self, client_with_db):
        """测试支出录入 POST"""
        data = {
            "amount": "1000.00",
            "expense_type": "房租",
            "bank_type": "G银行",
            "description": "测试支出",
        }
        response = client_with_db.post("/expense/new", data=data, follow_redirects=True)
        assert response.status_code == 200


class TestCustomersAPI:
    """测试客户管理 API"""

    def test_customers_list_page(self, client):
        """测试客户列表页"""
        response = client.get("/customers")
        assert response.status_code == 200

    def test_customers_page_content(self, client):
        """测试客户列表页包含客户信息"""
        response = client.get("/customers")
        html = response.data.decode("utf-8")
        assert "客户" in html


class TestReportsAPI:
    """测试报表功能 API"""

    def test_reports_page(self, client):
        """测试报表页面"""
        response = client.get("/reports")
        assert response.status_code == 200

    def test_reports_content(self, client):
        """测试报表页面包含报表类型"""
        response = client.get("/reports")
        html = response.data.decode("utf-8")
        assert "报表" in html


class TestSearchAPI:
    """测试搜索 API"""

    def test_api_search_get(self, client):
        """测试搜索 API GET 请求"""
        response = client.get("/api/search?q=test")
        assert response.status_code == 200

    def test_api_search_json_response(self, client):
        """测试搜索 API 返回 JSON"""
        response = client.get("/api/search?q=测试")
        assert response.content_type == "application/json"

    def test_api_search_empty_query(self, client):
        """测试搜索 API 空查询"""
        response = client.get("/api/search")
        assert response.status_code == 200


class TestStatsAPI:
    """测试统计 API"""

    def test_api_stats_get(self, client):
        """测试统计 API"""
        response = client.get("/api/stats")
        assert response.status_code == 200

    def test_api_stats_json_response(self, client):
        """测试统计 API 返回 JSON"""
        response = client.get("/api/stats")
        assert response.content_type == "application/json"

    def test_api_stats_content(self, client):
        """测试统计 API 返回数据结构"""
        response = client.get("/api/stats")
        data = json.loads(response.data)
        # 检查是否包含预期的统计字段
        assert isinstance(data, dict)


class TestErrorHandling:
    """测试错误处理"""

    def test_404_page(self, client):
        """测试 404 页面"""
        response = client.get("/nonexistent-page")
        assert response.status_code == 404

    def test_invalid_order_id(self, client):
        """测试无效的订单 ID"""
        response = client.get("/order/edit/invalid-id")
        # 应该返回错误或重定向
        assert response.status_code in [200, 302, 404]


class TestStaticFiles:
    """测试静态文件"""

    def test_static_css(self, client):
        """测试 CSS 文件可访问"""
        # 注意：Flask 开发服务器可能不提供静态文件
        # 这取决于具体配置
        pass


# 测试数据准备工具函数
def create_test_order_data():
    """生成测试订单数据"""
    return {
        "order_no": f"OX{datetime.now().strftime('%Y%m%d')}001",
        "customer_name": "测试客户有限公司",
        "item_description": "铝型材测试产品",
        "quantity": "100",
        "pricing_unit": "米",
        "unit_price": "5.50",
        "processes": ["OXIDATION"],
        "total_amount": "550.00",
    }


def create_test_income_data():
    """生成测试收入数据"""
    return {
        "amount": "10000.00",
        "bank_type": "G银行",
        "customer_name": "测试客户",
        "has_invoice": "1",
        "description": "测试收入录入",
    }


def create_test_expense_data():
    """生成测试支出数据"""
    return {
        "amount": "5000.00",
        "expense_type": "房租",
        "bank_type": "G银行",
        "description": "测试支出录入",
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
