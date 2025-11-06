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
