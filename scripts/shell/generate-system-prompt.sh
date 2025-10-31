#!/bin/bash
# Generate concatenated system prompt from theory documentation
#
# Usage:
#   ./generate-system-prompt.sh [quick|full]
#
# Options:
#   quick - Essential theory only (INVESTING_THEORY + VOLATILITY_ALPHA_THESIS)
#   full  - Complete framework (all theory documents)
#   (default: full)

MODE="${1:-full}"
OUTPUT_DIR="./output"
mkdir -p "$OUTPUT_DIR"

echo "Generating system prompt (mode: $MODE)..."

if [ "$MODE" = "quick" ]; then
    OUTPUT_FILE="$OUTPUT_DIR/system-prompt-quick.md"
    
    cat > "$OUTPUT_FILE" << 'EOF'
# Synthetic Dividend Algorithm - Quick Theory Reference

This is a condensed system prompt containing the essential theoretical foundation.
For complete context, see the full system prompt or individual theory documents.

---

EOF
    
    cat theory/INVESTING_THEORY.md >> "$OUTPUT_FILE"
    echo -e "\n\n---\n\n" >> "$OUTPUT_FILE"
    cat theory/VOLATILITY_ALPHA_THESIS.md >> "$OUTPUT_FILE"
    
    echo "✓ Quick system prompt generated: $OUTPUT_FILE"
    echo "  ($(wc -l < "$OUTPUT_FILE") lines)"
    
else
    OUTPUT_FILE="$OUTPUT_DIR/system-prompt-full.md"
    
    cat > "$OUTPUT_FILE" << 'EOF'
# Synthetic Dividend Algorithm - Complete Theoretical Framework

This is a comprehensive system prompt containing the complete theoretical foundation
for the Synthetic Dividend Algorithm. Use this to provide full context to AI assistants
working on this project.

Generated from theory/ folder documentation.

---

EOF
    
    # Concatenate in recommended reading order
    echo "## 1. Core Investment Theory" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    cat theory/INVESTING_THEORY.md >> "$OUTPUT_FILE"
    
    echo -e "\n\n---\n\n" >> "$OUTPUT_FILE"
    echo "## 2. Mathematical Foundations (Volatility Alpha Thesis)" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    cat theory/VOLATILITY_ALPHA_THESIS.md >> "$OUTPUT_FILE"
    
    echo -e "\n\n---\n\n" >> "$OUTPUT_FILE"
    echo "## 3. Metrics Interpretation Framework" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    cat theory/RETURN_METRICS_ANALYSIS.md >> "$OUTPUT_FILE"
    
    echo -e "\n\n---\n\n" >> "$OUTPUT_FILE"
    echo "## 4. Opportunity Cost Theory" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    cat theory/INITIAL_CAPITAL_THEORY.md >> "$OUTPUT_FILE"
    
    echo -e "\n\n---\n\n" >> "$OUTPUT_FILE"
    echo "## 5. Multi-Stock Portfolio Vision" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    cat theory/PORTFOLIO_VISION.md >> "$OUTPUT_FILE"
    
    echo -e "\n\n---\n\n" >> "$OUTPUT_FILE"
    echo "## 6. Development Philosophy" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    cat theory/CODING_PHILOSOPHY.md >> "$OUTPUT_FILE"
    
    echo "✓ Full system prompt generated: $OUTPUT_FILE"
    echo "  ($(wc -l < "$OUTPUT_FILE") lines)"
fi

echo ""
echo "You can now use this file as a system prompt for AI assistants."
echo "Example: cat $OUTPUT_FILE | pbcopy  # (macOS)"
echo "         cat $OUTPUT_FILE | clip     # (Windows)"
