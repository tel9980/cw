"""
NotificationService Example Usage

演示如何使用NotificationService发送桌面通知和企业微信通知。
"""

from notification_service import NotificationService
from datetime import date


def example_1_desktop_notification():
    """示例1：发送桌面通知"""
    print("=" * 60)
    print("示例1：发送桌面通知")
    print("=" * 60)
    
    # 创建通知服务
    service = NotificationService()
    
    # 发送简单的桌面通知
    success = service.send_desktop_notification(
        title="税务申报提醒",
        message="增值税申报截止日期为3天后（2024年1月15日），请及时完成申报。"
    )
    
    if success:
        print("✓ 桌面通知发送成功")
    else:
        print("✗ 桌面通知发送失败")
    
    print()


def example_2_custom_desktop_notification():
    """示例2：自定义桌面通知参数"""
    print("=" * 60)
    print("示例2：自定义桌面通知参数")
    print("=" * 60)
    
    service = NotificationService()
    
    # 自定义应用名称和显示时长
    success = service.send_desktop_notification(
        title="应收账款逾期提醒",
        message="客户【ABC公司】有一笔金额为50,000元的应收账款已逾期30天，请及时催收。",
        app_name="财务助手Pro",
        timeout=15  # 显示15秒
    )
    
    if success:
        print("✓ 自定义桌面通知发送成功")
    else:
        print("✗ 自定义桌面通知发送失败")
    
    print()


def example_3_wechat_notification():
    """示例3：发送企业微信通知"""
    print("=" * 60)
    print("示例3：发送企业微信通知")
    print("=" * 60)
    
    service = NotificationService()
    
    # 企业微信webhook地址（需要替换为实际地址）
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE"
    
    # 发送企业微信通知
    success = service.send_wechat_notification(
        webhook_url=webhook_url,
        message="【财务提醒】\n现金流预警：预计7天后现金流不足，请及时安排资金。\n当前余额：50,000元\n预计支出：80,000元"
    )
    
    if success:
        print("✓ 企业微信通知发送成功")
    else:
        print("✗ 企业微信通知发送失败（请检查webhook地址是否正确）")
    
    print()


def example_4_wechat_notification_with_mentions():
    """示例4：发送带@用户的企业微信通知"""
    print("=" * 60)
    print("示例4：发送带@用户的企业微信通知")
    print("=" * 60)
    
    service = NotificationService()
    
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE"
    
    # 发送带@用户的通知
    success = service.send_wechat_notification(
        webhook_url=webhook_url,
        message="【紧急提醒】\n税务申报截止日期为明天，请立即处理！",
        mentioned_list=["zhangsan", "lisi"],  # @指定用户
        mentioned_mobile_list=["13800138000"]  # @指定手机号
    )
    
    if success:
        print("✓ 带@用户的企业微信通知发送成功")
    else:
        print("✗ 带@用户的企业微信通知发送失败")
    
    print()


def example_5_multi_channel_notification():
    """示例5：通过多个渠道发送通知"""
    print("=" * 60)
    print("示例5：通过多个渠道发送通知")
    print("=" * 60)
    
    service = NotificationService()
    
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE"
    
    # 同时发送桌面通知和企业微信通知
    results = service.send_notification(
        title="应付账款到期提醒",
        message="供应商【XYZ公司】的应付账款将于3天后到期，金额：100,000元，请及时安排付款。",
        channels=["desktop", "wechat"],
        wechat_webhook_url=webhook_url
    )
    
    print(f"桌面通知: {'✓ 成功' if results.get('desktop') else '✗ 失败'}")
    print(f"企业微信通知: {'✓ 成功' if results.get('wechat') else '✗ 失败'}")
    
    print()


def example_6_retry_logic():
    """示例6：演示重试逻辑"""
    print("=" * 60)
    print("示例6：演示重试逻辑")
    print("=" * 60)
    
    # 创建带自定义重试参数的服务
    service = NotificationService(
        max_retries=5,  # 最多重试5次
        retry_delay=1   # 每次重试间隔1秒
    )
    
    print(f"配置: 最大重试次数={service.max_retries}, 重试延迟={service.retry_delay}秒")
    
    # 尝试发送通知（如果失败会自动重试）
    success = service.send_desktop_notification(
        title="测试重试",
        message="这是一个测试重试逻辑的通知"
    )
    
    if success:
        print("✓ 通知发送成功（可能经过了重试）")
    else:
        print("✗ 通知发送失败（已达到最大重试次数）")
    
    print()


def example_7_test_notifications():
    """示例7：测试通知功能"""
    print("=" * 60)
    print("示例7：测试通知功能")
    print("=" * 60)
    
    service = NotificationService()
    
    # 测试桌面通知
    print("测试桌面通知...")
    desktop_ok = service.test_desktop_notification()
    print(f"桌面通知测试: {'✓ 通过' if desktop_ok else '✗ 失败'}")
    
    # 测试企业微信通知
    print("\n测试企业微信通知...")
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE"
    wechat_ok = service.test_wechat_notification(webhook_url)
    print(f"企业微信通知测试: {'✓ 通过' if wechat_ok else '✗ 失败'}")
    
    print()


def example_8_real_world_scenario():
    """示例8：真实场景 - 税务申报提醒"""
    print("=" * 60)
    print("示例8：真实场景 - 税务申报提醒")
    print("=" * 60)
    
    service = NotificationService()
    
    # 模拟税务申报提醒场景
    tax_deadline = date(2024, 1, 15)
    days_until_deadline = 3
    
    title = f"税务申报提醒（还有{days_until_deadline}天）"
    message = f"""
【增值税申报提醒】

申报截止日期：{tax_deadline.strftime('%Y年%m月%d日')}
剩余时间：{days_until_deadline}天

请及时完成以下工作：
1. 核对本月销项发票
2. 核对本月进项发票
3. 填写增值税申报表
4. 在线提交申报

如有问题，请联系财务主管。
    """.strip()
    
    # 发送通知
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE"
    
    results = service.send_notification(
        title=title,
        message=message,
        channels=["desktop", "wechat"],
        wechat_webhook_url=webhook_url,
        mentioned_list=["accountant1", "accountant2"]  # @相关会计人员
    )
    
    print(f"通知发送结果:")
    print(f"  桌面通知: {'✓ 成功' if results.get('desktop') else '✗ 失败'}")
    print(f"  企业微信通知: {'✓ 成功' if results.get('wechat') else '✗ 失败'}")
    
    print()


def example_9_error_handling():
    """示例9：错误处理"""
    print("=" * 60)
    print("示例9：错误处理")
    print("=" * 60)
    
    service = NotificationService()
    
    # 测试空webhook地址
    print("测试1: 空webhook地址")
    success = service.send_wechat_notification(
        webhook_url="",
        message="测试消息"
    )
    print(f"结果: {'✓ 成功' if success else '✗ 失败（预期行为）'}")
    
    # 测试无效webhook地址
    print("\n测试2: 无效webhook地址")
    success = service.send_wechat_notification(
        webhook_url="invalid-url",
        message="测试消息"
    )
    print(f"结果: {'✓ 成功' if success else '✗ 失败（预期行为）'}")
    
    # 测试未知渠道
    print("\n测试3: 未知通知渠道")
    results = service.send_notification(
        title="测试",
        message="测试",
        channels=["unknown_channel"]
    )
    print(f"结果: {results}")
    
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("NotificationService 使用示例")
    print("=" * 60 + "\n")
    
    print("注意：")
    print("1. 桌面通知需要安装 plyer 库: pip install plyer")
    print("2. 企业微信通知需要安装 requests 库: pip install requests")
    print("3. 企业微信通知需要配置有效的 webhook 地址")
    print("4. 部分示例可能因为缺少依赖或配置而失败，这是正常的")
    print()
    
    # 运行示例
    try:
        example_1_desktop_notification()
    except Exception as e:
        print(f"示例1执行出错: {e}\n")
    
    try:
        example_2_custom_desktop_notification()
    except Exception as e:
        print(f"示例2执行出错: {e}\n")
    
    try:
        example_3_wechat_notification()
    except Exception as e:
        print(f"示例3执行出错: {e}\n")
    
    try:
        example_4_wechat_notification_with_mentions()
    except Exception as e:
        print(f"示例4执行出错: {e}\n")
    
    try:
        example_5_multi_channel_notification()
    except Exception as e:
        print(f"示例5执行出错: {e}\n")
    
    try:
        example_6_retry_logic()
    except Exception as e:
        print(f"示例6执行出错: {e}\n")
    
    try:
        example_7_test_notifications()
    except Exception as e:
        print(f"示例7执行出错: {e}\n")
    
    try:
        example_8_real_world_scenario()
    except Exception as e:
        print(f"示例8执行出错: {e}\n")
    
    try:
        example_9_error_handling()
    except Exception as e:
        print(f"示例9执行出错: {e}\n")
    
    print("=" * 60)
    print("所有示例执行完毕")
    print("=" * 60)


if __name__ == "__main__":
    main()
