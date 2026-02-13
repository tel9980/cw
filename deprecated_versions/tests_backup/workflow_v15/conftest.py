# -*- coding: utf-8 -*-
"""
Pytest Configuration
测试配置文件
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Hypothesis配置
from hypothesis import settings, Verbosity

# 设置Hypothesis默认配置
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=1000, verbosity=Verbosity.verbose)
settings.register_profile("dev", max_examples=10, verbosity=Verbosity.verbose)

# 使用默认配置
settings.load_profile("default")


@pytest.fixture
def temp_storage_path(tmp_path):
    """临时存储路径fixture"""
    return str(tmp_path / "test_storage")


@pytest.fixture
def sample_user_id():
    """示例用户ID"""
    return "test_user_001"
