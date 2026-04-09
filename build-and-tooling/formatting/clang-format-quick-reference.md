# clang-format Quick Reference Card

## 🚨 Your Code Failed Jenkins - What to Do?

### Step 1: Understand the Error
Look for this pattern in Jenkins output:
```
clang-format: <filename>
14,18c14,17
< YOUR CODE (WRONG)
---
> EXPECTED CODE (CORRECT)
```

### Step 2: Quick Fix (Choose One)

#### Option A: Auto-fix with clang-format (FASTEST)
```bash
# Fix the specific file mentioned in error
clang-format -i -style=file ap/src/wlan-drivers/ar/os_if/ar_os_if_ar_meta.h

# Fix all modified .c/.h files
git diff --name-only | grep -E '\.(c|h)$' | xargs clang-format -i -style=file

# Commit and push
git add .
git commit -m "Fix clang-format issues"
git push
```

#### Option B: Manual Fix (if you understand the issue)
1. Look at the diff in Jenkins output
2. Edit the file to match the expected format
3. Commit and push

---

## 📋 Your Project's Formatting Rules

### Critical Rules That Cause Jenkins Failures:

#### 1. ❌ NO Extra Spaces in Macros
```c
// ❌ WRONG:
#define FLAG_A  (1 << 0)

// ✅ CORRECT:
#define FLAG_A (1 << 0)
```

#### 2. 🔧 Function Braces on New Line
```c
// ❌ WRONG:
void function() {
  code();
}

// ✅ CORRECT:
void function()
{
  code();
}
```

#### 3. 🎛️ Control Statement Braces on Same Line
```c
// ✅ CORRECT:
if (condition) {
  code();
}
```

#### 4. 📏 Multi-Statement Inline Functions
```c
// ❌ WRONG:
static inline void clear(struct foo* f) { f->x = 0; f->y = 0; }

// ✅ CORRECT:
static inline void clear(struct foo* f)
{
  f->x = 0;
  f->y = 0;
}
```

#### 5. 📐 Line Length: 120 Characters Max
```c
// ❌ WRONG (>120 chars):
static inline void very_long_function_name_with_many_params(struct foo* f, int a, int b, int c, int d, int e, int f, int g)

// ✅ CORRECT (wrapped):
static inline void very_long_function_name_with_many_params(
    struct foo* f, int a, int b, int c, int d, int e, int f, int g)
```

#### 6. 🔢 Indentation: 2 Spaces (Not Tabs)
```c
// ❌ WRONG (tabs or 4 spaces):
void function()
{
    code();    // 4 spaces or tab
}

// ✅ CORRECT (2 spaces):
void function()
{
  code();      // 2 spaces
}
```

---

## 🛠️ Useful Commands

### Before Committing:
```bash
# Format all modified files
git diff --name-only | grep -E '\.(c|h)$' | xargs clang-format -i -style=file

# Check specific file (dry-run, no changes)
clang-format -style=file <file>

# Verify file is correctly formatted
clang-format -style=file <file> | diff <file> - && echo "✅ OK" || echo "❌ NEEDS FORMATTING"

# Run full linter check (same as Jenkins)
make check_linters
```

### Setup Auto-Format on Save:
```bash
# VSCode: Install "C/C++" extension
# Settings → Editor: Format On Save → ✅

# CLion/IntelliJ:
# Settings → Editor → Code Style → C/C++ → Import .clang-format

# Vim: Install vim-clang-format plugin
```

---

## 🔍 How Jenkins Validates (Behind the Scenes)

```
1. Jenkins detects your commit
   ↓
2. Runs: make check_linters
   ↓
3. For each .c/.h file:
   clang-format -style=file <file> | diff <file> -
   ↓
4. If ANY difference found:
   ❌ BUILD FAILS
   Shows diff in console
   ↓
5. You fix formatting and push again
```

---

## 📁 Key Files in Your Project

| File | Purpose |
|------|---------|
| `.clang-format` | Formatting rules (Google style + customizations) |
| `scripts/linter.mk` | Jenkins linter validation logic |
| `Makefile` | Includes linter.mk (line 18) |
| `scripts/vars.mk` | Jenkins/CI variables |

---

## 🎯 Pre-Commit Checklist

Before `git push`:

- [ ] Run `clang-format -i -style=file` on modified .c/.h files
- [ ] Check no lines exceed 120 characters
- [ ] Function braces on new line
- [ ] No extra spaces in macro definitions
- [ ] Multi-statement inline functions are multi-line
- [ ] Indentation is 2 spaces
- [ ] (Optional) Run `make check_linters` locally

---

## 💡 Pro Tips

1. **Use IDE auto-format on save** - saves time
2. **Set up pre-commit hook** - catches errors before push
3. **Keep clang-format installed locally** - test before pushing
4. **When in doubt, run**: `clang-format -i -style=file <file>`
5. **Match existing code style** in the file you're editing

---

## 🆘 Common Issues

### "clang-format: command not found"
```bash
# Install clang-format
# macOS: brew install clang-format
# Ubuntu: apt-get install clang-format
# CentOS: yum install clang-tools-extra
```

### "Multiple formatting errors"
```bash
# Fix all at once
find . -name "*.c" -o -name "*.h" | xargs clang-format -i -style=file
```

### "Still failing after fixing"
```bash
# Make sure you committed the formatted version
git status
git add <file>
git commit -m "Fix formatting"
git push
```

---

**Quick Access**: 
- Full Guide: `~/docs/clang-format-jenkins-guide.md`
- Global Rules: `~/.augment/rules/c-cpp-formatting.md`
