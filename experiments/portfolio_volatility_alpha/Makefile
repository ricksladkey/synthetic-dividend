.PHONY: all clean

PYTHON = ../../.venv/Scripts/python.exe
OUTPUT_CSV = results.csv
OUTPUT_SUMMARY = SUMMARY.md

all: $(OUTPUT_CSV)

$(OUTPUT_CSV):
	@echo "================================================================================"
	@echo "Portfolio Volatility Alpha Experiment"
	@echo "================================================================================"
	@echo ""
	@echo "Testing 5-asset portfolio (NVDA, GOOG, PLTR, BTC-USD, ETH-USD) vs VOO baseline"
	@echo "Period: 2023-01-01 to 2024-12-31"
	@echo ""
	$(PYTHON) -m src.research.portfolio_volatility_alpha
	@echo ""
	@echo "================================================================================"
	@echo "Generation complete! Results saved to: $(OUTPUT_CSV) and $(OUTPUT_SUMMARY)"
	@echo "================================================================================"

clean:
	rm -f $(OUTPUT_CSV) $(OUTPUT_SUMMARY)
