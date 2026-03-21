# sk_buff Modification Guide

## Rule of Thumb: Making Changes Reflect Everywhere

When modifying `struct sk_buff`, follow this checklist to ensure changes propagate correctly across the entire 
codebase.

---

## 1. Kernel Patch Updates (Mandatory)

The `sk_buff` structure is defined in the kernel and modified via **patches**. You must update patches for 
**all supported kernel/platform versions**:

### Patch Locations
```
ap/platform/patches/kernel/
├── 4.4/                      # Kernel 4.4 patches
├── 5.4/                      # Kernel 5.4 patches
│   ├── common/               # Shared across all 5.4 platforms
│   ├── 12.2/                 # SPF 12.2 specific
│   │   ├── common/           # Shared across 12.2 platforms
│   │   ├── C_430/            # Platform-specific
│   │   ├── C_460/
│   │   └── O_435/
│   └── 12.5/                 # SPF 12.5 specific
│       ├── common/
│       ├── C_400/
│       ├── C_430/
│       ├── O_405/
│       └── O_435/
```

### Files to Modify in Each Patch

1. **`include/linux/skbuff.h`** - Add/modify field in `struct sk_buff`
2. **`net/core/skbuff.c`** - Initialize field in these functions:
   - `__alloc_skb()` - Main allocation
   - `__build_skb()` - Build from data pointer
   - `skb_clone()` - Clone handling (copy or reset)

---

## 2. Initialization Checklist

| Function | Location | Action |
|----------|----------|--------|
| `__alloc_skb()` | `net/core/skbuff.c` | Initialize new field (e.g., `skb->my_field = 0;`) |
| `__build_skb()` | `net/core/skbuff.c` | Initialize new field |
| `skb_clone()` | `net/core/skbuff.c` | Copy from source OR reset (depends on semantics) |

---

## 3. Version-Specific Patch Strategy

### When to create separate patches:

| Scenario | Strategy |
|----------|----------|
| Same change across all platforms | Create in `common/` directory |
| Version-specific line numbers | Create separate patches per version |
| Platform-specific behavior | Create in platform-specific directory |

### Example: Adding `ar_meta` field

Created patches:
- `ap/platform/patches/kernel/5.4/12.5/common/ar_skb_meta_cache_12_5.patch`
- `ap/platform/patches/kernel/5.4/12.2/common/skb_data_12_2.patch` (if different offsets)

---

## 4. Driver-Level Consumers

After modifying `sk_buff`, update all driver code that uses it:

### Key Locations
```
ap/src/wlan-drivers/QCA/licensed/
├── spf12_5_cs/
│   ├── offload/os/linux/netbuf.c      # SKB allocation wrappers
│   ├── cmn_dev/qdf/linux/src/qdf_nbuf.c  # QDF nbuf layer
│   └── os/linux/include/wbuf_private.h    # Buffer helpers
├── spf12_2_csu2/
│   └── (same structure)
├── 11.1_ap_spf11/
│   └── (same structure)
└── ... (other versions)
```

### Accessor Functions
If adding a new field, consider adding accessor macros/functions:
- In `qdf_nbuf.h` for QDF layer
- In `wbuf_private.h` for wbuf layer
- In `compat_skbuff.h` for compatibility

---

## 5. Quick Reference: Complete Change Workflow

```
1. Create/Update Kernel Patches
└── For EACH supported version (12.2, 12.5, etc.)
├── include/linux/skbuff.h  → Add field
└── net/core/skbuff.c       → Initialize in alloc/build/clone

2. Update Driver Layer (if needed)
└── For EACH driver version
├── qdf_nbuf.c/h  → Add helper functions
└── netbuf.c      → Allocation changes

3. Update Consumers
└── All code that needs to read/write the new field

4. Test on ALL Platforms
└── Build and test each platform variant
```

---

## 6. Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Forgetting a kernel version | Grep for existing sk_buff patches to find all locations |
| Not initializing in `skb_clone()` | Decide: copy value OR reset to zero |
| Line number drift between versions | Verify patch context matches each kernel version |
| Missing driver updates | Search for `sk_buff` usage in `wlan-drivers/` |

---

## 7. Search Commands for Impact Analysis

```bash
# Find all sk_buff patches
find ap/platform/patches -name "*.patch" | xargs grep -l "sk_buff"

# Find all driver files using sk_buff
grep -r "struct sk_buff" ap/src/wlan-drivers/ --include="*.c" --include="*.h"

# Find netbuf/qdf_nbuf allocations
grep -r "__alloc_skb\|skb_clone\|dev_alloc_skb" ap/src/

# Find all patch directories for a kernel version
ls -la ap/platform/patches/kernel/5.4/*/common/
```

---

## 8. Example: Adding a New Field

```c
// In include/linux/skbuff.h - struct sk_buff definition
struct sk_buff {
  ...
  refcount_t      users;
    
  /* Your new field with documentation */
  __u16           my_new_field;   /* Description of purpose */
    
  ...
};

// In net/core/skbuff.c - __alloc_skb()
skb->my_new_field = 0;

// In net/core/skbuff.c - __build_skb()
skb->my_new_field = 0;

// In net/core/skbuff.c - skb_clone()
n->my_new_field = skb->my_new_field;  // OR n->my_new_field = 0;
```

---

## Summary

**Rule of Thumb**: Any `sk_buff` change requires:
1. ✅ Patches for **all kernel versions** (4.4, 5.4)
2. ✅ Patches for **all platform versions** (12.2, 12.5, etc.)
3. ✅ Initialization in `__alloc_skb()`, `__build_skb()`, `skb_clone()`
4. ✅ Driver layer updates if accessor functions needed
5. ✅ Build verification on all target platforms

