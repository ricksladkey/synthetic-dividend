class Stock:
    def __init__(self, ticker, quantity):
        self.ticker = ticker
        self.quantity = quantity

    def get_ticker(self):
        return self.ticker

    def get_quantity(self):
        return self.quantity

    def calculate_investment_value(self, current_price):
        return self.quantity * current_price

    def __str__(self):
        return f"Stock(ticker={self.ticker}, quantity={self.quantity})"