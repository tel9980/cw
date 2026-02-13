"""
Industry-specific modules for Oxidation Factory

This package contains industry-specific functionality for oxidation factory:
- ProcessingOrderManager: 加工订单管理
- OutsourcedProcessingManager: 外发加工管理
- IndustryClassifier: 行业费用分类器
"""

from .processing_order_manager import ProcessingOrderManager
from .outsourced_processing_manager import OutsourcedProcessingManager
from .industry_classifier import IndustryClassifier

__all__ = [
    'ProcessingOrderManager',
    'OutsourcedProcessingManager',
    'IndustryClassifier'
]
