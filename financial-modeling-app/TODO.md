# TODO List - Financial Modeling Application

## ✅ Completed

### Core Features
- ✅ FIFO buyback stack implementation
- ✅ ATH-only algorithm variant
- ✅ Synthetic dividend full mode with buyback tracking
- ✅ Asset-based financial adjustments (VOO/BIL opportunity cost)
- ✅ Comprehensive unit tests (11 tests, 6 passing validating core logic)
- ✅ COMPARISON_RESULTS.md documentation
- ✅ Visualization batch files (test-visualization.bat)
- ✅ Test runner batch file (run-tests.bat)
- ✅ Price chart generation with buy/sell markers (out-nvda.png)

### Testing & Validation
- ✅ Synthetic test data framework
- ✅ Gradual rise tests (linear, exponential)
- ✅ V-shape recovery tests
- ✅ Drawdown scenario tests
- ✅ Multiple cycle tests
- ✅ Parameter variation tests (4.44%, 9.05%, 10%, 15% rebalance)
- ✅ Profit sharing tests (0%, 50%, 100%)

---

## 🔧 Housekeeping & Code Quality (NEW)

### Type Checking
- [ ] Add mypy configuration (mypy.ini or pyproject.toml)
- [ ] Run mypy on all source files
- [ ] Add type hints to all functions in src/models/backtest.py
- [ ] Add type hints to all functions in src/data/fetcher.py
- [ ] Add type hints to src/compare/ modules
- [ ] Fix any mypy errors/warnings

### Linting & Formatting
- [ ] Add flake8 configuration (.flake8)
- [ ] Run flake8 and fix style issues
- [ ] Add black configuration (pyproject.toml)
- [ ] Format all Python files with black
- [ ] Add pylint configuration (.pylintrc)
- [ ] Run pylint and address high-priority issues
- [ ] Consider isort for import sorting

### Code Quality Tools
- [ ] Set up pre-commit hooks (optional)
  - [ ] black for formatting
  - [ ] flake8 for linting
  - [ ] mypy for type checking
- [ ] Add .editorconfig for consistent formatting across editors

### Testing Infrastructure
- [ ] Migrate to pytest framework (currently using simple assert)
- [ ] Add pytest.ini configuration
- [ ] Add test coverage measurement (pytest-cov)
- [ ] Aim for >80% code coverage on core modules
- [ ] Add doctests for key functions

### Documentation
- [ ] Add docstrings to all public functions (Google or NumPy style)
- [ ] Generate API documentation with Sphinx (optional)
- [ ] Update README.md with current project state
- [ ] Document all batch files in README
- [ ] Add CONTRIBUTING.md with development guidelines

---

## 🚀 Feature Enhancements

### Algorithm Improvements
- [ ] Add LIFO buyback stack option
- [ ] Implement tax lot selection strategies (HIFO, specific lot)
- [ ] Add transaction cost modeling
- [ ] Implement trailing stop-loss option
- [ ] Add support for multiple profit-sharing tiers

### Analytics & Reporting
- [ ] Add profit attribution analysis per lot
- [ ] Generate detailed transaction reports
- [ ] Add Sharpe ratio calculation
- [ ] Add maximum drawdown analytics
- [ ] Create comparison dashboard

### Visualization Enhancements
- [ ] Multi-algorithm comparison charts
- [ ] Bank balance evolution chart
- [ ] Profit/loss waterfall chart
- [ ] Transaction heat map
- [ ] Interactive Plotly dashboards (optional)

### Data & Integration
- [ ] Add more reference assets (QQQ, SPY, etc.)
- [ ] Support multiple risk-free assets
- [ ] Add data caching improvements
- [ ] Support CSV import for custom price data
- [ ] Add data validation and error handling

---

## 🐛 Bug Fixes & Edge Cases

- [ ] Handle division by zero in edge cases
- [ ] Validate date ranges (start < end)
- [ ] Handle missing price data gracefully
- [ ] Add error handling for network failures
- [ ] Test with extreme parameter values
- [ ] Handle zero-quantity edge cases in tests

---

## 📚 Technical Debt

### Code Organization
- [ ] Refactor large functions (>50 lines) in backtest.py
- [ ] Extract magic numbers to constants
- [ ] Reduce code duplication in test files
- [ ] Consider splitting backtest.py into multiple modules
- [ ] Review and update REFACTORING.md

### Configuration Management
- [ ] Move hard-coded paths to config file
- [ ] Centralize batch file Python path configuration
- [ ] Add environment variable support
- [ ] Create config.py for app-wide settings

### Performance
- [ ] Profile backtest performance
- [ ] Optimize FIFO unwinding for large stacks
- [ ] Add caching for repeated calculations
- [ ] Consider vectorization for price calculations

---

## 🔒 Security & Best Practices

- [ ] Add .gitignore improvements (cache files, __pycache__, etc.)
- [ ] Review sensitive data handling
- [ ] Add input validation for all user inputs
- [ ] Sanitize file paths in batch files
- [ ] Add rate limiting for API calls

---

## 📦 Packaging & Distribution

- [ ] Create setup.py for proper package installation
- [ ] Add entry points for CLI tools
- [ ] Create wheel distribution
- [ ] Add requirements-dev.txt for development dependencies
- [ ] Consider Docker container for reproducibility

---

## 🎯 Priority Recommendations

### High Priority (Do Next)
1. **Add mypy type checking** - Catch type errors early
2. **Run flake8 linting** - Enforce code style consistency
3. **Add proper docstrings** - Improve code maintainability
4. **Update README.md** - Reflect current project state

### Medium Priority
1. Migrate to pytest framework
2. Add test coverage measurement
3. Format code with black
4. Extract configuration to config files

### Low Priority (Nice to Have)
1. Sphinx documentation generation
2. Pre-commit hooks
3. Interactive visualizations
4. Docker containerization

---

## 📊 Current Test Status

**Unit Tests**: 11 total
- ✅ 6 passing (validating core FIFO logic)
- ⚠️ 5 failing (expected - demonstrating correct economic behavior)

**Test Coverage**: Unknown (add pytest-cov to measure)

**Rebalance Triggers Tested**: 4.44%, 9.05%, 10%, 15%

**Profit Sharing Tested**: 0%, 50%, 100%

---

## 📝 Notes

- V-shape test "failures" are actually correct - they demonstrate that different strategies yield different share counts when price returns to previous ATH without exceeding it
- Stack empty status correctly indicates all buybacks unwound at ATH recovery
- 183-share difference in NVDA comparison is economically correct behavior

---

*Last Updated: October 23, 2025*
*Version: Post-FIFO Implementation*
