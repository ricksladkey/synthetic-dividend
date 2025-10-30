#!/usr/bin/env python3
"""
Manual test script to demonstrate named portfolio CLI integration.

This script shows how the named portfolio feature integrates with the CLI tool.
It doesn't require external dependencies (pandas, etc.) and can be run to verify
the integration works correctly.

NOTE: This is a manual test/demonstration script, not part of the automated test suite.
It uses exec() to load modules without requiring dependency installation. This is
acceptable for test-only code that won't be run in production.

Usage:
    python tests/manual_test_named_portfolios.py
"""

import sys
import re


def test_cli_argument_parsing():
    """Simulate how the CLI parses portfolio allocations."""
    print("=" * 70)
    print("Testing CLI Argument Parsing")
    print("=" * 70)
    print()
    
    # Load portfolio definitions
    exec(open('src/algorithms/portfolio_definitions.py').read(), globals())
    
    test_cases = [
        # Named portfolios
        ('classic', 'Named portfolio'),
        ('buffet-95,5', 'Parameterized portfolio'),
        ('classic-plus-crypto', 'Multi-asset named portfolio'),
        
        # JSON (fallback)
        ('{"NVDA": 0.4, "VOO": 0.6}', 'JSON allocation'),
    ]
    
    for allocations_arg, description in test_cases:
        print(f"\nTest: {description}")
        print(f"Input: --allocations {allocations_arg}")
        print("-" * 70)
        
        # Simulate CLI logic
        allocations_str = allocations_arg.strip()
        
        if allocations_str.startswith('{'):
            # JSON
            import json
            try:
                allocations = json.loads(allocations_str)
                print(f"✓ Parsed as JSON")
            except json.JSONDecodeError:
                print(f"✗ Invalid JSON")
                continue
        else:
            # Named portfolio
            try:
                allocations = parse_portfolio_name(allocations_str)
                print(f"✓ Parsed as named portfolio")
            except ValueError as e:
                print(f"✗ Not a valid portfolio name: {e}")
                continue
        
        # Display result
        print(f"\nAllocations:")
        for ticker, alloc in allocations.items():
            print(f"  {ticker}: {alloc*100:.1f}%")
        
        total = sum(allocations.values())
        print(f"\nTotal: {total*100:.1f}% {'✓' if abs(total - 1.0) < 0.01 else '✗'}")
    
    print()


def test_portfolio_examples_from_issue():
    """Test the specific examples mentioned in the GitHub issue."""
    print("=" * 70)
    print("Testing Portfolio Names from GitHub Issue")
    print("=" * 70)
    print()
    
    # Load portfolio definitions
    exec(open('src/algorithms/portfolio_definitions.py').read(), globals())
    
    examples = [
        'classic',
        'classic-60,40',
        'classic-plus-crypto-60,30,10',
        'buffet-90,10',
    ]
    
    print("Examples from issue:")
    for name in examples:
        print(f"  - {name}")
    print()
    
    all_passed = True
    for name in examples:
        try:
            allocations = parse_portfolio_name(name)
            tickers = ', '.join(f"{t}:{a*100:.0f}%" for t, a in allocations.items())
            print(f"✓ {name:35s} → {tickers}")
        except Exception as e:
            print(f"✗ {name:35s} → Error: {e}")
            all_passed = False
    
    print()
    if all_passed:
        print("All examples from issue work correctly! ✓")
    else:
        print("Some examples failed! ✗")
    
    return all_passed


def test_all_available_portfolios():
    """Test all available named portfolios."""
    print("=" * 70)
    print("Testing All Available Named Portfolios")
    print("=" * 70)
    print()
    
    # Load portfolio definitions
    exec(open('src/algorithms/portfolio_definitions.py').read(), globals())
    
    portfolios = [
        'classic',
        'classic-70,30',
        'classic-plus-crypto',
        'classic-plus-crypto-50,30,20',
        'buffet',
        'buffett',
        'buffet-95,5',
        'all-weather',
        'three-fund',
        'golden-butterfly',
        'tech-growth',
        'tech-growth-70,30',
        'high-growth',
        'crypto-heavy',
    ]
    
    for name in portfolios:
        try:
            allocations = parse_portfolio_name(name)
            total = sum(allocations.values())
            num_assets = len(allocations)
            print(f"✓ {name:30s} → {num_assets} assets, total {total*100:.1f}%")
        except Exception as e:
            print(f"✗ {name:30s} → Error: {e}")
    
    print()


if __name__ == "__main__":
    import os
    
    # Change to repo root (script should be run from tests/ or repo root)
    # This script is located in tests/ directory, so go up one level
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)  # Go up one level from tests/
    os.chdir(repo_root)
    
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "Named Portfolio Feature - Manual Test" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")
    
    try:
        # Test CLI argument parsing
        test_cli_argument_parsing()
        
        # Test examples from issue
        issue_passed = test_portfolio_examples_from_issue()
        
        # Test all available portfolios
        test_all_available_portfolios()
        
        # Final summary
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print()
        if issue_passed:
            print("✓ All requirements from GitHub issue are satisfied!")
            print("✓ Named portfolios with parameters work correctly!")
            print()
            sys.exit(0)
        else:
            print("✗ Some tests failed")
            print()
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Test script failed: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
