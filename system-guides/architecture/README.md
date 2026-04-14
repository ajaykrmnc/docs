# Computer Architecture and System Programming Guides

This directory contains comprehensive guides on computer architecture and system programming topics, designed for system programmers who need deep understanding of how modern processors execute code.

## Document Overview

### Core Architecture

1. **[Machine Code Interpretation](machine_code_interpretation.md)**
   - ISA fundamentals (x86-64)
   - Register usage and calling conventions
   - Instruction encoding and operands
   - Data movement, arithmetic, and control flow
   - Procedures, stack frames, and calling conventions
   - Array and structure access patterns
   - **Prerequisites**: None (start here)
   - **Complexity**: Beginner to Intermediate

2. **[Microarchitecture and Pipelining](microarchitecture_and_pipelining.md)**
   - Architecture vs. microarchitecture distinction
   - Instruction pipelining (5-stage RISC pipeline)
   - Pipeline hazards (structural, data, control)
   - Forwarding and stall reduction
   - Superscalar execution and ILP
   - Performance analysis and optimization
   - **Prerequisites**: Machine Code Interpretation
   - **Complexity**: Intermediate

3. **[Out-of-Order Execution](out_of_order_execution.md)**
   - Why out-of-order execution is necessary
   - Register renaming (RAT, ROB)
   - Tomasulo's algorithm
   - Reservation stations and data forwarding
   - Speculative execution
   - Security implications (Spectre, Meltdown)
   - **Prerequisites**: Pipelining
   - **Complexity**: Advanced

4. **[Branch Prediction](branch_prediction.md)**
   - The branch prediction problem
   - Static vs. dynamic prediction
   - 1-bit, 2-bit saturating counters
   - Correlating predictors (gshare)
   - Tournament predictors
   - Branch Target Buffer (BTB)
   - Return address stack
   - **Prerequisites**: Pipelining
   - **Complexity**: Intermediate to Advanced

### Memory Systems

5. **[Cache Coherency Protocols](cache_coherency_protocols.md)**
   - The cache coherency problem
   - Snooping-based coherency
   - MESI protocol (Modified, Exclusive, Shared, Invalid)
   - MOESI protocol (adds Owned state)
   - False sharing and performance implications
   - Directory-based coherency
   - **Prerequisites**: Basic cache knowledge
   - **Complexity**: Advanced

6. **[Virtual Memory Implementation](virtual_memory_implementation.md)**
   - Virtual to physical address translation
   - Single-level and multi-level page tables
   - Translation Lookaside Buffer (TLB)
   - Page fault handling
   - Demand paging and copy-on-write
   - Huge pages (2MB, 1GB)
   - TLB optimization strategies
   - **Prerequisites**: Machine Code Interpretation
   - **Complexity**: Intermediate to Advanced

### Advanced Topics

7. **[Dynamic Binary Instrumentation](dynamic_binary_instrumentation.md)**
   - DBI concepts and architecture
   - Code cache and basic block translation
   - Instrumentation techniques
   - Major frameworks (Pin, DynamoRIO, Frida)
   - Applications (debugging, profiling, security)
   - Performance overhead and optimization
   - **Prerequisites**: Machine Code Interpretation
   - **Complexity**: Advanced

8. **[Just-In-Time Compilation](just_in_time_compilation.md)**
   - JIT vs. AOT vs. interpretation
   - Tiered compilation (interpreter → C1 → C2)
   - Optimization techniques (inlining, type specialization)
   - Code generation and IR
   - Deoptimization and guards
   - Practical implementations (HotSpot, V8, LLVM)
   - **Prerequisites**: Machine Code Interpretation
   - **Complexity**: Advanced

9. **[Hardware Transactional Memory](hardware_transactional_memory.md)**
   - Transactional memory fundamentals
   - Intel TSX (HLE and RTM)
   - Conflict detection and resolution
   - Capacity and abort limitations
   - Hybrid lock/transaction approaches
   - Performance characteristics
   - **Prerequisites**: Cache Coherency
   - **Complexity**: Advanced

## Learning Paths

### Path 1: Performance Optimization
```
1. Machine Code Interpretation
2. Microarchitecture and Pipelining
3. Cache Coherency Protocols
4. Branch Prediction
5. Out-of-Order Execution
```
**Focus**: Writing high-performance code, understanding bottlenecks

### Path 2: Systems Programming
```
1. Machine Code Interpretation
2. Virtual Memory Implementation
3. Dynamic Binary Instrumentation
4. Just-In-Time Compilation
```
**Focus**: OS development, runtime systems, language implementation

### Path 3: Concurrency and Parallelism
```
1. Machine Code Interpretation
2. Cache Coherency Protocols
3. Hardware Transactional Memory
```
**Focus**: Multithreaded programming, synchronization

### Path 4: Computer Architecture
```
1. Machine Code Interpretation
2. Microarchitecture and Pipelining
3. Branch Prediction
4. Out-of-Order Execution
5. Cache Coherency Protocols
```
**Focus**: Understanding modern processor design

## Key Concepts Map

```
                    Machine Code Interpretation
                              │
                ┌─────────────┴──────────────┐
                │                            │
         Pipelining                   Virtual Memory
                │                            │
        ┌───────┴───────┐                   │
        │               │                   │
  Branch Pred.    Out-of-Order              │
        │               │                   │
        └───────┬───────┘                   │
                │                            │
         Cache Coherency ───────────────────┘
                │
        ┌───────┴───────┐
        │               │
      HTM             DBI / JIT
```

## Practical Applications

### Performance Profiling
- **Relevant docs**: Pipelining, Branch Prediction, Cache Coherency
- **Tools**: perf, VTune, uProf
- **Focus**: Understanding performance counters, identifying bottlenecks

### Compiler Development
- **Relevant docs**: Machine Code, Pipelining, JIT Compilation
- **Tools**: LLVM, GCC
- **Focus**: Code generation, optimization passes

### Operating Systems
- **Relevant docs**: Virtual Memory, Cache Coherency
- **Tools**: Linux kernel source
- **Focus**: Memory management, synchronization primitives

### Security Research
- **Relevant docs**: Out-of-Order Execution, DBI
- **Tools**: Frida, AFL, LibFuzzer
- **Focus**: Side-channel attacks, fuzzing, taint analysis

### Language Runtimes
- **Relevant docs**: JIT Compilation, Virtual Memory, DBI
- **Tools**: V8, HotSpot, PyPy
- **Focus**: Dynamic optimization, garbage collection

## Recommended Tools

### Performance Analysis
- **Linux perf**: Hardware performance counters
- **Intel VTune**: Comprehensive profiling (x86)
- **AMD μProf**: AMD-specific profiling
- **valgrind/cachegrind**: Cache simulation

### Instrumentation
- **Intel Pin**: x86/x86-64 DBI framework
- **DynamoRIO**: Cross-platform DBI
- **Frida**: Dynamic instrumentation (mobile focus)

### Benchmarking
- **Google Benchmark**: C++ microbenchmarking
- **likwid**: Hardware performance monitoring
- **rdtsc**: Cycle-accurate measurement

### Visualization
- **Flamegraph**: Stack trace visualization
- **perf-map-agent**: Java symbol mapping
- **Compiler Explorer**: See generated assembly

## Additional Resources

### Books
- *Computer Systems: A Programmer's Perspective* (Bryant & O'Hallaron)
- *Computer Architecture: A Quantitative Approach* (Hennessy & Patterson)
- *Modern Processor Design* (Shen & Lipasti)

### Online Resources
- Intel® 64 and IA-32 Architectures Optimization Reference Manual
- Agner Fog's optimization guides (agner.org/optimize)
- AMD Software Optimization Guide

### Research Papers
- Tomasulo: "An Efficient Algorithm for Exploiting Multiple Arithmetic Units"
- Yeh & Patt: "Two-Level Adaptive Training Branch Prediction"
- Gharachorloo et al.: "Memory Consistency and Event Ordering"

## Document Conventions

### Code Examples
- **Assembly**: AT&T syntax (Linux/GCC convention)
- **C/C++**: POSIX-compliant where applicable
- **Measurements**: x86-64 unless specified

### Terminology
- **Cycle**: CPU clock cycle
- **IPC**: Instructions Per Cycle
- **CPI**: Cycles Per Instruction
- **Latency**: Time to complete operation
- **Throughput**: Operations per unit time

---

**Last Updated**: 2026-04-11
**Maintainer**: System Architecture Documentation Project
