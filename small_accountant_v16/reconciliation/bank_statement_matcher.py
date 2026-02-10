"""
Bank Statement Matcher for V1.6 Small Accountant Practical Enhancement

This module implements the BankStatementMatcher class that matches bank statement
records with system transaction records, supporting both exact and fuzzy matching.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple, Set
from difflib import SequenceMatcher

from small_accountant_v16.models.core_models import (
    BankRecord,
    TransactionRecord,
    Discrepancy,
    DiscrepancyType
)


@dataclass
class MatchConfig:
    """匹配配置"""
    # 金额容差（百分比，例如 0.01 表示 1%）
    amount_tolerance_percent: float = 0.0
    # 金额容差（绝对值）
    amount_tolerance_absolute: Decimal = Decimal("0.00")
    # 日期容差（天数）
    date_tolerance_days: int = 0
    # 往来单位名称相似度阈值（0.0-1.0）
    counterparty_similarity_threshold: float = 0.8
    # 描述相似度阈值（0.0-1.0）
    description_similarity_threshold: float = 0.6
    # 是否启用模糊匹配
    enable_fuzzy_matching: bool = True


@dataclass
class Match:
    """匹配结果"""
    bank_record: BankRecord
    system_record: TransactionRecord
    confidence: float  # 匹配置信度 (0.0-1.0)
    match_type: str  # 'exact' or 'fuzzy'
    match_details: dict  # 匹配详情


@dataclass
class MatchResult:
    """匹配结果集"""
    matches: List[Match]
    unmatched_bank_records: List[BankRecord]
    unmatched_system_records: List[TransactionRecord]
    total_bank_records: int
    total_system_records: int
    matched_count: int
    
    @property
    def match_rate(self) -> float:
        """匹配率"""
        if self.total_bank_records == 0:
            return 0.0
        return self.matched_count / self.total_bank_records


class BankStatementMatcher:
    """
    银行流水匹配器
    
    负责将银行流水记录与系统交易记录进行匹配，支持精确匹配和模糊匹配。
    """
    
    def __init__(self, config: Optional[MatchConfig] = None):
        """
        初始化匹配器
        
        Args:
            config: 匹配配置，如果为None则使用默认配置
        """
        self.config = config or MatchConfig()
    
    def match_transactions(
        self,
        bank_records: List[BankRecord],
        system_records: List[TransactionRecord]
    ) -> MatchResult:
        """
        匹配银行流水和系统交易记录
        
        Args:
            bank_records: 银行流水记录列表
            system_records: 系统交易记录列表
        
        Returns:
            MatchResult: 匹配结果
        """
        matches: List[Match] = []
        matched_bank_ids: Set[str] = set()
        matched_system_ids: Set[str] = set()
        
        # 第一轮：精确匹配
        for bank_record in bank_records:
            if bank_record.id in matched_bank_ids:
                continue
            
            for system_record in system_records:
                if system_record.id in matched_system_ids:
                    continue
                
                if self._is_exact_match(bank_record, system_record):
                    match = Match(
                        bank_record=bank_record,
                        system_record=system_record,
                        confidence=1.0,
                        match_type='exact',
                        match_details={
                            'amount_match': True,
                            'date_match': True,
                            'counterparty_match': True
                        }
                    )
                    matches.append(match)
                    matched_bank_ids.add(bank_record.id)
                    matched_system_ids.add(system_record.id)
                    break
        
        # 第二轮：模糊匹配（如果启用）
        if self.config.enable_fuzzy_matching:
            for bank_record in bank_records:
                if bank_record.id in matched_bank_ids:
                    continue
                
                best_match: Optional[Tuple[TransactionRecord, float, dict]] = None
                
                for system_record in system_records:
                    if system_record.id in matched_system_ids:
                        continue
                    
                    confidence, details = self._calculate_fuzzy_match(
                        bank_record, system_record
                    )
                    
                    if confidence > 0.7:  # 置信度阈值
                        if best_match is None or confidence > best_match[1]:
                            best_match = (system_record, confidence, details)
                
                if best_match:
                    system_record, confidence, details = best_match
                    match = Match(
                        bank_record=bank_record,
                        system_record=system_record,
                        confidence=confidence,
                        match_type='fuzzy',
                        match_details=details
                    )
                    matches.append(match)
                    matched_bank_ids.add(bank_record.id)
                    matched_system_ids.add(system_record.id)
        
        # 收集未匹配的记录
        unmatched_bank_records = [
            br for br in bank_records if br.id not in matched_bank_ids
        ]
        unmatched_system_records = [
            sr for sr in system_records if sr.id not in matched_system_ids
        ]
        
        return MatchResult(
            matches=matches,
            unmatched_bank_records=unmatched_bank_records,
            unmatched_system_records=unmatched_system_records,
            total_bank_records=len(bank_records),
            total_system_records=len(system_records),
            matched_count=len(matches)
        )
    
    def identify_discrepancies(self, match_result: MatchResult) -> List[Discrepancy]:
        """
        识别差异
        
        Args:
            match_result: 匹配结果
        
        Returns:
            List[Discrepancy]: 差异列表
        """
        discrepancies: List[Discrepancy] = []
        discrepancy_id = 1
        
        # 1. 检查模糊匹配中的金额差异
        for match in match_result.matches:
            if match.match_type == 'fuzzy':
                amount_diff = abs(
                    match.bank_record.amount - match.system_record.amount
                )
                if amount_diff > Decimal("0.01"):  # 超过1分钱的差异
                    discrepancy = Discrepancy(
                        id=f"DISC-{discrepancy_id:04d}",
                        type=DiscrepancyType.AMOUNT_DIFF,
                        bank_record=match.bank_record,
                        system_record=match.system_record,
                        difference_amount=amount_diff,
                        description=(
                            f"金额差异：银行流水 {match.bank_record.amount}，"
                            f"系统记录 {match.system_record.amount}，"
                            f"差额 {amount_diff}"
                        )
                    )
                    discrepancies.append(discrepancy)
                    discrepancy_id += 1
        
        # 2. 银行流水中存在但系统中缺失的记录
        for bank_record in match_result.unmatched_bank_records:
            discrepancy = Discrepancy(
                id=f"DISC-{discrepancy_id:04d}",
                type=DiscrepancyType.MISSING_SYSTEM,
                bank_record=bank_record,
                system_record=None,
                difference_amount=bank_record.amount,
                description=(
                    f"系统记录缺失：银行流水显示 {bank_record.transaction_date} "
                    f"{bank_record.counterparty} {bank_record.amount}，"
                    f"但系统中未找到对应记录"
                )
            )
            discrepancies.append(discrepancy)
            discrepancy_id += 1
        
        # 3. 系统中存在但银行流水中缺失的记录
        for system_record in match_result.unmatched_system_records:
            discrepancy = Discrepancy(
                id=f"DISC-{discrepancy_id:04d}",
                type=DiscrepancyType.MISSING_BANK,
                bank_record=None,
                system_record=system_record,
                difference_amount=system_record.amount,
                description=(
                    f"银行流水缺失：系统记录显示 {system_record.date} "
                    f"{system_record.description} {system_record.amount}，"
                    f"但银行流水中未找到对应记录"
                )
            )
            discrepancies.append(discrepancy)
            discrepancy_id += 1
        
        return discrepancies
    
    def _is_exact_match(
        self,
        bank_record: BankRecord,
        system_record: TransactionRecord
    ) -> bool:
        """
        检查是否精确匹配
        
        Args:
            bank_record: 银行流水记录
            system_record: 系统交易记录
        
        Returns:
            bool: 是否精确匹配
        """
        # 金额必须完全相等
        if bank_record.amount != system_record.amount:
            return False
        
        # 日期必须完全相等
        if bank_record.transaction_date != system_record.date:
            return False
        
        # 往来单位名称必须匹配（忽略大小写和空格）
        bank_counterparty = bank_record.counterparty.strip().lower()
        system_counterparty = system_record.description.strip().lower()
        
        # 检查是否包含关系或完全相等
        if bank_counterparty == system_counterparty:
            return True
        if bank_counterparty in system_counterparty:
            return True
        if system_counterparty in bank_counterparty:
            return True
        
        return False
    
    def _calculate_fuzzy_match(
        self,
        bank_record: BankRecord,
        system_record: TransactionRecord
    ) -> Tuple[float, dict]:
        """
        计算模糊匹配的置信度
        
        Args:
            bank_record: 银行流水记录
            system_record: 系统交易记录
        
        Returns:
            Tuple[float, dict]: (置信度, 匹配详情)
        """
        scores = []
        details = {}
        
        # 1. 金额匹配度
        amount_match, amount_score = self._match_amount(
            bank_record.amount, system_record.amount
        )
        scores.append(amount_score * 0.4)  # 权重40%
        details['amount_match'] = amount_match
        details['amount_score'] = amount_score
        
        # 2. 日期匹配度
        date_match, date_score = self._match_date(
            bank_record.transaction_date, system_record.date
        )
        scores.append(date_score * 0.3)  # 权重30%
        details['date_match'] = date_match
        details['date_score'] = date_score
        
        # 3. 往来单位匹配度
        counterparty_score = self._match_counterparty(
            bank_record.counterparty, system_record.description
        )
        scores.append(counterparty_score * 0.3)  # 权重30%
        details['counterparty_score'] = counterparty_score
        
        # 总置信度
        confidence = sum(scores)
        
        return confidence, details
    
    def _match_amount(
        self,
        bank_amount: Decimal,
        system_amount: Decimal
    ) -> Tuple[bool, float]:
        """
        匹配金额
        
        Args:
            bank_amount: 银行流水金额
            system_amount: 系统记录金额
        
        Returns:
            Tuple[bool, float]: (是否匹配, 匹配分数)
        """
        diff = abs(bank_amount - system_amount)
        
        # 检查绝对容差
        if diff <= self.config.amount_tolerance_absolute:
            return True, 1.0
        
        # 检查百分比容差
        if self.config.amount_tolerance_percent > 0:
            max_amount = max(abs(bank_amount), abs(system_amount))
            if max_amount > 0:
                percent_diff = float(diff / max_amount)
                if percent_diff <= self.config.amount_tolerance_percent:
                    # 根据差异百分比计算分数
                    score = 1.0 - (percent_diff / self.config.amount_tolerance_percent)
                    return True, max(score, 0.7)
        
        # 金额不匹配
        return False, 0.0
    
    def _match_date(
        self,
        bank_date: date,
        system_date: date
    ) -> Tuple[bool, float]:
        """
        匹配日期
        
        Args:
            bank_date: 银行流水日期
            system_date: 系统记录日期
        
        Returns:
            Tuple[bool, float]: (是否匹配, 匹配分数)
        """
        if bank_date == system_date:
            return True, 1.0
        
        # 检查日期容差
        diff_days = abs((bank_date - system_date).days)
        if diff_days <= self.config.date_tolerance_days:
            # 根据日期差异计算分数
            if self.config.date_tolerance_days > 0:
                score = 1.0 - (diff_days / (self.config.date_tolerance_days + 1))
                return True, max(score, 0.7)
            else:
                return True, 1.0
        
        # 日期不匹配
        return False, 0.0
    
    def _match_counterparty(
        self,
        bank_counterparty: str,
        system_description: str
    ) -> float:
        """
        匹配往来单位名称
        
        Args:
            bank_counterparty: 银行流水往来单位
            system_description: 系统记录描述
        
        Returns:
            float: 匹配分数 (0.0-1.0)
        """
        # 标准化字符串
        bank_str = bank_counterparty.strip().lower()
        system_str = system_description.strip().lower()
        
        # 完全相等
        if bank_str == system_str:
            return 1.0
        
        # 包含关系
        if bank_str in system_str or system_str in bank_str:
            return 0.9
        
        # 使用序列匹配算法计算相似度
        similarity = SequenceMatcher(None, bank_str, system_str).ratio()
        
        # 只有超过阈值才认为匹配
        if similarity >= self.config.counterparty_similarity_threshold:
            return similarity
        
        return 0.0
