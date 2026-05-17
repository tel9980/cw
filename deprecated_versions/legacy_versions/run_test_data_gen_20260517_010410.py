# -*- coding: utf-8 -*-
import sys
import importlib.util

# Load the module
spec = importlib.util.spec_from_file_location("test_data_gen", "生成V1.5测试数据.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Run the function
module.generate_test_data()
