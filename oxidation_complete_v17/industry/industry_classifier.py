"""
Industry Classifier for Oxidation Factory

This module provides automatic expense classification for oxidation factory industry.
Uses keyword-based rules to classify transactions with confidence scores.
"""

from typing import Dict, List, Tuple, Optional
import json
import os
from decimal import Decimal


class IndustryClassifier:
    """氧化加工行业费用分类器
    
    功能:
    - 自动识别氧化加工行业的常见费用
    - 基于关键词规则进行分类
    - 提供分类置信度评估
    - 支持收入和支出分类
    """
    
    def __init__(self, config_file: str = None):
        """初始化分类器
        
        Args:
            config_file: 配置文件路径,如果为None则使用默认配置
        """
        self.config_file = config_file
        self.rules = self._load_classification_rules()
    
    def _load_classification_rules(self) -> Dict:
        """加载分类规则
        
        Returns:
            分类规则字典
        """
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('expense_classification', {})
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        
        # 返回默认规则
        return self._get_default_rules()
    
    def _get_default_rules(self) -> Dict:
        """获取默认分类规则
        
        Returns:
            默认分类规则字典
        """
        return {
            "income_categories": [
                {
                    "code": "processing_income",
                    "name": "加工费收入",
                    "keywords": ["加工费", "氧化费", "表面处理费", "订单", "客户付款"],
                    "confidence_threshold": 0.7
                },
                {
                    "code": "other_income",
                    "name": "其他收入",
                    "keywords": ["利息", "补贴", "退款", "其他"],
                    "confidence_threshold": 0.5
                }
            ],
            "expense_categories": [
                {
                    "code": "raw_materials",
                    "name": "原材料",
                    "subcategories": ["三酸", "片碱", "亚钠", "色粉", "除油剂"],
                    "keywords": ["三酸", "片碱", "亚钠", "色粉", "除油剂", "化工", "原料", 
                                "硫酸", "硝酸", "盐酸", "氢氧化钠", "烧碱", "亚硫酸钠", 
                                "染料", "着色剂", "清洗剂", "脱脂剂"],
                    "confidence_threshold": 0.7
                },
                {
                    "code": "fixtures",
                    "name": "挂具",
                    "keywords": ["挂具", "夹具", "治具", "工装"],
                    "confidence_threshold": 0.7
                },
                {
                    "code": "outsourced_processing",
                    "name": "外发加工费",
                    "subcategories": ["喷砂", "拉丝", "抛光"],
                    "keywords": ["喷砂", "拉丝", "抛光", "外发", "委外", "加工费", "表面处理"],
                    "confidence_threshold": 0.7
                },
                {
                    "code": "rent",
                    "name": "房租",
                    "keywords": ["房租", "租金", "厂房", "场地", "物业"],
                    "confidence_threshold": 0.9
                },
                {
                    "code": "utilities",
                    "name": "水电费",
                    "keywords": ["水费", "电费", "水电", "电力", "自来水", "供电"],
                    "confidence_threshold": 0.7
                },
                {
                    "code": "salary",
                    "name": "工资",
                    "keywords": ["工资", "薪资", "薪酬", "劳务", "社保", "公积金", "奖金"],
                    "confidence_threshold": 0.7
                },
                {
                    "code": "daily_expenses",
                    "name": "日常费用",
                    "keywords": ["办公", "差旅", "通讯", "交通", "餐费", "招待", "快递", "邮费"],
                    "confidence_threshold": 0.7
                },
                {
                    "code": "other_expenses",
                    "name": "其他支出",
                    "keywords": ["维修", "保养", "杂费", "其他", "备件"],
                    "confidence_threshold": 0.5
                }
            ]
        }
    
    def classify_income(
        self,
        description: str,
        counterparty: str = "",
        amount: Optional[Decimal] = None
    ) -> Tuple[str, str, float]:
        """分类收入
        
        Args:
            description: 交易描述
            counterparty: 往来单位名称
            amount: 金额(可选)
            
        Returns:
            (分类代码, 分类名称, 置信度)
        """
        text = f"{description} {counterparty}".lower()
        
        best_match = None
        best_confidence = 0.0
        
        for category in self.rules.get("income_categories", []):
            confidence = self._calculate_confidence(text, category["keywords"])
            
            if confidence >= category["confidence_threshold"] and confidence > best_confidence:
                best_match = category
                best_confidence = confidence
        
        if best_match:
            return (best_match["code"], best_match["name"], best_confidence)
        else:
            # 默认分类为其他收入
            return ("other_income", "其他收入", 0.3)
    
    def classify_expense(
        self,
        description: str,
        counterparty: str = "",
        amount: Optional[Decimal] = None
    ) -> Tuple[str, str, float]:
        """分类支出
        
        Args:
            description: 交易描述
            counterparty: 往来单位名称
            amount: 金额(可选)
            
        Returns:
            (分类代码, 分类名称, 置信度)
        """
        text = f"{description} {counterparty}".lower()
        
        best_match = None
        best_confidence = 0.0
        
        # 按照特定顺序检查分类,优先检查更具体的分类
        # 排除"其他支出"类别,最后再检查
        categories = self.rules.get("expense_categories", [])
        specific_categories = [c for c in categories if c["code"] != "other_expenses"]
        other_category = next((c for c in categories if c["code"] == "other_expenses"), None)
        
        # 先检查具体分类
        for category in specific_categories:
            confidence = self._calculate_confidence(text, category["keywords"])
            
            # DEBUG
            # print(f"DEBUG classify_expense: category={category['code']}, confidence={confidence}, threshold={category['confidence_threshold']}")
            
            # 只要置信度大于0且超过阈值,就认为匹配
            if confidence > 0 and confidence >= category["confidence_threshold"]:
                if confidence > best_confidence:
                    best_match = category
                    best_confidence = confidence
        
        # 如果没有找到匹配,使用"其他支出"
        if not best_match and other_category:
            return (other_category["code"], other_category["name"], 0.3)
        
        if best_match:
            return (best_match["code"], best_match["name"], best_confidence)
        else:
            # 默认分类为其他支出
            return ("other_expenses", "其他支出", 0.3)
    
    def _calculate_confidence(self, text: str, keywords: List[str]) -> float:
        """计算分类置信度
        
        Args:
            text: 待分类文本
            keywords: 关键词列表
            
        Returns:
            置信度(0.0-1.0)
        """
        if not keywords:
            return 0.0
        
        matched_keywords = 0
        
        for keyword in keywords:
            if keyword.lower() in text:
                matched_keywords += 1
        
        # 如果没有匹配,返回0
        if matched_keywords == 0:
            return 0.0
        
        # 如果有匹配,根据匹配数量给予置信度
        # 1个匹配: 0.75
        # 2个匹配: 0.85
        # 3个及以上: 0.95
        if matched_keywords == 1:
            confidence = 0.75
        elif matched_keywords == 2:
            confidence = 0.85
        else:
            confidence = 0.95
        
        return confidence
    
    def classify_transaction(
        self,
        transaction_type: str,
        description: str,
        counterparty: str = "",
        amount: Optional[Decimal] = None
    ) -> Dict:
        """分类交易
        
        Args:
            transaction_type: 交易类型("income"或"expense")
            description: 交易描述
            counterparty: 往来单位名称
            amount: 金额(可选)
            
        Returns:
            分类结果字典
        """
        if transaction_type.lower() == "income":
            code, name, confidence = self.classify_income(description, counterparty, amount)
        else:
            code, name, confidence = self.classify_expense(description, counterparty, amount)
        
        return {
            "category_code": code,
            "category_name": name,
            "confidence": confidence,
            "is_low_confidence": confidence < 0.7
        }
    
    def batch_classify(
        self,
        transactions: List[Dict]
    ) -> List[Dict]:
        """批量分类交易
        
        Args:
            transactions: 交易列表,每个交易包含type, description, counterparty, amount
            
        Returns:
            分类结果列表
        """
        results = []
        
        for transaction in transactions:
            result = self.classify_transaction(
                transaction.get("type", "expense"),
                transaction.get("description", ""),
                transaction.get("counterparty", ""),
                transaction.get("amount")
            )
            
            # 添加原始交易信息
            result["original_transaction"] = transaction
            results.append(result)
        
        return results
    
    def get_low_confidence_items(
        self,
        classification_results: List[Dict]
    ) -> List[Dict]:
        """获取低置信度分类项
        
        Args:
            classification_results: 分类结果列表
            
        Returns:
            低置信度项列表
        """
        return [r for r in classification_results if r.get("is_low_confidence", False)]
    
    def get_category_info(self, category_code: str, transaction_type: str = "expense") -> Optional[Dict]:
        """获取分类信息
        
        Args:
            category_code: 分类代码
            transaction_type: 交易类型("income"或"expense")
            
        Returns:
            分类信息字典,如果不存在返回None
        """
        categories_key = "income_categories" if transaction_type == "income" else "expense_categories"
        categories = self.rules.get(categories_key, [])
        
        for category in categories:
            if category["code"] == category_code:
                return category
        
        return None
    
    def get_all_categories(self, transaction_type: str = "expense") -> List[Dict]:
        """获取所有分类
        
        Args:
            transaction_type: 交易类型("income"或"expense")
            
        Returns:
            分类列表
        """
        categories_key = "income_categories" if transaction_type == "income" else "expense_categories"
        return self.rules.get(categories_key, [])
    
    def add_custom_keyword(
        self,
        category_code: str,
        keyword: str,
        transaction_type: str = "expense"
    ) -> bool:
        """添加自定义关键词
        
        Args:
            category_code: 分类代码
            keyword: 关键词
            transaction_type: 交易类型("income"或"expense")
            
        Returns:
            是否添加成功
        """
        category_info = self.get_category_info(category_code, transaction_type)
        if not category_info:
            return False
        
        if keyword not in category_info["keywords"]:
            category_info["keywords"].append(keyword)
            return True
        
        return False
