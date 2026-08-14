# Comprehensive Guide: Header Files and Binary Libraries

## Introduction

When working with hardware SDKs from vendors like Qualcomm, NVIDIA, Intel, or ARM, you'll typically receive:

- **Header files** (`.h`, `.hpp`): Human-readable interface definitions
- **Binary libraries** (`.so`, `.a`, `.dll`, `.lib`): Compiled machine code

This distribution model is fundamental to how compiled languages like C and C++ work, and serves multiple purposes from
intellectual property protection to ensuring binary compatibility.

This guide provides a comprehensive understanding of:

- Why this distribution model exists
- How header files define interfaces
- How binary libraries contain implementations
- How the compilation and linking process connects them
- Practical considerations for developers

---

## Why Vendors Distribute Headers + Binaries

### 1. Intellectual Property Protection

The most significant reason vendors provide only headers and binaries is to protect their intellectual property.

```
┌─────────────────────────────────────────────────────────────────┐
│                    SOURCE CODE (Hidden)                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  // Qualcomm's secret sauce                              │   │
│  │  int qc_neural_process(float* data, int size) {          │   │
│  │      // Proprietary algorithm worth millions             │   │
│  │      // Years of R&D investment                          │   │
│  │      // Patented techniques                              │   │
│  │      // Hardware-specific optimizations                  │   │
│  │  }                                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              COMPILATION (One-way process)               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│                    BINARY (Distributed)                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  0x55 0x48 0x89 0xe5 0x48 0x83 0xec 0x20 ...             │   │
│  │  (Nearly impossible to reverse engineer)                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**What's protected:**

- Proprietary algorithms
- Hardware-specific optimizations
- Trade secrets and patented techniques
- Years of research and development

### 2. Licensing and Business Model

| Distribution Model | Control Level | Use Case             |
| ------------------ | ------------- | -------------------- |
| Source Code        | Low           | Open source projects |
| Headers + Binary   | High          | Commercial SDKs      |
| Binary Only        | Very High     | Closed plugins       |

Vendors can:

- License the same binary to multiple customers
- Enforce usage restrictions through licensing
- Provide different feature sets in different binary versions
- Track and control distribution

### 3. Quality and Consistency

```
┌─────────────────────────────────────────────────────────────────┐
│                 WITHOUT PRE-COMPILED BINARIES                   │
├─────────────────────────────────────────────────────────────────┤
│  Developer A: Compiles with GCC 9, -O2, Linux                   │
│  Developer B: Compiles with Clang 14, -O3, macOS                │
│  Developer C: Compiles with MSVC, /O2, Windows                  │
│                                                                 │
│  Result: Different binaries, potential bugs, inconsistent       │
│          performance, harder to debug and support               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  WITH PRE-COMPILED BINARIES                     │
├─────────────────────────────────────────────────────────────────┤
│  All Developers: Use the same tested, optimized binary          │
│                                                                 │
│  Result: Consistent behavior, verified performance,             │
│          easier support, known compatibility                    │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Reducing Build Complexity

Pre-compiled binaries eliminate:

- Complex build dependencies
- Platform-specific build configurations
- Compiler compatibility issues
- Build time for large codebases

---

## Understanding Header Files

### What Header Files Contain

Header files are the **public interface** to a library. They declare what exists without revealing how it works.

```c
/* ============================================================
 * Example: qualcomm_hexagon_sdk.h
 * This is what Qualcomm provides to developers
 * ============================================================ */

#ifndef QUALCOMM_HEXAGON_SDK_H
#define QUALCOMM_HEXAGON_SDK_H

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================
 * 1. PREPROCESSOR DEFINITIONS (Constants and Macros)
 * ============================================================ */

#define QC_SDK_VERSION_MAJOR    3
#define QC_SDK_VERSION_MINOR    5
#define QC_SDK_VERSION_PATCH    1

#define QC_MAX_TENSOR_DIMS      8
#define QC_MAX_BATCH_SIZE       256

/* Error codes */
#define QC_SUCCESS              0
#define QC_ERROR_INVALID_PARAM  -1
#define QC_ERROR_OUT_OF_MEMORY  -2
#define QC_ERROR_NOT_SUPPORTED  -3
#define QC_ERROR_DEVICE_BUSY    -4

/* Feature flags */
#define QC_FEATURE_FP16         (1 << 0)
#define QC_FEATURE_INT8         (1 << 1)
#define QC_FEATURE_DYNAMIC      (1 << 2)

/* ============================================================
 * 2. TYPE DEFINITIONS
 * ============================================================ */

typedef int32_t qc_status_t;
typedef uint64_t qc_handle_t;
typedef void* qc_context_t;

/* ============================================================
 * 3. ENUMERATIONS
 * ============================================================ */

typedef enum {
  QC_DEVICE_CPU = 0,
  QC_DEVICE_GPU = 1,
  QC_DEVICE_DSP = 2,
  QC_DEVICE_NPU = 3
} qc_device_type_t;

typedef enum {
  QC_DTYPE_FLOAT32 = 0,
  QC_DTYPE_FLOAT16 = 1,
  QC_DTYPE_INT8    = 2,
  QC_DTYPE_UINT8   = 3,
  QC_DTYPE_INT32   = 4
} qc_data_type_t;

typedef enum {
  QC_LAYOUT_NHWC = 0,  /* Batch, Height, Width, Channels */
  QC_LAYOUT_NCHW = 1   /* Batch, Channels, Height, Width */
} qc_tensor_layout_t;

/* ============================================================
 * 4. STRUCTURE DEFINITIONS
 * ============================================================ */

/**
 * Tensor descriptor structure
 * Describes the shape and properties of a tensor
 */
typedef struct {
  uint32_t dims[QC_MAX_TENSOR_DIMS];  /* Dimension sizes */
  uint32_t num_dims;                   /* Number of dimensions */
  qc_data_type_t dtype;                /* Data type */
  qc_tensor_layout_t layout;           /* Memory layout */
  size_t size_bytes;                   /* Total size in bytes */
} qc_tensor_desc_t;

/**
 * Device configuration structure
 */
typedef struct {
  qc_device_type_t device_type;
  uint32_t device_id;
  uint32_t num_threads;
  uint32_t priority;
  uint32_t features;                   /* Bitmask of QC_FEATURE_* */
} qc_device_config_t;

/**
 * Performance metrics structure
 */
typedef struct {
  uint64_t inference_time_us;
  uint64_t memory_peak_bytes;
  uint32_t power_level;
  float utilization_percent;
} qc_perf_metrics_t;

/* ============================================================
 * 5. FUNCTION DECLARATIONS (The Interface)
 * ============================================================ */

/**
 * Initialize the Qualcomm SDK
 *
 * @param config    Pointer to device configuration
 * @param context   Output pointer to created context
 * @return          QC_SUCCESS on success, error code otherwise
 */
qc_status_t qc_initialize(
  const qc_device_config_t* config,
  qc_context_t* context
);

/**
 * Shutdown and cleanup
 *
 * @param context   Context to destroy
 * @return          QC_SUCCESS on success
 */
qc_status_t qc_shutdown(qc_context_t context);

/**
 * Load a neural network model
 *
 * @param context       Active context
 * @param model_path    Path to model file
 * @param handle        Output model handle
 * @return              QC_SUCCESS on success
 */
qc_status_t qc_load_model(
  qc_context_t context,
  const char* model_path,
  qc_handle_t* handle
);

/**
 * Run inference on loaded model
 *
 * @param handle        Model handle
 * @param input_data    Input tensor data
 * @param input_desc    Input tensor descriptor
 * @param output_data   Output buffer
 * @param output_desc   Output tensor descriptor
 * @return              QC_SUCCESS on success
 */
qc_status_t qc_run_inference(
  qc_handle_t handle,
  const void* input_data,
  const qc_tensor_desc_t* input_desc,
  void* output_data,
  qc_tensor_desc_t* output_desc
);

/**
 * Get performance metrics from last inference
 *
 * @param handle    Model handle
 * @param metrics   Output metrics structure
 * @return          QC_SUCCESS on success
 */
qc_status_t qc_get_metrics(
  qc_handle_t handle,
  qc_perf_metrics_t* metrics
);

/**
 * Get human-readable error string
 *
 * @param status    Status code
 * @return          Error string (do not free)
 */
const char* qc_get_error_string(qc_status_t status);

#ifdef __cplusplus
}
#endif

#endif /* QUALCOMM_HEXAGON_SDK_H */
```

### Header File Components Breakdown

```
┌─────────────────────────────────────────────────────────────────┐
│                    HEADER FILE ANATOMY                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ INCLUDE GUARDS                                            │  │
│   │ #ifndef / #define / #endif                                │  │
│  │ Purpose: Prevent multiple inclusion                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ PREPROCESSOR DEFINITIONS                                  │  │
│  │ #define constants, macros, feature flags                  │  │
│  │ Purpose: Compile-time constants, configuration            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ TYPE DEFINITIONS                                          │  │
│  │ typedef, enum, struct, union, class                       │  │
│  │ Purpose: Define data structures and types                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ FUNCTION DECLARATIONS                                     │  │
│  │ Return type, name, parameters (no body!)                  │  │
│  │ Purpose: Define the callable interface                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why Each Component Matters

| Component             | What Compiler Learns          | Why It's Needed                    |
| --------------------- | ----------------------------- | ---------------------------------- |
| Include Guards        | File boundaries               | Prevents redefinition errors       |
| Macros/Constants      | Literal values                | Inline substitution, configuration |
| Type Definitions      | Size, layout, alignment       | Memory allocation, access patterns |
| Enumerations          | Valid values, underlying type | Type safety, switch statements     |
| Struct Definitions    | Member offsets, total size    | Memory layout, member access       |
| Function Declarations | Signature, calling convention | Validate calls, generate call code |

---

## Understanding Binary Libraries

### What's Inside a Binary Library

A compiled binary library contains:

```
┌─────────────────────────────────────────────────────────────────┐
│                    BINARY LIBRARY STRUCTURE                     │
│                    (libqualcomm.so example)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ELF HEADER (for Linux .so files)                          │  │
│  │ • Magic number (0x7F 'E' 'L' 'F')                        │  │
│  │ • Architecture (x86_64, ARM64, etc.)                      │  │
│  │ • Entry point                                             │  │
│  │ • Section/Program header offsets                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ SYMBOL TABLE (.symtab / .dynsym)                          │  │
│  │ • qc_initialize      → offset 0x00012340                  │  │
│  │ • qc_shutdown        → offset 0x00012890                  │  │
│  │ • qc_load_model      → offset 0x00013100                  │  │
│  │ • qc_run_inference   → offset 0x00015670                  │  │
│  │ (Maps symbol names to code locations)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ CODE SECTION (.text)                                      │  │
│  │ 0x00012340: 55                    push   rbp              │  │
│  │ 0x00012341: 48 89 e5              mov    rbp, rsp         │  │
│  │ 0x00012344: 48 83 ec 20           sub    rsp, 0x20        │  │
│  │ 0x00012348: 48 89 7d e8           mov    [rbp-0x18], rdi  │  │
│  │ ...                                                       │  │
│  │ (Actual machine instructions)                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ DATA SECTIONS                                             │  │
│  │ • .data    - Initialized global variables                 │  │
│  │ • .rodata  - Read-only data (strings, constants)          │  │
│  │ • .bss     - Uninitialized global variables               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ RELOCATION TABLES (.rel / .rela)                          │  │
│  │ • Addresses that need fixing at load time                 │  │
│  │ • External symbol references                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Examining a Binary Library

You can inspect binary libraries using various tools:

```bash
# List exported symbols
nm -D libqualcomm.so

# Output example:
# 0000000000012340 T qc_initialize
# 0000000000012890 T qc_shutdown
# 0000000000013100 T qc_load_model
# 0000000000015670 T qc_run_inference
# 0000000000018200 T qc_get_metrics
# 0000000000018450 T qc_get_error_string

# View library information
file libqualcomm.so
# Output: ELF 64-bit LSB shared object, ARM aarch64, version 1 (SYSV),
#         dynamically linked, stripped

# List dependencies
ldd libqualcomm.so
# Output:
#   linux-vdso.so.1
#   libc.so.6 => /lib/aarch64-linux-gnu/libc.so.6
#   libm.so.6 => /lib/aarch64-linux-gnu/libm.so.6
#   libpthread.so.0 => /lib/aarch64-linux-gnu/libpthread.so.0

# Disassemble (shows machine code, not original source)
objdump -d libqualcomm.so | head -50
```

---

## The Compilation and Linking Process

### Complete Build Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        COMPLETE BUILD PIPELINE                          │
└─────────────────────────────────────────────────────────────────────────┘

SOURCE FILES                    HEADER FILES
┌────────────┐                  ┌────────────┐
│  main.c    │                  │ qualcomm.h │
│  utils.c   │                  │ my_app.h   │
│  model.c   │                  │ config.h   │
└─────┬──────┘                  └─────┬──────┘
│                               │
└───────────────┬───────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      PHASE 1: PREPROCESSING                             │
│                         (cpp / cc -E)                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  • Processes #include directives (copies header content)                │
│  • Expands #define macros                                               │
│  • Evaluates #if / #ifdef conditionals                                  │
│  • Removes comments                                                     │
│  • Generates: main.i, utils.i, model.i (preprocessed source)            │
└─────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      PHASE 2: COMPILATION                               │
│                         (cc -S)                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  • Lexical analysis (tokenization)                                      │
│  • Syntax analysis (parsing to AST)                                     │
│  • Semantic analysis (type checking)                                    │
│  • Optimization passes                                                  │
│  • Code generation                                                      │
│  • Generates: main.s, utils.s, model.s (assembly code)                  │
└─────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      PHASE 3: ASSEMBLY                                  │
│                         (as)                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  • Converts assembly to machine code                                    │
│  • Creates symbol table entries                                         │
│  • Generates relocation entries for unresolved symbols                  │
│  • Generates: main.o, utils.o, model.o (object files)                   │
└─────────────────────────────────────────────────────────────────────────┘
│
│    ┌─────────────────────┐
│    │  BINARY LIBRARY     │
│    │  libqualcomm.so     │
│    │  (from Qualcomm)    │
│    └──────────┬──────────┘
│               │
└───────┬───────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      PHASE 4: LINKING                                   │
│                         (ld)                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  • Combines all object files                                            │
│  • Resolves symbol references                                           │
│  • Links against binary libraries                                       │
│  • Applies relocations                                                  │
│  • Creates final executable or shared library                           │
│  • Generates: my_application (executable)                               │
└─────────────────────────────────────────────────────────────────────────┘
│
▼
┌──────────────┐
│ EXECUTABLE   │
│ ./my_app     │
└──────────────┘
```

### Detailed Phase Breakdown

#### Phase 1: Preprocessing

```c
/* Before preprocessing: main.c */
#include "qualcomm.h"
#define BATCH_SIZE 32

int main() {
  qc_context_t ctx;
  qc_device_config_t config = {
    .device_type = QC_DEVICE_DSP,
    .num_threads = BATCH_SIZE
  };
  return qc_initialize(&config, &ctx);
}
```

```c
/* After preprocessing: main.i (simplified) */
/* Contents of qualcomm.h inserted here */
typedef int32_t qc_status_t;
typedef void* qc_context_t;
typedef enum { QC_DEVICE_CPU = 0, QC_DEVICE_DSP = 2 } qc_device_type_t;
typedef struct { qc_device_type_t device_type; uint32_t num_threads; } qc_device_config_t;
qc_status_t qc_initialize(const qc_device_config_t* config, qc_context_t* context);
/* End of qualcomm.h */

int main() {
  qc_context_t ctx;
  qc_device_config_t config = {
    .device_type = 2,        /* QC_DEVICE_DSP replaced */
    .num_threads = 32        /* BATCH_SIZE replaced */
  };
  return qc_initialize(&config, &ctx);
}
```

#### Phase 2-3: Compilation and Assembly

```
Object File: main.o
┌─────────────────────────────────────────────────────────────────┐
│ SYMBOL TABLE                                                    │
├─────────────────────────────────────────────────────────────────┤
│ Symbol              │ Type      │ Section │ Value               │
├─────────────────────┼───────────┼─────────┼─────────────────────┤
│ main                │ FUNC      │ .text   │ 0x00000000          │
│ qc_initialize       │ UNDEFINED │ *UND*   │ 0x00000000          │ ← Needs linking!
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ CODE SECTION (.text)                                            │
├─────────────────────────────────────────────────────────────────┤
│ 0x00: push   rbp                                                │
│ 0x01: mov    rbp, rsp                                           │
│ 0x04: sub    rsp, 0x30                                          │
│ ...                                                             │
│ 0x28: call   0x00000000    ; ← placeholder for qc_initialize    │
│ ...                                                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ RELOCATION TABLE                                                │
├─────────────────────────────────────────────────────────────────┤
│ Offset  │ Type          │ Symbol                                │
├─────────┼───────────────┼───────────────────────────────────────┤
│ 0x29    │ R_X86_64_PLT32│ qc_initialize                         │ ← Fix this address!
└─────────────────────────────────────────────────────────────────┘
```

#### Phase 4: Linking

```
LINKER INPUT
┌──────────────────────────────┐
│                              │
┌────┴────┐                    ┌────┴────┐
│ main.o  │                    │libqc.so │
└────┬────┘                    └────┬────┘
│                              │
│  Symbol: qc_initialize       │  Symbol: qc_initialize
│  Status: UNDEFINED           │  Status: DEFINED @ 0x12340
│                              │
└──────────────┬───────────────┘
│
▼
┌─────────────────┐
│     LINKER      │
│                 │
│ 1. Find all     │
│    undefined    │
│    symbols      │
│                 │
│ 2. Search libs  │
│    for defs     │
│                 │
│ 3. Update       │
│    relocations  │
│                 │
│ 4. Create       │
│    executable   │
└────────┬────────┘
│
▼
┌─────────────────┐
│   EXECUTABLE    │
│                 │
│ call 0x12340    │ ← Address resolved!
└─────────────────┘
```

---

## How Headers and Binaries Work Together

### The Contract Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         THE CONTRACT MODEL                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   HEADER FILE (qualcomm.h)              BINARY (libqualcomm.so)         │
│   ═══════════════════════               ═════════════════════           │
│   "I promise these                      "I implement these              │
│    functions exist                       functions exactly              │
│    with these signatures"                as promised"                   │
│                                                                         │
│   ┌─────────────────────┐               ┌─────────────────────┐        │
│   │ CONTRACT:           │               │ IMPLEMENTATION:     │        │
│   │                     │               │                     │        │
│   │ int add(int, int);  │◄─────────────►│ int add(int a,      │        │
│   │                     │   MUST MATCH  │         int b) {    │        │
│   │                     │               │   return a + b;     │        │
│   │                     │               │ }                   │        │
│   └─────────────────────┘               └─────────────────────┘        │
│                                                                         │
│   YOUR CODE uses the                    LINKER connects your            │
│   contract to make calls                calls to implementation         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Information Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      INFORMATION FLOW                                   │
└─────────────────────────────────────────────────────────────────────────┘

COMPILE TIME
┌───────────────────────────────────────────────────────────┐
│                                                           │
│   Your Code              Header File                      │
│   ┌──────────┐          ┌──────────────┐                 │
│   │          │ includes │              │                 │
│   │ #include ├─────────►│ Declarations │                 │
│   │          │          │ Types        │                 │
│   │ call     │◄─────────┤ Signatures   │                 │
│   │ func()   │ validates│              │                 │
│   │          │          └──────────────┘                 │
│   └────┬─────┘                                           │
│        │                                                 │
│        │ generates                                       │
│        ▼                                                 │
│   ┌──────────┐                                           │
│   │ Object   │ (with unresolved symbols)                 │
│   │ File .o  │                                           │
│   └────┬─────┘                                           │
│        │                                                 │
└────────┼─────────────────────────────────────────────────┘
│
│              LINK TIME
┌────────┼─────────────────────────────────────────────────┐
│        │                                                 │
│        │            Binary Library                       │
│        │            ┌──────────────┐                     │
│        │            │              │                     │
│        │  resolves  │ Symbol Table │                     │
│        ├───────────►│ Machine Code │                     │
│        │  against   │              │                     │
│        │            └──────────────┘                     │
│        │                                                 │
│        ▼                                                 │
│   ┌──────────┐                                           │
│   │Executable│ (all symbols resolved)                    │
│   └────┬─────┘                                           │
│        │                                                 │
└────────┼─────────────────────────────────────────────────┘
│
│              RUN TIME
┌────────┼─────────────────────────────────────────────────┐
│        ▼                                                 │
│   ┌──────────┐          ┌──────────────┐                 │
│   │  Your    │ calls    │   Library    │                 │
│   │  Code    ├─────────►│   Code       │                 │
│   │          │◄─────────┤   Executes   │                 │
│   │          │ returns  │              │                 │
│   └──────────┘          └──────────────┘                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Types of Binary Libraries

### Static Libraries (.a / .lib)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        STATIC LIBRARIES                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Extension: .a (Unix/Linux), .lib (Windows)                             │
│                                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐               │
│  │   main.o    │     │  libqc.a    │     │  final.exe  │               │
│  │             │     │             │     │             │               │
│  │ call func() │  +  │ func() code │  =  │ main code   │               │
│  │             │     │             │     │ func() code │               │
│  │   100 KB    │     │   500 KB    │     │   600 KB    │               │
│  └─────────────┘     └─────────────┘     └─────────────┘               │
│                                                                         │
│  CHARACTERISTICS:                                                       │
│  • Library code copied INTO executable                                  │
│  • Larger executable size                                               │
│  • No runtime dependencies on library                                   │
│  • Faster startup (no dynamic loading)                                  │
│  • Each executable has its own copy                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Dynamic/Shared Libraries (.so / .dll)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DYNAMIC LIBRARIES                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Extension: .so (Unix/Linux), .dll (Windows), .dylib (macOS)            │
│                                                                         │
│  ┌─────────────┐                         ┌─────────────┐               │
│  │   main.o    │                         │  final.exe  │               │
│  │             │                         │             │               │
│  │ call func() │           link          │ main code   │               │
│  │             │  ───────────────────►   │ PLT stub    │               │
│  │   100 KB    │                         │   105 KB    │               │
│  └─────────────┘                         └──────┬──────┘               │
│                                                 │                       │
│  ┌─────────────┐                               │ loads at runtime      │
│  │  libqc.so   │◄──────────────────────────────┘                       │
│  │             │                                                        │
│  │ func() code │  (shared in memory)                                   │
│  │   500 KB    │                                                        │
│  └─────────────┘                                                        │
│                                                                         │
│  CHARACTERISTICS:                                                       │
│  • Library loaded at runtime                                            │
│  • Smaller executable size                                              │
│  • Library can be updated independently                                 │
│  • Shared memory between processes                                      │
│  • Slight overhead for dynamic binding                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Comparison Table

| Aspect              | Static Library (.a)    | Dynamic Library (.so)    |
| ------------------- | ---------------------- | ------------------------ |
| **Linking Time**    | Compile time           | Runtime                  |
| **Executable Size** | Larger                 | Smaller                  |
| **Memory Usage**    | Duplicated per process | Shared between processes |
| **Updates**         | Requires recompilation | Just replace library     |
| **Distribution**    | Single file            | Executable + libraries   |
| **Load Time**       | Faster                 | Slightly slower          |
| **Flexibility**     | Less                   | More (plugins, etc.)     |

---

## Symbol Resolution and Binding

### Symbol Types

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SYMBOL TYPES                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  DEFINED SYMBOLS (T, D, B, R)                                           │
│  ─────────────────────────────                                          │
│  • The symbol is implemented in this file                               │
│  • Has an address/value                                                 │
│                                                                         │
│  nm output:                                                             │
│  0000000000001234 T qc_initialize    ← T = Text (code) section          │
│  0000000000005678 D global_config    ← D = Data section                 │
│  0000000000008000 B uninitialized    ← B = BSS section                  │
│  0000000000001000 R readonly_data    ← R = Read-only data               │
│                                                                         │
│  UNDEFINED SYMBOLS (U)                                                  │
│  ─────────────────────                                                  │
│  • Referenced but not implemented here                                  │
│  • Must be resolved by linker                                           │
│                                                                         │
│  nm output:                                                             │
│                   U qc_initialize    ← Used but not defined             │
│                   U printf           ← From libc                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Dynamic Symbol Resolution

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PROCEDURE LINKAGE TABLE (PLT)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAZY BINDING (Default)                                                 │
│  ──────────────────────                                                 │
│                                                                         │
│  First call to qc_initialize():                                         │
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │  Your Code   │    │     PLT      │    │   Dynamic    │              │
│  │              │    │              │    │   Linker     │              │
│  │ call func    ├───►│ jmp to GOT   ├───►│              │              │
│  │              │    │              │    │ Resolve sym  │              │
│  │              │    │              │◄───┤ Update GOT   │              │
│  │              │◄───┤ jmp to func  │    │              │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│                                                                         │
│  Subsequent calls:                                                      │
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │  Your Code   │    │     PLT      │    │  Library     │              │
│  │              │    │              │    │              │              │
│  │ call func    ├───►│ jmp to GOT   ├───►│ qc_init()    │              │
│  │              │◄───┤ (now cached) │◄───┤              │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│                                                                         │
│  GOT = Global Offset Table (contains resolved addresses)                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Application Binary Interface (ABI)

### What is ABI?

The ABI defines low-level interface conventions between binary modules:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    APPLICATION BINARY INTERFACE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     CALLING CONVENTION                           │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │ • How function arguments are passed (registers vs stack)        │   │
│  │ • How return values are returned                                 │   │
│  │ • Which registers must be preserved by callee                    │   │
│  │ • Stack alignment requirements                                   │   │
│  │                                                                  │   │
│  │ Example (x86-64 System V ABI):                                   │   │
│  │   Args: RDI, RSI, RDX, RCX, R8, R9, then stack                  │   │
│  │   Return: RAX (integer), XMM0 (float)                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      DATA LAYOUT                                 │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │ • Size of primitive types (int = 4 bytes, long = 8 bytes)       │   │
│  │ • Struct member alignment and padding                            │   │
│  │ • Endianness (little-endian vs big-endian)                       │   │
│  │                                                                  │   │
│  │ Example struct layout:                                           │   │
│  │   struct { char a; int b; char c; }                             │   │
│  │   Memory: [a][pad][pad][pad][b][b][b][b][c][pad][pad][pad]      │   │
│  │   Size: 12 bytes (with alignment)                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    NAME MANGLING (C++)                           │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │ • How C++ function names are encoded                             │   │
│  │ • Includes namespace, class, parameter types                     │   │
│  │                                                                  │   │
│  │ Example:                                                         │   │
│  │   void MyClass::process(int x, float y)                         │   │
│  │   Mangled: _ZN7MyClass7processEif                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### ABI Compatibility Importance

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ABI COMPATIBILITY ISSUES                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  HEADER says:                    BINARY expects:                        │
│  struct Data {                   struct Data {                          │
│      int value;      ──────►         int value;         ✓ Match        │
│      float coeff;    ──────►         float coeff;       ✓ Match        │
│  };                              };                                     │
│  sizeof = 8 bytes                sizeof = 8 bytes                       │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  PROBLEM: Header version mismatch                                       │
│                                                                         │
│  Old HEADER:                     New BINARY:                            │
│  struct Data {                   struct Data {                          │
│      int value;      ──────►         int value;         ✓              │
│      float coeff;    ──────►         float coeff;       ✓              │
│  };                                  int new_field;     ✗ MISSING!     │
│  sizeof = 8 bytes                };                                    │
│                                  sizeof = 12 bytes                      │
│                                                                         │
│  RESULT: Memory corruption, crashes, undefined behavior                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Practical Examples

### Example 1: Using Qualcomm SDK

```c
/* my_inference_app.c */

#include <stdio.h>
#include <stdlib.h>
#include "qualcomm_hexagon_sdk.h"  /* Header from Qualcomm */

int main(int argc, char* argv[]) {
  qc_status_t status;
  qc_context_t ctx = NULL;
  qc_handle_t model = 0;

  /* Configure for Hexagon DSP */
  qc_device_config_t config = {
    .device_type = QC_DEVICE_DSP,
    .device_id = 0,
    .num_threads = 4,
    .priority = 1,
    .features = QC_FEATURE_FP16 | QC_FEATURE_INT8
  };

  /* Initialize SDK */
  status = qc_initialize(&config, &ctx);
  if (status != QC_SUCCESS) {
    fprintf(stderr, "Init failed: %s\n", qc_get_error_string(status));
    return 1;
  }

  /* Load model */
  status = qc_load_model(ctx, "model.dlc", &model);
  if (status != QC_SUCCESS) {
    fprintf(stderr, "Load failed: %s\n", qc_get_error_string(status));
    qc_shutdown(ctx);
    return 1;
  }

  /* Prepare input */
  float input_data[224 * 224 * 3];
  float output_data[1000];

  qc_tensor_desc_t input_desc = {
    .dims = {1, 224, 224, 3},
    .num_dims = 4,
    .dtype = QC_DTYPE_FLOAT32,
    .layout = QC_LAYOUT_NHWC
  };

  qc_tensor_desc_t output_desc = {0};

  /* Run inference */
  status = qc_run_inference(model, input_data, &input_desc,
                            output_data, &output_desc);

  /* Get metrics */
  qc_perf_metrics_t metrics;
  qc_get_metrics(model, &metrics);
  printf("Inference time: %lu us\n", metrics.inference_time_us);

  /* Cleanup */
  qc_shutdown(ctx);
  return 0;
}
```

### Build Commands

```bash
# Compile (uses header for declarations)
gcc -c my_inference_app.c -I/path/to/qualcomm/include -o my_inference_app.o

# Link (connects to binary library)
gcc my_inference_app.o -L/path/to/qualcomm/lib -lqualcomm -o my_inference_app

# Or all in one step
gcc my_inference_app.c \
-I/path/to/qualcomm/include \
-L/path/to/qualcomm/lib \
-lqualcomm \
-o my_inference_app

# Run (needs library at runtime for .so)
export LD_LIBRARY_PATH=/path/to/qualcomm/lib:$LD_LIBRARY_PATH
./my_inference_app
```

### Example 2: CMake Integration

```cmake
# CMakeLists.txt

cmake_minimum_required(VERSION 3.16)
project(QualcommInferenceApp)

# Set paths to Qualcomm SDK
set(QUALCOMM_SDK_PATH "/opt/qualcomm/hexagon_sdk")
set(QUALCOMM_INCLUDE_DIR "${QUALCOMM_SDK_PATH}/include")
set(QUALCOMM_LIB_DIR "${QUALCOMM_SDK_PATH}/lib")

# Find the library
find_library(QUALCOMM_LIBRARY
    NAMES qualcomm qc_hexagon
    PATHS ${QUALCOMM_LIB_DIR}
    REQUIRED
)

# Create executable
add_executable(my_inference_app
    src/main.c
    src/utils.c
)

# Include directories (for header files)
target_include_directories(my_inference_app PRIVATE
    ${QUALCOMM_INCLUDE_DIR}
)

# Link against binary library
target_link_libraries(my_inference_app PRIVATE
    ${QUALCOMM_LIBRARY}
)

# Set RPATH for runtime library location
set_target_properties(my_inference_app PROPERTIES
    INSTALL_RPATH "${QUALCOMM_LIB_DIR}"
    BUILD_WITH_INSTALL_RPATH TRUE
)
```

---

## Common Issues and Troubleshooting

### Issue 1: Undefined Reference

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ERROR: undefined reference to `qc_initialize'                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CAUSE: Linker can't find the symbol definition                         │
│                                                                         │
│  POSSIBLE SOLUTIONS:                                                    │
│                                                                         │
│  1. Library not specified:                                              │
│     gcc main.o -lqualcomm -o app    ← Add -l flag                      │
│                                                                         │
│  2. Library path not specified:                                         │
│     gcc main.o -L/path/to/lib -lqualcomm -o app                        │
│                                                                         │
│  3. Wrong library order (dependencies):                                 │
│     gcc main.o -lqualcomm -lpthread -lm -o app                         │
│     (dependent libraries should come AFTER)                             │
│                                                                         │
│  4. Symbol not exported from library:                                   │
│     nm -D libqualcomm.so | grep qc_initialize                          │
│     (check if symbol exists)                                            │
│                                                                         │
│  5. C++ name mangling issue:                                            │
│     Wrap declarations in extern "C" { } in header                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Issue 2: Header/Binary Version Mismatch

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SYMPTOM: Crashes, garbage data, or unexpected behavior                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CAUSE: Header file version doesn't match binary version                │
│                                                                         │
│  DETECTION:                                                             │
│                                                                         │
│  // Check version at compile time vs runtime                           │
│  printf("Header version: %d.%d.%d\n",                                  │
│         QC_SDK_VERSION_MAJOR,                                          │
│         QC_SDK_VERSION_MINOR,                                          │
│         QC_SDK_VERSION_PATCH);                                         │
│                                                                         │
│  // If library provides version function                               │
│  const char* lib_version = qc_get_version();                           │
│  printf("Library version: %s\n", lib_version);                         │
│                                                                         │
│  SOLUTION: Use matching header and library versions                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Issue 3: Runtime Library Not Found

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ERROR: error while loading shared libraries: libqualcomm.so:           │
│         cannot open shared object file: No such file or directory       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CAUSE: Dynamic linker can't find .so file at runtime                   │
│                                                                         │
│  SOLUTIONS:                                                             │
│                                                                         │
│  1. Set LD_LIBRARY_PATH:                                                │
│     export LD_LIBRARY_PATH=/path/to/lib:$LD_LIBRARY_PATH               │
│                                                                         │
│  2. Install to system location:                                         │
│     sudo cp libqualcomm.so /usr/local/lib/                             │
│     sudo ldconfig                                                       │
│                                                                         │
│  3. Use RPATH during linking:                                           │
│     gcc main.o -L/path -lqualcomm -Wl,-rpath,/path -o app              │
│                                                                         │
│  4. Create config file:                                                 │
│     echo "/path/to/lib" | sudo tee /etc/ld.so.conf.d/qualcomm.conf     │
│     sudo ldconfig                                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Issue 4: Architecture Mismatch

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ERROR: skipping incompatible libqualcomm.so when searching for -lqc    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CAUSE: Library compiled for different architecture                     │
│                                                                         │
│  DETECTION:                                                             │
│                                                                         │
│  file libqualcomm.so                                                    │
│  # Output: ELF 64-bit LSB shared object, ARM aarch64                   │
│                                                                         │
│  file my_app.o                                                          │
│  # Output: ELF 64-bit LSB relocatable, x86-64    ← MISMATCH!           │
│                                                                         │
│  SOLUTION: Use library matching your target architecture                │
│  • x86_64 binary for x86_64 compilation                                │
│  • aarch64 binary for ARM64 compilation                                │
│  • Use cross-compilation toolchain if needed                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Best Practices

### For SDK Users

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      BEST PRACTICES FOR SDK USERS                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. VERSION MANAGEMENT                                                  │
│     • Keep headers and binaries from the same SDK release               │
│     • Document which SDK version your project uses                      │
│     • Test thoroughly when upgrading SDK versions                       │
│                                                                         │
│  2. BUILD SYSTEM INTEGRATION                                            │
│     • Use CMake/Meson find_package or pkg-config                       │
│     • Don't hardcode paths; use variables                               │
│     • Set up proper include/library directories                         │
│                                                                         │
│  3. RUNTIME CONSIDERATIONS                                              │
│     • Bundle required .so files with your application                   │
│     • Use RPATH for portable deployments                                │
│     • Document library dependencies                                     │
│                                                                         │
│  4. ERROR HANDLING                                                      │
│     • Always check return codes from SDK functions                      │
│     • Use provided error string functions                               │
│     • Implement graceful fallbacks                                      │
│                                                                         │
│  5. DEBUGGING                                                           │
│     • Check symbol availability with nm/objdump                         │
│     • Use ldd to verify library loading                                 │
│     • Enable SDK debug logging if available                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure Example

```
my_project/
├── CMakeLists.txt
├── src/
│   ├── main.c
│   └── inference.c
├── include/
│   └── my_app.h
├── third_party/
│   └── qualcomm_sdk/
│       ├── include/
│       │   ├── qualcomm_hexagon_sdk.h
│       │   ├── qc_types.h
│       │   └── qc_errors.h
│       └── lib/
│           ├── linux_x86_64/
│           │   └── libqualcomm.so
│           ├── linux_aarch64/
│           │   └── libqualcomm.so
│           └── android_arm64/
│               └── libqualcomm.so
├── build/
└── README.md
```

---

## Glossary

| Term                       | Definition                                                                            |
| -------------------------- | ------------------------------------------------------------------------------------- |
| **Header File**            | A file containing declarations, type definitions, and macros that define an interface |
| **Binary Library**         | Compiled machine code packaged for linking with other programs                        |
| **Static Library**         | Library code copied into executable at link time (.a, .lib)                           |
| **Dynamic/Shared Library** | Library loaded at runtime, shared between processes (.so, .dll)                       |
| **Symbol**                 | A name representing a function, variable, or other entity in code                     |
| **Symbol Table**           | Data structure mapping symbol names to addresses                                      |
| **Linker**                 | Tool that combines object files and libraries into executables                        |
| **Object File**            | Compiled code before linking, with unresolved symbols (.o, .obj)                      |
| **PLT**                    | Procedure Linkage Table - enables lazy binding of dynamic symbols                     |
| **GOT**                    | Global Offset Table - stores resolved addresses of dynamic symbols                    |
| **ABI**                    | Application Binary Interface - low-level interface conventions                        |
| **Calling Convention**     | Rules for how functions pass arguments and return values                              |
| **Name Mangling**          | Encoding of C++ symbol names to include type information                              |
| **RPATH**                  | Runtime search path embedded in executable for finding libraries                      |
| **Relocation**             | Process of adjusting addresses when code is loaded at different locations             |
| **Undefined Symbol**       | Symbol referenced but not defined in current object file                              |

---

## References

1. **ELF Format Specification**: https://refspecs.linuxfoundation.org/elf/elf.pdf
2. **System V ABI**: https://refspecs.linuxbase.org/elf/x86_64-abi-0.99.pdf
3. **GNU Linker Documentation**: https://sourceware.org/binutils/docs/ld/
4. **Dynamic Linking in Linux**: https://www.akkadia.org/drepper/dsohowto.pdf

---

_Document Version: 1.0_
_Last Updated: 2024_
