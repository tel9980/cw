# -*- coding: utf-8 -*-
"""
One-Click Operations Manager for Oxidation Factory
氧化加工厂一键操作管理器 - 提供智能默认值的原子化操作

从V1.5复用并适配氧化加工厂业务特点
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


class OxidationOneClickOperationManager:
    """
    氧化加工厂一键操作管理器
    
    负责：
    - 提供智能默认值的一键交易录入
    - 原子化操作（验证+计算+保存）
    - 批量操作处理
    - 常用操作模板
    - 错误处理和回滚
    
    Requirements: B3, B4
    """
    
    def __init__(
        self,
        transaction_storage,
        processing_order_manager,
        outsourced_processing_manager,
        bank_account_manager,
        smart_learning_engine=None,
        storage_path: str = "data/one_click_operations"
    ):
        """
        初始化一键操作管理器
        
        Args:
            transaction_storage: 交易存储实例
            processing_order_manager: 加工订单管理器
            outsourced_processing_manager: 外发加工管理器
            bank_account_manager: 银行账户管理器
            smart_learning_engine: 智能学习引擎（可选）
            storage_path: 数据存储路径
        """
        self.transaction_storage = transaction_storage
        self.order_manager = processing_order_manager
        self.outsourced_manager = outsourced_processing_manager
        self.account_manager = bank_account_manager
        self.learning_engine = smart_learning_engine
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 操作模板库
        self.operation_templates: Dict[str, Dict[str, Any]] = {}
        
        # 操作历史（用于回滚）
        self.operation_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # 验证器注册表
        self.validators: Dict[str, Callable] = {}
        
        # 初始化默认模板和处理器
        self._initialize_default_templates()
        self._register_default_handlers()
        
        logger.info("OxidationOneClickOperationManager initialized")
    
    def _initialize_default_templates(self) -> None:
        """初始化氧化加工厂专用操作模板"""
        
        # 1. 加工订单录入模板
        self.operation_templates['order_entry'] = {
            'template_id': 'order_entry',
            'name': '加工订单录入',
            'description': '快速录入加工订单',
            'operation_type': 'processing_order',
            'required_fields': ['customer_id', 'quantity', 'pricing_unit', 'unit_price'],
            'optional_fields': ['description', 'delivery_date', 'special_requirements'],
            'default_values': {
                'pricing_unit': '件',
                'status': 'pending'
            },
            'validation_rules': {
                'quantity': {'min': 1, 'type': 'number'},
                'unit_price': {'min': 0.01, 'type': 'amount'}
            }
        }
        
        # 2. 外发加工录入模板
        self.operation_templates['outsourced_entry'] = {
            'template_id': 'outsourced_entry',
            'name': '外发加工录入',
            'description': '快速录入外发加工记录',
            'operation_type': 'outsourced_processing',
            'required_fields': ['order_id', 'process_type', 'vendor_id', 'cost'],
            'optional_fields': ['notes', 'expected_return_date'],
            'default_values': {
                'process_type': '喷砂'
            },
            'validation_rules': {
                'cost': {'min': 0.01, 'type': 'amount'}
            }
        }
        
        # 3. 收款录入模板
        self.operation_templates['payment_received'] = {
            'template_id': 'payment_received',
            'name': '收款录入',
            'description': '快速录入客户付款',
            'operation_type': 'income',
            'required_fields': ['date', 'amount', 'customer_id', 'bank_account_id'],
            'optional_fields': ['description', 'order_ids'],
            'default_values': {
                'bank_account_id': 'G银行',
                'category': '加工费收入'
            },
            'validation_rules': {
                'amount': {'min': 0.01, 'type': 'amount'},
                'date': {'type': 'date', 'max': 'today'}
            }
        }
        
        # 4. 原材料采购录入模板
        self.operation_templates['material_purchase'] = {
            'template_id': 'material_purchase',
            'name': '原材料采购',
            'description': '快速录入原材料采购',
            'operation_type': 'expense',
            'required_fields': ['date', 'amount', 'vendor_id', 'material_type'],
            'optional_fields': ['description', 'quantity', 'unit'],
            'default_values': {
                'category': '原材料采购'
            },
            'validation_rules': {
                'amount': {'min': 0.01, 'type': 'amount'},
                'date': {'type': 'date', 'max': 'today'}
            }
        }
        
        # 5. 批量收款模板
        self.operation_templates['batch_collection'] = {
            'template_id': 'batch_collection',
            'name': '批量收款',
            'description': '批量处理多笔收款',
            'operation_type': 'batch_income',
            'required_fields': ['date', 'items'],
            'optional_fields': ['bank_account_id', 'notes'],
            'default_values': {
                'bank_account_id': 'G银行'
            },
            'validation_rules': {
                'items': {'type': 'list', 'min_length': 1}
            }
        }
        
        logger.info(f"Initialized {len(self.operation_templates)} operation templates")
    
    def _register_default_handlers(self) -> None:
        """注册默认的验证器"""
        self.validators['amount'] = self._validate_amount
        self.validators['date'] = self._validate_date
        self.validators['number'] = self._validate_number
        self.validators['list'] = self._validate_list
        
        logger.info("Registered default validators")
    
    def execute_one_click_operation(
        self,
        template_id: str,
        user_id: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行一键操作（原子化：验证+计算+保存）
        
        Args:
            template_id: 操作模板ID
            user_id: 用户ID
            data: 操作数据
            context: 额外上下文信息
        
        Returns:
            Dict: 操作结果
        
        Requirements: B3
        """
        operation_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # 1. 获取模板
            template = self.operation_templates.get(template_id)
            if not template:
                raise OperationError(f"Template {template_id} not found")
            
            # 2. 应用默认值
            enriched_data = self._apply_defaults(template, data)
            
            # 3. 验证数据
            validation_result = self._validate_operation_data(template, enriched_data)
            if not validation_result['valid']:
                raise ValidationError(
                    f"Validation failed: {validation_result['errors']}"
                )
            
            # 4. 执行计算
            calculated_data = self._perform_calculations(template, enriched_data)
            
            # 5. 保存数据（原子操作）
            save_result = self._save_operation_data(
                template, calculated_data, user_id
            )
            
            # 6. 记录操作历史（用于回滚）
            self._record_operation_history(
                operation_id, user_id, template_id, calculated_data, save_result
            )
            
            # 7. 如果有智能学习引擎，记录交易用于学习
            if self.learning_engine:
                self.learning_engine.record_transaction(
                    user_id=user_id,
                    transaction_type=template.get('operation_type'),
                    transaction_data=calculated_data
                )
                
                # 如果用户修改了智能默认值，学习纠正
                prediction = {}
                actual = calculated_data.copy()
                for field in calculated_data:
                    if field.startswith('_') and field.endswith('_smart_default'):
                        original_field = field[1:-len('_smart_default')]
                        smart_meta = calculated_data[field]
                        prediction[original_field] = smart_meta.get('suggested_value')
                
                if prediction:
                    self.learning_engine.learn_from_correction(prediction, actual)
            
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
    
    def _apply_defaults(
        self,
        template: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        应用默认值（包括智能默认值）
        
        Args:
            template: 操作模板
            data: 用户提供的数据
        
        Returns:
            Dict: 填充后的数据
        
        Requirements: B4
        """
        enriched_data = data.copy()
        
        # 1. 应用模板默认值
        for field, default_value in template.get('default_values', {}).items():
            if field not in enriched_data or enriched_data[field] is None:
                enriched_data[field] = default_value
        
        # 2. 如果有智能学习引擎，应用智能默认值
        if self.learning_engine:
            operation_type = template.get('operation_type')
            context = {
                'user_id': data.get('user_id', 'default_user'),
                'entity_id': data.get('customer_id') or data.get('vendor_id')
            }
            
            smart_defaults = self.learning_engine.generate_smart_defaults(
                operation_type, context
            )
            
            # 应用智能默认值（只填充未提供的字段）
            for field, smart_default in smart_defaults.items():
                if field not in enriched_data or enriched_data[field] is None:
                    enriched_data[field] = smart_default.suggested_value
                    # 记录智能默认值的元数据
                    enriched_data[f'_{field}_smart_default'] = {
                        'confidence': smart_default.confidence,
                        'reasoning': smart_default.reasoning,
                        'alternatives': [
                            {'value': alt.value, 'confidence': alt.confidence}
                            for alt in smart_default.alternatives
                        ]
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
        
        operation_type = template.get('operation_type')
        
        # 加工订单：计算总金额
        if operation_type == 'processing_order':
            if 'quantity' in calculated_data and 'unit_price' in calculated_data:
                calculated_data['total_amount'] = (
                    calculated_data['quantity'] * calculated_data['unit_price']
                )
        
        # 批量操作：计算总额
        elif operation_type in ['batch_income', 'batch_expense']:
            items = calculated_data.get('items', [])
            total = sum(item.get('amount', 0) for item in items)
            calculated_data['total_amount'] = total
            calculated_data['item_count'] = len(items)
        
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
        operation_type = template.get('operation_type')
        
        # 加工订单
        if operation_type == 'processing_order':
            order_id = self.order_manager.create_order(
                customer_id=data['customer_id'],
                quantity=data['quantity'],
                pricing_unit=data['pricing_unit'],
                unit_price=data['unit_price'],
                description=data.get('description'),
                delivery_date=data.get('delivery_date'),
                special_requirements=data.get('special_requirements')
            )
            return {'order_id': order_id, 'saved': True}
        
        # 外发加工
        elif operation_type == 'outsourced_processing':
            outsourced_id = self.outsourced_manager.create_outsourced_processing(
                order_id=data['order_id'],
                process_type=data['process_type'],
                vendor_id=data['vendor_id'],
                cost=data['cost'],
                notes=data.get('notes'),
                expected_return_date=data.get('expected_return_date')
            )
            return {'outsourced_id': outsourced_id, 'saved': True}
        
        # 收入/支出交易
        elif operation_type in ['income', 'expense']:
            transaction_id = self.transaction_storage.add_transaction(
                date=data['date'],
                amount=data['amount'],
                counterparty_id=data.get('customer_id') or data.get('vendor_id'),
                category=data.get('category'),
                description=data.get('description'),
                transaction_type=operation_type,
                bank_account_id=data.get('bank_account_id')
            )
            return {'transaction_id': transaction_id, 'saved': True}
        
        # 批量操作
        elif operation_type in ['batch_income', 'batch_expense']:
            transaction_ids = []
            for item in data.get('items', []):
                trans_id = self.transaction_storage.add_transaction(
                    date=data['date'],
                    amount=item['amount'],
                    counterparty_id=item.get('counterparty_id'),
                    category=item.get('category'),
                    description=item.get('description'),
                    transaction_type='income' if operation_type == 'batch_income' else 'expense',
                    bank_account_id=data.get('bank_account_id')
                )
                transaction_ids.append(trans_id)
            return {
                'transaction_ids': transaction_ids,
                'saved': True,
                'count': len(transaction_ids)
            }
        
        # 默认保存
        return self._default_save(data, user_id, operation_type)
    
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
    
    def execute_batch_operation(
        self,
        template_id: str,
        user_id: str,
        items: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行批量操作
        
        Args:
            template_id: 操作模板ID
            user_id: 用户ID
            items: 批量操作项列表
            context: 上下文信息
        
        Returns:
            Dict: 批量操作结果
        
        Requirements: B3
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
    
    def get_operation_templates(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取可用的操作模板
        
        Args:
            user_id: 用户ID
        
        Returns:
            List[Dict]: 操作模板列表
        """
        return list(self.operation_templates.values())
    
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
        
        Requirements: B3
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
    
    def _validate_number(self, value: Any, rules: Dict[str, Any]) -> None:
        """验证数字"""
        try:
            num = float(value)
            if 'min' in rules and num < rules['min']:
                raise ValidationError(f"数值不能小于 {rules['min']}")
            if 'max' in rules and num > rules['max']:
                raise ValidationError(f"数值不能大于 {rules['max']}")
        except (ValueError, TypeError):
            raise ValidationError("必须是有效的数字")
    
    def _validate_list(self, value: Any, rules: Dict[str, Any]) -> None:
        """验证列表"""
        if not isinstance(value, list):
            raise ValidationError("必须是列表类型")
        
        if 'min_length' in rules and len(value) < rules['min_length']:
            raise ValidationError(f"列表长度不能少于 {rules['min_length']}")
        
        if 'max_length' in rules and len(value) > rules['max_length']:
            raise ValidationError(f"列表长度不能超过 {rules['max_length']}")
    
    def _default_save(
        self,
        data: Dict[str, Any],
        user_id: str,
        operation_type: str
    ) -> Dict[str, Any]:
        """默认保存逻辑"""
        record_id = str(uuid.uuid4())
        
        save_path = self.storage_path / f"{operation_type}_{record_id}.json"
        
        record_data = {
            'record_id': record_id,
            'user_id': user_id,
            'type': operation_type,
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
