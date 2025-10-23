from dataclasses import dataclass
from typing import Union

import pandas as pd


@dataclass
class Stock:
    ticker: str
    quantity: int = 0

    def get_ticker(self) -> str:
        return self.ticker

    def get_quantity(self) -> int:
        return int(self.quantity)

    def calculate_investment_value(self, current_price: Union[float, int]) -> float:
        return float(self.quantity) * float(current_price)

    def value_series(self, price_series: "pd.Series") -> "pd.Series":
        """Return a pandas Series with the position value for each price point."""
        return price_series.astype(float) * int(self.quantity)

    def buy(self, amount: int) -> None:
        """Increase quantity by amount (int)."""
        self.quantity = int(self.quantity) + int(amount)

    def sell(self, amount: int) -> None:
        """Decrease quantity by amount (int), not going below zero."""
        self.quantity = max(0, int(self.quantity) - int(amount))

    def to_dict(self) -> dict:
        return {"ticker": self.ticker, "quantity": int(self.quantity)}

    def __str__(self) -> str:
        return f"Stock(ticker={self.ticker}, quantity={self.quantity})"
