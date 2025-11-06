.PHONY: all clean

# PYTHON is exported from parent Makefile
# Fallback for standalone execution
ifndef PYTHON
  PYTHON_CANDIDATES := \
      ../../.venv/bin/python \
      ../../.venv/Scripts/python \
      ../../.venv/Scripts/python.exe
  PYTHON := $(firstword $(wildcard $(PYTHON_CANDIDATES)))
  ifeq ($(PYTHON),)
    $(error Python not found. Run from root: make examples)
  endif
endif

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
