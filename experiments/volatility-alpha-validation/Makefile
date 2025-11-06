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
