#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能计算器

功能：
- 订单金额计算
- 委外成本估算
- 利润计算
- 快速报价
"""

import sys
import io

# Windows编码支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from decimal import Decimal, ROUND_HALF_UP


class SmartCalculator:
    """智能计算器"""

    # 计价单位
    PRICING_UNITS = {
        "件": "PIECE",
        "条": "STRIP",
        "只": "UNIT",
        "个": "ITEM",
        "米": "METER",
        "公斤": "KILOGRAM",
        "平方米": "SQUARE_METER",
    }

    # 工序
    PROCESSES = ["喷砂", "拉丝", "抛光", "氧化"]

    # 委外成本参考比例
    OUTSOURCING_RATES = {
        "喷砂": Decimal("0.30"),  # 约30%成本
        "拉丝": Decimal("0.25"),  # 约25%成本
        "抛光": Decimal("0.25"),  # 约25%成本
        "氧化": Decimal("0.00"),  # 本厂完成，不委外
    }

    def __init__(self):
        pass

    def calculate_order(self, quantity, unit_price, processes, outsourced=None):
        """计算订单金额"""
        quantity = Decimal(str(quantity))
        unit_price = Decimal(str(unit_price))

        # 基础金额
        base_amount = quantity * unit_price

        # 委外成本
        outsourcing_cost = Decimal("0")
        if outsourced:
            for proc in outsourced:
                if proc in self.OUTSOURCING_RATES:
                    outsourcing_cost += base_amount * self.OUTSOURCING_RATES[proc]

        # 预估利润（扣除委外成本）
        estimated_profit = base_amount - outsourcing_cost

        # 成本率
        cost_rate = (outsourcing_cost / base_amount * 100) if base_amount > 0 else 0

        return {
            "quantity": quantity,
            "unit_price": unit_price,
            "base_amount": base_amount.quantize(Decimal("0.01")),
            "outsourcing_cost": outsourcing_cost.quantize(Decimal("0.01")),
            "estimated_profit": estimated_profit.quantize(Decimal("0.01")),
            "cost_rate": cost_rate,
            "processes": processes,
            "outsourced": outsourced or [],
        }

    def quick_quote(self, item_type, quantity, unit):
        """快速报价"""
        # 参考单价（根据市场情况调整）
        reference_prices = {
            "铝型材": {
                "米": Decimal("3.00"),
                "公斤": Decimal("1.50"),
            },
            "铝板": {
                "平方米": Decimal("25.00"),
                "公斤": Decimal("1.20"),
            },
            "螺丝": {
                "件": Decimal("0.10"),
                "个": Decimal("0.10"),
            },
            "把手": {
                "只": Decimal("3.00"),
                "个": Decimal("3.00"),
            },
            "铝条": {
                "条": Decimal("2.00"),
                "米": Decimal("2.00"),
            },
        }

        if item_type in reference_prices and unit in reference_prices[item_type]:
            ref_price = reference_prices[item_type][unit]
            total = Decimal(str(quantity)) * ref_price

            # 根据数量给折扣建议
            discount = Decimal("0")
            if quantity >= 1000:
                discount = Decimal("0.95")  # 95折
            elif quantity >= 500:
                discount = Decimal("0.97")  # 97折
            elif quantity >= 100:
                discount = Decimal("0.98")  # 98折

            if discount > 0:
                final_price = total * discount
                return {
                    "item_type": item_type,
                    "quantity": quantity,
                    "unit": unit,
                    "reference_price": ref_price,
                    "original_total": total.quantize(Decimal("0.01")),
                    "discount": discount,
                    "final_price": final_price.quantize(Decimal("0.01")),
                    "note": f"数量{quantity}，享受{int((1 - discount) * 100)}%折扣",
                }
            else:
                return {
                    "item_type": item_type,
                    "quantity": quantity,
                    "unit": unit,
                    "reference_price": ref_price,
                    "total": total.quantize(Decimal("0.01")),
                    "note": "标准报价",
                }

        return None

    def calculate_batch_orders(self, orders):
        """批量计算多个订单"""
        results = []
        total_amount = Decimal("0")
        total_outsourcing = Decimal("0")

        for order in orders:
            result = self.calculate_order(
                order["quantity"],
                order["unit_price"],
                order.get("processes", []),
                order.get("outsourced", []),
            )
            results.append(result)
            total_amount += result["base_amount"]
            total_outsourcing += result["outsourcing_cost"]

        total_profit = total_amount - total_outsourcing

        return {
            "orders": results,
            "total_amount": total_amount.quantize(Decimal("0.01")),
            "total_outsourcing": total_outsourcing.quantize(Decimal("0.01")),
            "total_profit": total_profit.quantize(Decimal("0.01")),
            "avg_margin": (total_profit / total_amount * 100)
            if total_amount > 0
            else 0,
        }

    def price_breakdown(self, total_price, quantity):
        """价格分解"""
        quantity = Decimal(str(quantity))
        unit_price = total_price / quantity

        return {
            "total": total_price.quantize(Decimal("0.01")),
            "quantity": quantity,
            "unit_price": unit_price.quantize(Decimal("0.001")),
            "per_100": (unit_price * 100).quantize(Decimal("0.01")),
            "per_1000": (unit_price * 1000).quantize(Decimal("0.01")),
        }


def interactive_calculator():
    """交互式计算器"""
    calc = SmartCalculator()

    print("\n" + "=" * 70)
    print("氧化加工厂财务系统 V2.0 - 智能计算器")
    print("=" * 70)

    while True:
        print("\n[1] 订单金额计算")
        print("[2] 快速报价")
        print("[3] 价格分解")
        print("[4] 批量计算")
        print("[0] 退出")

        choice = input("\n请选择: ").strip()

        if choice == "0":
            break
        elif choice == "1":
            try:
                quantity = Decimal(input("数量: "))
                unit_price = Decimal(input("单价(元): "))

                print("\n工序 (可多选，空格分隔):")
                print("1.喷砂 2.拉丝 3.抛光 4.氧化")
                proc_input = input("选择: ").strip()

                processes = []
                proc_map = {"1": "喷砂", "2": "拉丝", "3": "抛光", "4": "氧化"}
                for p in proc_input.split():
                    if p in proc_map:
                        processes.append(proc_map[p])

                print("\n委外工序 (可多选，空格分隔):")
                print("1.喷砂 2.拉丝 3.抛光")
                out_input = input("选择: ").strip()

                outsourced = []
                for p in out_input.split():
                    if p in proc_map:
                        outsourced.append(proc_map[p])

                result = calc.calculate_order(
                    quantity, unit_price, processes, outsourced
                )

                print("\n" + "-" * 70)
                print("计算结果:")
                print("-" * 70)
                print(f"  数量: {result['quantity']}")
                print(f"  单价: ¥{result['unit_price']:.2f}")
                print(f"  工序: {', '.join(result['processes'])}")
                print(
                    f"  委外: {', '.join(result['outsourced']) if result['outsourced'] else '无'}"
                )
                print("-" * 70)
                print(f"  订单金额: ¥{result['base_amount']:,.2f}")
                print(
                    f"  委外成本: ¥{result['outsourcing_cost']:,.2f} ({result['cost_rate']:.1f}%)"
                )
                print(f"  预估利润: ¥{result['estimated_profit']:,.2f}")
                print("-" * 70)

            except Exception as e:
                print(f"\n[错误] {e}")

        elif choice == "2":
            print("\n物品类型:")
            print("1.铝型材 2.铝板 3.螺丝 4.把手 5.铝条")
            type_map = {
                "1": "铝型材",
                "2": "铝板",
                "3": "螺丝",
                "4": "把手",
                "5": "铝条",
            }
            type_choice = input("选择: ").strip()

            if type_choice in type_map:
                item_type = type_map[type_choice]
                quantity = int(input("数量: "))

                print("\n计价单位:")
                units = ["件", "条", "只", "个", "米", "公斤", "平方米"]
                for i, u in enumerate(units, 1):
                    print(f"{i}.{u}", end="  ")
                print()
                unit_choice = input("选择: ").strip()

                if unit_choice.isdigit() and 1 <= int(unit_choice) <= len(units):
                    unit = units[int(unit_choice) - 1]

                    result = calc.quick_quote(item_type, quantity, unit)
                    if result:
                        print("\n" + "-" * 70)
                        print("快速报价:")
                        print("-" * 70)
                        print(f"  物品: {result['item_type']}")
                        print(f"  数量: {result['quantity']} {result['unit']}")
                        print(
                            f"  参考价: ¥{result['reference_price']:.2f}/{result['unit']}"
                        )
                        if "discount" in result:
                            print(f"  原价: ¥{result['original_total']:,.2f}")
                            print(f"  折扣: {int((1 - result['discount']) * 100)}% off")
                            print(f"  折后价: ¥{result['final_price']:,.2f}")
                        else:
                            print(f"  总价: ¥{result['total']:,.2f}")
                        print(f"  备注: {result['note']}")
                        print("-" * 70)

        elif choice == "3":
            try:
                total = Decimal(input("总价(元): "))
                qty = Decimal(input("数量: "))

                result = calc.price_breakdown(total, qty)

                print("\n" + "-" * 70)
                print("价格分解:")
                print("-" * 70)
                print(f"  总价: ¥{result['total']:,.2f}")
                print(f"  数量: {result['quantity']}")
                print(f"  单价: ¥{result['unit_price']:.3f}")
                print(f"  每100个: ¥{result['per_100']:,.2f}")
                print(f"  每1000个: ¥{result['per_1000']:,.2f}")
                print("-" * 70)

            except Exception as e:
                print(f"\n[错误] {e}")

        elif choice == "4":
            print("\n批量计算 (输入空数量结束)")
            orders = []

            while True:
                print(f"\n订单 {len(orders) + 1}:")
                qty_str = input("  数量 (回车结束): ").strip()
                if not qty_str:
                    break

                try:
                    qty = Decimal(qty_str)
                    price = Decimal(input("  单价: "))
                    orders.append(
                        {"quantity": qty, "unit_price": price, "processes": ["氧化"]}
                    )
                except Exception:
                    print("  [错误] 输入无效")

            if orders:
                result = calc.calculate_batch_orders(orders)

                print("\n" + "=" * 70)
                print("批量计算结果:")
                print("=" * 70)
                print(f"  订单数: {len(result['orders'])}")
                print(f"  总金额: ¥{result['total_amount']:,.2f}")
                print(f"  委外成本: ¥{result['total_outsourcing']:,.2f}")
                print(f"  总利润: ¥{result['total_profit']:,.2f}")
                print(f"  平均利润率: {result['avg_margin']:.1f}%")
                print("=" * 70)


if __name__ == "__main__":
    interactive_calculator()
