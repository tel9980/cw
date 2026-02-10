# -*- coding: utf-8 -*-
"""
Basic Workflow Demo
基础工作流演示 - 展示如何使用V1.5工作流引擎
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflow_v15 import WorkflowEngine, ContextEngine, ProgressiveDisclosureManager
from workflow_v15.models.context_models import Activity
from datetime import datetime


def demo_morning_workflow():
    """演示早晨工作流"""
    print("=" * 60)
    print("V1.5 早晨工作流演示")
    print("=" * 60)
    
    # 创建工作流引擎
    engine = WorkflowEngine()
    
    # 启动早晨工作流
    print("\n1. 启动早晨工作流...")
    session = engine.start_workflow(
        workflow_type="morning_setup",
        context={"user_id": "demo_user", "date": datetime.now().strftime("%Y-%m-%d")},
        user_id="demo_user"
    )
    
    print(f"   ✓ 工作流会话已创建: {session.session_id}")
    print(f"   ✓ 工作流类型: {session.workflow_type.value}")
    print(f"   ✓ 总步骤数: {len(session.steps)}")
    print(f"   ✓ 当前进度: {session.get_progress() * 100:.0f}%")
    
    # 显示工作流步骤
    print("\n2. 工作流步骤:")
    for i, step in enumerate(session.steps, 1):
        print(f"   {i}. {step.name}")
        print(f"      - {step.description}")
        print(f"      - 预计耗时: {step.estimated_duration}秒")
    
    # 执行第一个步骤
    print("\n3. 执行第一个步骤...")
    result = engine.execute_step(
        session_id=session.session_id,
        step_data={"action": "reviewed_tasks", "notes": "已查看今日任务"}
    )
    
    print(f"   ✓ 步骤状态: {result.status.value}")
    print(f"   ✓ 执行结果: {result.message}")
    print(f"   ✓ 当前进度: {session.get_progress() * 100:.0f}%")
    
    # 获取下一步建议
    print("\n4. 获取下一步建议...")
    suggestions = engine.get_next_suggestions(session.session_id)
    if suggestions:
        print(f"   建议的下一步操作:")
        for suggestion in suggestions:
            print(f"   - {suggestion.name}: {suggestion.description}")
            print(f"     (置信度: {suggestion.confidence * 100:.0f}%)")
    
    print("\n" + "=" * 60)


def demo_context_analysis():
    """演示上下文分析"""
    print("\n" + "=" * 60)
    print("V1.5 上下文分析演示")
    print("=" * 60)
    
    # 创建上下文引擎
    context_engine = ContextEngine()
    
    # 记录一些用户活动
    print("\n1. 记录用户活动...")
    activities = [
        Activity(
            activity_id="act1",
            user_id="demo_user",
            action_type="transaction_entry",
            function_code="1",
            timestamp=datetime.now(),
            duration=120.0
        ),
        Activity(
            activity_id="act2",
            user_id="demo_user",
            action_type="report_view",
            function_code="31",
            timestamp=datetime.now(),
            duration=60.0
        )
    ]
    
    for activity in activities:
        context_engine.record_activity("demo_user", activity)
        print(f"   ✓ 记录活动: {activity.action_type}")
    
    # 分析当前上下文
    print("\n2. 分析当前上下文...")
    analysis = context_engine.analyze_current_context("demo_user")
    
    print(f"   ✓ 分析时间: {analysis.analysis_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   ✓ 时间上下文: {analysis.current_time_context.time_type.value}")
    print(f"   ✓ 业务周期: {analysis.business_cycle_position.value}")
    print(f"   ✓ 置信度: {analysis.confidence_score * 100:.0f}%")
    
    # 显示建议的优先级
    print("\n3. 建议的优先级任务:")
    for priority in analysis.suggested_priorities[:3]:
        print(f"   - {priority.title}")
        print(f"     优先级: {priority.priority.value}")
        print(f"     原因: {priority.reason}")
    
    # 生成智能默认值
    print("\n4. 生成智能默认值...")
    defaults = context_engine.generate_smart_defaults(
        transaction_type="income",
        context={"user_id": "demo_user"}
    )
    
    for field_name, default in defaults.items():
        print(f"   {field_name}: {default.suggested_value}")
        print(f"   - 置信度: {default.confidence * 100:.0f}%")
        print(f"   - 原因: {default.reasoning}")
    
    print("\n" + "=" * 60)


def demo_progressive_disclosure():
    """演示渐进式披露"""
    print("\n" + "=" * 60)
    print("V1.5 渐进式披露演示")
    print("=" * 60)
    
    from workflow_v15.core.progressive_disclosure import Action, HelpContent
    
    # 创建管理器
    manager = ProgressiveDisclosureManager(max_primary_actions=5)
    
    # 注册一些操作
    print("\n1. 注册操作...")
    actions_data = [
        ("1", "收入记录", "记录收入交易", True),
        ("2", "支出记录", "记录支出交易", True),
        ("15", "银行流水", "管理银行流水", True),
        ("31", "日结报告", "生成日结报告", True),
        ("53", "数据备份", "备份财务数据", True),
        ("56", "帮助文档", "查看帮助", False),
        ("57", "查看日志", "查看操作日志", False),
    ]
    
    for func_code, name, desc, is_primary in actions_data:
        action = Action(
            action_id=f"action_{func_code}",
            name=name,
            description=desc,
            function_code=func_code,
            is_primary=is_primary
        )
        manager.register_action(action)
        print(f"   ✓ 注册: {name} ({'主要' if is_primary else '次要'})")
    
    # 获取主要操作
    print("\n2. 获取主要操作（最多5个）...")
    primary_actions = manager.get_primary_actions(context="main_menu")
    print(f"   返回 {len(primary_actions)} 个主要操作:")
    for action in primary_actions:
        print(f"   - {action.name}")
    
    # 模拟用户使用
    print("\n3. 模拟用户使用模式...")
    manager.record_action_usage("demo_user", "action_1")
    manager.record_action_usage("demo_user", "action_1")
    manager.record_action_usage("demo_user", "action_1")
    manager.record_action_usage("demo_user", "action_31")
    manager.record_action_usage("demo_user", "action_31")
    print("   ✓ 记录了用户操作")
    
    # 检测用户级别
    user_level = manager.get_user_level("demo_user")
    print(f"   ✓ 用户级别: {user_level}")
    
    # 根据使用模式调整菜单
    print("\n4. 根据使用模式调整菜单...")
    user_patterns = {
        "user_id": "demo_user",
        "function_usage_count": {"1": 3, "31": 2}
    }
    menu_config = manager.adapt_menu_priority(user_patterns)
    
    print(f"   调整后的主要操作:")
    for action in menu_config.primary_actions[:3]:
        print(f"   - {action.name} (使用次数: {action.usage_count})")
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "V1.5 小会计工作流优化演示" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        # 运行演示
        demo_morning_workflow()
        demo_context_analysis()
        demo_progressive_disclosure()
        
        print("\n✓ 所有演示完成！")
        print("\n提示: 这些功能可以与现有的V1.4代码无缝集成。")
        
    except Exception as e:
        print(f"\n✗ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
