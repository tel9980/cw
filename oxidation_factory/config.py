# -*- coding: utf-8 -*-
"""
配置管理模块
负责加载和管理氧化加工厂的配置信息
"""

import os
import json
from typing import Dict, List, Any, Optional

class OxidationConfig:
    """氧化加工厂配置管理类"""
    
    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为 财务数据/配置文件
        """
        if config_dir is None:
            # 默认配置目录
            root_dir = os.getcwd()
            config_dir = os.path.join(root_dir, "财务数据", "配置文件")
        
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "oxidation_config.json")
        
        # 默认配置
        self._default_config = self._get_default_config()
        
        # 加载配置
        self.config = self._load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "version": "1.0",
            "industry": "oxidation_factory",
            "pricing_units": ["件", "条", "只", "个", "米长", "米重", "平方"],
            "outsourced_processes": ["喷砂", "拉丝", "抛光"],
            "material_types": ["三酸", "片碱", "亚钠", "色粉", "除油剂", "挂具"],
            "bank_accounts": {
                "G银行基本户": {"type": "对公账户", "has_invoice": True, "is_cash": False},
                "N银行": {"type": "现金账户", "has_invoice": False, "is_cash": True},
                "微信": {"type": "现金账户", "has_invoice": False, "is_cash": True}
            },
            "default_categories": {
                "收入": ["加工费收入", "其他收入"],
                "支出": [
                    "原材料-三酸", "原材料-片碱", "原材料-亚钠",
                    "原材料-色粉", "原材料-除油剂", "挂具",
                    "外发加工-喷砂", "外发加工-拉丝", "外发加工-抛光",
                    "房租", "水电费", "工资", "日常费用", "其他支出"
                ]
            }
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        优先级：用户配置 > 行业配置 > 默认配置
        """
        config = self._default_config.copy()
        
        # 尝试加载行业配置文件
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    industry_config = json.load(f)
                    # 合并配置
                    config.update(industry_config)
                print(f"✅ 已加载氧化加工厂配置: {self.config_file}")
            except Exception as e:
                print(f"⚠️ 加载配置文件失败: {e}，使用默认配置")
        
        return config
    
    def reload(self):
        """重新加载配置"""
        self.config = self._load_config()
        print("✅ 配置已重新加载")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        return self.config.get(key, default)
    
    def get_pricing_units(self) -> List[str]:
        """获取计价单位列表"""
        return self.config.get("pricing_units", [])
    
    def get_outsourced_processes(self) -> List[str]:
        """获取外发工序列表"""
        return self.config.get("outsourced_processes", [])
    
    def get_material_types(self) -> List[str]:
        """获取原材料类型列表"""
        return self.config.get("material_types", [])
    
    def get_bank_accounts(self) -> Dict[str, Dict]:
        """获取银行账户配置"""
        return self.config.get("bank_accounts", {})
    
    def get_default_categories(self) -> Dict[str, List[str]]:
        """获取默认费用分类"""
        return self.config.get("default_categories", {})
    
    def get_category_keywords(self) -> Dict[str, List[str]]:
        """获取分类关键词映射"""
        return self.config.get("category_keywords", {})
    
    def get_order_status_list(self) -> List[str]:
        """获取订单状态列表"""
        return self.config.get("order_status", ["待生产", "生产中", "已完工", "已结算"])
    
    def get_reconcile_status_list(self) -> List[str]:
        """获取对账状态列表"""
        return self.config.get("reconcile_status", ["未对账", "部分对账", "已对账"])
    
    def is_ai_enabled(self) -> bool:
        """检查AI分类是否启用"""
        ai_config = self.config.get("ai_classification", {})
        return ai_config.get("enabled", True)
    
    def get_ai_confidence_threshold(self) -> float:
        """获取AI分类置信度阈值"""
        ai_config = self.config.get("ai_classification", {})
        return ai_config.get("confidence_threshold", 0.8)
    
    def get_ai_context(self) -> str:
        """获取AI分类上下文"""
        ai_config = self.config.get("ai_classification", {})
        return ai_config.get("context", "")
    
    def validate(self) -> bool:
        """
        验证配置完整性
        
        Returns:
            配置是否有效
        """
        required_keys = ["pricing_units", "outsourced_processes", "material_types", "bank_accounts"]
        
        for key in required_keys:
            if key not in self.config:
                print(f"❌ 配置缺少必需项: {key}")
                return False
        
        # 验证计价单位不为空
        if not self.config["pricing_units"]:
            print("❌ 计价单位列表不能为空")
            return False
        
        print("✅ 配置验证通过")
        return True


# 全局配置实例
_global_config: Optional[OxidationConfig] = None

def get_config() -> OxidationConfig:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = OxidationConfig()
    return _global_config

def reload_config():
    """重新加载全局配置"""
    global _global_config
    if _global_config is not None:
        _global_config.reload()
    else:
        _global_config = OxidationConfig()
