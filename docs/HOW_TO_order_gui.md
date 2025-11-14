# Order Calculator GUI - How To Use

## Overview
The Order Calculator GUI helps you calculate and execute synthetic dividend orders using the Synthetic Dividend Algorithm. This tool provides an interactive interface for managing your positions with professional broker-style order displays and visual price analysis.

## First-Time Setup

### 1. Enter Your Position Details
- **Ticker**: Enter the stock symbol (e.g., NVDA, SPY)
- **Holdings**: Your current number of shares owned
- **Last Price**: The price you last bought or sold shares at
- **Current Price**: Today's current market price
- **SDN**: Synthetic Dividend Number (typically 2-8, controls bracket spacing)
- **Profit %**: Your target profit sharing percentage (typically 25-75%)
- **Bracket Seed**: Optional starting price for bracket calculations

### 2. Calculate Orders
Click the **"Calculate Orders"** button to generate buy and sell bracket orders based on your inputs.

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

### 2. Update Current Price
Only update the **Current Price** field with today's market price. All other settings remain from your last session.

### 3. Recalculate
Click **"Calculate Orders"** to update brackets based on the new price.

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
- All your position parameters
- BUY/SELL buttons for order execution
- Calculate Orders button

### Broker Orders Section (Upper Right)
- Read-only displays of broker-ready order syntax
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

- **SDN Values**: Lower SDN (2-4) = tighter brackets, higher SDN (6-8) = wider brackets
- **Bracket Seed**: Use when you want brackets to start at a specific price level
- **Profit %**: Higher percentages mean more aggressive profit-taking
- **Data Persistence**: All settings are automatically saved per ticker
- **Quick Updates**: On return visits, you typically only need to update the current price

## Algorithm Details

The Synthetic Dividend Algorithm creates a "bracket" trading strategy where:
- Buy orders are placed below current price
- Sell orders are placed above current price
- Orders are spaced geometrically using the SDN parameter
- Profit sharing determines how much profit is taken vs. reinvested

This creates an automated dollar-cost averaging system that buys low and sells high systematically.