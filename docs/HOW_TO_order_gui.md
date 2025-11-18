# Order Calculator GUI - How To Use

## Overview
The Order Calculator GUI helps you calculate and execute synthetic dividend orders using the Synthetic Dividend Algorithm. This tool provides an interactive interface for managing your positions with professional broker-style order displays and visual price analysis.

## First-Time Setup

### 1. Enter Your Position Details

**Your Position** (top row - most important):
- **Ticker**: Enter the stock symbol (e.g., NVDA, SPY)
- **Holdings**: Your current number of shares owned
- **Last Trade Price**: The price you last bought or sold shares at

**Strategy Settings**:
- **Start Date**: Beginning of price history period (default: 1 year ago)
- **End Date**: End of price history period (default: today)
- **Bracket Spacing**: Controls how tight or wide your buy/sell brackets are (2-8)
 - Lower numbers (2-4) = tighter brackets, more frequent trades
 - Higher numbers (6-8) = wider brackets, less frequent trades
- **Profit Sharing %**: Percentage of profits to take vs. reinvest (typically 25-75%)
 - Higher = more aggressive profit-taking
- **Starting Price**: Optional - lock bracket levels to a specific price point

### 2. Calculate Orders
Orders are calculated automatically as you type. The system fetches current price data and generates buy/sell bracket orders based on your inputs.

### 3. Review the Results
- **Broker Orders**: Read-only displays show the exact broker syntax for buy/sell orders
- **Price Chart**: Visual chart with:
 - Historical price data (log scale)
 - Buy/sell bracket lines (red/green dashed)
 - Last transaction price (blue solid)
 - Buy/sell signal dots from backtesting
 - Mathematical reference grid (powers of 2 and subdivisions)

## Returning User Workflow

### 1. Select Your Ticker
Use the dropdown to select a previously used ticker - all your settings will be automatically loaded.

### 2. Review Current Data
The system automatically fetches the latest market price based on your **End Date** (typically today). All settings remain from your last session.

### 3. Auto-Calculation
Orders are recalculated automatically when you change any field. No need to click a calculate button!

## Executing Orders

### BUY Button
- Executes the calculated buy order
- Adds shares to your holdings
- Updates last/current price to execution price
- Automatically recalculates new bracket orders

### SELL Button
- Executes the calculated sell order
- Removes shares from your holdings
- Updates last/current price to execution price
- Automatically recalculates new bracket orders

## Understanding the Interface

### Input Section (Left)
The input section is now organized into three clear groups:

1. **Your Position** - Current holdings and last trade price
2. **Strategy Settings** - Date range, bracket spacing, and profit sharing
3. **Actions** - BUY, SELL, and Help buttons

### Broker Orders Section (Upper Right)
- **Current Price**: Latest market price from your selected end date
- **Buy Order**: Ready-to-execute buy order in broker format
- **Sell Order**: Ready-to-execute sell order in broker format
- Format: `BUY TICKER QTY @ $PRICE = $AMOUNT`

### Chart Tab
- **Price Chart**: Historical data with brackets and signals
- **Order Details**: Detailed calculation breakdown

### Signal Visualization
- **Red dots**: Buy signals from backtesting
- **Green dots**: Sell signals from backtesting
- **Inset box**: Total buy/sell signal counts

### Reference Grid
- **Solid gray lines**: Powers of 2 ($1, $2, $4, $8, etc.)
- **Dashed gray lines**: 8 subdivisions between each power of 2

## Tips

- **Bracket Spacing**: Lower values (2-4) = tighter brackets (more trades), higher (6-8) = wider brackets (fewer trades)
- **Starting Price**: Use when you want to lock bracket levels to a specific price (advanced feature)
- **Profit Sharing**: Higher percentages mean more aggressive profit-taking
- **Data Persistence**: All settings are automatically saved per ticker
- **Auto-Calculation**: Orders update automatically as you type - no calculate button needed!
- **Quick Workflow**: Select ticker from dropdown → verify/adjust settings → execute BUY or SELL

## Algorithm Details

The Synthetic Dividend Algorithm creates a "bracket" trading strategy where:
- Buy orders are placed below current price
- Sell orders are placed above current price
- Orders are spaced geometrically using the Bracket Spacing parameter
- Profit Sharing determines how much profit is taken vs. reinvested

This creates a systematic approach to buying low and selling high with mathematical precision.