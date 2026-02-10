# -*- coding: utf-8 -*-
"""
氧化加工厂财务助手 V1.4 - 增强版
专为小企业会计设计的全功能财务管理工具
V1.4新增：用户体验优化、智能分析、数据验证增强、性能优化
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import threading
from functools import lru_cache

# 导入氧化加工厂模块
try:
    from oxidation_factory import get_config, get_storage
    from oxidation_factory.order_wizard import create_order_interactive
    from oxidation_factory.order_manager import Order
    from 财务数据管理器 import financial_manager
    print("✅ 氧化加工厂模块加载成功")
except Exception as e:
    print(f"⚠️ 模块加载失败: {e}")
    print("💡 提示：请确保 oxidation_factory 模块在当前目录")
    sys.exit(1)

# 设置日志
def setup_logging():
    """设置日志记录"""
    log_dir = "财务数据/运行日志"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

setup_logging()
logger = logging.getLogger(__name__)

class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# V1.4 新增：用户体验增强类
class EnhancedUI:
    """增强用户界面类"""
    
    def __init__(self):
        self.recent_functions = []
        self.shortcuts = {
            'q': '99',  # 快速退出
            'h': '56',  # 帮助
            'l': '57',  # 查看日志
            'b': '53',  # 备份
        }
        self.customer_cache = []
        self.load_customer_cache()
    
    def load_customer_cache(self):
        """加载客户缓存"""
        try:
            # 从订单中提取客户名称
            storage = get_storage()
            orders = storage.get_all_orders()
            customers = set()
            for order in orders:
                customers.add(order.get('customer', ''))
            
            # 从收支记录中提取客户名称
            from 氧化加工厂财务助手_全能版 import finance_manager
            transactions = finance_manager.load_transactions()
            for trans in transactions:
                if trans.get('customer'):
                    customers.add(trans['customer'])
            
            self.customer_cache = sorted(list(customers))
        except Exception as e:
            logger.warning(f"加载客户缓存失败: {e}")
            self.customer_cache = []
    
    def add_recent_function(self, func_code: str, func_name: str):
        """添加最近使用的功能"""
        recent_item = {'code': func_code, 'name': func_name, 'time': datetime.now()}
        
        # 移除重复项
        self.recent_functions = [item for item in self.recent_functions 
                               if item['code'] != func_code]
        
        # 添加到开头
        self.recent_functions.insert(0, recent_item)
        
        # 只保留最近10个
        self.recent_functions = self.recent_functions[:10]
    
    def show_recent_menu(self):
        """显示最近使用功能菜单"""
        if not self.recent_functions:
            return
        
        print(f"\n{Color.CYAN}🔥 最近使用：{Color.ENDC}")
        for i, func in enumerate(self.recent_functions[:5], 1):
            time_str = func['time'].strftime("%H:%M")
            print(f"  {Color.WARNING}r{i}{Color.ENDC}. {func['name']} ({time_str})")
    
    def show_shortcuts(self):
        """显示快捷键"""
        print(f"\n{Color.CYAN}⚡ 快捷键：{Color.ENDC}")
        print(f"  {Color.WARNING}q{Color.ENDC} - 退出系统")
        print(f"  {Color.WARNING}h{Color.ENDC} - 使用教程")
        print(f"  {Color.WARNING}l{Color.ENDC} - 查看日志")
        print(f"  {Color.WARNING}b{Color.ENDC} - 数据备份")
    
    def auto_complete_customer(self, partial_name: str) -> List[str]:
        """客户名称自动补全"""
        if not partial_name:
            return self.customer_cache[:5]
        
        matches = []
        partial_lower = partial_name.lower()
        
        for customer in self.customer_cache:
            if partial_lower in customer.lower():
                matches.append(customer)
                if len(matches) >= 5:
                    break
        
        return matches
    
    def handle_shortcut(self, input_str: str) -> Optional[str]:
        """处理快捷键输入"""
        input_str = input_str.strip().lower()
        
        # 处理最近使用功能 (r1, r2, etc.)
        if input_str.startswith('r') and len(input_str) == 2:
            try:
                index = int(input_str[1]) - 1
                if 0 <= index < len(self.recent_functions):
                    return self.recent_functions[index]['code']
            except ValueError:
                pass
        
        # 处理普通快捷键
        return self.shortcuts.get(input_str)

# V1.4 新增：数据验证增强类
class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_amount(amount_str: str, min_val: float = 0, max_val: float = 10000000) -> Tuple[bool, str, float]:
        """
        验证金额
        
        Returns:
            (是否有效, 错误信息, 金额值)
        """
        try:
            amount = float(amount_str.replace(',', ''))
            
            if amount < min_val:
                return False, f"金额不能小于 {min_val:,.2f} 元", 0
            
            if amount > max_val:
                return False, f"金额不能大于 {max_val:,.2f} 元", 0
            
            # 检查小数位数
            if '.' in amount_str and len(amount_str.split('.')[1]) > 2:
                return False, "金额最多保留2位小数", 0
            
            return True, "", amount
            
        except ValueError:
            return False, "请输入有效的数字", 0
    
    @staticmethod
    def validate_date(date_str: str) -> Tuple[bool, str, Optional[datetime]]:
        """验证日期格式"""
        if not date_str:
            return True, "", datetime.now()
        
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            
            # 检查日期合理性
            today = datetime.now()
            if date_obj > today + timedelta(days=30):
                return False, "日期不能超过今天30天", None
            
            if date_obj < datetime(2020, 1, 1):
                return False, "日期不能早于2020年", None
            
            return True, "", date_obj
            
        except ValueError:
            return False, "日期格式错误，请使用 YYYY-MM-DD 格式", None
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> Tuple[bool, str]:
        """验证日期范围"""
        start_valid, start_msg, start_obj = DataValidator.validate_date(start_date)
        if not start_valid:
            return False, f"开始日期错误：{start_msg}"
        
        end_valid, end_msg, end_obj = DataValidator.validate_date(end_date)
        if not end_valid:
            return False, f"结束日期错误：{end_msg}"
        
        if start_obj and end_obj and start_obj > end_obj:
            return False, "开始日期不能晚于结束日期"
        
        return True, ""
    
    @staticmethod
    def check_duplicate_customer(customer_name: str, existing_customers: List[str]) -> Tuple[bool, str, List[str]]:
        """检查客户重复"""
        if not customer_name:
            return True, "", []
        
        # 完全匹配
        if customer_name in existing_customers:
            return False, f"客户 '{customer_name}' 已存在", []
        
        # 相似度检查
        similar_customers = []
        customer_lower = customer_name.lower()
        
        for existing in existing_customers:
            existing_lower = existing.lower()
            
            # 包含关系检查
            if (customer_lower in existing_lower or 
                existing_lower in customer_lower):
                similar_customers.append(existing)
        
        if similar_customers:
            return False, f"发现相似客户：{', '.join(similar_customers)}", similar_customers
        
        return True, "", []

# V1.4 新增：智能分析器
class IntelligentAnalyzer:
    """智能分析器"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存
    
    @lru_cache(maxsize=128)
    def analyze_revenue_trend(self, months: int = 6) -> Dict:
        """收入趋势分析"""
        try:
            from 氧化加工厂财务助手_全能版 import finance_manager
            transactions = finance_manager.load_transactions()
            
            # 按月统计收入
            monthly_revenue = defaultdict(float)
            today = datetime.now()
            
            for trans in transactions:
                if trans['type'] != '收入':
                    continue
                
                trans_date = datetime.strptime(trans['date'], "%Y-%m-%d")
                month_key = trans_date.strftime("%Y-%m")
                monthly_revenue[month_key] += trans['amount']
            
            # 获取最近几个月的数据
            recent_months = []
            for i in range(months):
                month_date = today - timedelta(days=30 * i)
                month_key = month_date.strftime("%Y-%m")
                recent_months.append({
                    'month': month_key,
                    'revenue': monthly_revenue.get(month_key, 0)
                })
            
            recent_months.reverse()
            
            # 计算趋势
            if len(recent_months) >= 2:
                recent_avg = sum(m['revenue'] for m in recent_months[-3:]) / min(3, len(recent_months))
                earlier_avg = sum(m['revenue'] for m in recent_months[:-3]) / max(1, len(recent_months) - 3)
                
                if recent_avg > earlier_avg * 1.1:
                    trend = 'increasing'
                elif recent_avg < earlier_avg * 0.9:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
                
                growth_rate = ((recent_avg - earlier_avg) / max(earlier_avg, 1)) * 100
            else:
                trend = 'insufficient_data'
                growth_rate = 0
            
            return {
                'trend': trend,
                'growth_rate': growth_rate,
                'monthly_data': recent_months,
                'recommendations': self._generate_revenue_recommendations(trend, growth_rate)
            }
            
        except Exception as e:
            logger.error(f"收入趋势分析失败: {e}")
            return {'trend': 'error', 'growth_rate': 0, 'monthly_data': [], 'recommendations': []}
    
    def analyze_customer_value(self) -> List[Dict]:
        """客户价值分析"""
        try:
            from 氧化加工厂财务助手_全能版 import finance_manager
            
            # 获取客户交易数据
            transactions = finance_manager.load_transactions()
            orders = get_storage().get_all_orders()
            
            customer_stats = defaultdict(lambda: {
                'total_revenue': 0,
                'order_count': 0,
                'avg_order_value': 0,
                'last_order_date': None,
                'unpaid_amount': 0,
                'payment_history': []
            })
            
            # 统计收入交易
            for trans in transactions:
                if trans['type'] == '收入' and trans.get('customer'):
                    customer = trans['customer']
                    customer_stats[customer]['total_revenue'] += trans['amount']
                    customer_stats[customer]['payment_history'].append({
                        'date': trans['date'],
                        'amount': trans['amount']
                    })
            
            # 统计订单
            for order in orders:
                customer = order['customer']
                customer_stats[customer]['order_count'] += 1
                customer_stats[customer]['unpaid_amount'] += order.get('unpaid_amount', 0)
                
                order_date = datetime.strptime(order['order_date'], "%Y-%m-%d")
                if (not customer_stats[customer]['last_order_date'] or 
                    order_date > customer_stats[customer]['last_order_date']):
                    customer_stats[customer]['last_order_date'] = order_date
            
            # 计算客户价值评分
            customer_analysis = []
            for customer, stats in customer_stats.items():
                if stats['order_count'] > 0:
                    stats['avg_order_value'] = stats['total_revenue'] / stats['order_count']
                
                # 计算价值评分 (0-100)
                revenue_score = min(stats['total_revenue'] / 10000 * 40, 40)  # 收入贡献 (40分)
                frequency_score = min(stats['order_count'] / 10 * 30, 30)     # 订单频次 (30分)
                
                # 最近活跃度 (30分)
                if stats['last_order_date']:
                    days_since_last = (datetime.now() - stats['last_order_date']).days
                    if days_since_last <= 30:
                        recency_score = 30
                    elif days_since_last <= 90:
                        recency_score = 20
                    elif days_since_last <= 180:
                        recency_score = 10
                    else:
                        recency_score = 0
                else:
                    recency_score = 0
                
                value_score = revenue_score + frequency_score + recency_score
                
                # 风险评估
                risk_level = 'low'
                if stats['unpaid_amount'] > stats['total_revenue'] * 0.3:
                    risk_level = 'high'
                elif stats['unpaid_amount'] > stats['total_revenue'] * 0.1:
                    risk_level = 'medium'
                
                customer_analysis.append({
                    'customer': customer,
                    'value_score': round(value_score, 1),
                    'total_revenue': stats['total_revenue'],
                    'order_count': stats['order_count'],
                    'avg_order_value': stats['avg_order_value'],
                    'unpaid_amount': stats['unpaid_amount'],
                    'last_order_date': stats['last_order_date'],
                    'risk_level': risk_level,
                    'recommendations': self._generate_customer_recommendations(stats, risk_level)
                })
            
            return sorted(customer_analysis, key=lambda x: x['value_score'], reverse=True)
            
        except Exception as e:
            logger.error(f"客户价值分析失败: {e}")
            return []
    
    def _generate_revenue_recommendations(self, trend: str, growth_rate: float) -> List[str]:
        """生成收入建议"""
        recommendations = []
        
        if trend == 'increasing':
            recommendations.append("📈 收入呈上升趋势，建议继续保持当前策略")
            if growth_rate > 20:
                recommendations.append("🚀 增长强劲，可考虑扩大产能或提高价格")
        elif trend == 'decreasing':
            recommendations.append("📉 收入呈下降趋势，需要关注市场变化")
            recommendations.append("💡 建议分析客户流失原因，制定挽回策略")
            if growth_rate < -20:
                recommendations.append("⚠️ 下降幅度较大，建议紧急制定应对措施")
        else:
            recommendations.append("📊 收入相对稳定，可考虑寻找新的增长点")
        
        return recommendations
    
    def _generate_customer_recommendations(self, stats: Dict, risk_level: str) -> List[str]:
        """生成客户建议"""
        recommendations = []
        
        if risk_level == 'high':
            recommendations.append("🚨 高风险客户，建议加强收款管理")
            recommendations.append("📞 建议主动联系客户了解付款计划")
        elif risk_level == 'medium':
            recommendations.append("⚠️ 中等风险，建议关注收款情况")
        
        if stats['last_order_date']:
            days_since_last = (datetime.now() - stats['last_order_date']).days
            if days_since_last > 90:
                recommendations.append("📅 客户较长时间未下单，建议主动联系维护关系")
        
        if stats['avg_order_value'] > 5000:
            recommendations.append("💎 高价值客户，建议提供优质服务")
        
        return recommendations

# 全局增强UI实例
enhanced_ui = EnhancedUI()
data_validator = DataValidator()
intelligent_analyzer = IntelligentAnalyzer()
# V1.4 新增：预警系统
class AlertSystem:
    """预警系统"""
    
    def __init__(self):
        self.alerts = []
        self.alert_rules = {
            'overdue_receivables': {'enabled': True, 'threshold_days': 30},
            'cost_anomaly': {'enabled': True, 'threshold_percent': 20},
            'low_profit': {'enabled': True, 'threshold_percent': 10},
            'cash_flow': {'enabled': True, 'threshold_amount': 10000}
        }
    
    def check_all_alerts(self) -> List[Dict]:
        """检查所有预警"""
        self.alerts = []
        
        try:
            if self.alert_rules['overdue_receivables']['enabled']:
                self._check_overdue_receivables()
            
            if self.alert_rules['cost_anomaly']['enabled']:
                self._check_cost_anomaly()
            
            if self.alert_rules['low_profit']['enabled']:
                self._check_low_profit()
            
            if self.alert_rules['cash_flow']['enabled']:
                self._check_cash_flow()
                
        except Exception as e:
            logger.error(f"预警检查失败: {e}")
        
        return self.alerts
    
    def _check_overdue_receivables(self):
        """检查逾期应收账款"""
        try:
            orders = get_storage().get_all_orders()
            threshold_days = self.alert_rules['overdue_receivables']['threshold_days']
            
            for order in orders:
                if order.get('unpaid_amount', 0) > 0:
                    order_date = datetime.strptime(order['order_date'], "%Y-%m-%d")
                    days_overdue = (datetime.now() - order_date).days
                    
                    if days_overdue > threshold_days:
                        self._create_alert(
                            type='OVERDUE',
                            level='HIGH' if days_overdue > 60 else 'MEDIUM',
                            message=f"客户 {order['customer']} 逾期 {days_overdue} 天，未收款 {order['unpaid_amount']:.2f} 元",
                            action=f"建议联系客户催收，订单号：{order['order_no']}",
                            data={'order_no': order['order_no'], 'days_overdue': days_overdue}
                        )
        except Exception as e:
            logger.error(f"检查逾期应收失败: {e}")
    
    def _check_cost_anomaly(self):
        """检查成本异常"""
        try:
            from 氧化加工厂财务助手_全能版 import finance_manager
            transactions = finance_manager.load_transactions()
            
            # 计算最近30天和历史90天的平均成本
            today = datetime.now()
            recent_costs = []
            historical_costs = []
            
            for trans in transactions:
                if trans['type'] != '支出':
                    continue
                
                trans_date = datetime.strptime(trans['date'], "%Y-%m-%d")
                days_ago = (today - trans_date).days
                
                if days_ago <= 30:
                    recent_costs.append(trans['amount'])
                elif days_ago <= 120:
                    historical_costs.append(trans['amount'])
            
            if recent_costs and historical_costs:
                recent_avg = sum(recent_costs) / len(recent_costs)
                historical_avg = sum(historical_costs) / len(historical_costs)
                threshold_percent = self.alert_rules['cost_anomaly']['threshold_percent']
                
                if recent_avg > historical_avg * (1 + threshold_percent / 100):
                    increase_percent = ((recent_avg - historical_avg) / historical_avg) * 100
                    self._create_alert(
                        type='COST_ANOMALY',
                        level='HIGH' if increase_percent > 50 else 'MEDIUM',
                        message=f"近期成本异常增高 {increase_percent:.1f}%，当前平均 {recent_avg:.2f} 元/笔",
                        action="建议检查成本构成，分析增长原因",
                        data={'increase_percent': increase_percent}
                    )
        except Exception as e:
            logger.error(f"检查成本异常失败: {e}")
    
    def _check_low_profit(self):
        """检查低利润预警"""
        try:
            from 氧化加工厂财务助手_全能版 import finance_manager
            transactions = finance_manager.load_transactions()
            
            # 计算最近30天的利润率
            today = datetime.now()
            recent_income = 0
            recent_expense = 0
            
            for trans in transactions:
                trans_date = datetime.strptime(trans['date'], "%Y-%m-%d")
                if (today - trans_date).days <= 30:
                    if trans['type'] == '收入':
                        recent_income += trans['amount']
                    else:
                        recent_expense += trans['amount']
            
            if recent_income > 0:
                profit_rate = ((recent_income - recent_expense) / recent_income) * 100
                threshold_percent = self.alert_rules['low_profit']['threshold_percent']
                
                if profit_rate < threshold_percent:
                    self._create_alert(
                        type='LOW_PROFIT',
                        level='HIGH' if profit_rate < 0 else 'MEDIUM',
                        message=f"近期利润率偏低 {profit_rate:.1f}%，收入 {recent_income:.2f} 元，支出 {recent_expense:.2f} 元",
                        action="建议分析成本结构，优化定价策略",
                        data={'profit_rate': profit_rate}
                    )
        except Exception as e:
            logger.error(f"检查利润预警失败: {e}")
    
    def _check_cash_flow(self):
        """检查现金流预警"""
        try:
            orders = get_storage().get_all_orders()
            total_unpaid = sum(order.get('unpaid_amount', 0) for order in orders)
            threshold_amount = self.alert_rules['cash_flow']['threshold_amount']
            
            if total_unpaid > threshold_amount:
                self._create_alert(
                    type='CASH_FLOW',
                    level='MEDIUM',
                    message=f"应收账款较高 {total_unpaid:.2f} 元，可能影响现金流",
                    action="建议加强收款管理，制定收款计划",
                    data={'total_unpaid': total_unpaid}
                )
        except Exception as e:
            logger.error(f"检查现金流预警失败: {e}")
    
    def _create_alert(self, type: str, level: str, message: str, action: str, data: Dict = None):
        """创建预警"""
        alert = {
            'id': len(self.alerts) + 1,
            'type': type,
            'level': level,
            'message': message,
            'action': action,
            'data': data or {},
            'created_at': datetime.now(),
            'status': 'ACTIVE'
        }
        self.alerts.append(alert)
    
    def show_alerts(self):
        """显示预警信息"""
        alerts = self.check_all_alerts()
        
        if not alerts:
            print(f"\n{Color.GREEN}✅ 暂无预警信息，系统运行正常{Color.ENDC}")
            return
        
        print(f"\n{Color.WARNING}⚠️ 系统预警 ({len(alerts)} 条){Color.ENDC}")
        print("=" * 70)
        
        for alert in alerts:
            level_color = Color.FAIL if alert['level'] == 'HIGH' else Color.WARNING
            level_icon = "🚨" if alert['level'] == 'HIGH' else "⚠️"
            
            print(f"\n{level_icon} {level_color}{alert['level']}{Color.ENDC} - {alert['type']}")
            print(f"   {alert['message']}")
            print(f"   💡 建议：{alert['action']}")
        
        print("=" * 70)

# V1.4 新增：性能监控器
class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.operation_times = {}
    
    def start_operation(self, operation_name: str):
        """开始操作计时"""
        self.operation_times[operation_name] = time.time()
    
    def end_operation(self, operation_name: str) -> float:
        """结束操作计时"""
        if operation_name in self.operation_times:
            duration = time.time() - self.operation_times[operation_name]
            del self.operation_times[operation_name]
            return duration
        return 0
    
    def get_memory_usage(self) -> Dict:
        """获取内存使用情况"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss': memory_info.rss / 1024 / 1024,  # MB
                'vms': memory_info.vms / 1024 / 1024,  # MB
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'rss': 0, 'vms': 0, 'percent': 0}
    
    def show_performance_info(self):
        """显示性能信息"""
        uptime = time.time() - self.start_time
        memory = self.get_memory_usage()
        
        print(f"\n{Color.CYAN}📊 系统性能信息{Color.ENDC}")
        print(f"  运行时间：{uptime:.1f} 秒")
        print(f"  内存使用：{memory['rss']:.1f} MB ({memory['percent']:.1f}%)")

# 全局实例
alert_system = AlertSystem()
performance_monitor = PerformanceMonitor()

# V1.4 增强的用户消息类
class UserMessage:
    """用户消息工具类 - V1.4增强版"""
    
    @staticmethod
    def success(message: str):
        print(f"\n✅ {message}")
        logger.info(f"SUCCESS: {message}")
    
    @staticmethod
    def warning(message: str):
        print(f"\n⚠️ {message}")
        logger.warning(f"WARNING: {message}")
    
    @staticmethod
    def error(message: str):
        print(f"\n❌ {message}")
        logger.error(f"ERROR: {message}")
    
    @staticmethod
    def info(message: str):
        print(f"\n💡 {message}")
        logger.info(f"INFO: {message}")
    
    @staticmethod
    def confirm(message: str, default: bool = False) -> bool:
        """确认对话框 - V1.4增强版"""
        default_text = " [Y/n]" if default else " [y/N]"
        while True:
            response = input(f"\n❓ {message}{default_text}: ").strip().lower()
            
            if not response:
                return default
            
            if response in ['y', 'yes', '是', '确定', '1']:
                return True
            elif response in ['n', 'no', '否', '取消', '0']:
                return False
            else:
                print("请输入 y(是) 或 n(否)")
    
    @staticmethod
    def input_with_validation(prompt: str, validator_func=None, auto_complete_func=None) -> str:
        """带验证的输入 - V1.4新增"""
        while True:
            # 显示自动补全提示
            if auto_complete_func:
                suggestions = auto_complete_func("")
                if suggestions:
                    print(f"💡 建议：{', '.join(suggestions[:3])}")
            
            user_input = input(f"{prompt}: ").strip()
            
            if not user_input:
                return ""
            
            # 自动补全匹配
            if auto_complete_func:
                suggestions = auto_complete_func(user_input)
                if len(suggestions) == 1 and suggestions[0].lower().startswith(user_input.lower()):
                    if UserMessage.confirm(f"是否使用 '{suggestions[0]}'", True):
                        user_input = suggestions[0]
            
            # 验证输入
            if validator_func:
                is_valid, error_msg = validator_func(user_input)
                if not is_valid:
                    UserMessage.error(error_msg)
                    continue
            
            return user_input
    
    @staticmethod
    def show_progress(current: int, total: int, desc: str = "处理中", width: int = 30):
        """显示进度条 - V1.4增强版"""
        if total == 0:
            return
        
        percent = (current / total) * 100
        filled_length = int(width * current // total)
        bar = '█' * filled_length + '░' * (width - filled_length)
        
        # 添加颜色
        if percent < 30:
            color = Color.FAIL
        elif percent < 70:
            color = Color.WARNING
        else:
            color = Color.GREEN
        
        print(f'\r{desc}: {color}|{bar}|{Color.ENDC} {percent:.1f}% ({current}/{total})', 
              end='', flush=True)
        
        if current == total:
            print()  # 换行

# V1.4 增强的财务管理器
class EnhancedFinanceManager:
    """增强财务管理器 - V1.4版本"""
    
    def __init__(self):
        self.data_dir = "财务数据"
        self.ensure_directories()
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存
    
    def ensure_directories(self):
        """确保目录存在"""
        dirs = [
            f"{self.data_dir}/收支记录",
            f"{self.data_dir}/银行流水",
            f"{self.data_dir}/税务资料",
            f"{self.data_dir}/月度报表",
            f"{self.data_dir}/年度报表",
            f"{self.data_dir}/凭证档案",
            f"{self.data_dir}/合同档案",
            f"{self.data_dir}/自动备份",  # V1.4新增
            f"{self.data_dir}/智能分析"   # V1.4新增
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    @lru_cache(maxsize=32)
    def load_transactions_cached(self, cache_key: str = None) -> List[Dict]:
        """缓存版本的加载收支记录"""
        return self.load_transactions()
    
    def load_transactions(self) -> List[Dict]:
        """加载收支记录"""
        file_path = f"{self.data_dir}/收支记录/transactions.json"
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载收支记录失败: {e}")
        return []
    
    def save_transactions(self, transactions: List[Dict]) -> bool:
        """保存收支记录"""
        file_path = f"{self.data_dir}/收支记录/transactions.json"
        try:
            # 创建备份
            if os.path.exists(file_path):
                backup_path = f"{self.data_dir}/自动备份/transactions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                import shutil
                shutil.copy2(file_path, backup_path)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(transactions, f, ensure_ascii=False, indent=2)
            
            # 清除缓存
            self.load_transactions_cached.cache_clear()
            return True
        except Exception as e:
            logger.error(f"保存收支记录失败: {e}")
            return False
    
    def add_transaction_enhanced(self, transaction: Dict) -> bool:
        """增强版添加收支记录"""
        try:
            # 数据验证
            required_fields = ['type', 'date', 'amount', 'category', 'description']
            for field in required_fields:
                if field not in transaction:
                    raise ValueError(f"缺少必要字段: {field}")
            
            # 金额验证
            is_valid, error_msg, amount = data_validator.validate_amount(str(transaction['amount']))
            if not is_valid:
                raise ValueError(error_msg)
            transaction['amount'] = amount
            
            # 日期验证
            is_valid, error_msg, date_obj = data_validator.validate_date(transaction['date'])
            if not is_valid:
                raise ValueError(error_msg)
            
            transactions = self.load_transactions()
            transaction['id'] = len(transactions) + 1
            transaction['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            transaction['version'] = '1.4'  # 版本标记
            
            transactions.append(transaction)
            
            if self.save_transactions(transactions):
                # 更新客户缓存
                if transaction.get('customer'):
                    enhanced_ui.load_customer_cache()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"添加收支记录失败: {e}")
            return False
    
    def auto_backup(self) -> bool:
        """自动备份数据"""
        try:
            backup_dir = f"{self.data_dir}/自动备份"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 备份收支记录
            transactions_file = f"{self.data_dir}/收支记录/transactions.json"
            if os.path.exists(transactions_file):
                backup_file = f"{backup_dir}/transactions_{timestamp}.json"
                import shutil
                shutil.copy2(transactions_file, backup_file)
            
            # 备份订单数据
            orders_file = "财务数据/本地订单/orders.json"
            if os.path.exists(orders_file):
                backup_file = f"{backup_dir}/orders_{timestamp}.json"
                import shutil
                shutil.copy2(orders_file, backup_file)
            
            # 清理旧备份（保留最近10个）
            self._cleanup_old_backups(backup_dir)
            
            logger.info(f"自动备份完成: {timestamp}")
            return True
            
        except Exception as e:
            logger.error(f"自动备份失败: {e}")
            return False
    
    def _cleanup_old_backups(self, backup_dir: str):
        """清理旧备份文件"""
        try:
            import glob
            
            # 获取所有备份文件
            backup_files = glob.glob(f"{backup_dir}/*.json")
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            # 删除超过10个的旧备份
            for old_backup in backup_files[10:]:
                os.remove(old_backup)
                logger.info(f"删除旧备份: {old_backup}")
                
        except Exception as e:
            logger.error(f"清理旧备份失败: {e}")

# 全局增强财务管理器
enhanced_finance_manager = EnhancedFinanceManager()
# V1.4 增强的主菜单显示
def show_enhanced_main_menu():
    """显示增强主菜单 - V1.4版本"""
    print("\n" + "=" * 80)
    print(f"{Color.HEADER}            氧化加工厂财务助手 V1.4 - 增强版{Color.ENDC}")
    print("=" * 80)
    
    # 显示系统状态
    alerts = alert_system.check_all_alerts()
    if alerts:
        high_alerts = [a for a in alerts if a['level'] == 'HIGH']
        if high_alerts:
            print(f"{Color.FAIL}🚨 {len(high_alerts)} 个高优先级预警{Color.ENDC}")
        else:
            print(f"{Color.WARNING}⚠️ {len(alerts)} 个预警{Color.ENDC}")
    else:
        print(f"{Color.GREEN}✅ 系统运行正常{Color.ENDC}")
    
    # 显示最近使用功能
    enhanced_ui.show_recent_menu()
    
    # 显示快捷键
    enhanced_ui.show_shortcuts()
    
    print(f"\n{Color.CYAN}【订单管理】{Color.ENDC}")
    print("  01. 📋 新建加工订单        02. 📖 查看订单列表")
    print("  03. ✏️  编辑订单信息        04. 🔍 搜索订单")
    print("  05. 💰 记录收款            06. 📊 订单统计分析")
    print("  07. 📤 导出订单到Excel")
    
    print(f"\n{Color.CYAN}【收支管理】{Color.ENDC}")
    print("  11. 💸 记录支出            12. 💵 记录收入")
    print("  13. 📋 查看收支明细        14. 📊 收支统计")
    print("  15. 🏦 银行流水管理        16. 📤 导出收支报表")
    
    print(f"\n{Color.CYAN}【税务管理】{Color.ENDC}")
    print("  21. 🧾 增值税管理          22. 📋 所得税计算")
    print("  23. 📊 税务报表            24. 📁 税务资料归档")
    
    print(f"\n{Color.CYAN}【报表中心】{Color.ENDC}")
    print("  31. 📈 利润表              32. 📊 资产负债表")
    print("  33. 💰 现金流量表          34. 📋 财务分析报告")
    print("  35. 📅 月度汇总            36. 📆 年度汇总")
    
    print(f"\n{Color.CYAN}【档案管理】{Color.ENDC}")
    print("  41. 📄 凭证管理            42. 📋 合同管理")
    print("  43. 👥 客户档案            44. 🏪 供应商档案")
    
    print(f"\n{Color.CYAN}【智能分析】{Color.ENDC} {Color.WARNING}[V1.4新增]{Color.ENDC}")
    print("  61. 📈 收入趋势分析        62. 👥 客户价值分析")
    print("  63. ⚠️  预警中心            64. 📊 智能报告")
    
    print(f"\n{Color.CYAN}【系统管理】{Color.ENDC}")
    print("  51. 📊 生成示例数据        52. 🗑️  数据清理")
    print("  53. 💾 数据备份            54. 📥 数据恢复")
    print("  55. ⚙️  系统配置            56. 📖 使用教程")
    print("  57. 📋 查看运行日志        58. 📊 性能监控 {Color.WARNING}[V1.4新增]{Color.ENDC}")
    
    print(f"\n{Color.CYAN}【其他功能】{Color.ENDC}")
    print("  99. 🚪 退出系统")
    
    print("\n" + "=" * 80)

# V1.4 新增功能实现

def enhanced_record_expense():
    """增强版记录支出 - V1.4"""
    print("\n" + "=" * 70)
    print("     记录支出 - V1.4增强版")
    print("=" * 70)
    
    try:
        performance_monitor.start_operation("record_expense")
        
        # 获取支出分类
        config = get_config()
        categories = config.get_default_categories().get('支出', [])
        
        print("\n💡 支出分类：")
        for i, category in enumerate(categories, 1):
            print(f"  {i:2d}. {category}")
        
        # 增强的日期输入
        date_str = UserMessage.input_with_validation(
            "支出日期（格式：2026-01-01，直接回车使用今天）",
            lambda x: data_validator.validate_date(x)[0:2]
        )
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        # 增强的金额输入
        while True:
            amount_str = input("支出金额: ").strip()
            if not amount_str:
                UserMessage.info("操作已取消")
                return
            
            is_valid, error_msg, amount = data_validator.validate_amount(amount_str)
            if is_valid:
                break
            else:
                UserMessage.error(error_msg)
        
        # 智能分类选择
        while True:
            category_input = input(f"选择支出分类（1-{len(categories)}）或输入关键词: ").strip()
            
            if category_input.isdigit():
                category_idx = int(category_input) - 1
                if 0 <= category_idx < len(categories):
                    category = categories[category_idx]
                    break
                else:
                    UserMessage.error("无效的分类选择")
            else:
                # 智能匹配分类
                matched_categories = []
                for cat in categories:
                    if category_input.lower() in cat.lower():
                        matched_categories.append(cat)
                
                if len(matched_categories) == 1:
                    category = matched_categories[0]
                    if UserMessage.confirm(f"是否使用分类 '{category}'", True):
                        break
                elif len(matched_categories) > 1:
                    print("找到多个匹配的分类：")
                    for i, cat in enumerate(matched_categories, 1):
                        print(f"  {i}. {cat}")
                    choice = input("请选择: ").strip()
                    if choice.isdigit() and 1 <= int(choice) <= len(matched_categories):
                        category = matched_categories[int(choice) - 1]
                        break
                
                UserMessage.error("未找到匹配的分类，请重新选择")
        
        # 支出说明（带智能提示）
        description = input("支出说明: ").strip()
        if not description:
            description = category
        
        # 支付方式选择
        print("\n支付方式：")
        payment_methods = ["G银行基本户", "N银行", "微信", "现金", "其他"]
        for i, method in enumerate(payment_methods, 1):
            print(f"  {i}. {method}")
        
        payment_choice = input("选择支付方式（1-5）: ").strip()
        payment_method = payment_methods[int(payment_choice) - 1] if payment_choice.isdigit() and 1 <= int(payment_choice) <= 5 else "其他"
        
        # 确认信息
        print(f"\n{Color.CYAN}支出信息确认：{Color.ENDC}")
        print(f"  日期：{date_str}")
        print(f"  金额：{Color.WARNING}{amount:,.2f} 元{Color.ENDC}")
        print(f"  分类：{category}")
        print(f"  说明：{description}")
        print(f"  支付方式：{payment_method}")
        
        if not UserMessage.confirm("确认记录此支出？"):
            UserMessage.info("操作已取消")
            return
        
        # 保存支出记录
        transaction = {
            'type': '支出',
            'date': date_str,
            'amount': amount,
            'category': category,
            'description': description,
            'payment_method': payment_method,
            'status': '已支付'
        }
        
        if enhanced_finance_manager.add_transaction_enhanced(transaction):
            UserMessage.success("支出记录成功！")
            
            # 自动备份
            enhanced_finance_manager.auto_backup()
            
            # 记录操作时间
            duration = performance_monitor.end_operation("record_expense")
            logger.info(f"支出记录完成，耗时: {duration:.2f}秒")
        else:
            UserMessage.error("支出记录失败")
            
    except Exception as e:
        UserMessage.error(f"记录支出时发生错误: {str(e)}")
        logger.error(f"记录支出异常: {str(e)}", exc_info=True)

def enhanced_record_income():
    """增强版记录收入 - V1.4"""
    print("\n" + "=" * 70)
    print("     记录收入 - V1.4增强版")
    print("=" * 70)
    
    try:
        performance_monitor.start_operation("record_income")
        
        # 获取收入分类
        config = get_config()
        categories = config.get_default_categories().get('收入', [])
        
        print("\n💡 收入分类：")
        for i, category in enumerate(categories, 1):
            print(f"  {i:2d}. {category}")
        
        # 增强的日期输入
        date_str = UserMessage.input_with_validation(
            "收入日期（格式：2026-01-01，直接回车使用今天）",
            lambda x: data_validator.validate_date(x)[0:2]
        )
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        # 增强的金额输入
        while True:
            amount_str = input("收入金额: ").strip()
            if not amount_str:
                UserMessage.info("操作已取消")
                return
            
            is_valid, error_msg, amount = data_validator.validate_amount(amount_str)
            if is_valid:
                break
            else:
                UserMessage.error(error_msg)
        
        # 分类选择
        category_choice = input(f"选择收入分类（1-{len(categories)}）: ").strip()
        try:
            category_idx = int(category_choice) - 1
            if 0 <= category_idx < len(categories):
                category = categories[category_idx]
            else:
                UserMessage.error("无效的分类选择")
                return
        except ValueError:
            UserMessage.error("请输入有效的数字")
            return
        
        description = input("收入说明: ").strip()
        if not description:
            description = category
        
        # 客户名称（带自动补全）
        customer = UserMessage.input_with_validation(
            "客户名称（可选）",
            auto_complete_func=enhanced_ui.auto_complete_customer
        )
        
        # 收款方式选择
        print("\n收款方式：")
        payment_methods = ["G银行基本户", "N银行", "微信", "现金", "其他"]
        for i, method in enumerate(payment_methods, 1):
            print(f"  {i}. {method}")
        
        payment_choice = input("选择收款方式（1-5）: ").strip()
        payment_method = payment_methods[int(payment_choice) - 1] if payment_choice.isdigit() and 1 <= int(payment_choice) <= 5 else "其他"
        
        # 发票信息
        has_invoice = UserMessage.confirm("是否开具发票？")
        invoice_no = ""
        if has_invoice:
            invoice_no = input("发票号码: ").strip()
        
        # 确认信息
        print(f"\n{Color.CYAN}收入信息确认：{Color.ENDC}")
        print(f"  日期：{date_str}")
        print(f"  金额：{Color.GREEN}{amount:,.2f} 元{Color.ENDC}")
        print(f"  分类：{category}")
        print(f"  说明：{description}")
        if customer:
            print(f"  客户：{customer}")
        print(f"  收款方式：{payment_method}")
        if has_invoice:
            print(f"  发票号码：{invoice_no}")
        
        if not UserMessage.confirm("确认记录此收入？"):
            UserMessage.info("操作已取消")
            return
        
        # 保存收入记录
        transaction = {
            'type': '收入',
            'date': date_str,
            'amount': amount,
            'category': category,
            'description': description,
            'customer': customer,
            'payment_method': payment_method,
            'has_invoice': has_invoice,
            'invoice_no': invoice_no,
            'status': '已收款'
        }
        
        if enhanced_finance_manager.add_transaction_enhanced(transaction):
            UserMessage.success("收入记录成功！")
            
            # 自动备份
            enhanced_finance_manager.auto_backup()
            
            # 记录操作时间
            duration = performance_monitor.end_operation("record_income")
            logger.info(f"收入记录完成，耗时: {duration:.2f}秒")
        else:
            UserMessage.error("收入记录失败")
            
    except Exception as e:
        UserMessage.error(f"记录收入时发生错误: {str(e)}")
        logger.error(f"记录收入异常: {str(e)}", exc_info=True)

def revenue_trend_analysis():
    """收入趋势分析 - V1.4新增"""
    print("\n" + "=" * 70)
    print("     收入趋势分析 - V1.4智能分析")
    print("=" * 70)
    
    try:
        performance_monitor.start_operation("revenue_analysis")
        
        # 选择分析期间
        print("\n分析期间：")
        print("  1. 最近3个月")
        print("  2. 最近6个月")
        print("  3. 最近12个月")
        
        period_choice = input("选择分析期间（1-3）: ").strip()
        months_map = {"1": 3, "2": 6, "3": 12}
        months = months_map.get(period_choice, 6)
        
        UserMessage.info(f"正在分析最近{months}个月的收入趋势...")
        
        # 执行分析
        analysis_result = intelligent_analyzer.analyze_revenue_trend(months)
        
        if analysis_result['trend'] == 'error':
            UserMessage.error("分析失败，请检查数据")
            return
        
        # 显示分析结果
        print(f"\n" + "=" * 70)
        print(f"                收入趋势分析报告")
        print(f"              最近{months}个月")
        print("=" * 70)
        
        # 趋势信息
        trend = analysis_result['trend']
        growth_rate = analysis_result['growth_rate']
        
        if trend == 'increasing':
            trend_icon = "📈"
            trend_color = Color.GREEN
            trend_text = "上升趋势"
        elif trend == 'decreasing':
            trend_icon = "📉"
            trend_color = Color.FAIL
            trend_text = "下降趋势"
        elif trend == 'stable':
            trend_icon = "📊"
            trend_color = Color.CYAN
            trend_text = "稳定趋势"
        else:
            trend_icon = "❓"
            trend_color = Color.WARNING
            trend_text = "数据不足"
        
        print(f"\n{Color.CYAN}趋势分析：{Color.ENDC}")
        print(f"  {trend_icon} 总体趋势：{trend_color}{trend_text}{Color.ENDC}")
        if growth_rate != 0:
            growth_color = Color.GREEN if growth_rate > 0 else Color.FAIL
            print(f"  📊 增长率：{growth_color}{growth_rate:+.1f}%{Color.ENDC}")
        
        # 月度数据
        monthly_data = analysis_result['monthly_data']
        if monthly_data:
            print(f"\n{Color.CYAN}月度收入明细：{Color.ENDC}")
            for data in monthly_data[-6:]:  # 显示最近6个月
                month = data['month']
                revenue = data['revenue']
                print(f"  {month}：{revenue:>12,.2f} 元")
        
        # 建议
        recommendations = analysis_result['recommendations']
        if recommendations:
            print(f"\n{Color.CYAN}智能建议：{Color.ENDC}")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("=" * 70)
        
        # 询问是否保存报告
        if UserMessage.confirm("是否保存此分析报告？"):
            report_dir = "财务数据/智能分析"
            os.makedirs(report_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_dir}/收入趋势分析_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"收入趋势分析报告\n")
                    f.write(f"分析期间：最近{months}个月\n")
                    f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write(f"趋势分析：\n")
                    f.write(f"  总体趋势：{trend_text}\n")
                    if growth_rate != 0:
                        f.write(f"  增长率：{growth_rate:+.1f}%\n")
                    
                    f.write(f"\n月度收入明细：\n")
                    for data in monthly_data:
                        f.write(f"  {data['month']}：{data['revenue']:>12,.2f} 元\n")
                    
                    f.write(f"\n智能建议：\n")
                    for i, rec in enumerate(recommendations, 1):
                        f.write(f"  {i}. {rec}\n")
                
                UserMessage.success(f"分析报告已保存：{filename}")
                
            except Exception as e:
                UserMessage.error(f"保存报告失败：{str(e)}")
        
        duration = performance_monitor.end_operation("revenue_analysis")
        logger.info(f"收入趋势分析完成，耗时: {duration:.2f}秒")
        
    except Exception as e:
        UserMessage.error(f"收入趋势分析时发生错误: {str(e)}")
        logger.error(f"收入趋势分析异常: {str(e)}", exc_info=True)

def customer_value_analysis():
    """客户价值分析 - V1.4新增"""
    print("\n" + "=" * 70)
    print("     客户价值分析 - V1.4智能分析")
    print("=" * 70)
    
    try:
        performance_monitor.start_operation("customer_analysis")
        
        UserMessage.info("正在分析客户价值，请稍候...")
        
        # 执行分析
        customer_analysis = intelligent_analyzer.analyze_customer_value()
        
        if not customer_analysis:
            UserMessage.warning("暂无客户数据可分析")
            return
        
        # 显示分析结果
        print(f"\n" + "=" * 70)
        print(f"                客户价值分析报告")
        print(f"              共{len(customer_analysis)}个客户")
        print("=" * 70)
        
        print(f"\n{Color.CYAN}客户价值排名（前10名）：{Color.ENDC}")
        
        for i, customer in enumerate(customer_analysis[:10], 1):
            # 价值评分颜色
            score = customer['value_score']
            if score >= 80:
                score_color = Color.GREEN
                level = "⭐⭐⭐"
            elif score >= 60:
                score_color = Color.CYAN
                level = "⭐⭐"
            elif score >= 40:
                score_color = Color.WARNING
                level = "⭐"
            else:
                score_color = Color.FAIL
                level = ""
            
            # 风险等级颜色
            risk = customer['risk_level']
            if risk == 'high':
                risk_color = Color.FAIL
                risk_icon = "🚨"
            elif risk == 'medium':
                risk_color = Color.WARNING
                risk_icon = "⚠️"
            else:
                risk_color = Color.GREEN
                risk_icon = "✅"
            
            print(f"\n{i:2d}. {Color.BOLD}{customer['customer']}{Color.ENDC} {level}")
            print(f"    价值评分：{score_color}{score:.1f}/100{Color.ENDC}")
            print(f"    总收入：{customer['total_revenue']:>10,.2f} 元")
            print(f"    订单数：{customer['order_count']:>10} 个")
            print(f"    平均订单：{customer['avg_order_value']:>8,.2f} 元")
            print(f"    未收款：{customer['unpaid_amount']:>10,.2f} 元")
            print(f"    风险等级：{risk_icon} {risk_color}{risk.upper()}{Color.ENDC}")
            
            if customer['last_order_date']:
                days_ago = (datetime.now() - customer['last_order_date']).days
                print(f"    最后订单：{days_ago} 天前")
            
            # 显示建议
            if customer['recommendations']:
                print(f"    💡 建议：{customer['recommendations'][0]}")
        
        # 统计汇总
        total_customers = len(customer_analysis)
        high_value_customers = len([c for c in customer_analysis if c['value_score'] >= 80])
        high_risk_customers = len([c for c in customer_analysis if c['risk_level'] == 'high'])
        
        print(f"\n{Color.CYAN}客户统计汇总：{Color.ENDC}")
        print(f"  客户总数：{total_customers} 个")
        print(f"  高价值客户：{Color.GREEN}{high_value_customers} 个{Color.ENDC} (评分≥80)")
        print(f"  高风险客户：{Color.FAIL}{high_risk_customers} 个{Color.ENDC}")
        
        print("=" * 70)
        
        # 询问是否保存报告
        if UserMessage.confirm("是否保存此分析报告？"):
            report_dir = "财务数据/智能分析"
            os.makedirs(report_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_dir}/客户价值分析_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"客户价值分析报告\n")
                    f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write(f"客户价值排名：\n")
                    for i, customer in enumerate(customer_analysis, 1):
                        f.write(f"\n{i:2d}. {customer['customer']}\n")
                        f.write(f"    价值评分：{customer['value_score']:.1f}/100\n")
                        f.write(f"    总收入：{customer['total_revenue']:,.2f} 元\n")
                        f.write(f"    订单数：{customer['order_count']} 个\n")
                        f.write(f"    平均订单：{customer['avg_order_value']:,.2f} 元\n")
                        f.write(f"    未收款：{customer['unpaid_amount']:,.2f} 元\n")
                        f.write(f"    风险等级：{customer['risk_level'].upper()}\n")
                        
                        if customer['recommendations']:
                            f.write(f"    建议：{customer['recommendations'][0]}\n")
                    
                    f.write(f"\n客户统计汇总：\n")
                    f.write(f"  客户总数：{total_customers} 个\n")
                    f.write(f"  高价值客户：{high_value_customers} 个 (评分≥80)\n")
                    f.write(f"  高风险客户：{high_risk_customers} 个\n")
                
                UserMessage.success(f"分析报告已保存：{filename}")
                
            except Exception as e:
                UserMessage.error(f"保存报告失败：{str(e)}")
        
        duration = performance_monitor.end_operation("customer_analysis")
        logger.info(f"客户价值分析完成，耗时: {duration:.2f}秒")
        
    except Exception as e:
        UserMessage.error(f"客户价值分析时发生错误: {str(e)}")
        logger.error(f"客户价值分析异常: {str(e)}", exc_info=True)

def alert_center():
    """预警中心 - V1.4新增"""
    print("\n" + "=" * 70)
    print("     预警中心 - V1.4智能预警")
    print("=" * 70)
    
    try:
        performance_monitor.start_operation("alert_check")
        
        UserMessage.info("正在检查系统预警...")
        
        # 显示预警信息
        alert_system.show_alerts()
        
        # 预警设置
        print(f"\n{Color.CYAN}预警设置：{Color.ENDC}")
        for rule_name, rule_config in alert_system.alert_rules.items():
            status = "✅ 启用" if rule_config['enabled'] else "❌ 禁用"
            print(f"  {rule_name}: {status}")
        
        # 操作选项
        print(f"\n{Color.CYAN}操作选项：{Color.ENDC}")
        print("  1. 刷新预警")
        print("  2. 预警设置")
        print("  3. 预警历史")
        print("  4. 返回主菜单")
        
        choice = input("请选择操作（1-4）: ").strip()
        
        if choice == "1":
            UserMessage.info("正在刷新预警...")
            alert_system.show_alerts()
        elif choice == "2":
            print("\n预警设置功能开发中...")
        elif choice == "3":
            print("\n预警历史功能开发中...")
        
        duration = performance_monitor.end_operation("alert_check")
        logger.info(f"预警检查完成，耗时: {duration:.2f}秒")
        
    except Exception as e:
        UserMessage.error(f"预警中心时发生错误: {str(e)}")
        logger.error(f"预警中心异常: {str(e)}", exc_info=True)

def intelligent_report():
    """智能报告 - V1.4新增"""
    print("\n" + "=" * 70)
    print("     智能报告 - V1.4综合分析")
    print("=" * 70)
    
    try:
        performance_monitor.start_operation("intelligent_report")
        
        UserMessage.info("正在生成智能报告，请稍候...")
        
        # 综合分析
        print(f"\n" + "=" * 70)
        print(f"                智能综合分析报告")
        print(f"              {datetime.now().strftime('%Y年%m月%d日')}")
        print("=" * 70)
        
        # 1. 收入趋势
        print(f"\n{Color.CYAN}📈 收入趋势分析{Color.ENDC}")
        revenue_analysis = intelligent_analyzer.analyze_revenue_trend(3)
        trend = revenue_analysis['trend']
        growth_rate = revenue_analysis['growth_rate']
        
        if trend == 'increasing':
            print(f"  ✅ 收入呈上升趋势，增长率 {growth_rate:+.1f}%")
        elif trend == 'decreasing':
            print(f"  ⚠️ 收入呈下降趋势，下降率 {growth_rate:+.1f}%")
        else:
            print(f"  📊 收入相对稳定")
        
        # 2. 客户价值
        print(f"\n{Color.CYAN}👥 客户价值分析{Color.ENDC}")
        customer_analysis = intelligent_analyzer.analyze_customer_value()
        if customer_analysis:
            high_value_count = len([c for c in customer_analysis if c['value_score'] >= 80])
            print(f"  📊 共有 {len(customer_analysis)} 个客户，其中 {high_value_count} 个高价值客户")
            
            if customer_analysis:
                top_customer = customer_analysis[0]
                print(f"  🏆 最有价值客户：{top_customer['customer']} (评分: {top_customer['value_score']:.1f})")
        
        # 3. 预警信息
        print(f"\n{Color.CYAN}⚠️ 系统预警{Color.ENDC}")
        alerts = alert_system.check_all_alerts()
        if alerts:
            high_alerts = [a for a in alerts if a['level'] == 'HIGH']
            medium_alerts = [a for a in alerts if a['level'] == 'MEDIUM']
            print(f"  🚨 高优先级预警：{len(high_alerts)} 个")
            print(f"  ⚠️ 中等优先级预警：{len(medium_alerts)} 个")
            
            if high_alerts:
                print(f"  💡 紧急处理：{high_alerts[0]['message']}")
        else:
            print(f"  ✅ 暂无预警，系统运行正常")
        
        # 4. 性能信息
        print(f"\n{Color.CYAN}📊 系统性能{Color.ENDC}")
        performance_monitor.show_performance_info()
        
        # 5. 智能建议
        print(f"\n{Color.CYAN}💡 智能建议{Color.ENDC}")
        suggestions = []
        
        if revenue_analysis['recommendations']:
            suggestions.extend(revenue_analysis['recommendations'])
        
        if alerts:
            suggestions.append("建议及时处理系统预警，确保业务正常运行")
        
        if not suggestions:
            suggestions.append("系统运行良好，建议继续保持当前管理水平")
        
        for i, suggestion in enumerate(suggestions[:5], 1):
            print(f"  {i}. {suggestion}")
        
        print("=" * 70)
        
        # 询问是否保存报告
        if UserMessage.confirm("是否保存此智能报告？"):
            report_dir = "财务数据/智能分析"
            os.makedirs(report_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_dir}/智能综合报告_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"智能综合分析报告\n")
                    f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write(f"收入趋势分析：\n")
                    f.write(f"  趋势：{trend}\n")
                    f.write(f"  增长率：{growth_rate:+.1f}%\n\n")
                    
                    f.write(f"客户价值分析：\n")
                    if customer_analysis:
                        f.write(f"  客户总数：{len(customer_analysis)}\n")
                        f.write(f"  高价值客户：{high_value_count}\n")
                        f.write(f"  最有价值客户：{customer_analysis[0]['customer']}\n\n")
                    
                    f.write(f"系统预警：\n")
                    f.write(f"  预警总数：{len(alerts)}\n")
                    for alert in alerts[:3]:
                        f.write(f"  - {alert['message']}\n")
                    
                    f.write(f"\n智能建议：\n")
                    for i, suggestion in enumerate(suggestions, 1):
                        f.write(f"  {i}. {suggestion}\n")
                
                UserMessage.success(f"智能报告已保存：{filename}")
                
            except Exception as e:
                UserMessage.error(f"保存报告失败：{str(e)}")
        
        duration = performance_monitor.end_operation("intelligent_report")
        logger.info(f"智能报告生成完成，耗时: {duration:.2f}秒")
        
    except Exception as e:
        UserMessage.error(f"生成智能报告时发生错误: {str(e)}")
        logger.error(f"智能报告异常: {str(e)}", exc_info=True)

def performance_monitor_view():
    """性能监控 - V1.4新增"""
    print("\n" + "=" * 70)
    print("     性能监控 - V1.4系统监控")
    print("=" * 70)
    
    try:
        # 显示性能信息
        performance_monitor.show_performance_info()
        
        # 显示缓存信息
        print(f"\n{Color.CYAN}📊 缓存信息{Color.ENDC}")
        cache_info = enhanced_finance_manager.load_transactions_cached.cache_info()
        print(f"  缓存命中：{cache_info.hits} 次")
        print(f"  缓存未命中：{cache_info.misses} 次")
        print(f"  缓存大小：{cache_info.currsize}/{cache_info.maxsize}")
        
        if cache_info.hits + cache_info.misses > 0:
            hit_rate = cache_info.hits / (cache_info.hits + cache_info.misses) * 100
            print(f"  命中率：{hit_rate:.1f}%")
        
        # 显示数据统计
        print(f"\n{Color.CYAN}📊 数据统计{Color.ENDC}")
        try:
            transactions = enhanced_finance_manager.load_transactions()
            orders = get_storage().get_all_orders()
            
            print(f"  收支记录：{len(transactions)} 条")
            print(f"  订单记录：{len(orders)} 条")
            
            # 计算数据大小
            import sys
            transactions_size = sys.getsizeof(str(transactions)) / 1024  # KB
            orders_size = sys.getsizeof(str(orders)) / 1024  # KB
            
            print(f"  数据大小：{transactions_size + orders_size:.1f} KB")
            
        except Exception as e:
            print(f"  数据统计获取失败：{e}")
        
        # 操作选项
        print(f"\n{Color.CYAN}操作选项：{Color.ENDC}")
        print("  1. 清除缓存")
        print("  2. 内存优化")
        print("  3. 性能测试")
        print("  4. 返回主菜单")
        
        choice = input("请选择操作（1-4）: ").strip()
        
        if choice == "1":
            enhanced_finance_manager.load_transactions_cached.cache_clear()
            UserMessage.success("缓存已清除")
        elif choice == "2":
            import gc
            gc.collect()
            UserMessage.success("内存优化完成")
        elif choice == "3":
            UserMessage.info("性能测试功能开发中...")
        
    except Exception as e:
        UserMessage.error(f"性能监控时发生错误: {str(e)}")
        logger.error(f"性能监控异常: {str(e)}", exc_info=True)
# V1.4 主程序
def main():
    """主函数 - V1.4增强版"""
    print(f"\n{Color.GREEN}{'=' * 80}{Color.ENDC}")
    print(f"{Color.GREEN}       欢迎使用氧化加工厂财务助手 V1.4 - 增强版！{Color.ENDC}")
    print(f"{Color.GREEN}{'=' * 80}{Color.ENDC}")
    
    print(f"\n{Color.CYAN}🚀 V1.4 增强版新特性：{Color.ENDC}")
    print("  ✨ 用户体验优化 - 快捷操作、智能提示、自动补全")
    print("  🧠 智能分析功能 - 收入趋势、客户价值、预警系统")
    print("  🔒 数据验证增强 - 金额验证、日期检查、重复检测")
    print("  ⚡ 性能优化 - 缓存机制、内存优化、响应加速")
    print("  🛡️ 自动备份 - 数据安全、版本控制、恢复机制")
    
    print(f"\n{Color.CYAN}💡 V1.4 使用提示：{Color.ENDC}")
    print("  ✅ 支持快捷键操作（q-退出, h-帮助, l-日志, b-备份）")
    print("  ✅ 智能客户名称自动补全")
    print("  ✅ 最近使用功能快速访问（r1, r2...）")
    print("  ✅ 实时预警和智能分析")
    print("  ✅ 增强的数据验证和错误提示")
    
    logger.info("V1.4系统启动成功")
    
    # 启动时检查预警
    alerts = alert_system.check_all_alerts()
    if alerts:
        high_alerts = [a for a in alerts if a['level'] == 'HIGH']
        if high_alerts:
            print(f"\n{Color.FAIL}🚨 检测到 {len(high_alerts)} 个高优先级预警，建议及时处理！{Color.ENDC}")
    
    while True:
        try:
            show_enhanced_main_menu()
            
            user_input = input(f"\n{Color.BOLD}请选择功能编号（支持快捷键）：{Color.ENDC}").strip()
            
            # 处理快捷键
            shortcut_result = enhanced_ui.handle_shortcut(user_input)
            if shortcut_result:
                choice = shortcut_result
            else:
                choice = user_input
            
            # 记录功能使用
            function_name = ""
            
            # 订单管理
            if choice == "01":
                function_name = "新建加工订单"
                from 氧化加工厂财务助手_全能版 import create_order
                create_order()
            elif choice == "02":
                function_name = "查看订单列表"
                from 氧化加工厂财务助手_全能版 import list_orders
                list_orders()
            elif choice == "03":
                function_name = "编辑订单信息"
                UserMessage.info("订单编辑功能请使用小白专版")
            elif choice == "04":
                function_name = "搜索订单"
                UserMessage.info("订单搜索功能请使用小白专版")
            elif choice == "05":
                function_name = "记录收款"
                UserMessage.info("收款记录功能请使用小白专版")
            elif choice == "06":
                function_name = "订单统计分析"
                UserMessage.info("订单统计功能请使用小白专版")
            elif choice == "07":
                function_name = "导出订单到Excel"
                UserMessage.info("订单导出功能请使用小白专版")
            
            # 收支管理 - V1.4增强版
            elif choice == "11":
                function_name = "记录支出"
                enhanced_record_expense()
            elif choice == "12":
                function_name = "记录收入"
                enhanced_record_income()
            elif choice == "13":
                function_name = "查看收支明细"
                from 氧化加工厂财务助手_全能版 import view_transactions
                view_transactions()
            elif choice == "14":
                function_name = "收支统计"
                from 氧化加工厂财务助手_全能版 import transaction_statistics
                transaction_statistics()
            elif choice == "15":
                function_name = "银行流水管理"
                from 氧化加工厂财务助手_全能版 import bank_statement_management
                bank_statement_management()
            elif choice == "16":
                function_name = "导出收支报表"
                from 氧化加工厂财务助手_全能版 import export_transaction_report
                export_transaction_report()
            
            # 税务管理
            elif choice == "21":
                function_name = "增值税管理"
                from 氧化加工厂财务助手_全能版 import tax_management
                tax_management()
            elif choice == "22":
                function_name = "所得税计算"
                from 氧化加工厂财务助手_全能版 import income_tax_calculation
                income_tax_calculation()
            elif choice == "23":
                function_name = "税务报表"
                from 氧化加工厂财务助手_全能版 import tax_report_center
                tax_report_center()
            elif choice == "24":
                function_name = "税务资料归档"
                from 氧化加工厂财务助手_全能版 import tax_document_archive
                tax_document_archive()
            
            # 报表中心
            elif choice == "31":
                function_name = "利润表"
                from 氧化加工厂财务助手_全能版 import generate_profit_report
                generate_profit_report()
            elif choice == "32":
                function_name = "资产负债表"
                from 氧化加工厂财务助手_全能版 import balance_sheet_report
                balance_sheet_report()
            elif choice == "33":
                function_name = "现金流量表"
                from 氧化加工厂财务助手_全能版 import cash_flow_statement
                cash_flow_statement()
            elif choice == "34":
                function_name = "财务分析报告"
                from 氧化加工厂财务助手_全能版 import financial_analysis_report
                financial_analysis_report()
            elif choice == "35":
                function_name = "月度汇总"
                from 氧化加工厂财务助手_全能版 import monthly_summary
                monthly_summary()
            elif choice == "36":
                function_name = "年度汇总"
                from 氧化加工厂财务助手_全能版 import annual_summary
                annual_summary()
            
            # 档案管理
            elif choice == "41":
                function_name = "凭证管理"
                from 氧化加工厂财务助手_全能版 import voucher_management
                voucher_management()
            elif choice == "42":
                function_name = "合同管理"
                from 氧化加工厂财务助手_全能版 import contract_management
                contract_management()
            elif choice == "43":
                function_name = "客户档案"
                from 氧化加工厂财务助手_全能版 import customer_management
                customer_management()
            elif choice == "44":
                function_name = "供应商档案"
                from 氧化加工厂财务助手_全能版 import supplier_management
                supplier_management()
            
            # 智能分析 - V1.4新增
            elif choice == "61":
                function_name = "收入趋势分析"
                revenue_trend_analysis()
            elif choice == "62":
                function_name = "客户价值分析"
                customer_value_analysis()
            elif choice == "63":
                function_name = "预警中心"
                alert_center()
            elif choice == "64":
                function_name = "智能报告"
                intelligent_report()
            
            # 系统管理
            elif choice == "51":
                function_name = "生成示例数据"
                from 氧化加工厂财务助手_全能版 import generate_demo_data
                generate_demo_data()
            elif choice == "52":
                function_name = "数据清理"
                from 氧化加工厂财务助手_全能版 import data_cleanup
                data_cleanup()
            elif choice == "53":
                function_name = "数据备份"
                from 氧化加工厂财务助手_全能版 import data_backup
                data_backup()
            elif choice == "54":
                function_name = "数据恢复"
                from 氧化加工厂财务助手_全能版 import data_restore
                data_restore()
            elif choice == "55":
                function_name = "系统配置"
                from 氧化加工厂财务助手_全能版 import system_configuration
                system_configuration()
            elif choice == "56":
                function_name = "使用教程"
                from 氧化加工厂财务助手_全能版 import show_tutorial
                show_tutorial()
            elif choice == "57":
                function_name = "查看运行日志"
                from 氧化加工厂财务助手_全能版 import show_logs
                show_logs()
            elif choice == "58":
                function_name = "性能监控"
                performance_monitor_view()
            
            elif choice == "99":
                logger.info("用户正常退出系统")
                print(f"\n{Color.GREEN}👋 感谢使用氧化加工厂财务助手 V1.4 增强版，再见！{Color.ENDC}\n")
                break
            else:
                UserMessage.error("无效选择，请重新输入")
                continue
            
            # 记录最近使用的功能
            if function_name:
                enhanced_ui.add_recent_function(choice, function_name)
            
            # V1.4新增：操作完成提示
            if choice not in ["99"]:
                print(f"\n{Color.CYAN}💡 提示：输入 'q' 快速退出，'h' 查看帮助{Color.ENDC}")
                input(f"{Color.CYAN}按回车键继续...{Color.ENDC}")
            
        except KeyboardInterrupt:
            logger.warning("用户中断操作")
            print(f"\n\n{Color.WARNING}⚠️ 用户中断操作{Color.ENDC}")
            if UserMessage.confirm("确定要退出系统吗？"):
                logger.info("用户确认退出系统")
                print(f"{Color.GREEN}👋 感谢使用，再见！{Color.ENDC}\n")
                break
        except Exception as e:
            logger.critical(f"主程序异常: {str(e)}", exc_info=True)
            UserMessage.error(f"程序异常：{str(e)}")
            UserMessage.info("系统将继续运行，如问题持续请查看日志")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"程序启动异常: {str(e)}", exc_info=True)
        print(f"\n{Color.FAIL}❌ 程序启动异常：{str(e)}{Color.ENDC}\n")
        import traceback
        traceback.print_exc()