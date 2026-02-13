"""
Counterparty Alias Manager for V1.7 Oxidation Factory Complete

This module provides alias management for counterparties to support flexible
name matching in bank statements and reconciliation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Set
import json
import os
from difflib import SequenceMatcher


@dataclass
class CounterpartyAlias:
    """往来单位别名"""
    counterparty_id: str
    counterparty_name: str
    alias: str
    created_at: datetime
    created_by: str
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "counterparty_id": self.counterparty_id,
            "counterparty_name": self.counterparty_name,
            "alias": self.alias,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CounterpartyAlias":
        """从字典创建"""
        return cls(
            counterparty_id=data["counterparty_id"],
            counterparty_name=data["counterparty_name"],
            alias=data["alias"],
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=data["created_by"],
        )


@dataclass
class AliasMatchResult:
    """别名匹配结果"""
    counterparty_id: str
    counterparty_name: str
    matched_alias: str
    confidence: float  # 匹配置信度 (0.0-1.0)
    match_type: str  # 'exact', 'alias', 'fuzzy'


class CounterpartyAliasManager:
    """
    往来单位别名管理器
    
    功能:
    - 为往来单位添加别名
    - 自动匹配银行流水中的往来单位名称
    - 检测别名冲突
    - 批量导入别名
    - 智能建议别名
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化别名管理器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.aliases_file = os.path.join(data_dir, "counterparty_aliases.json")
        
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 加载别名数据
        self.aliases: List[CounterpartyAlias] = self._load_aliases()
        
        # 构建索引以加速查询
        self._rebuild_index()
    
    def add_alias(
        self,
        counterparty_id: str,
        counterparty_name: str,
        alias: str,
        created_by: str = "system"
    ) -> CounterpartyAlias:
        """
        为往来单位添加别名
        
        Args:
            counterparty_id: 往来单位ID
            counterparty_name: 往来单位名称
            alias: 别名
            created_by: 创建人
        
        Returns:
            CounterpartyAlias: 创建的别名记录
        
        Raises:
            ValueError: 如果别名已存在或冲突
        """
        # 标准化别名
        alias = alias.strip()
        
        # 检查别名是否已存在
        existing = self._find_exact_alias(alias)
        if existing:
            if existing.counterparty_id == counterparty_id:
                raise ValueError(f"别名已存在: {alias}")
            else:
                raise ValueError(
                    f"别名冲突: {alias} 已被 {existing.counterparty_name} 使用"
                )
        
        # 创建别名记录
        alias_record = CounterpartyAlias(
            counterparty_id=counterparty_id,
            counterparty_name=counterparty_name,
            alias=alias,
            created_at=datetime.now(),
            created_by=created_by,
        )
        
        # 添加到列表
        self.aliases.append(alias_record)
        
        # 重建索引
        self._rebuild_index()
        
        # 保存到文件
        self._save_aliases()
        
        return alias_record
    
    def add_aliases_batch(
        self,
        aliases_data: List[Dict[str, str]],
        created_by: str = "system"
    ) -> Dict[str, any]:
        """
        批量添加别名
        
        Args:
            aliases_data: 别名数据列表,每项包含:
                - counterparty_id: 往来单位ID
                - counterparty_name: 往来单位名称
                - alias: 别名
            created_by: 创建人
        
        Returns:
            Dict: 导入结果统计
                - total: 总数
                - success: 成功数
                - failed: 失败数
                - errors: 错误列表
        """
        total = len(aliases_data)
        success = 0
        failed = 0
        errors = []
        
        for i, data in enumerate(aliases_data, 1):
            try:
                self.add_alias(
                    counterparty_id=data["counterparty_id"],
                    counterparty_name=data["counterparty_name"],
                    alias=data["alias"],
                    created_by=created_by,
                )
                success += 1
            except Exception as e:
                failed += 1
                errors.append({
                    "row": i,
                    "data": data,
                    "error": str(e),
                })
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "errors": errors,
        }
    
    def remove_alias(
        self,
        counterparty_id: str,
        alias: str
    ) -> bool:
        """
        删除别名
        
        Args:
            counterparty_id: 往来单位ID
            alias: 别名
        
        Returns:
            bool: 是否成功删除
        """
        alias = alias.strip()
        
        # 查找并删除别名
        for i, alias_record in enumerate(self.aliases):
            if (alias_record.counterparty_id == counterparty_id and
                alias_record.alias == alias):
                del self.aliases[i]
                self._rebuild_index()
                self._save_aliases()
                return True
        
        return False
    
    def get_aliases(self, counterparty_id: str) -> List[str]:
        """
        获取往来单位的所有别名
        
        Args:
            counterparty_id: 往来单位ID
        
        Returns:
            List[str]: 别名列表
        """
        return [
            alias_record.alias
            for alias_record in self.aliases
            if alias_record.counterparty_id == counterparty_id
        ]
    
    def match_counterparty(
        self,
        name: str,
        similarity_threshold: float = 0.8
    ) -> Optional[AliasMatchResult]:
        """
        匹配往来单位(支持别名和模糊匹配)
        
        Args:
            name: 要匹配的名称(来自银行流水等)
            similarity_threshold: 模糊匹配的相似度阈值
        
        Returns:
            AliasMatchResult: 匹配结果,如果没有匹配则返回None
        """
        name = name.strip()
        
        # 1. 精确匹配别名
        exact_match = self._find_exact_alias(name)
        if exact_match:
            return AliasMatchResult(
                counterparty_id=exact_match.counterparty_id,
                counterparty_name=exact_match.counterparty_name,
                matched_alias=exact_match.alias,
                confidence=1.0,
                match_type='alias',
            )
        
        # 2. 精确匹配往来单位名称
        for alias_record in self.aliases:
            if alias_record.counterparty_name.strip() == name:
                return AliasMatchResult(
                    counterparty_id=alias_record.counterparty_id,
                    counterparty_name=alias_record.counterparty_name,
                    matched_alias=name,
                    confidence=1.0,
                    match_type='exact',
                )
        
        # 3. 模糊匹配
        best_match = None
        best_similarity = 0.0
        
        name_lower = name.lower()
        
        for alias_record in self.aliases:
            # 检查别名
            alias_lower = alias_record.alias.lower()
            similarity = SequenceMatcher(None, name_lower, alias_lower).ratio()
            
            if similarity > best_similarity and similarity >= similarity_threshold:
                best_similarity = similarity
                best_match = AliasMatchResult(
                    counterparty_id=alias_record.counterparty_id,
                    counterparty_name=alias_record.counterparty_name,
                    matched_alias=alias_record.alias,
                    confidence=similarity,
                    match_type='fuzzy',
                )
            
            # 检查往来单位名称
            counterparty_lower = alias_record.counterparty_name.lower()
            similarity = SequenceMatcher(None, name_lower, counterparty_lower).ratio()
            
            if similarity > best_similarity and similarity >= similarity_threshold:
                best_similarity = similarity
                best_match = AliasMatchResult(
                    counterparty_id=alias_record.counterparty_id,
                    counterparty_name=alias_record.counterparty_name,
                    matched_alias=alias_record.counterparty_name,
                    confidence=similarity,
                    match_type='fuzzy',
                )
        
        return best_match
    
    def detect_conflicts(self) -> List[Dict[str, any]]:
        """
        检测别名冲突
        
        Returns:
            List[Dict]: 冲突列表,每项包含:
                - alias: 冲突的别名
                - counterparties: 使用该别名的往来单位列表
        """
        # 按别名分组
        alias_groups: Dict[str, List[CounterpartyAlias]] = {}
        for alias_record in self.aliases:
            alias_lower = alias_record.alias.lower()
            if alias_lower not in alias_groups:
                alias_groups[alias_lower] = []
            alias_groups[alias_lower].append(alias_record)
        
        # 找出冲突
        conflicts = []
        for alias, records in alias_groups.items():
            # 检查是否有不同的往来单位使用相同别名
            counterparty_ids = set(r.counterparty_id for r in records)
            if len(counterparty_ids) > 1:
                conflicts.append({
                    "alias": alias,
                    "counterparties": [
                        {
                            "id": r.counterparty_id,
                            "name": r.counterparty_name,
                        }
                        for r in records
                    ],
                })
        
        return conflicts
    
    def suggest_aliases(
        self,
        counterparty_name: str,
        bank_statement_names: List[str],
        similarity_threshold: float = 0.7
    ) -> List[str]:
        """
        智能建议别名
        
        根据银行流水中出现的名称,建议可能的别名
        
        Args:
            counterparty_name: 往来单位名称
            bank_statement_names: 银行流水中出现的名称列表
            similarity_threshold: 相似度阈值
        
        Returns:
            List[str]: 建议的别名列表
        """
        suggestions = []
        counterparty_lower = counterparty_name.lower()
        
        for bank_name in bank_statement_names:
            bank_name = bank_name.strip()
            bank_lower = bank_name.lower()
            
            # 跳过完全相同的名称
            if bank_lower == counterparty_lower:
                continue
            
            # 计算相似度
            similarity = SequenceMatcher(None, counterparty_lower, bank_lower).ratio()
            
            # 如果相似度足够高,建议作为别名
            if similarity >= similarity_threshold:
                # 检查是否已经是别名
                if not self._find_exact_alias(bank_name):
                    suggestions.append(bank_name)
        
        return suggestions
    
    def get_all_aliases(self) -> List[CounterpartyAlias]:
        """
        获取所有别名记录
        
        Returns:
            List[CounterpartyAlias]: 所有别名记录
        """
        return self.aliases.copy()
    
    def export_aliases(self) -> List[Dict[str, str]]:
        """
        导出别名数据(用于Excel导出)
        
        Returns:
            List[Dict]: 别名数据列表
        """
        return [
            {
                "往来单位ID": alias.counterparty_id,
                "往来单位名称": alias.counterparty_name,
                "别名": alias.alias,
                "创建时间": alias.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "创建人": alias.created_by,
            }
            for alias in self.aliases
        ]
    
    def _find_exact_alias(self, alias: str) -> Optional[CounterpartyAlias]:
        """查找精确匹配的别名"""
        alias_lower = alias.lower()
        for alias_record in self.aliases:
            if alias_record.alias.lower() == alias_lower:
                return alias_record
        return None
    
    def _rebuild_index(self):
        """重建索引以加速查询"""
        # 按往来单位ID索引
        self._by_counterparty: Dict[str, List[CounterpartyAlias]] = {}
        for alias_record in self.aliases:
            if alias_record.counterparty_id not in self._by_counterparty:
                self._by_counterparty[alias_record.counterparty_id] = []
            self._by_counterparty[alias_record.counterparty_id].append(alias_record)
        
        # 按别名索引(小写)
        self._by_alias: Dict[str, CounterpartyAlias] = {}
        for alias_record in self.aliases:
            alias_lower = alias_record.alias.lower()
            self._by_alias[alias_lower] = alias_record
    
    def _load_aliases(self) -> List[CounterpartyAlias]:
        """从文件加载别名数据"""
        if not os.path.exists(self.aliases_file):
            return []
        
        try:
            with open(self.aliases_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [CounterpartyAlias.from_dict(item) for item in data]
        except Exception:
            return []
    
    def _save_aliases(self):
        """保存别名数据到文件"""
        data = [alias.to_dict() for alias in self.aliases]
        with open(self.aliases_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
