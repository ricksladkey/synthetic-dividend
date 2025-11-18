#!/usr/bin/env python3
"""Remove emojis from markdown files for better compatibility and professionalism.

This script replaces emojis with text equivalents to avoid:
- Encoding issues (cp1252, ascii, etc.)
- Terminal rendering problems
- Copy-paste breaking scripts
- Accessibility issues with screen readers
"""

import sys
from pathlib import Path

# Emoji replacements (emoji -> text)
EMOJI_REPLACEMENTS = {
    # Checkmarks and status
    '✅': '[OK]',
    '❌': '[FAIL]',
    '✓': '[OK]',
    '✗': '[FAIL]',

    # Symbols
    '🎯': '',  # Remove decorative
    '📦': '',
    '🚀': '',
    '🛠️': '',
    '🛠': '',
    '🐳': '',
    '🔧': '',
    '🔑': '',
    '📚': '',
    '🌍': '',
    '🤖': '',
    '✨': '',
    '⚠️': 'WARNING:',
    '⚠': 'WARNING:',
    '💡': 'TIP:',
    '📋': '',
    '🐍': '',
    '⚙️': '',
    '🔒': '',
    '📈': '',
    '💰': '',
    '📊': '',
    '🏆': '',
    '💻': '',
    '🎨': '',
    '🔥': '',
}


def remove_emojis_from_file(file_path: Path, dry_run: bool = False) -> tuple[int, bool]:
    """Remove emojis from a single file.

    Returns:
        (replacements_made, file_modified)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return 0, False

    original_content = content
    replacements = 0

    for emoji, replacement in EMOJI_REPLACEMENTS.items():
        if emoji in content:
            count = content.count(emoji)
            content = content.replace(emoji, replacement)
            replacements += count

    # Clean up multiple spaces left by removed emojis
    import re
    content = re.sub(r'  +', ' ', content)  # Multiple spaces -> single space
    content = re.sub(r' \n', '\n', content)  # Space before newline -> just newline
    content = re.sub(r'\n\n\n+', '\n\n', content)  # Multiple blank lines -> double

    if content != original_content:
        if dry_run:
            print(f"[DRY RUN] {file_path}: {replacements} emoji replacements")
        else:
            file_path.write_text(content, encoding='utf-8')
            print(f"Updated {file_path}: {replacements} emoji replacements")
        return replacements, True

    return 0, False


def main():
    """Remove emojis from all markdown files."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be changed without modifying files')
    parser.add_argument('paths', nargs='*', default=['.'],
                        help='Paths to process (default: current directory)')
    args = parser.parse_args()

    total_files = 0
    modified_files = 0
    total_replacements = 0

    for path_str in args.paths:
        path = Path(path_str)

        if path.is_file():
            files = [path]
        else:
            # Find all markdown files
            files = list(path.rglob('*.md'))

        for file_path in files:
            replacements, modified = remove_emojis_from_file(file_path, args.dry_run)
            total_files += 1
            if modified:
                modified_files += 1
                total_replacements += replacements

    print()
    print(f"Summary:")
    print(f"  Total files processed: {total_files}")
    print(f"  Files modified: {modified_files}")
    print(f"  Total emoji replacements: {total_replacements}")

    if args.dry_run:
        print()
        print("This was a dry run. Use without --dry-run to actually modify files.")


if __name__ == '__main__':
    main()
