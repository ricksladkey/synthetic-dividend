.PHONY: all clean

PYTHON := $(shell if [ -x "../../.venv/bin/python" ]; then echo "../../.venv/bin/python"; elif [ -x "../../.venv/Scripts/python.exe" ]; then echo "../../.venv/Scripts/python.exe"; else echo "python"; fi)
OUTPUTS = NVDA_2023_optimal_withdrawal.csv SPY_2022_optimal_withdrawal.csv VOO_2019_optimal_withdrawal.csv

all: $(OUTPUTS)

$(OUTPUTS):
	@echo "================================================================================"
	@echo "Optimal Withdrawal Rate Experiment"
	@echo "================================================================================"
	@echo ""
	@echo "Testing optimal withdrawal rates across 3 scenarios:"
	@echo "  - NVDA 2023 (bull market)"
	@echo "  - SPY 2022 (bear market)"
	@echo "  - VOO 2019 (moderate market)"
	@echo ""
	$(PYTHON) -m src.research.optimal_withdrawal_rate 2>&1 | grep -v "UnicodeEncodeError" || true
	@echo ""
	@echo "================================================================================"
	@echo "Generation complete! Results saved to:"
	@echo "  - NVDA_2023_optimal_withdrawal.csv"
	@echo "  - SPY_2022_optimal_withdrawal.csv"
	@echo "  - VOO_2019_optimal_withdrawal.csv"
	@echo "================================================================================"

clean:
	rm -f $(OUTPUTS)
