"""Расчёт экономики ВУ·Пакета. Все входные значения — допущения, их нужно заменить измерениями."""
RATE = 84.20            # ₽ за $1, ЦБ РФ на 20.09.2026
TARGET = 300 * RATE     # $300 в рублях
FEE = 0.035             # комиссия ЮKassa по картам (тариф «от 3,5%»; СБП дешевле — считаем консервативно)
REFUND = 0.05           # доля возвратов (допущение); комиссию при возврате считаем невозвращаемой
FIXED = 700             # ₽/мес: VPS ~600 + домен ~100 (0 ₽ за VPS, если ставить на существующий сервер)


def month(price, sales, cac=None, ads=None):
    revenue = price * sales
    fees = revenue * FEE
    refunds = revenue * REFUND
    ads = ads if ads is not None else cac * sales
    profit = revenue - fees - refunds - ads - FIXED
    return dict(price=price, sales=sales, revenue=revenue, fees=fees, refunds=refunds, ads=ads, fixed=FIXED, profit=profit)


def net_per_sale(price):
    return price * (1 - REFUND) - price * FEE


def fmt(x):
    return f"{x:,.0f}".replace(",", " ")


if __name__ == "__main__":
    print(f"$300 = {fmt(TARGET)} ₽")
    for price in (1990, 2490, 2990):
        n = net_per_sale(price)
        print(f"\nЦена {price}: чистыми с продажи {fmt(n)} ₽; для $300 выручки нужно {TARGET / price:.1f} продаж")
        for cac in (0, 500, 1000, 1500, 2000):
            need = (TARGET + FIXED) / (n - cac) if n > cac else float("inf")
            print(f"  CAC {cac:>5}: для $300 прибыли нужно {need:5.1f} продаж/мес, реклама {fmt(need * cac)} ₽")
    print("\nCAC = CPC / конверсия клик→оплата (₽)")
    crs = (0.005, 0.01, 0.02, 0.03, 0.05)
    print("CPC  " + "".join(f"{c:>8.1%}" for c in crs))
    for cpc in (15, 30, 50, 80, 120):
        print(f"{cpc:>4} " + "".join(f"{fmt(cpc / c):>8}" for c in crs))
    print("\nСценарии, цена 2490")
    for name, kw in [("Консервативный", dict(sales=6, cac=1800)), ("Базовый", dict(sales=15, cac=1000)),
                     ("Оптимистичный", dict(sales=30, cac=700))]:
        m = month(2490, **kw)
        print(name, {k: fmt(v) for k, v in m.items()}, f"= ${m['profit'] / RATE:.0f}")
    print("\nПервые 3 месяца (базовый, сезон окт–дек 2026)")
    total = 0
    for name, sales, ads in [("Октябрь (тест $100)", 4, 8420), ("Ноябрь", 12, 14000), ("Декабрь", 20, 20000)]:
        m = month(2490, sales, ads=ads)
        total += m["profit"]
        print(name, {k: fmt(v) for k, v in m.items()}, f"= ${m['profit'] / RATE:.0f}")
    print(f"Итого за 3 месяца: {fmt(total)} ₽ = ${total / RATE:.0f}")
