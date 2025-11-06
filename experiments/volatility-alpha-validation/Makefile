.PHONY: all clean

PYTHON = $(shell if [ -f ../../.venv/bin/python ]; then echo ../../.venv/bin/python; elif [ -f ../../.venv/Scripts/python.exe ]; then echo ../../.venv/Scripts/python.exe; else echo python; fi)
OUTPUT_CSV = volatility_alpha_table.csv

all: $(OUTPUT_CSV)

$(OUTPUT_CSV):
	@echo "================================================================================"
	@echo "Volatility Alpha Validation Dataset Generator"
	@echo "================================================================================"
	@echo ""
	@echo "Analyzing 6 assets (NVDA, MSTR, BTC-USD, ETH-USD, PLTR, GLD)"
	@echo "Timeframes: 1, 2, and 3 years"
	@echo ""
	$(PYTHON) -m src.research.volatility_alpha_table
	@echo ""
	@echo "================================================================================"
	@echo "✅ Generation complete! Results saved to: $(OUTPUT_CSV)"
	@echo "================================================================================"

clean:
	rm -f $(OUTPUT_CSV)
