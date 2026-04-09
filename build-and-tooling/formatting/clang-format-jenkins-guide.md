# Understanding .clang-format and Jenkins Validation

## Overview
This document explains how clang-format works in your project and why Jenkins fails when code formatting is incorrect.

---

## Table of Contents
1. [Your Project's .clang-format Configuration](#your-projects-clang-format-configuration)
2. [How Jenkins Validates Code](#how-jenkins-validates-code)
3. [Understanding the Error Messages](#understanding-the-error-messages)
4. [How to Fix and Prevent Formatting Errors](#how-to-fix-and-prevent-formatting-errors)

---

## Your Project's .clang-format Configuration

### File Location: `.clang-format` (repository root)

```yaml
BasedOnStyle:  Google
---
Language:  Cpp

# This is to support perl annotations in server folder
TabWidth:  2
CommentPragmas:  '*'
ReflowComments:  false
AlignTrailingComments:  false

# Developer recommended settings
ColumnLimit:  120
SortIncludes:  false
BreakBeforeBraces:  Custom
BraceWrapping:
  AfterControlStatement:  false
  AfterEnum:  false
  AfterFunction:  true
  AfterStruct:  false
  AfterUnion:  false
  AfterExternBlock:  false
  BeforeElse:  false
  IndentBraces:  false
  SplitEmptyFunction:  true
  SplitEmptyRecord:  true

# Avoids arbitrary coding styles based on file
DerivePointerAlignment:  false
```

### Configuration Explained Line by Line:

#### 1. **BasedOnStyle: Google**
- Uses Google C++ Style Guide as the foundation
- Google style: 2-space indentation, 80-char limit (overridden below)
- Compact, readable style preferred by many projects

#### 2. **Language: Cpp**
- Applies these rules to C++ and C files (.c, .h, .cc, .cpp, .hpp)

#### 3. **TabWidth: 2**
- Indentation is 2 spaces (not tabs)
- **Why your code failed**: If you used tabs or 4 spaces, it would be reformatted

#### 4. **CommentPragmas: '*'**
- Treats all comments as pragmas (special compiler directives)
- **Result**: Comments are NOT reflowed or reformatted

#### 5. **ReflowComments: false**
- Does NOT automatically wrap/reflow long comments
- **Why**: Preserves manual comment formatting, especially for ASCII art or tables

#### 6. **AlignTrailingComments: false**
- Does NOT align trailing comments (comments at end of line)
```c
// Without alignment (your setting):
int x = 1;  // comment
int longer_var = 2;  // another comment

// With alignment (NOT your setting):
int x = 1;           // comment
int longer_var = 2;  // another comment
```

#### 7. **ColumnLimit: 120**
- **IMPORTANT**: Maximum line length is 120 characters
- Google default is 80, but your project uses 120
- **Why your code might fail**: Lines longer than 120 chars will be wrapped

#### 8. **SortIncludes: false**
- Does NOT automatically sort #include statements
- **Why**: Preserves manual ordering (some projects need specific include order)

#### 9. **BreakBeforeBraces: Custom**
- Uses custom brace placement rules (defined in BraceWrapping section)
- Overrides Google's default brace style

#### 10. **BraceWrapping Settings**:

**AfterControlStatement: false**
```c
// Your style (false):
if (condition) {
  code();
}

// If true:
if (condition)
{
  code();
}
```

**AfterEnum: false**
```c
// Your style (false):
enum Color {
  RED, GREEN, BLUE
};
```

**AfterFunction: true** ⭐ **CRITICAL**
```c
// Your style (true):
void function(int param)
{
  code();
}

// If false (Google default):
void function(int param) {
  code();
}
```
**Why your code failed**: This is a KEY difference from Google style!

**AfterStruct: false**
```c
// Your style (false):
struct Point {
  int x, y;
};
```

**SplitEmptyFunction: true**
```c
// Your style (true):
void empty()
{
}

// If false:
void empty() {}
```

**SplitEmptyRecord: true**
```c
// Your style (true):
struct Empty
{
};

// If false:
struct Empty {};
```

#### 11. **DerivePointerAlignment: false**
- Does NOT try to guess pointer alignment style from existing code
- Uses Google's default: `int* ptr` (asterisk with type, not variable)

---

## How Jenkins Validates Code

### The Validation Pipeline

Jenkins uses the `scripts/linter.mk` Makefile to check code formatting.

#### Step 1: Jenkins Calls `check_linters` Target
```makefile
# From scripts/linter.mk line 173-185
check_linters: ERR_FILE := $(shell mktemp)
check_linters: $(CLANG_FORMAT_BIN) ...
    @echo "=================="; \
    if [ -s $(ERR_FILE) ]; then \
        cat $(ERR_FILE); \
        rm -f $(ERR_FILE); \
        exit 1; \
    fi
```

#### Step 2: For Each Changed C/C++ File
```makefile
# From scripts/linter.mk line 104-106
elif [ "$@" = "$(CLANG_FORMAT_BIN)" ]; then \
    echo "$@: $$chk_file"; \
    $@ -style=file "$$chk_file" | diff ./$$chk_file -; \
```

**What this does:**
1. Runs `clang-format -style=file file.c` (formats the file based on .clang-format)
2. Pipes output to `diff` comparing formatted version vs. actual file
3. If there's ANY difference, `diff` exits with non-zero code
4. Error is logged to ERR_FILE

#### Step 3: Collect All Errors
```makefile
# From scripts/linter.mk line 142-144
if [ $$? -ne 0 ]; then \
    echo "$@ Error: $$chk_file" >> $(ERR_FILE); \
fi; \
```

#### Step 4: Jenkins Fails if ERR_FILE Not Empty
```makefile
if [ -s $(ERR_FILE) ]; then \
    cat $(ERR_FILE); \
    exit 1; \
fi
```

---

## Understanding the Error Messages

### Your Error Output Breakdown:

```
[2026-03-26T17:02:41.712Z] clang-format: ap/src/wlan-drivers/ar/os_if/ar_os_if_ar_meta.h
```
- Jenkins is checking this file

```
14,18c14,17
< #define AR_META_FLAG_IS_CLASSIFIED  (1 << 0)
< #define AR_META_FLAG_IS_RX  (1 << 1)
---
> #define AR_META_FLAG_IS_CLASSIFIED (1 << 0)
> #define AR_META_FLAG_IS_RX (1 << 1)
```

**What this means:**
- Lines 14-18 in your file need to change to lines 14-17
- `<` = Your current code (WRONG)
- `>` = What clang-format expects (CORRECT)
- **Issue**: Extra spaces between macro name and value

```
23,24c22,30
< static inline void ar_os_if_ar_meta_set_reserve(struct sk_buff* skb, uint8_t reserve) { skb->ar_meta.reserve = reserve; }
---
> static inline void ar_os_if_ar_meta_set_reserve(struct sk_buff* skb, uint8_t reserve)
> {
>   skb->ar_meta.reserve = reserve;
> }
```

**What this means:**
- Your one-liner function needs to be multi-line
- **Why**: Based on Google style + your custom settings
- **Reason**: Function bodies should start on new line after opening brace

```
fatal: ambiguous argument 'HEAD': unknown revision or path not in the working tree.
```
- Git command failed (not critical for understanding formatting)
- Likely git repository initialization issue

```
clang-format Error: ap/src/wlan-drivers/ar/os_if/ar_os_if_ar_meta.h
make: *** [/src/code.arista.io/mgmt/wifi-ap/scripts/linter.mk:177: check_linters] Error 1
```
- **Final result**: Jenkins build FAILED due to formatting errors

---

## How to Fix and Prevent Formatting Errors

### Method 1: Manual Fix (What We Did)
1. Identify formatting issues from diff output
2. Edit file manually to match expected format
3. Commit and push

### Method 2: Auto-Fix with clang-format (RECOMMENDED)
```bash
# Format a single file
clang-format -i -style=file ap/src/wlan-drivers/ar/os_if/ar_os_if_ar_meta.h

# Format all changed files in your branch
git diff --name-only HEAD | grep -E '\.(c|h|cpp|hpp|cc)$' | xargs clang-format -i -style=file

# Check without modifying (dry-run)
clang-format --dry-run --Werror -style=file <file>
```

### Method 3: Pre-Commit Hook
```bash
# Create .git/hooks/pre-commit
#!/bin/bash
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(c|h|cpp|hpp)$')
if [ -n "$FILES" ]; then
    clang-format -i -style=file $FILES
    git add $FILES
fi
```

### Method 4: IDE Integration
- **VSCode**: Install "C/C++" extension, enable "Format on Save"
- **CLion/IntelliJ**: Settings → Editor → Code Style → Import .clang-format
- **Vim**: Use vim-clang-format plugin
- **Emacs**: Use clang-format.el

---

## Common Formatting Issues and Solutions

### Issue 1: Macro Spacing
```c
// ❌ WRONG (extra spaces):
#define FLAG_A  (1 << 0)

// ✅ CORRECT (single space):
#define FLAG_A (1 << 0)
```

### Issue 2: Function Braces
```c
// ❌ WRONG (brace on same line for functions):
void func() {
  code();
}

// ✅ CORRECT (brace on new line - AfterFunction: true):
void func()
{
  code();
}

// ⚠️ BUT for control statements (AfterControlStatement: false):
if (cond) {  // ✅ CORRECT (brace on same line)
  code();
}
```

### Issue 3: Inline Functions
```c
// ✅ CORRECT (simple one-liner):
static inline int get_x(struct foo* f) { return f->x; }

// ❌ WRONG (multi-statement on one line):
static inline void clear(struct foo* f) { f->x = 0; f->y = 0; }

// ✅ CORRECT (multi-statement, multi-line):
static inline void clear(struct foo* f)
{
  f->x = 0;
  f->y = 0;
}
```

### Issue 4: Line Length
```c
// ❌ WRONG (>120 characters):
static inline void very_long_function_name_with_many_parameters(struct some_struct* ptr, int param1, int param2, int param3, int param4)

// ✅ CORRECT (wrapped to fit 120 char limit):
static inline void very_long_function_name_with_many_parameters(
    struct some_struct* ptr, int param1, int param2, int param3, int param4)
```

---

## Quick Reference Checklist

Before committing C/C++ code:

- [ ] Run `clang-format -i -style=file` on modified files
- [ ] Check `ColumnLimit: 120` - no lines longer than 120 chars
- [ ] Function braces on new line (`AfterFunction: true`)
- [ ] Control statement braces on same line (`AfterControlStatement: false`)
- [ ] No extra spaces in macro definitions
- [ ] Multi-statement inline functions are multi-line
- [ ] Indentation is 2 spaces, not tabs
- [ ] Test locally: `make check_linters` (if available)

---

## Jenkins Pipeline Path

```
Developer commits code
    ↓
Jenkins detects change
    ↓
Runs: make check_linters
    ↓
Executes: scripts/linter.mk
    ↓
For each .c/.h file:
  clang-format -style=file <file> | diff <file> -
    ↓
If diff shows differences:
  Log error to ERR_FILE
    ↓
If ERR_FILE not empty:
  Print errors
  Exit 1 (BUILD FAILED)
    ↓
Developer sees error in Jenkins
Developer fixes formatting
Developer commits again
```

---

## Useful Commands

```bash
# Check which files would be formatted
git diff --name-only HEAD | grep -E '\.(c|h)$'

# Format all C/C++ files in a directory
find ap/src/wlan-drivers/ar -name "*.c" -o -name "*.h" | xargs clang-format -i -style=file

# Show what clang-format would change (without modifying)
clang-format -style=file <file>

# Verify file is correctly formatted (exit code 0 = OK)
clang-format -style=file <file> | diff <file> - && echo "OK" || echo "NEEDS FORMATTING"

# Format only staged files
git diff --cached --name-only | grep -E '\.(c|h)$' | xargs clang-format -i -style=file
```

---

**Last updated**: 2026-03-26  
**Your Project**: wifi-ap (Arista Networks)  
**Jenkins Pipeline**: Code Review Linter Check
