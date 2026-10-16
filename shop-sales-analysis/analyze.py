from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
INPUT_FILE = ROOT / "data" / "sales.csv"
OUTPUT_DIR = ROOT / "reports"
REQUIRED_COLUMNS = {
    "order_id",
    "date",
    "category",
    "product",
    "quantity",
    "unit_price",
    "unit_cost",
}


def prepare_sales(data):
    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(f"Не хватает столбцов: {', '.join(sorted(missing))}")
    if data.empty:
        raise ValueError("В файле нет продаж.")
    data = data.copy()
    if data[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("В обязательных столбцах есть пропуски.")
    if data["order_id"].duplicated().any():
        raise ValueError("Номера заказов повторяются: ожидается одна строка на заказ.")
    for column in ["order_id", "category", "product"]:
        if data[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"В столбце {column} есть пустые значения.")

    data["date"] = pd.to_datetime(data["date"], format="%Y-%m-%d", errors="raise")
    for column in ["quantity", "unit_price", "unit_cost"]:
        data[column] = pd.to_numeric(data[column], errors="raise")
        if data[column].isin([float("inf"), float("-inf")]).any():
            raise ValueError(f"В столбце {column} есть бесконечное значение.")
    if (data["quantity"] <= 0).any() or (data["quantity"] % 1 != 0).any():
        raise ValueError("Количество должно быть целым положительным числом.")
    if (data["unit_price"] <= 0).any() or (data["unit_cost"] < 0).any():
        raise ValueError(
            "Цена должна быть положительной, себестоимость — неотрицательной."
        )

    data["quantity"] = data["quantity"].astype(int)
    data["revenue"] = data["quantity"] * data["unit_price"]
    data["cost"] = data["quantity"] * data["unit_cost"]
    data["gross_profit"] = data["revenue"] - data["cost"]
    data["month"] = data["date"].dt.to_period("M").astype(str)
    return data.sort_values(["date", "order_id"]).reset_index(drop=True)


def build_summary(data):
    revenue = float(data["revenue"].sum())
    profit = float(data["gross_profit"].sum())
    return {
        "period_start": data["date"].min().strftime("%Y-%m-%d"),
        "period_end": data["date"].max().strftime("%Y-%m-%d"),
        "orders": len(data),
        "units_sold": int(data["quantity"].sum()),
        "revenue": round(revenue, 2),
        "cost": round(float(data["cost"].sum()), 2),
        "gross_profit": round(profit, 2),
        "average_order": round(revenue / len(data), 2),
        "gross_margin_percent": round(profit / revenue * 100, 2),
    }


def build_tables(data):
    monthly = data.groupby("month", as_index=False).agg(
        orders=("order_id", "count"),
        revenue=("revenue", "sum"),
        gross_profit=("gross_profit", "sum"),
    )
    categories = (
        data.groupby("category", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            gross_profit=("gross_profit", "sum"),
        )
        .sort_values("revenue", ascending=False)
    )
    products = (
        data.groupby("product", as_index=False)
        .agg(
            units_sold=("quantity", "sum"),
            revenue=("revenue", "sum"),
        )
        .sort_values(["units_sold", "product"], ascending=[False, True])
    )
    return monthly, categories, products


def save_dashboard(monthly, categories, products, output_path):
    plt.style.use("ggplot")
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), layout="constrained")
    period = f"{monthly['month'].iloc[0]} — {monthly['month'].iloc[-1]}"
    fig.suptitle(f"Анализ продаж · {period}", fontsize=17)

    axes[0, 0].plot(monthly["month"], monthly["revenue"], marker="o", color="#2563eb")
    axes[0, 0].set_title("Выручка по месяцам")
    axes[0, 0].set_ylabel("Условные единицы")
    axes[0, 0].tick_params(axis="x", rotation=25)

    ordered_categories = categories.sort_values("revenue")
    axes[0, 1].barh(
        ordered_categories["category"], ordered_categories["revenue"], color="#0d9488"
    )
    axes[0, 1].set_title("Выручка по категориям")
    axes[0, 1].set_xlabel("Условные единицы")

    top_products = products.head(5).sort_values("units_sold")
    axes[1, 0].barh(
        top_products["product"], top_products["units_sold"], color="#7c3aed"
    )
    axes[1, 0].set_title("Топ-5 товаров по количеству")
    axes[1, 0].set_xlabel("Продано единиц")

    axes[1, 1].bar(monthly["month"], monthly["gross_profit"], color="#ea580c")
    axes[1, 1].set_title("Валовая прибыль по месяцам")
    axes[1, 1].set_ylabel("Условные единицы")
    axes[1, 1].tick_params(axis="x", rotation=25)

    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main():
    try:
        data = prepare_sales(pd.read_csv(INPUT_FILE))
    except (OSError, ValueError, pd.errors.ParserError) as error:
        raise SystemExit(f"Ошибка входных данных: {error}")

    summary = build_summary(data)
    monthly, categories, products = build_tables(data)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(
        OUTPUT_DIR / "monthly.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.2f",
    )
    categories.to_csv(
        OUTPUT_DIR / "categories.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.2f",
    )
    products.to_csv(
        OUTPUT_DIR / "products.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.2f",
    )
    pd.DataFrame([summary]).to_csv(
        OUTPUT_DIR / "summary.csv", index=False, encoding="utf-8-sig"
    )
    save_dashboard(monthly, categories, products, OUTPUT_DIR / "dashboard.png")

    print(f"Период: {summary['period_start']} — {summary['period_end']}")
    print(f"Заказов: {summary['orders']}; продано единиц: {summary['units_sold']}")
    print(f"Выручка: {summary['revenue']:,.2f} у.е.")
    print(f"Валовая прибыль: {summary['gross_profit']:,.2f} у.е.")
    print(f"Средний чек: {summary['average_order']:,.2f} у.е.")
    print(f"Валовая рентабельность продаж: {summary['gross_margin_percent']:.2f}%")
    print(f"Лидер по выручке: {categories.iloc[0]['category']}")
    print(f"Отчёты: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
