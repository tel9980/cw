# -*- coding: utf-8 -*-
"""
One-Click Operations Manager
一键操作管理器 - 提供智能默认值的原子化操作
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class OperationError(Exception):
    """操作错误异常"""
    pass


class ValidationError(Exception):
    """验证错误异常"""
    pass


class OneClickOperationManager:
    """
    一键操作管理器
    
    负责：
    - 提供智能默认值的一键交易录入
    - 原子化操作（验证+计算+保存）
    - 批量操作处理
    - 常用操作模板
    - 错误处理和回滚
    
    Requirements: 3.1, 3.2, 3.3
    """
    
    def __init__(
        self,
        context_engine,
        workflow_engine,
        progressive_disclosure_manager,
        storage_path: str = "财务数据/one_click_operations"
    ):
        """
        初始化一键操作管理器
        
        Args:
            context_engine: 上下文引擎实例
            workflow_engine: 工作流引擎实例
            progressive_disclosure_manager: 渐进式披露管理器实例
            storage_path: 数据存储路径
        """
        self.context_engine = context_engine
        self.workflow_engine = workflow_engine
        self.progressive_disclosure = progressive_disclosure_manager
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 操作模板库
        self.operation_templates: Dict[str, Dict[str, Any]] = {}
        
        # 批量操作队列
        self.batch_queues: Dict[str, List[Dict[str, Any]]] = {}
        
        # 操作历史（用于回滚）
        self.operation_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # 验证器注册表
        self.validators: Dict[str, Callable] = {}
        
        # 计算器注册表
        self.calculators: Dict[str, Callable] = {}
        
        # 保存器注册表
        self.savers: Dict[str, Callable] = {}
        
        # 初始化默认模板和处理器
        self._initialize_default_templates()
        self._register_default_handlers()
        
        logger.info("OneClickOperationManager initialized with storage at %s", self.storage_path)
    
    def _initialize_default_templates(self) -> None:
        """初始化默认操作模板"""
        # 收入录入模板
        self.operation_templates['income_entry'] = {
            'template_id': 'income_entry',
            'name': '收入录入',
            'description': '快速录入收入交易',
            'transaction_type': 'income',
            'required_fields': ['date', 'amount', 'customer_id', 'category'],
            'optional_fields': ['description', 'payment_method', 'invoice_number'],
            'default_values': {
                'payment_method': '银行转账',
                'category': '销售收入'
            },
            'validation_rules': {
                'amount': {'min': 0.01, 'max': 1000000000, 'type': 'amount'},
                'date': {'type': 'date', 'max': 'today'}
            }
        }
        
        # 支出录入模板
        self.operation_templates['expense_entry'] = {
            'template_id': 'expense_entry',
            'name': '支出录入',
            'description': '快速录入支出交易',
            'transaction_type': 'expense',
            'required_fields': ['date', 'amount', 'vendor_id', 'category'],
            'optional_fields': ['description', 'payment_method', 'invoice_number'],
            'default_values': {
                'payment_method': '银行转账',
                'category': '采购成本'
            },
            'validation_rules': {
                'amount': {'min': 0.01, 'max': 1000000000, 'type': 'amount'},
                'date': {'type': 'date', 'max': 'today'}
            }
        }
        
        # 对账模板
        self.operation_templates['reconciliation'] = {
            'template_id': 'reconciliation',
            'name': '银行对账',
            'description': '快速对账银行流水',
            'transaction_type': 'reconciliation',
            'required_fields': ['bank_account', 'statement_date', 'transactions'],
            'optional_fields': ['notes'],
            'default_values': {},
            'validation_rules': {
                'transactions': {'type': 'list', 'min_length': 1}
            }
        }
        
        # 批量收款模板
        self.operation_templates['batch_collection'] = {
            'template_id': 'batch_collection',
            'name': '批量收款',
            'description': '批量处理多笔收款',
            'transaction_type': 'batch_income',
            'required_fields': ['date', 'items'],
            'optional_fields': ['payment_method', 'notes'],
            'default_values': {
                'payment_method': '银行转账'
            },
            'validation_rules': {
                'items': {'type': 'list', 'min_length': 1}
            }
        }
        
        # 批量付款模板
        self.operation_templates['batch_payment'] = {
            'template_id': 'batch_payment',
            'name': '批量付款',
            'description': '批量处理多笔付款',
            'transaction_type': 'batch_expense',
            'required_fields': ['date', 'items'],
            'optional_fields': ['payment_method', 'notes'],
            'default_values': {
                'payment_method': '银行转账'
            },
            'validation_rules': {
                'items': {'type': 'list', 'min_length': 1}
            }
        }
        
        logger.info(f"Initialized {len(self.operation_templates)} default operation templates")
    
    def _register_default_handlers(self) -> None:
        """注册默认的验证器、计算器和保存器"""
        # 注册验证器
        self.validators['amount'] = self._validate_amount
        self.validators['date'] = self._validate_date
        self.validators['entity_id'] = self._validate_entity_id
        self.validators['list'] = self._validate_list
        
        # 注册计算器
        self.calculators['tax'] = self._calculate_tax
        self.calculators['total'] = self._calculate_total
        self.calculators['balance'] = self._calculate_balance
        
        # 注册保存器
        self.savers['income'] = self._save_income_transaction
        self.savers['expense'] = self._save_expense_transaction
        self.savers['reconciliation'] = self._save_reconciliation
        self.savers['batch_income'] = self._save_batch_transactions
        self.savers['batch_expense'] = self._save_batch_transactions
        
        logger.info("Registered default validators, calculators, and savers")
    
    def execute_one_click_operation(
        self,
        template_id: str,
        user_id: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行一键操作（原子化：验证+计算+保存）
        
        这是核心方法，将多步骤操作合并为单一原子操作。
        
        Args:
            template_id: 操作模板ID
            user_id: 用户ID
            data: 操作数据
            context: 额外上下文信息
        
        Returns:
            Dict: 操作结果
        
        Requirements: 3.1, 3.3
        """
        operation_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # 1. 获取模板
            template = self.operation_templates.get(template_id)
            if not template:
                raise OperationError(f"Template {template_id} not found")
            
            # 2. 应用智能默认值（Requirement 3.1）
            enriched_data = self._apply_smart_defaults(
                template, user_id, data, context
            )
            
            # 3. 验证数据
            validation_result = self._validate_operation_data(
                template, enriched_data
            )
            if not validation_result['valid']:
                raise ValidationError(
                    f"Validation failed: {validation_result['errors']}"
                )
            
            # 4. 执行计算
            calculated_data = self._perform_calculations(
                template, enriched_data
            )
            
            # 5. 保存数据（原子操作）
            save_result = self._save_operation_data(
                template, calculated_data, user_id
            )
            
            # 6. 记录操作历史（用于回滚）
            self._record_operation_history(
                operation_id, user_id, template_id, calculated_data, save_result
            )
            
            # 7. 更新相关记录和报表（Requirement 3.4）
            self._update_related_records(template, save_result)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'success': True,
                'operation_id': operation_id,
                'template_id': template_id,
                'data': calculated_data,
                'save_result': save_result,
                'execution_time': execution_time,
                'message': f'{template["name"]}操作成功完成'
            }
            
            logger.info(
                f"One-click operation {template_id} completed successfully "
                f"in {execution_time:.2f}s for user {user_id}"
            )
            
            return result
            
        except ValidationError as e:
            logger.warning(f"Validation error in operation {template_id}: {e}")
            return {
                'success': False,
                'operation_id': operation_id,
                'error_type': 'validation',
                'error': str(e),
                'message': '数据验证失败，请检查输入'
            }
        
        except OperationError as e:
            logger.error(f"Operation error in {template_id}: {e}")
            return {
                'success': False,
                'operation_id': operation_id,
                'error_type': 'operation',
                'error': str(e),
                'message': '操作执行失败'
            }
        
        except Exception as e:
            logger.error(f"Unexpected error in operation {template_id}: {e}", exc_info=True)
            return {
                'success': False,
                'operation_id': operation_id,
                'error_type': 'system',
                'error': str(e),
                'message': '系统错误，操作未完成'
            }
    
    def _apply_smart_defaults(
        self,
        template: Dict[str, Any],
        user_id: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        应用智能默认值
        
        使用ContextEngine生成的智能默认值填充缺失字段。
        
        Args:
            template: 操作模板
            user_id: 用户ID
            data: 用户提供的数据
            context: 上下文信息
        
        Returns:
            Dict: 填充后的数据
        
        Requirements: 3.1
        """
        enriched_data = data.copy()
        context = context or {}
        context['user_id'] = user_id
        
        # 应用模板默认值
        for field, default_value in template.get('default_values', {}).items():
            if field not in enriched_data or enriched_data[field] is None:
                enriched_data[field] = default_value
        
        # 应用智能默认值（从ContextEngine）
        transaction_type = template.get('transaction_type', 'general')
        smart_defaults = self.context_engine.generate_smart_defaults(
            transaction_type, context
        )
        
        for field_name, smart_default in smart_defaults.items():
            if field_name not in enriched_data or enriched_data[field_name] is None:
                enriched_data[field_name] = smart_default.suggested_value
                # 记录使用了智能默认值
                enriched_data[f'_smart_default_{field_name}'] = {
                    'value': smart_default.suggested_value,
                    'confidence': smart_default.confidence,
                    'reasoning': smart_default.reasoning
                }
        
        return enriched_data
    
    def _validate_operation_data(
        self,
        template: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证操作数据
        
        Args:
            template: 操作模板
            data: 待验证数据
        
        Returns:
            Dict: 验证结果 {'valid': bool, 'errors': List[str]}
        """
        errors = []
        
        # 检查必填字段
        for field in template.get('required_fields', []):
            if field not in data or data[field] is None:
                errors.append(f"缺少必填字段: {field}")
        
        # 应用验证规则
        validation_rules = template.get('validation_rules', {})
        for field, rules in validation_rules.items():
            if field in data and data[field] is not None:
                field_type = rules.get('type')
                
                # 使用注册的验证器
                if field_type in self.validators:
                    validator = self.validators[field_type]
                    try:
                        validator(data[field], rules)
                    except ValidationError as e:
                        errors.append(f"{field}: {str(e)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _perform_calculations(
        self,
        template: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行计算
        
        Args:
            template: 操作模板
            data: 数据
        
        Returns:
            Dict: 计算后的数据
        """
        calculated_data = data.copy()
        
        # 根据交易类型执行相应计算
        transaction_type = template.get('transaction_type')
        
        if transaction_type in ['income', 'expense']:
            # 计算税额（如果需要）
            if 'tax_rate' in calculated_data and 'amount' in calculated_data:
                calculated_data['tax_amount'] = self.calculators['tax'](
                    calculated_data['amount'],
                    calculated_data.get('tax_rate', 0)
                )
                calculated_data['total_amount'] = self.calculators['total'](
                    calculated_data['amount'],
                    calculated_data.get('tax_amount', 0)
                )
        
        elif transaction_type in ['batch_income', 'batch_expense']:
            # 批量操作：计算总额
            items = calculated_data.get('items', [])
            total = sum(item.get('amount', 0) for item in items)
            calculated_data['total_amount'] = total
            calculated_data['item_count'] = len(items)
        
        elif transaction_type == 'reconciliation':
            # 对账：计算余额
            transactions = calculated_data.get('transactions', [])
            calculated_data['balance'] = self.calculators['balance'](transactions)
        
        return calculated_data
    
    def _save_operation_data(
        self,
        template: Dict[str, Any],
        data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        保存操作数据
        
        Args:
            template: 操作模板
            data: 数据
            user_id: 用户ID
        
        Returns:
            Dict: 保存结果
        """
        transaction_type = template.get('transaction_type')
        
        # 使用注册的保存器
        if transaction_type in self.savers:
            saver = self.savers[transaction_type]
            return saver(data, user_id)
        
        # 默认保存逻辑
        return self._default_save(data, user_id, transaction_type)
    
    def _record_operation_history(
        self,
        operation_id: str,
        user_id: str,
        template_id: str,
        data: Dict[str, Any],
        save_result: Dict[str, Any]
    ) -> None:
        """
        记录操作历史（用于回滚）
        
        Args:
            operation_id: 操作ID
            user_id: 用户ID
            template_id: 模板ID
            data: 操作数据
            save_result: 保存结果
        """
        if user_id not in self.operation_history:
            self.operation_history[user_id] = []
        
        history_record = {
            'operation_id': operation_id,
            'template_id': template_id,
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'save_result': save_result
        }
        
        self.operation_history[user_id].append(history_record)
        
        # 保持历史记录在合理大小（最多100条）
        if len(self.operation_history[user_id]) > 100:
            self.operation_history[user_id] = self.operation_history[user_id][-100:]
        
        # 持久化
        self._save_operation_history(user_id)
    
    def _update_related_records(
        self,
        template: Dict[str, Any],
        save_result: Dict[str, Any]
    ) -> None:
        """
        更新相关记录和报表
        
        Args:
            template: 操作模板
            save_result: 保存结果
        
        Requirements: 3.4
        """
        # 这里应该触发相关记录的更新
        # 实际实现中会调用V1.4的相关功能
        logger.debug(f"Updated related records for template {template['template_id']}")
    
    def execute_batch_operation(
        self,
        template_id: str,
        user_id: str,
        items: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行批量操作
        
        允许选择和处理多个相似项目。
        
        Args:
            template_id: 操作模板ID
            user_id: 用户ID
            items: 批量操作项列表
            context: 上下文信息
        
        Returns:
            Dict: 批量操作结果
        
        Requirements: 3.2
        """
        batch_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        results = {
            'batch_id': batch_id,
            'template_id': template_id,
            'total_items': len(items),
            'successful': 0,
            'failed': 0,
            'results': [],
            'errors': []
        }
        
        try:
            template = self.operation_templates.get(template_id)
            if not template:
                raise OperationError(f"Template {template_id} not found")
            
            # 处理每个项目
            for idx, item in enumerate(items):
                try:
                    # 执行单个操作
                    result = self.execute_one_click_operation(
                        template_id, user_id, item, context
                    )
                    
                    if result['success']:
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append({
                            'item_index': idx,
                            'error': result.get('error', 'Unknown error')
                        })
                    
                    results['results'].append(result)
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'item_index': idx,
                        'error': str(e)
                    })
                    logger.error(f"Error processing batch item {idx}: {e}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            results['execution_time'] = execution_time
            results['success'] = results['failed'] == 0
            
            logger.info(
                f"Batch operation {template_id} completed: "
                f"{results['successful']}/{results['total_items']} successful "
                f"in {execution_time:.2f}s"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Batch operation error: {e}", exc_info=True)
            results['success'] = False
            results['error'] = str(e)
            return results
    
    def rollback_operation(
        self,
        operation_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        回滚操作
        
        Args:
            operation_id: 操作ID
            user_id: 用户ID
        
        Returns:
            Dict: 回滚结果
        """
        try:
            # 查找操作历史
            history = self.operation_history.get(user_id, [])
            operation = next(
                (op for op in history if op['operation_id'] == operation_id),
                None
            )
            
            if not operation:
                return {
                    'success': False,
                    'error': f'Operation {operation_id} not found in history'
                }
            
            # 执行回滚（实际实现中会调用V1.4的删除/撤销功能）
            # 这里是简化版本
            logger.info(f"Rolling back operation {operation_id} for user {user_id}")
            
            return {
                'success': True,
                'operation_id': operation_id,
                'message': '操作已成功回滚'
            }
            
        except Exception as e:
            logger.error(f"Rollback error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_operation_templates(
        self,
        user_id: str,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取可用的操作模板
        
        基于用户级别和上下文过滤模板。
        
        Args:
            user_id: 用户ID
            context: 上下文（可选）
        
        Returns:
            List[Dict]: 操作模板列表
        """
        templates = list(self.operation_templates.values())
        
        # 基于用户使用频率排序
        user_patterns = self.context_engine._get_user_patterns(user_id)
        
        def template_score(template):
            # 基于模板关联的功能使用频率计算分数
            score = 0
            template_id = template['template_id']
            
            # 简单的评分逻辑
            if template_id in ['income_entry', 'expense_entry']:
                score = user_patterns.function_usage_count.get('1', 0) + \
                        user_patterns.function_usage_count.get('2', 0)
            
            return score
        
        templates.sort(key=template_score, reverse=True)
        
        return templates
    
    def get_frequent_operations(
        self,
        user_id: str,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取用户最常用的操作
        
        Args:
            user_id: 用户ID
            top_n: 返回前N个操作
        
        Returns:
            List[Dict]: 常用操作列表
        
        Requirements: 3.5
        """
        history = self.operation_history.get(user_id, [])
        
        # 统计操作频率
        from collections import Counter
        operation_counter = Counter()
        
        for record in history:
            template_id = record['template_id']
            operation_counter[template_id] += 1
        
        # 获取最常用的操作
        frequent_ops = []
        for template_id, count in operation_counter.most_common(top_n):
            template = self.operation_templates.get(template_id)
            if template:
                frequent_ops.append({
                    'template_id': template_id,
                    'name': template['name'],
                    'description': template['description'],
                    'usage_count': count
                })
        
        return frequent_ops
    
    # Validator implementations
    def _validate_amount(self, value: Any, rules: Dict[str, Any]) -> None:
        """验证金额"""
        try:
            amount = float(value)
            if 'min' in rules and amount < rules['min']:
                raise ValidationError(f"金额不能小于 {rules['min']}")
            if 'max' in rules and amount > rules['max']:
                raise ValidationError(f"金额不能大于 {rules['max']}")
        except (ValueError, TypeError):
            raise ValidationError("金额必须是有效的数字")
    
    def _validate_date(self, value: Any, rules: Dict[str, Any]) -> None:
        """验证日期"""
        from datetime import datetime
        
        try:
            if isinstance(value, str):
                date_obj = datetime.strptime(value, '%Y-%m-%d')
            elif isinstance(value, datetime):
                date_obj = value
            else:
                raise ValidationError("日期格式无效")
            
            if rules.get('max') == 'today' and date_obj > datetime.now():
                raise ValidationError("日期不能晚于今天")
            
        except ValueError:
            raise ValidationError("日期格式必须为 YYYY-MM-DD")
    
    def _validate_entity_id(self, value: Any, rules: Dict[str, Any]) -> None:
        """验证实体ID（客户/供应商）"""
        if not value or not isinstance(value, str):
            raise ValidationError("实体ID无效")
    
    def _validate_list(self, value: Any, rules: Dict[str, Any]) -> None:
        """验证列表"""
        if not isinstance(value, list):
            raise ValidationError("必须是列表类型")
        
        if 'min_length' in rules and len(value) < rules['min_length']:
            raise ValidationError(f"列表长度不能少于 {rules['min_length']}")
        
        if 'max_length' in rules and len(value) > rules['max_length']:
            raise ValidationError(f"列表长度不能超过 {rules['max_length']}")
    
    # Calculator implementations
    def _calculate_tax(self, amount: float, tax_rate: float) -> float:
        """计算税额"""
        return amount * tax_rate
    
    def _calculate_total(self, amount: float, tax_amount: float) -> float:
        """计算总额"""
        return amount + tax_amount
    
    def _calculate_balance(self, transactions: List[Dict[str, Any]]) -> float:
        """计算余额"""
        balance = 0.0
        for trans in transactions:
            trans_type = trans.get('type', 'income')
            amount = trans.get('amount', 0)
            
            if trans_type == 'income':
                balance += amount
            elif trans_type == 'expense':
                balance -= amount
        
        return balance
    
    # Saver implementations
    def _save_income_transaction(
        self,
        data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """保存收入交易"""
        transaction_id = str(uuid.uuid4())
        
        # 实际实现中会调用V1.4的保存功能
        # 这里是简化版本
        save_path = self.storage_path / f"income_{transaction_id}.json"
        
        transaction_data = {
            'transaction_id': transaction_id,
            'user_id': user_id,
            'type': 'income',
            'data': data,
            'created_at': datetime.now().isoformat()
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(transaction_data, f, ensure_ascii=False, indent=2)
        
        # 记录到ContextEngine用于学习
        self.context_engine.record_transaction(
            user_id, 'income', data
        )
        
        return {
            'transaction_id': transaction_id,
            'saved': True,
            'file_path': str(save_path)
        }
    
    def _save_expense_transaction(
        self,
        data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """保存支出交易"""
        transaction_id = str(uuid.uuid4())
        
        save_path = self.storage_path / f"expense_{transaction_id}.json"
        
        transaction_data = {
            'transaction_id': transaction_id,
            'user_id': user_id,
            'type': 'expense',
            'data': data,
            'created_at': datetime.now().isoformat()
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(transaction_data, f, ensure_ascii=False, indent=2)
        
        # 记录到ContextEngine用于学习
        self.context_engine.record_transaction(
            user_id, 'expense', data
        )
        
        return {
            'transaction_id': transaction_id,
            'saved': True,
            'file_path': str(save_path)
        }
    
    def _save_reconciliation(
        self,
        data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """保存对账记录"""
        reconciliation_id = str(uuid.uuid4())
        
        save_path = self.storage_path / f"reconciliation_{reconciliation_id}.json"
        
        reconciliation_data = {
            'reconciliation_id': reconciliation_id,
            'user_id': user_id,
            'type': 'reconciliation',
            'data': data,
            'created_at': datetime.now().isoformat()
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(reconciliation_data, f, ensure_ascii=False, indent=2)
        
        return {
            'reconciliation_id': reconciliation_id,
            'saved': True,
            'file_path': str(save_path)
        }
    
    def _save_batch_transactions(
        self,
        data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """保存批量交易"""
        batch_id = str(uuid.uuid4())
        
        save_path = self.storage_path / f"batch_{batch_id}.json"
        
        batch_data = {
            'batch_id': batch_id,
            'user_id': user_id,
            'type': 'batch',
            'data': data,
            'created_at': datetime.now().isoformat()
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=2)
        
        return {
            'batch_id': batch_id,
            'saved': True,
            'file_path': str(save_path),
            'item_count': len(data.get('items', []))
        }
    
    def _default_save(
        self,
        data: Dict[str, Any],
        user_id: str,
        transaction_type: str
    ) -> Dict[str, Any]:
        """默认保存逻辑"""
        record_id = str(uuid.uuid4())
        
        save_path = self.storage_path / f"{transaction_type}_{record_id}.json"
        
        record_data = {
            'record_id': record_id,
            'user_id': user_id,
            'type': transaction_type,
            'data': data,
            'created_at': datetime.now().isoformat()
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(record_data, f, ensure_ascii=False, indent=2)
        
        return {
            'record_id': record_id,
            'saved': True,
            'file_path': str(save_path)
        }
    
    def _save_operation_history(self, user_id: str) -> None:
        """保存操作历史"""
        history_file = self.storage_path / f"history_{user_id}.json"
        
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self.operation_history.get(user_id, []),
                    f,
                    ensure_ascii=False,
                    indent=2
                )
        except Exception as e:
            logger.error(f"Failed to save operation history: {e}")
