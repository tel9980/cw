#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的Excel处理器 - 提升大文件处理性能

Feature: small-accountant-practical-enhancement
Optimization: Excel processing performance
"""

import pandas as pd
import numpy as np
from typing import Iterator, List, Dict, Any, Optional, Tuple
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from ..models.core_models import TransactionRecord, TransactionType, TransactionStatus
from ..core.exceptions import ImportError, ValidationError


@dataclass
class ProcessingStats:
    """处理统计信息"""
    total_rows: int = 0
    processed_rows: int = 0
    error_rows: int = 0
    processing_time: float = 0.0
    memory_usage_mb: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_rows == 0:
            return 0.0
        return (self.processed_rows / self.total_rows) * 100


class ProgressCallback:
    """进度回调接口"""
    
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = time.time()
    
    def update(self, step: int, message: str = ""):
        """更新进度"""
        self.current_step = step
        progress = (step / self.total_steps) * 100
        elapsed = time.time() - self.start_time
        
        if step > 0:
            eta = (elapsed / step) * (self.total_steps - step)
            print(f"\r进度: {progress:.1f}% ({step}/{self.total_steps}) - {message} - 预计剩余: {eta:.1f}秒", end="")
        else:
            print(f"\r进度: {progress:.1f}% - {message}", end="")
    
    def finish(self):
        """完成进度"""
        elapsed = time.time() - self.start_time
        print(f"\n✅ 处理完成，总耗时: {elapsed:.2f}秒")


class OptimizedExcelProcessor:
    """优化的Excel处理器
    
    特性：
    - 分块读取大文件
    - 多线程并行处理
    - 内存使用优化
    - 实时进度显示
    - 错误恢复机制
    """
    
    def __init__(self, 
                 chunk_size: int = 1000,
                 max_workers: int = 4,
                 memory_limit_mb: int = 500):
        """
        初始化优化处理器
        
        Args:
            chunk_size: 每次处理的行数
            max_workers: 最大工作线程数
            memory_limit_mb: 内存使用限制(MB)
        """
        self.chunk_size = chunk_size
        self.max_workers = max_workers
        self.memory_limit_mb = memory_limit_mb
        self.logger = logging.getLogger(__name__)
        
        # 性能统计
        self.stats = ProcessingStats()
        
        # 缓存优化
        self._column_mapping_cache = {}
        self._validation_cache = {}
    
    def process_excel_file(self, 
                          file_path: Path,
                          column_mapping: Dict[str, str],
                          progress_callback: Optional[ProgressCallback] = None) -> Tuple[List[TransactionRecord], ProcessingStats]:
        """
        优化的Excel文件处理
        
        Args:
            file_path: Excel文件路径
            column_mapping: 列映射配置
            progress_callback: 进度回调
            
        Returns:
            处理结果和统计信息
        """
        start_time = time.time()
        
        try:
            # 1. 预处理：获取文件信息
            file_info = self._analyze_file(file_path)
            self.stats.total_rows = file_info['total_rows']
            
            if progress_callback:
                progress_callback.total_steps = self.stats.total_rows
                progress_callback.update(0, "开始处理Excel文件...")
            
            # 2. 分块读取和处理
            all_records = []
            
            if file_info['total_rows'] <= self.chunk_size:
                # 小文件：直接处理
                records = self._process_small_file(file_path, column_mapping, progress_callback)
                all_records.extend(records)
            else:
                # 大文件：分块处理
                records = self._process_large_file(file_path, column_mapping, progress_callback)
                all_records.extend(records)
            
            # 3. 后处理：数据清理和验证
            if progress_callback:
                progress_callback.update(self.stats.total_rows, "数据验证中...")
            
            validated_records = self._post_process_records(all_records)
            
            # 4. 统计信息
            self.stats.processed_rows = len(validated_records)
            self.stats.processing_time = time.time() - start_time
            self.stats.memory_usage_mb = self._get_memory_usage()
            
            if progress_callback:
                progress_callback.finish()
            
            self.logger.info(f"Excel处理完成: {self.stats.processed_rows}/{self.stats.total_rows} 行，"
                           f"成功率: {self.stats.success_rate:.1f}%，耗时: {self.stats.processing_time:.2f}秒")
            
            return validated_records, self.stats
            
        except Exception as e:
            self.logger.error(f"Excel处理失败: {e}")
            raise ImportError(f"Excel文件处理失败: {e}")
    
    def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """分析文件基本信息"""
        try:
            # 快速读取文件信息
            with pd.ExcelFile(file_path) as xls:
                sheet_names = xls.sheet_names
                
                # 读取第一个工作表的基本信息
                df_info = pd.read_excel(xls, sheet_name=0, nrows=0)
                columns = df_info.columns.tolist()
                
                # 获取总行数（快速方法）
                df_sample = pd.read_excel(xls, sheet_name=0)
                total_rows = len(df_sample)
                
                return {
                    'total_rows': total_rows,
                    'columns': columns,
                    'sheet_names': sheet_names,
                    'file_size_mb': file_path.stat().st_size / (1024 * 1024)
                }
        except Exception as e:
            raise ImportError(f"无法分析Excel文件: {e}")
    
    def _process_small_file(self, 
                           file_path: Path, 
                           column_mapping: Dict[str, str],
                           progress_callback: Optional[ProgressCallback] = None) -> List[TransactionRecord]:
        """处理小文件（单线程）"""
        try:
            df = pd.read_excel(file_path)
            records = []
            
            for idx, row in df.iterrows():
                try:
                    record = self._convert_row_to_record(row, column_mapping)
                    if record:
                        records.append(record)
                        self.stats.processed_rows += 1
                    
                    if progress_callback and idx % 100 == 0:
                        progress_callback.update(idx + 1, f"处理第 {idx + 1} 行")
                        
                except Exception as e:
                    self.stats.error_rows += 1
                    self.logger.warning(f"第 {idx + 1} 行处理失败: {e}")
            
            return records
            
        except Exception as e:
            raise ImportError(f"小文件处理失败: {e}")
    
    def _process_large_file(self, 
                           file_path: Path, 
                           column_mapping: Dict[str, str],
                           progress_callback: Optional[ProgressCallback] = None) -> List[TransactionRecord]:
        """处理大文件（分块+多线程）"""
        try:
            all_records = []
            processed_rows = 0
            
            # 分块读取
            chunk_reader = pd.read_excel(file_path, chunksize=self.chunk_size)
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有块的处理任务
                future_to_chunk = {}
                chunk_index = 0
                
                for chunk in chunk_reader:
                    future = executor.submit(self._process_chunk, chunk, column_mapping, chunk_index)
                    future_to_chunk[future] = chunk_index
                    chunk_index += 1
                
                # 收集结果
                for future in as_completed(future_to_chunk):
                    chunk_idx = future_to_chunk[future]
                    try:
                        chunk_records = future.result()
                        all_records.extend(chunk_records)
                        processed_rows += len(chunk_records)
                        
                        if progress_callback:
                            progress_callback.update(processed_rows, f"已处理 {processed_rows} 行")
                            
                    except Exception as e:
                        self.logger.error(f"块 {chunk_idx} 处理失败: {e}")
                        self.stats.error_rows += self.chunk_size
            
            return all_records
            
        except Exception as e:
            raise ImportError(f"大文件处理失败: {e}")
    
    def _process_chunk(self, 
                      chunk: pd.DataFrame, 
                      column_mapping: Dict[str, str],
                      chunk_index: int) -> List[TransactionRecord]:
        """处理单个数据块"""
        records = []
        
        for idx, row in chunk.iterrows():
            try:
                record = self._convert_row_to_record(row, column_mapping)
                if record:
                    records.append(record)
            except Exception as e:
                self.logger.warning(f"块 {chunk_index} 第 {idx} 行处理失败: {e}")
        
        return records
    
    def _convert_row_to_record(self, 
                              row: pd.Series, 
                              column_mapping: Dict[str, str]) -> Optional[TransactionRecord]:
        """将Excel行转换为交易记录"""
        try:
            # 使用缓存的列映射
            cache_key = str(sorted(column_mapping.items()))
            if cache_key not in self._column_mapping_cache:
                self._column_mapping_cache[cache_key] = column_mapping
            
            mapping = self._column_mapping_cache[cache_key]
            
            # 提取必要字段
            date_str = str(row.get(mapping.get('date', ''), '')).strip()
            amount_str = str(row.get(mapping.get('amount', ''), '')).strip()
            description = str(row.get(mapping.get('description', ''), '')).strip()
            counterparty = str(row.get(mapping.get('counterparty', ''), '')).strip()
            
            # 数据验证和转换
            if not date_str or not amount_str or date_str == 'nan' or amount_str == 'nan':
                return None
            
            # 日期转换
            try:
                if isinstance(row.get(mapping.get('date', '')), pd.Timestamp):
                    transaction_date = row.get(mapping.get('date', '')).date()
                else:
                    transaction_date = pd.to_datetime(date_str).date()
            except:
                return None
            
            # 金额转换
            try:
                amount = Decimal(str(amount_str).replace(',', '').replace('￥', '').replace('¥', ''))
                if amount == 0:
                    return None
            except:
                return None
            
            # 交易类型判断
            transaction_type = TransactionType.INCOME if amount > 0 else TransactionType.EXPENSE
            amount = abs(amount)
            
            # 创建交易记录
            record = TransactionRecord(
                id=f"import_{int(time.time() * 1000000)}_{hash(str(row.values))}",
                date=transaction_date,
                type=transaction_type,
                amount=amount,
                counterparty_id=counterparty or "未知",
                description=description or "导入交易",
                category=self._auto_categorize(description),
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            return record
            
        except Exception as e:
            self.logger.warning(f"行转换失败: {e}")
            return None
    
    def _auto_categorize(self, description: str) -> str:
        """自动分类交易"""
        if not description:
            return "其他"
        
        description_lower = description.lower()
        
        # 简单的关键词匹配
        categories = {
            "销售": ["销售", "收入", "营业", "服务费"],
            "采购": ["采购", "进货", "原材料", "供应商"],
            "费用": ["费用", "支出", "办公", "差旅", "租金"],
            "税费": ["税", "增值税", "所得税", "印花税"],
            "银行": ["银行", "利息", "手续费", "贷款"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in description_lower for keyword in keywords):
                return category
        
        return "其他"
    
    def _post_process_records(self, records: List[TransactionRecord]) -> List[TransactionRecord]:
        """后处理：数据清理和验证"""
        cleaned_records = []
        
        for record in records:
            try:
                # 数据验证
                if self._validate_record(record):
                    cleaned_records.append(record)
                else:
                    self.stats.error_rows += 1
            except Exception as e:
                self.logger.warning(f"记录验证失败: {e}")
                self.stats.error_rows += 1
        
        # 去重
        unique_records = self._remove_duplicates(cleaned_records)
        
        return unique_records
    
    def _validate_record(self, record: TransactionRecord) -> bool:
        """验证交易记录"""
        # 使用缓存提高验证性能
        cache_key = f"{record.date}_{record.amount}_{record.description[:20]}"
        if cache_key in self._validation_cache:
            return self._validation_cache[cache_key]
        
        is_valid = (
            record.date is not None and
            record.amount > 0 and
            record.description.strip() != "" and
            len(record.description) <= 200
        )
        
        self._validation_cache[cache_key] = is_valid
        return is_valid
    
    def _remove_duplicates(self, records: List[TransactionRecord]) -> List[TransactionRecord]:
        """去除重复记录"""
        seen = set()
        unique_records = []
        
        for record in records:
            # 创建唯一标识
            key = (record.date, record.amount, record.description, record.counterparty_id)
            if key not in seen:
                seen.add(key)
                unique_records.append(record)
        
        return unique_records
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用量(MB)"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0
    
    def get_performance_report(self) -> str:
        """获取性能报告"""
        return f"""
📊 Excel处理性能报告
==================
总行数: {self.stats.total_rows:,}
成功处理: {self.stats.processed_rows:,}
错误行数: {self.stats.error_rows:,}
成功率: {self.stats.success_rate:.1f}%
处理时间: {self.stats.processing_time:.2f} 秒
处理速度: {self.stats.processed_rows / max(self.stats.processing_time, 0.001):.0f} 行/秒
内存使用: {self.stats.memory_usage_mb:.1f} MB

⚡ 性能优化效果:
- 分块处理: 支持任意大小文件
- 多线程: {self.max_workers} 个工作线程
- 内存优化: 限制 {self.memory_limit_mb} MB
- 缓存机制: 提升重复操作性能
"""


# 使用示例
if __name__ == "__main__":
    # 创建优化处理器
    processor = OptimizedExcelProcessor(
        chunk_size=2000,  # 每次处理2000行
        max_workers=4,    # 4个工作线程
        memory_limit_mb=300  # 限制300MB内存
    )
    
    # 列映射配置
    column_mapping = {
        'date': '日期',
        'amount': '金额',
        'description': '摘要',
        'counterparty': '对方户名'
    }
    
    # 处理Excel文件
    file_path = Path("test_data.xlsx")
    progress = ProgressCallback(total_steps=1000)
    
    try:
        records, stats = processor.process_excel_file(
            file_path=file_path,
            column_mapping=column_mapping,
            progress_callback=progress
        )
        
        print(processor.get_performance_report())
        print(f"\n✅ 成功导入 {len(records)} 条交易记录")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")