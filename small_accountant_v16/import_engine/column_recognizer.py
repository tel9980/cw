"""
Excel列识别器模块

智能识别Excel文件中的列名，并映射到系统字段。
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class ColumnMapping:
    """列映射结果"""
    source_columns: List[str]
    target_fields: Dict[str, str]
    confidence: float
    unmapped_columns: List[str]
    missing_required_fields: List[str]


class ExcelColumnRecognizer:
    """Excel列识别器
    
    智能识别Excel列名并映射到系统字段。
    支持常见的列名变体和模糊匹配。
    """
    
    # 交易记录字段映射规则
    TRANSACTION_FIELD_PATTERNS = {
        'date': [
            r'日期', r'时间', r'交易日期', r'发生日期', r'业务日期',
            r'date', r'time', r'transaction_date', r'trans_date'
        ],
        'type': [
            r'类型', r'交易类型', r'业务类型', r'收支类型',
            r'type', r'trans_type', r'transaction_type'
        ],
        'amount': [
            r'金额', r'交易金额', r'发生额', r'数额', r'收入', r'支出',
            r'amount', r'money', r'value', r'sum'
        ],
        'counterparty_id': [
            r'往来单位', r'客户', r'供应商', r'对方', r'交易对象',
            r'counterparty', r'customer', r'supplier', r'partner'
        ],
        'description': [
            r'描述', r'说明', r'备注', r'摘要', r'用途',
            r'description', r'note', r'memo', r'remark', r'comment'
        ],
        'category': [
            r'分类', r'类别', r'科目', r'项目',
            r'category', r'class', r'subject'
        ],
        'status': [
            r'状态', r'status', r'state'
        ]
    }
    
    # 往来单位字段映射规则
    COUNTERPARTY_FIELD_PATTERNS = {
        'name': [
            r'名称', r'单位名称', r'公司名称', r'客户名称', r'供应商名称',
            r'name', r'company', r'company_name'
        ],
        'type': [
            r'类型', r'单位类型', r'往来类型',
            r'type', r'counterparty_type'
        ],
        'contact_person': [
            r'联系人', r'负责人', r'经办人',
            r'contact', r'contact_person', r'person'
        ],
        'phone': [
            r'电话', r'联系电话', r'手机', r'联系方式',
            r'phone', r'tel', r'mobile', r'telephone'
        ],
        'email': [
            r'邮箱', r'电子邮箱', r'email', r'e-mail', r'mail'
        ],
        'address': [
            r'地址', r'联系地址', r'公司地址',
            r'address', r'addr', r'location'
        ],
        'tax_id': [
            r'税号', r'纳税人识别号', r'统一社会信用代码',
            r'tax_id', r'tax_number', r'tin'
        ]
    }
    
    # 必需字段定义
    REQUIRED_TRANSACTION_FIELDS = ['date', 'type', 'amount']
    REQUIRED_COUNTERPARTY_FIELDS = ['name', 'type']
    
    def __init__(self):
        """初始化列识别器"""
        pass
    
    def recognize_columns(
        self,
        column_names: List[str],
        data_type: str = 'transaction'
    ) -> ColumnMapping:
        """识别Excel列名并生成映射
        
        Args:
            column_names: Excel文件中的列名列表
            data_type: 数据类型，'transaction' 或 'counterparty'
            
        Returns:
            ColumnMapping: 列映射结果
        """
        if data_type == 'transaction':
            patterns = self.TRANSACTION_FIELD_PATTERNS
            required_fields = self.REQUIRED_TRANSACTION_FIELDS
        elif data_type == 'counterparty':
            patterns = self.COUNTERPARTY_FIELD_PATTERNS
            required_fields = self.REQUIRED_COUNTERPARTY_FIELDS
        else:
            raise ValueError(f"不支持的数据类型: {data_type}")
        
        # 执行列名匹配
        target_fields = {}
        matched_columns = set()
        confidence_scores = []
        
        for field_name, field_patterns in patterns.items():
            best_match, confidence = self._find_best_match(
                column_names, field_patterns
            )
            if best_match:
                target_fields[field_name] = best_match
                matched_columns.add(best_match)
                confidence_scores.append(confidence)
        
        # 计算总体置信度
        overall_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores else 0.0
        )
        
        # 识别未映射的列
        unmapped_columns = [
            col for col in column_names if col not in matched_columns
        ]
        
        # 识别缺失的必需字段
        missing_required = [
            field for field in required_fields
            if field not in target_fields
        ]
        
        return ColumnMapping(
            source_columns=column_names,
            target_fields=target_fields,
            confidence=overall_confidence,
            unmapped_columns=unmapped_columns,
            missing_required_fields=missing_required
        )
    
    def _find_best_match(
        self,
        column_names: List[str],
        patterns: List[str]
    ) -> Tuple[Optional[str], float]:
        """在列名中查找最佳匹配
        
        Args:
            column_names: 列名列表
            patterns: 匹配模式列表
            
        Returns:
            (最佳匹配的列名, 置信度)
        """
        best_match = None
        best_score = 0.0
        
        for column in column_names:
            for pattern in patterns:
                score = self._calculate_match_score(column, pattern)
                if score > best_score:
                    best_score = score
                    best_match = column
        
        # 只返回置信度足够高的匹配（>0.5）
        if best_score > 0.5:
            return best_match, best_score
        return None, 0.0
    
    def _calculate_match_score(self, column: str, pattern: str) -> float:
        """计算列名与模式的匹配分数
        
        Args:
            column: 列名
            pattern: 匹配模式（正则表达式）
            
        Returns:
            匹配分数 (0.0-1.0)
        """
        # 标准化列名（去除空格、转小写）
        normalized_column = column.strip().lower()
        normalized_pattern = pattern.lower()
        
        # 完全匹配
        if normalized_column == normalized_pattern:
            return 1.0
        
        # 正则匹配
        try:
            if re.search(normalized_pattern, normalized_column):
                # 根据匹配长度计算分数
                match_length = len(normalized_pattern)
                column_length = len(normalized_column)
                return 0.7 + 0.3 * (match_length / column_length)
        except re.error:
            pass
        
        # 包含匹配
        if normalized_pattern in normalized_column:
            return 0.6
        
        # 模糊匹配（计算相似度）
        similarity = self._calculate_similarity(
            normalized_column, normalized_pattern
        )
        if similarity > 0.7:
            return similarity * 0.5
        
        return 0.0
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算两个字符串的相似度（简单版本）
        
        使用最长公共子序列算法
        
        Args:
            str1: 字符串1
            str2: 字符串2
            
        Returns:
            相似度 (0.0-1.0)
        """
        if not str1 or not str2:
            return 0.0
        
        # 计算最长公共子序列长度
        m, n = len(str1), len(str2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if str1[i-1] == str2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        lcs_length = dp[m][n]
        max_length = max(m, n)
        
        return lcs_length / max_length if max_length > 0 else 0.0
    
    def suggest_mapping(
        self,
        column_names: List[str],
        data_type: str = 'transaction'
    ) -> Dict[str, List[str]]:
        """为每个系统字段建议可能的列名
        
        Args:
            column_names: Excel文件中的列名列表
            data_type: 数据类型，'transaction' 或 'counterparty'
            
        Returns:
            字段名 -> 候选列名列表的映射
        """
        if data_type == 'transaction':
            patterns = self.TRANSACTION_FIELD_PATTERNS
        elif data_type == 'counterparty':
            patterns = self.COUNTERPARTY_FIELD_PATTERNS
        else:
            raise ValueError(f"不支持的数据类型: {data_type}")
        
        suggestions = {}
        
        for field_name, field_patterns in patterns.items():
            candidates = []
            for column in column_names:
                for pattern in field_patterns:
                    score = self._calculate_match_score(column, pattern)
                    if score > 0.3:  # 降低阈值以显示更多候选
                        candidates.append((column, score))
                        break
            
            # 按分数排序并去重
            candidates = sorted(
                set(candidates), key=lambda x: x[1], reverse=True
            )
            suggestions[field_name] = [col for col, _ in candidates[:3]]
        
        return suggestions
