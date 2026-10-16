import csv
import random
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CATALOG = [
    ("Аксессуары", "Рюкзак", 90, 52),
    ("Аксессуары", "Бутылка для воды", 25, 12),
    ("Аксессуары", "Поясная сумка", 40, 22),
    ("Одежда", "Футболка", 35, 18),
    ("Одежда", "Худи", 110, 66),
    ("Одежда", "Шорты", 45, 24),
    ("Инвентарь", "Мяч", 55, 30),
    ("Инвентарь", "Коврик", 50, 25),
    ("Инвентарь", "Скакалка", 20, 8),
]


def generate_sales():
    rng = random.Random(42)
    rows = []
    first_day = date(2026, 1, 1)
    for number in range(1, 241):
        category, product, price, cost = rng.choice(CATALOG)
        rows.append(
            {
                "order_id": f"ORD-{number:04d}",
                "date": (first_day + timedelta(days=rng.randrange(181))).isoformat(),
                "category": category,
                "product": product,
                "quantity": rng.randint(1, 4),
                "unit_price": price,
                "unit_cost": cost,
            }
        )
    return sorted(rows, key=lambda row: (row["date"], row["order_id"]))


def main():
    rows = generate_sales()
    output = ROOT / "data" / "sales.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Создано {len(rows)} демонстрационных заказов: {output}")


if __name__ == "__main__":
    main()
