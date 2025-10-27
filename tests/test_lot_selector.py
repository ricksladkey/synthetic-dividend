"""Tests for lot selection strategies."""

import pytest
from datetime import date
from src.models.lot_selector import (
    get_selector,
    available_strategies,
    FIFOSelector,
    LIFOSelector,
    HighestCostSelector,
    LowestCostSelector,
)
from src.models.holding import Transaction


@pytest.fixture
def sample_transactions():
    """Create sample transactions for testing lot selection."""
    return [
        # Oldest purchase (lowest cost)
        Transaction(
            transaction_type='BUY',
            shares=100,
            purchase_date=date(2024, 1, 1),
            purchase_price=100.0,
            notes="First buy"
        ),
        # Middle purchase (medium cost)
        Transaction(
            transaction_type='BUY',
            shares=50,
            purchase_date=date(2024, 6, 1),
            purchase_price=150.0,
            notes="Second buy"
        ),
        # Newest purchase (highest cost)
        Transaction(
            transaction_type='BUY',
            shares=75,
            purchase_date=date(2024, 12, 1),
            purchase_price=200.0,
            notes="Third buy"
        ),
    ]


def test_fifo_selector_name():
    """Test FIFO selector returns correct name."""
    selector = FIFOSelector()
    assert selector.name() == "FIFO"


def test_lifo_selector_name():
    """Test LIFO selector returns correct name."""
    selector = LIFOSelector()
    assert selector.name() == "LIFO"


def test_fifo_selects_oldest_first(sample_transactions):
    """Test FIFO selects transactions from oldest to newest."""
    selector = FIFOSelector()
    lots = list(selector.select_lots(sample_transactions))
    
    # Should get all 3 in chronological order
    assert len(lots) == 3
    assert lots[0].purchase_date == date(2024, 1, 1)
    assert lots[1].purchase_date == date(2024, 6, 1)
    assert lots[2].purchase_date == date(2024, 12, 1)


def test_lifo_selects_newest_first(sample_transactions):
    """Test LIFO selects transactions from newest to oldest."""
    selector = LIFOSelector()
    lots = list(selector.select_lots(sample_transactions))
    
    # Should get all 3 in reverse chronological order
    assert len(lots) == 3
    assert lots[0].purchase_date == date(2024, 12, 1)
    assert lots[1].purchase_date == date(2024, 6, 1)
    assert lots[2].purchase_date == date(2024, 1, 1)


def test_highest_cost_selects_by_price(sample_transactions):
    """Test HIGHEST_COST selects most expensive lots first."""
    selector = HighestCostSelector()
    lots = list(selector.select_lots(sample_transactions))
    
    # Should get all 3 sorted by price descending
    assert len(lots) == 3
    assert lots[0].purchase_price == 200.0  # Highest
    assert lots[1].purchase_price == 150.0  # Middle
    assert lots[2].purchase_price == 100.0  # Lowest


def test_lowest_cost_selects_by_price(sample_transactions):
    """Test LOWEST_COST selects cheapest lots first."""
    selector = LowestCostSelector()
    lots = list(selector.select_lots(sample_transactions))
    
    # Should get all 3 sorted by price ascending
    assert len(lots) == 3
    assert lots[0].purchase_price == 100.0  # Lowest
    assert lots[1].purchase_price == 150.0  # Middle
    assert lots[2].purchase_price == 200.0  # Highest


def test_selectors_skip_closed_transactions(sample_transactions):
    """Test that all selectors skip closed transactions."""
    # Close the middle transaction
    sample_transactions[1].close(sale_date=date(2024, 7, 1), sale_price=160.0)
    
    fifo = FIFOSelector()
    lifo = LIFOSelector()
    
    fifo_lots = list(fifo.select_lots(sample_transactions))
    lifo_lots = list(lifo.select_lots(sample_transactions))
    
    # Both should only return 2 open transactions
    assert len(fifo_lots) == 2
    assert len(lifo_lots) == 2
    
    # Neither should include the closed transaction
    for lot in fifo_lots + lifo_lots:
        assert lot.purchase_price != 150.0


def test_selectors_skip_sell_transactions():
    """Test that selectors only return BUY transactions."""
    transactions = [
        Transaction(
            transaction_type='BUY',
            shares=100,
            purchase_date=date(2024, 1, 1),
            purchase_price=100.0,
        ),
        Transaction(
            transaction_type='SELL',
            shares=50,
            purchase_date=date(2024, 2, 1),
            purchase_price=110.0,
            sale_date=date(2024, 2, 1),
            sale_price=110.0,
        ),
        Transaction(
            transaction_type='BUY',
            shares=75,
            purchase_date=date(2024, 3, 1),
            purchase_price=105.0,
        ),
    ]
    
    selector = FIFOSelector()
    lots = list(selector.select_lots(transactions))
    
    # Should only get the 2 BUY transactions
    assert len(lots) == 2
    assert all(lot.transaction_type == 'BUY' for lot in lots)


def test_get_selector_fifo():
    """Test get_selector returns correct FIFO instance."""
    selector = get_selector('FIFO')
    assert isinstance(selector, FIFOSelector)
    assert selector.name() == 'FIFO'


def test_get_selector_lifo():
    """Test get_selector returns correct LIFO instance."""
    selector = get_selector('LIFO')
    assert isinstance(selector, LIFOSelector)
    assert selector.name() == 'LIFO'


def test_get_selector_highest_cost():
    """Test get_selector returns correct HIGHEST_COST instance."""
    selector = get_selector('HIGHEST_COST')
    assert isinstance(selector, HighestCostSelector)
    assert selector.name() == 'HIGHEST_COST'


def test_get_selector_lowest_cost():
    """Test get_selector returns correct LOWEST_COST instance."""
    selector = get_selector('LOWEST_COST')
    assert isinstance(selector, LowestCostSelector)
    assert selector.name() == 'LOWEST_COST'


def test_get_selector_invalid_strategy():
    """Test get_selector raises error for invalid strategy."""
    with pytest.raises(ValueError) as exc_info:
        get_selector('INVALID_STRATEGY')
    
    assert "Unknown lot selection strategy 'INVALID_STRATEGY'" in str(exc_info.value)
    assert "Available:" in str(exc_info.value)


def test_available_strategies():
    """Test available_strategies returns all registered strategies."""
    strategies = available_strategies()
    
    assert 'FIFO' in strategies
    assert 'LIFO' in strategies
    assert 'HIGHEST_COST' in strategies
    assert 'LOWEST_COST' in strategies
    assert len(strategies) == 4


def test_selector_returns_iterator(sample_transactions):
    """Test that select_lots returns an iterator, not a list."""
    selector = FIFOSelector()
    result = selector.select_lots(sample_transactions)
    
    # Should be an iterator
    assert hasattr(result, '__iter__')
    assert hasattr(result, '__next__')
    
    # Can be consumed
    lots = list(result)
    assert len(lots) == 3
