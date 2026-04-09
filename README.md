# Developer Documentation Index

## C/C++ Code Formatting & Jenkins

### Quick Access Guide:

1. **🚨 Jenkins Failed? Start Here:**
   - [clang-format Quick Reference](./clang-format-quick-reference.md)
   - Fast fixes for common formatting errors
   - Copy-paste commands to fix issues

2. **📖 Deep Dive - Understanding Everything:**
   - [Complete clang-format & Jenkins Guide](./clang-format-jenkins-guide.md)
   - Line-by-line .clang-format explanation
   - How Jenkins validates your code
   - Error message interpretation

3. **🤖 Augment AI Rules (Auto-Applied):**
   - Global Rules: `~/.augment/rules/c-cpp-formatting.md`
   - These rules are automatically used by Augment AI when writing C/C++ code

---

## Document Summary

| Document | Size | Purpose |
|----------|------|---------|
| `clang-format-quick-reference.md` | 4.7 KB | Quick fixes, checklists, common issues |
| `clang-format-jenkins-guide.md` | 11 KB | Complete guide with detailed explanations |
| `~/.augment/rules/c-cpp-formatting.md` | 5.3 KB | Global AI coding rules (auto-applied) |

---

## Most Common Issues & Quick Fixes

### Issue 1: Extra Spaces in Macros
```bash
# Auto-fix:
clang-format -i -style=file <file>
```

### Issue 2: Function Brace Placement
```bash
# Auto-fix all modified files:
git diff --name-only | grep -E '\.(c|h)$' | xargs clang-format -i -style=file
```

### Issue 3: Multi-Statement Inline Functions
```bash
# Auto-fix:
clang-format -i -style=file <file>
```

---

## Your Project's Key Settings

- **Style Base**: Google C++ Style Guide
- **Column Limit**: 120 characters
- **Indentation**: 2 spaces
- **Function Braces**: New line (`AfterFunction: true`)
- **Control Braces**: Same line (`AfterControlStatement: false`)

---

## Useful Commands

```bash
# Format all modified C/C++ files (MOST USEFUL)
git diff --name-only | grep -E '\.(c|h)$' | xargs clang-format -i -style=file

# Check if file is correctly formatted
clang-format -style=file <file> | diff <file> - && echo "✅ OK" || echo "❌ NEEDS FORMATTING"

# Run full linter check (same as Jenkins)
make check_linters

# Format specific file
clang-format -i -style=file ap/src/wlan-drivers/ar/os_if/ar_os_if_ar_meta.h
```

---

## Setup Auto-Format in Your IDE

### VSCode
1. Install "C/C++" extension by Microsoft
2. Settings → Editor: Format On Save → Enable
3. Settings → C_Cpp: Clang_format_style → "file"

### CLion/IntelliJ IDEA
1. Settings → Editor → Code Style → C/C++
2. Click "Import Scheme" → ClangFormat
3. Enable "Format on Save"

### Vim
```vim
" Add to .vimrc
Plugin 'rhysd/vim-clang-format'
let g:clang_format#auto_format = 1
```

---

**Last Updated**: 2026-03-26  
**Project**: wifi-ap (Arista Networks)
