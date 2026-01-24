# ARM vs x86 Architecture Guide for AP Development

## Table of Contents

1. [Overview](#overview)
2. [Terminology Clarification](#terminology-clarification)
3. [Why ARM for Access Points](#why-arm-for-access-points)
4. [Instruction Set Architecture (ISA)](#instruction-set-architecture-isa)
5. [Register Architecture](#register-architecture)
6. [Memory Architecture](#memory-architecture)
7. [Endianness](#endianness)
8. [SIMD and Vector Processing](#simd-and-vector-processing)
9. [Atomic Operations and Synchronization](#atomic-operations-and-synchronization)
10. [Exception and Interrupt Handling](#exception-and-interrupt-handling)
11. [Security Architecture](#security-architecture)
12. [Boot Process](#boot-process)
13. [Cross-Compilation](#cross-compilation)
14. [Kernel Considerations](#kernel-considerations)
15. [Driver Development Implications](#driver-development-implications)
16. [Performance Characteristics](#performance-characteristics)
17. [Debugging Differences](#debugging-differences)
18. [Code Patterns for Portability](#code-patterns-for-portability)
19. [Summary](#summary)

---

## Overview

This document provides an extensive technical reference for understanding the architectural differences 
between ARM and x86/x86_64 processors. It is specifically tailored for developers working on the Arista Access 
Point (AP) codebase, which cross-compiles from x86_64 development machines to ARM64 (aarch64) target hardware.

### Document Purpose

- Explain why ARM is the target architecture for AP hardware
- Detail low-level architectural differences affecting code behavior
- Provide practical guidance for writing portable, efficient code
- Document codebase-specific patterns and configurations

---

## Terminology Clarification

### The ARM vs Linux Confusion

A common misconception is that "ARM" and "Linux" are alternatives. They operate at completely different 
layers:

| Concept | What It Is | Layer | Example |
|---------|------------|-------|---------|
| **ARM** | CPU instruction set architecture | Hardware | Cortex-A73, Cortex-A53 |
| **x86/x86_64** | CPU instruction set architecture | Hardware | Intel Core, AMD Ryzen |
| **Linux** | Operating system kernel | Software | Kernel 5.4, 6.6 |
| **Windows** | Operating system | Software | Windows 11 |

**Key Insight:** This codebase runs **Linux on ARM processors**. The cross-compilation produces ARM binaries 
that execute on ARM hardware running the Linux kernel.

### Architecture Naming Conventions

| Name | Bits | ARM Version | Notes |
|------|------|-------------|-------|
| arm | 32-bit | ARMv7 and earlier | Legacy, used in bootloader |
| arm64 / aarch64 | 64-bit | ARMv8+ | Current AP target |
| x86 | 32-bit | IA-32 | Legacy Intel/AMD |
| x86_64 / amd64 | 64-bit | x86-64 | Development machines |

---

## Why ARM for Access Points

### 1. Target Hardware - QCA SoCs

The codebase targets Qualcomm/Atheros (QCA) System-on-Chip (SoC) platforms:

| Platform | SoC | CPU Cores | CPU Type | Process | WiFi |
|----------|-----|-----------|----------|---------|------|
| BELLS | IPQ9574 | 4× Cortex-A73 | ARMv8.2-A | 14nm | WiFi 7 (802.11be) |
| MIAMI | IPQ5332 | 4× Cortex-A53 | ARMv8-A | 14nm | WiFi 7 (802.11be) |

These SoCs are specifically designed for networking equipment and integrate:
- Multi-core ARM CPU
- WiFi 6E/7 baseband processors
- Ethernet MAC/PHY
- PCIe controllers for radio modules
- Hardware crypto acceleration
- DDR4 memory controller

### 2. Power Efficiency Comparison

| Metric | ARM Cortex-A73 | ARM Cortex-A53 | Intel Xeon | Intel Atom |
|--------|----------------|----------------|------------|------------|
| TDP | 2-4W | 0.5-2W | 85-205W | 6-15W |
| Performance/Watt | Excellent | Very Good | Moderate | Good |
| Idle Power | ~100mW | ~50mW | 5-10W | 1-3W |
| PoE Compatible | Yes (802.3at) | Yes (802.3af) | No | Marginal |

**Why This Matters for APs:**
- **PoE Deployment**: 802.3at provides max 30W, 802.3bt up to 90W
- **Thermal Design**: Fanless operation requires low heat dissipation
- **24/7 Operation**: Lower power = lower operating costs
- **Reliability**: Lower temperatures = longer component lifespan

### 3. Integration Benefits

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ARM SoC (e.g., IPQ9574)                          │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Cortex-A73  │  │ Cortex-A73  │  │ Cortex-A73  │  │ Cortex-A73  │   │
│  │   Core 0    │  │   Core 1    │  │   Core 2    │  │   Core 3    │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         └─────────────┬──┴──────────────┬─┴─────────────────┘          │
│                       │                 │                               │
│              ┌────────┴────────┐  ┌─────┴─────┐                        │
│              │   L2 Cache      │  │    GIC    │                        │
│              │   (1MB shared)  │  │ Interrupt │                        │
│              └────────┬────────┘  └───────────┘                        │
│                       │                                                 │
│         ┌─────────────┴─────────────────────────────────┐              │
│         │              System Bus / NoC                  │              │
│         └─┬───────┬───────┬───────┬───────┬───────┬────┘              │
│           │       │       │       │       │       │                     │
│     ┌─────┴──┐ ┌──┴───┐ ┌─┴────┐ ┌┴─────┐ ┌┴─────┐ ┌┴─────┐           │
│     │ DDR4   │ │PCIe  │ │ WiFi │ │ ETH  │ │Crypto│ │ USB  │           │
│     │ Ctrl   │ │ x4   │ │  BB  │ │ MAC  │ │ Eng  │ │ 3.0  │           │
│     └────────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘           │
└─────────────────────────────────────────────────────────────────────────┘

Equivalent x86 System Would Require:
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ x86 CPU  │  │ Chipset  │  │ WiFi PCIe│  │ ETH PCIe │  │ Crypto   │
│          │  │ (PCH)    │  │   Card   │  │   NIC    │  │   Card   │
└──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
↑             ↑             ↑             ↑             ↑
└─────────────┴─────────────┴─────────────┴─────────────┘
Multiple chips, higher cost, more power
```

---

## Instruction Set Architecture (ISA)

### RISC vs CISC Philosophy

| Aspect | ARM (RISC) | x86 (CISC) |
|--------|------------|------------|
| **Philosophy** | Simple instructions, compiler optimizes | Complex instructions, hardware optimizes |
| **Instruction Count** | ~1000 instructions | ~1500+ instructions |
| **Instruction Length** | Fixed (32-bit ARM, 32-bit A64) | Variable (1-15 bytes) |
| **Execution** | Most in 1 cycle | Variable, micro-ops |
| **Decode Complexity** | Simple, parallel | Complex, sequential stages |

### Instruction Encoding

**ARM64 (A64):**
```
All instructions are exactly 32 bits:
┌────────────────────────────────────────┐
│ 31  28 │ 27  24 │ 23  ...  5 │ 4   0  │
│  cond  │  op    │  operands  │   Rd   │
└────────────────────────────────────────┘
```

**x86_64:**
```
Variable length (1-15 bytes):
┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐
│ Prefix  │  REX    │ Opcode  │ ModR/M  │   SIB   │  Disp   │ Imm
│ 0-4 B   │  0-1 B  │  1-3 B  │  0-1 B  │  0-1 B  │ 0-4 B   │ 0-8 B
└─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘
```

### Load-Store Architecture

ARM uses a **load-store architecture** where:
- Only LOAD and STORE instructions access memory
- All other operations work on registers

x86 uses a **register-memory architecture** where:
- Many instructions can operate directly on memory
- More flexible but harder to pipeline

```c
// Adding two memory values

// ARM64 Assembly (load-store):
LDR X0, [X1]      // Load value from address in X1
LDR X2, [X3]      // Load value from address in X3
ADD X0, X0, X2    // Add in registers
STR X0, [X4]      // Store result

// x86_64 Assembly (register-memory):
MOV RAX, [RBX]    // Load from memory
ADD RAX, [RCX]    // Add directly from memory
MOV [RDX], RAX    // Store result
```

### Conditional Execution

**ARM:** Extensive conditional execution without branches
```asm
// ARM64: Conditional select
CMP X0, X1
CSEL X2, X3, X4, GT  // X2 = (X0 > X1) ? X3 : X4
```

**x86:** Relies more on conditional jumps, some CMOV instructions
```asm
// x86_64: Conditional move
CMP RAX, RBX
CMOVG RCX, RDX       // RCX = RDX if RAX > RBX
```

---

## Register Architecture

### General Purpose Registers

| Aspect | ARM64 (AArch64) | x86_64 |
|--------|-----------------|--------|
| **GP Registers** | 31 × 64-bit (X0-X30) | 16 × 64-bit |
| **32-bit Access** | W0-W30 (lower 32 bits) | EAX, EBX, etc. |
| **Stack Pointer** | SP (dedicated) | RSP |
| **Link Register** | X30 (LR) | Uses stack |
| **Frame Pointer** | X29 (FP) | RBP |
| **Zero Register** | XZR (reads as 0) | None |

### ARM64 Register Map

```
┌─────────────────────────────────────────────────────────────────┐
│                        ARM64 Registers                          │
├─────────────────────────────────────────────────────────────────┤
│ General Purpose:                                                │
│   X0-X7   : Arguments / Return values                          │
│   X8      : Indirect result location                           │
│   X9-X15  : Caller-saved temporaries                           │
│   X16-X17 : Intra-procedure-call scratch (IP0, IP1)            │
│   X18     : Platform register (reserved)                        │
│   X19-X28 : Callee-saved registers                             │
│   X29     : Frame pointer (FP)                                  │
│   X30     : Link register (LR)                                  │
│   SP      : Stack pointer                                       │
│   XZR     : Zero register (always reads 0)                      │
│   PC      : Program counter (not directly accessible)           │
├─────────────────────────────────────────────────────────────────┤
│ SIMD/Floating-Point:                                            │
│   V0-V31  : 128-bit SIMD registers                              │
│   (Also accessible as B/H/S/D/Q for 8/16/32/64/128-bit)        │
├─────────────────────────────────────────────────────────────────┤
│ System:                                                         │
│   NZCV    : Condition flags (Negative, Zero, Carry, Overflow)  │
│   FPCR    : Floating-point control                              │
│   FPSR    : Floating-point status                               │
└─────────────────────────────────────────────────────────────────┘
```

### x86_64 Register Map

```
┌─────────────────────────────────────────────────────────────────┐
│                        x86_64 Registers                         │
├─────────────────────────────────────────────────────────────────┤
│ General Purpose (64/32/16/8-bit views):                        │
│   RAX/EAX/AX/AL : Accumulator, return value                    │
│   RBX/EBX/BX/BL : Base, callee-saved                           │
│   RCX/ECX/CX/CL : Counter, 4th argument                        │
│   RDX/EDX/DX/DL : Data, 3rd argument                           │
│   RSI/ESI/SI    : Source index, 2nd argument                   │
│   RDI/EDI/DI    : Destination, 1st argument                    │
│   RBP/EBP/BP    : Base pointer, callee-saved                   │
│   RSP/ESP/SP    : Stack pointer                                 │
│   R8-R15        : Extended registers (R8-R11 caller-saved)     │
├─────────────────────────────────────────────────────────────────┤
│ SIMD (SSE/AVX):                                                 │
│   XMM0-XMM15  : 128-bit SSE registers                          │
│   YMM0-YMM15  : 256-bit AVX registers                          │
│   ZMM0-ZMM31  : 512-bit AVX-512 registers                      │
├─────────────────────────────────────────────────────────────────┤
│ Special:                                                        │
│   RIP         : Instruction pointer                             │
│   RFLAGS      : Flags register                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Why More Registers Matter

More registers reduce memory traffic:

```c
// Function with many local variables
void process_packet(packet_t *pkt) {
  uint32_t src_ip = pkt->src_ip;
  uint32_t dst_ip = pkt->dst_ip;
  uint16_t src_port = pkt->src_port;
  uint16_t dst_port = pkt->dst_port;
  uint8_t  protocol = pkt->protocol;
  uint32_t seq_num = pkt->seq;
  uint32_t ack_num = pkt->ack;
  uint16_t flags = pkt->flags;
  // ... more processing
}

// ARM64: All 8 variables fit in registers (X0-X7 available for temps)
// x86_64: May need to spill some to stack with only 6 caller-saved regs
```

---

## Memory Architecture

### Memory Ordering Models

This is one of the most critical differences for driver and concurrent code:

| Aspect | ARM | x86 |
|--------|-----|-----|
| **Model** | Weakly Ordered | Strongly Ordered (TSO) |
| **Loads reordered with Loads** | Yes | No |
| **Loads reordered with Stores** | Yes | No |
| **Stores reordered with Stores** | Yes | No |
| **Stores reordered with Loads** | Yes | Yes |
| **Atomic ops reordered** | Yes (without barriers) | No |

### Memory Barriers

ARM requires explicit memory barriers:

| ARM Barrier | x86 Equivalent | Purpose |
|-------------|----------------|---------|
| `DMB` (Data Memory Barrier) | `MFENCE` | Order memory accesses |
| `DSB` (Data Synchronization Barrier) | `MFENCE` | Complete all memory accesses |
| `ISB` (Instruction Synchronization Barrier) | Serialize | Flush instruction pipeline |
| `DMB ISHLD` | `LFENCE` | Load barrier within inner shareable |
| `DMB ISHST` | `SFENCE` | Store barrier within inner shareable |

**Critical Code Pattern:**

```c
// Writing to a device register then reading status
// ARM: Requires explicit barrier
void arm_write_and_read(volatile uint32_t *reg, volatile uint32_t *status) {
  *reg = 0x1;
  __asm__ __volatile__("dmb sy" ::: "memory");  // Ensure write completes
  uint32_t s = *status;
}

// x86: Usually works without explicit barrier due to TSO
void x86_write_and_read(volatile uint32_t *reg, volatile uint32_t *status) {
  *reg = 0x1;
  // Implicit ordering for stores followed by loads
  uint32_t s = *status;
}
```

### Memory Alignment

| Aspect | ARM64 | ARMv7 | x86_64 |
|--------|-------|-------|--------|
| **Unaligned Access** | Supported (may be slow) | Trap or slow | Fully supported |
| **Atomic Alignment** | Must be naturally aligned | Must be aligned | Recommended aligned |
| **Default Struct Packing** | Natural alignment | Natural alignment | Natural alignment |
| **Cache Line Size** | Typically 64 bytes | 32-64 bytes | 64 bytes |

**Safe Unaligned Access Pattern (from codebase):**

```c
// From ap/src/radius_utils/common.h
// These macros work correctly regardless of alignment

static inline u16 WPA_GET_BE16(const u8* a) {
  return (a[0] << 8) | a[1];
}

static inline void WPA_PUT_BE16(u8* a, u16 val) {
  a[0] = val >> 8;
  a[1] = val & 0xff;
}

static inline u32 WPA_GET_BE32(const u8* a) {
  return ((u32)a[0] << 24) | ((u32)a[1] << 16) |
  ((u32)a[2] << 8) | a[3];
}
```

### Cache Architecture

| Aspect | ARM Cortex-A73 | ARM Cortex-A53 | Intel Core |
|--------|----------------|----------------|------------|
| **L1 I-Cache** | 64KB | 32KB | 32KB |
| **L1 D-Cache** | 64KB | 32KB | 32KB |
| **L2 Cache** | 1-4MB shared | 512KB-1MB shared | 256KB/core |
| **L3 Cache** | N/A (SoC-level) | N/A | 8-30MB shared |
| **Cache Line** | 64 bytes | 64 bytes | 64 bytes |
| **Coherency** | MOESI via CCI/CCN | MOESI via CCI | MESIF |

### Virtual Memory

| Aspect | ARM64 | x86_64 |
|--------|-------|--------|
| **Page Sizes** | 4KB, 16KB, 64KB | 4KB, 2MB, 1GB |
| **Virtual Address Bits** | 48 (or 52 with LVA) | 48 (or 57 with LA57) |
| **Physical Address Bits** | 48 (configurable) | 46-52 |
| **TLB Architecture** | Unified or Split | Split I/D TLB |
| **ASID** | 8 or 16 bits | 12 bits (PCID) |

---

## Endianness

### Configuration in Codebase

ARM supports both endianness modes, but the AP codebase uses little-endian:

```makefile
# From ap/src/wlan-drivers/QCA/licensed/spf12_5_cs/os/linux/public/arm64-elf.inc
COPTS += -DAH_BYTE_ORDER=AH_LITTLE_ENDIAN
COPTS += -mlittle-endian

# Big-endian option exists but not used:
# From arm64-be-elf.inc
COPTS += -DAH_BYTE_ORDER=AH_BIG_ENDIAN
COPTS += -DBIG_ENDIAN_HOST=1
COPTS += -mbig-endian
```

### Why Little-Endian?

| Factor | Little-Endian | Big-Endian |
|--------|---------------|------------|
| **Network Protocols** | Requires byte swap | Native order |
| **x86 Compatibility** | Native | Requires swap |
| **File Formats** | Most use LE | Some use BE |
| **Industry Trend** | Dominant | Declining |

### Byte Order Macros

```c
// From ap/src/radius_utils/common.h

#if __BYTE_ORDER == __LITTLE_ENDIAN
#define le_to_host16(n) (n)
#define host_to_le16(n) (n)
#define be_to_host16(n) bswap_16(n)
#define host_to_be16(n) bswap_16(n)
#define le_to_host32(n) (n)
#define host_to_le32(n) (n)
#define be_to_host32(n) bswap_32(n)
#define host_to_be32(n) bswap_32(n)
#elif __BYTE_ORDER == __BIG_ENDIAN
#define le_to_host16(n) bswap_16(n)
#define host_to_le16(n) bswap_16(n)
#define be_to_host16(n) (n)
#define host_to_be16(n) (n)
// ... etc
#endif
```

### Runtime Endianness Detection

```go
// From ap/src/go/arista-ap/netlink/netlink_util.go
func SetEndianess() {
  buf := [2]byte{}
  *(*uint16)(unsafe.Pointer(&buf[0])) = uint16(0xABCD)

  switch buf {
  case [2]byte{0xCD, 0xAB}:
    NativeByteOrder = binary.LittleEndian
  case [2]byte{0xAB, 0xCD}:
    NativeByteOrder = binary.BigEndian
  default:
    NativeByteOrder = nil
    glog.Errorf("Failed to determine system endianness")
  }
}
```

---

## SIMD and Vector Processing

### ARM NEON vs x86 SSE/AVX

| Aspect | ARM NEON | x86 SSE | x86 AVX | x86 AVX-512 |
|--------|----------|---------|---------|-------------|
| **Register Width** | 128-bit | 128-bit | 256-bit | 512-bit |
| **Register Count** | 32 (V0-V31) | 16 (XMM) | 16 (YMM) | 32 (ZMM) |
| **Int Elements** | 8×16, 4×32, 2×64 | Same | Same | Same |
| **FP Elements** | 4×float, 2×double | Same | 8×float, 4×double | 16×float, 8×double |

### NEON in WiFi Processing

NEON is used for:
- CRC calculations
- Encryption/decryption (AES-NI equivalent)
- Packet checksum offload
- Signal processing

```c
// Example: NEON accelerated memory copy (conceptual)
#ifdef __ARM_NEON
#include <arm_neon.h>

void neon_memcpy_64(void *dst, const void *src, size_t len) {
  uint8_t *d = dst;
  const uint8_t *s = src;

  while (len >= 64) {
    uint8x16x4_t data = vld1q_u8_x4(s);
    vst1q_u8_x4(d, data);
    s += 64; d += 64; len -= 64;
  }
}
#endif
```

---

## Atomic Operations and Synchronization

### Mechanism Comparison

| Aspect | ARM | x86 |
|--------|-----|-----|
| **Atomic RMW** | LL/SC (LDXR/STXR) or LSE | LOCK prefix |
| **CAS** | LDXR + STXR loop or CASA | LOCK CMPXCHG |
| **Atomic Add** | LDXR + ADD + STXR or LDADD | LOCK ADD |
| **Memory Barriers** | Explicit (DMB/DSB/ISB) | Implicit with LOCK |
| **Acquire/Release** | LDAR/STLR | MOV (acquire), XCHG (release) |

### Load-Linked / Store-Conditional (ARM)

```asm
// ARM64 atomic increment (without LSE)
atomic_inc:
LDXR  W0, [X1]       // Load-exclusive
ADD   W0, W0, #1     // Increment
STXR  W2, W0, [X1]   // Store-exclusive, W2 = 0 if success
CBNZ  W2, atomic_inc // Retry if failed
RET
```

### LOCK Prefix (x86)

```asm
// x86_64 atomic increment
atomic_inc:
LOCK INC DWORD PTR [RDI]  // Atomic increment
RET
```

### Codebase Abstraction

```c
// From ap/src/wlan-drivers/QCA/licensed/11.1_ap_spf11/adf/os/linux/adf_os_atomic_pvt.h

typedef atomic_t __adf_os_atomic_t;

static inline a_status_t __adf_os_atomic_init(__adf_os_atomic_t *v) {
  atomic_set(v, 0);
  return A_STATUS_OK;
}

static inline a_uint32_t __adf_os_atomic_read(__adf_os_atomic_t *v) {
  return (atomic_read(v));
}

static inline void __adf_os_atomic_inc(__adf_os_atomic_t *v) {
  atomic_inc(v);  // Linux kernel handles arch differences
}

static inline void __adf_os_atomic_dec(__adf_os_atomic_t *v) {
  atomic_dec(v);
}

static inline a_uint32_t __adf_os_atomic_dec_and_test(__adf_os_atomic_t *v) {
  return atomic_dec_and_test(v);
}
```

---

## Exception and Interrupt Handling

### Privilege Levels

| ARM Exception Level | x86 Ring | Purpose |
|---------------------|----------|---------|
| EL0 | Ring 3 | User applications |
| EL1 | Ring 0 | OS kernel |
| EL2 | Ring -1 (VMX root) | Hypervisor |
| EL3 | N/A (SMM similar) | Secure monitor (TrustZone) |

### Exception Model

```
ARM64 Exception Model:
┌─────────────────────────────────────────────────────────────────┐
│ EL3 - Secure Monitor                                            │
│   • Manages transitions between Secure/Non-secure worlds        │
│   • Implements TrustZone switching                              │
├─────────────────────────────────────────────────────────────────┤
│ EL2 - Hypervisor                                                │
│   • Virtualizes EL1 for VMs                                     │
│   • Stage-2 page table management                               │
├─────────────────────────────────────────────────────────────────┤
│ EL1 - OS Kernel                                                 │
│   • Linux kernel runs here                                      │
│   • Device drivers, interrupt handlers                          │
├─────────────────────────────────────────────────────────────────┤
│ EL0 - User Applications                                         │
│   • User-space programs                                         │
│   • Least privileged                                            │
└─────────────────────────────────────────────────────────────────┘
```

### Interrupt Controllers

| Aspect | ARM GIC | x86 APIC |
|--------|---------|----------|
| **Type** | Generic Interrupt Controller | Advanced PIC |
| **Max IRQs** | 1020 (GICv2), 65536 (GICv3) | 256 |
| **MSI Support** | Yes (ITS in GICv3) | Yes |
| **Priority Levels** | 256 | 16 |
| **Affinity** | Per-IRQ CPU targeting | Per-IRQ CPU targeting |

---

## Security Architecture

### ARM TrustZone vs x86 Security

| Feature | ARM TrustZone | x86 Equivalent |
|---------|---------------|----------------|
| **Secure World** | EL3 + Secure EL1/EL0 | SGX Enclaves |
| **Isolation** | Hardware bus-level | Memory encryption |
| **Secure Boot** | Integrated | UEFI Secure Boot |
| **Crypto Accel** | Optional (e.g., CryptoCell) | AES-NI |
| **Key Storage** | OTP, secure fuses | TPM |

### TrustZone Memory Map

```
┌─────────────────────────────────────────────────────────────────┐
│                    Physical Address Space                        │
├────────────────────────────┬────────────────────────────────────┤
│     Non-Secure World       │        Secure World                │
│     (Normal Linux)         │        (Trusted OS)                │
├────────────────────────────┼────────────────────────────────────┤
│  • Normal OS               │  • Secure OS (OP-TEE, etc.)        │
│  • User applications       │  • Key management                   │
│  • Network stack           │  • DRM                              │
│  • WiFi drivers            │  • Secure storage                   │
└────────────────────────────┴────────────────────────────────────┘
↑                              ↑
│   SMC (Secure Monitor Call)  │
└──────────────────────────────┘
```

---

## Boot Process

### ARM vs x86 Boot Sequence

| Stage | ARM | x86 |
|-------|-----|-----|
| **ROM Code** | BootROM (SoC) | BIOS/UEFI firmware |
| **1st Stage** | SPL/BL1 | SEC/PEI |
| **2nd Stage** | U-Boot/BL2 | DXE |
| **OS Loader** | U-Boot/BL33 | GRUB/Windows Boot Manager |
| **Kernel** | Linux Image | Linux bzImage |

### U-Boot Configuration (from codebase)

```makefile
# From ap/platform/cvendors/QCA/SPF/12.5/src/bootloader/Makefile.sdk

ARCH := arm
KERNELARCH := $(ARCH)
CROSS := $(strip $(CACHE_TOOL) $(ARCH)-openwrt-linux-muslgnueabi-)

ifeq ($(PLATFORM_CHIPSET),BELLS)
DEF_CONFIG := ipq9574_defconfig
TOOLS_NAME := toolchain-arm_cortex-a73_gcc-7.5.0_musl-1.1.24
endif

ifeq ($(PLATFORM_CHIPSET),MIAMI)
DEF_CONFIG := ipq5332_defconfig
TOOLS_NAME := toolchain-arm_cortex-a73_gcc-7.5.0_musl-1.1.24
endif
```

---

## Cross-Compilation Setup

### Build Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Development Machine (x86_64)                  │
│                                                                 │
│  ┌─────────────┐    ┌──────────────────────────────────────┐   │
│  │ Source Code │───▶│ ARM Cross-Compiler                   │   │
│  │   (.c/.h)   │    │ (aarch64-none-linux-gnu-gcc)         │   │
│  └─────────────┘    └──────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│                     ┌────────────────┐                          │
│                     │ ARM64 Binary   │                          │
│                     │ (ELF aarch64)  │                          │
│                     └───────┬────────┘                          │
└─────────────────────────────│───────────────────────────────────┘
│ Deploy
▼
┌─────────────────────────────────────────────────────────────────┐
│                  Target Device (ARM64)                           │
│  ┌──────────────────┐  ┌────────────────┐  ┌───────────────┐   │
│  │ QCA IPQ9574/5332 │  │ Linux Kernel   │  │ AP Software   │   │
│  │ (Cortex-A73/A53) │  │ (arm64)        │  │ (arm64)       │   │
│  └──────────────────┘  └────────────────┘  └───────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Toolchain Configuration

From `ap/scripts/tools_vars.mk`:
```makefile
TOOLS_NAME := arm-gnu-toolchain-11.3.rel1-x86_64-aarch64-none-linux-gnu
#                                        ^^^^^^ host   ^^^^^^^ target
HOST := $(ARCH)-none-linux-gnu
CROSS := $(strip $(CACHE_TOOL) $(HOST)-)
```

### Platform-Specific Toolchains

| Platform | Toolchain | Target CPU |
|----------|-----------|------------|
| BELLS | `toolchain-aarch64_cortex-a73_gcc-7.5.0_musl` | Cortex-A73 |
| MIAMI | `toolchain-aarch64_cortex-a53_gcc-12.3.0_musl` | Cortex-A53 |
| Unit Tests | Native x86_64 gcc | x86_64 (host) |

### Meson Cross-Compilation

From `ap/scripts/meson-aarch64-cross-compilation.txt`:
```ini
[host_machine]
system = 'linux'
cpu_family = 'aarch64'
cpu = 'aarch64'
endian = 'little'
```

---

## Compilation Flags

### ARM64 Flags

```makefile
ARCH := aarch64
ARCH_ARGS := -march=armv8-a -mtune=cortex-a73
TARGET := arm64-elf
KERNELARCH := arm64

COPTS += -mlittle-endian -fno-strict-aliasing -fno-common
COPTS += -mcmodel=large  # For code > 4GB from GOT
```

### ARMv7 Flags (Legacy/Bootloader)

```makefile
ARCH := arm
COPTS += -D__LINUX_ARM_ARCH__=7 -march=armv7-a
COPTS += -mabi=aapcs-linux -mno-thumb-interwork -msoft-float
COPTS += -mlittle-endian -fno-strict-aliasing -fno-common -mlong-calls
```

### x86_64 Flags (Unit Tests)

```makefile
COPTS += -Wno-maybe-uninitialized
COPTS += -Wno-error=int-to-pointer-cast
```

---

## Code Patterns for Portability

### Endianness Detection (Runtime)

```go
// From ap/src/go/arista-ap/netlink/netlink_util.go
func SetEndianess() {
  buf := [2]byte{}
  *(*uint16)(unsafe.Pointer(&buf[0])) = uint16(0xABCD)

  switch buf {
  case [2]byte{0xCD, 0xAB}:
    NativeByteOrder = binary.LittleEndian
  case [2]byte{0xAB, 0xCD}:
    NativeByteOrder = binary.BigEndian
  }
}
```

### Byte Swap Macros

```c
// From ap/src/radius_utils/common.h
#define le_to_host16(n) (n)           // Little-endian host
#define be_to_host16(n) bswap_16(n)   // Swap big-endian to host
#define host_to_le16(n) (n)
#define host_to_be16(n) bswap_16(n)
```

### Packed Structures

```c
// For wire protocols - same layout on ARM and x86
#ifdef __GNUC__
#define __ATTRIB_PACK __attribute__ ((packed))
#endif

struct __ATTRIB_PACK protocol_header {
  uint8_t  version;
  uint16_t length;
  uint32_t sequence;
};
```

### Atomic Operations Abstraction

```c
// From adf_os_atomic_pvt.h
typedef atomic_t __adf_os_atomic_t;

static inline void __adf_os_atomic_inc(__adf_os_atomic_t *v) {
  atomic_inc(v);  // Uses LDXR/STXR on ARM, LOCK on x86
}
```

---

## Kernel Considerations

### Kernel Configuration Differences

| Aspect | ARM64 Kernel | x86_64 Kernel |
|--------|--------------|---------------|
| **Image Format** | Image, zImage, uImage | bzImage, vmlinuz |
| **Compression** | gzip, lz4, lzma | gzip, bzip2, lzma, xz |
| **Device Tree** | Required (DTB) | ACPI (DTB optional) |
| **Early Console** | earlycon=pl011 | earlyprintk=serial |
| **Boot Params** | Device Tree + cmdline | Bootloader protocol |

### Device Tree vs ACPI

**ARM uses Device Tree:**
```dts
// Example device tree snippet for QCA SoC
/ {
  model = "Qualcomm IPQ9574";
  compatible = "qcom,ipq9574";

  cpus {
    #address-cells = <1>;
    #size-cells = <0>;

    cpu@0 {
      device_type = "cpu";
      compatible = "arm,cortex-a73";
      reg = <0x0>;
      enable-method = "psci";
    };
  };

  wifi@c000000 {
    compatible = "qcom,ipq9574-wifi";
    reg = <0x0c000000 0x1000000>;
    interrupts = <GIC_SPI 320 IRQ_TYPE_LEVEL_HIGH>;
  };
};
```

**x86 uses ACPI:**
```
// ACPI tables provided by firmware
// No device tree needed (usually)
```

### Kernel Module Loading

From codebase build configuration:
```makefile
# Kernel modules are built for ARM64
KERNELARCH := arm64
TARGET := arm64-elf

# Module suffix is same (.ko) but binary format differs
# ARM64: ELF 64-bit LSB relocatable, ARM aarch64
# x86_64: ELF 64-bit LSB relocatable, x86-64
```

---

## Driver Development Implications

### Memory-Mapped I/O

```c
// Correct way to access MMIO registers (arch-independent)
#include <linux/io.h>

void device_write_reg(void __iomem *base, u32 offset, u32 value) {
  // writel handles memory barriers and endianness
  writel(value, base + offset);
}

u32 device_read_reg(void __iomem *base, u32 offset) {
  // readl handles memory barriers and endianness
  return readl(base + offset);
}

// WRONG: Direct pointer access (may fail on ARM due to ordering)
void bad_device_write(volatile u32 *reg, u32 value) {
  *reg = value;  // No barrier, may not work correctly on ARM
}
```

### DMA Considerations

| Aspect | ARM | x86 |
|--------|-----|-----|
| **Cache Coherency** | Often non-coherent | Usually coherent |
| **DMA API** | Requires cache management | May skip cache ops |
| **IOMMU** | SMMU | VT-d, AMD-Vi |
| **Address Bits** | 32 or 40+ bit DMA | Usually 64-bit |

```c
// Correct DMA buffer allocation
void *buf;
dma_addr_t dma_handle;

buf = dma_alloc_coherent(dev, size, &dma_handle, GFP_KERNEL);
// This handles:
// - ARM: Allocates uncached memory or manages cache
// - x86: Usually just allocates from normal pool

// For streaming DMA:
dma_handle = dma_map_single(dev, buf, size, DMA_TO_DEVICE);
// ARM: Flushes cache
// x86: Often no-op

dma_sync_single_for_device(dev, dma_handle, size, DMA_TO_DEVICE);
// ARM: Flush cache to ensure device sees data
// x86: Usually no-op (cache snooping)
```

### Interrupt Handling

```c
// Platform device interrupt (from device tree on ARM)
static int wifi_probe(struct platform_device *pdev) {
  int irq;

  // ARM: Gets IRQ from device tree
  // x86: Gets IRQ from ACPI or PCI
  irq = platform_get_irq(pdev, 0);
  if (irq < 0)
    return irq;

  ret = request_irq(irq, wifi_isr, IRQF_SHARED, "wifi", dev);
  return ret;
}
```

---

## Performance Characteristics

### Instruction Throughput

| Metric | Cortex-A73 | Cortex-A53 | Intel Core i7 |
|--------|------------|------------|---------------|
| **Issue Width** | 2-wide | 2-wide | 4-6 wide |
| **Pipeline Depth** | 11-15 stages | 8 stages | 14-19 stages |
| **OoO Window** | 128 entries | 40 entries | 224+ entries |
| **Branch Predictor** | Good | Basic | Excellent |
| **Clock Speed** | 2.0-2.5 GHz | 1.0-1.8 GHz | 3.0-5.0 GHz |

### Performance per Watt

```
Performance Comparison (Relative to Cortex-A53 @ 1W):

┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  Cortex-A53 @ 1W     ████████████████ 1.0x                    │
│                                                                │
│  Cortex-A73 @ 3W     ████████████████████████████████ 3.5x    │
│                                                                │
│  Intel Atom @ 6W     ████████████████████████ 2.5x            │
│                                                                │
│  Intel Core @ 35W    ████████████████████████████████████ 8x  │
│                      (but 35x power consumption)               │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Cache Optimization

```c
// Cache-friendly packet processing
// Align to cache line boundary
struct __attribute__((aligned(64))) packet_buffer {
  uint8_t data[1536];
  uint16_t length;
  uint16_t flags;
  // Pad to cache line
  uint8_t _pad[64 - 4];
};

// Prefetch hints (architecture-specific intrinsics)
#ifdef __aarch64__
__builtin_prefetch(next_packet, 0, 3);  // Read, high locality
#endif
```

---

## Debugging Differences

### Debug Interfaces

| Aspect | ARM | x86 |
|--------|-----|-----|
| **Debug Protocol** | CoreSight, JTAG | Intel DCI, JTAG |
| **Trace** | ETM (Embedded Trace Macrocell) | Intel PT |
| **Breakpoints (HW)** | 6-16 | 4 |
| **Watchpoints (HW)** | 4-16 | 4 |
| **Debug Registers** | MDSCR_EL1, etc. | DR0-DR7 |

### GDB Differences

```bash
# Cross-debugging ARM target from x86 host

# Start GDB server on target (ARM)
$ gdbserver :1234 ./my_program

# Connect from host (x86)
$ aarch64-linux-gnu-gdb ./my_program
(gdb) target remote target_ip:1234
(gdb) break main
(gdb) continue
```

### JTAG/SWD Debug

```
ARM Debug Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                         CoreSight                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │  ETM    │  │  PTM    │  │  ITM    │  │  HTM    │            │
│  │ (trace) │  │ (prog)  │  │ (instr) │  │  (bus)  │            │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
│       └────────────┴───────────┴────────────┘                   │
│                         │                                        │
│                  ┌──────┴──────┐                                 │
│                  │   Funnel    │                                 │
│                  └──────┬──────┘                                 │
│                         │                                        │
│                  ┌──────┴──────┐                                 │
│                  │    TPIU     │ ──── Trace Port                │
│                  └──────┬──────┘                                 │
│                         │                                        │
│                  ┌──────┴──────┐                                 │
│                  │  DAP/JTAG   │ ──── Debug Port                │
│                  └─────────────┘                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Code Patterns for Portability

### Compiler Intrinsics Abstraction

```c
// Memory barrier abstraction
#ifdef __aarch64__
#define mb()    __asm__ __volatile__("dmb sy" ::: "memory")
#define rmb()   __asm__ __volatile__("dmb ld" ::: "memory")
#define wmb()   __asm__ __volatile__("dmb st" ::: "memory")
#elif defined(__x86_64__)
#define mb()    __asm__ __volatile__("mfence" ::: "memory")
#define rmb()   __asm__ __volatile__("lfence" ::: "memory")
#define wmb()   __asm__ __volatile__("sfence" ::: "memory")
#endif

// Or use Linux kernel macros which handle this automatically
#include <asm/barrier.h>
// mb(), rmb(), wmb(), smp_mb(), etc.
```

### Packed Structures for Wire Protocols

```c
// From codebase pattern
#ifdef __GNUC__
#define __ATTRIB_PACK __attribute__ ((packed))
#endif

// Network protocol header - identical layout on ARM and x86
struct __ATTRIB_PACK ieee80211_hdr {
  uint16_t frame_control;
  uint16_t duration_id;
  uint8_t  addr1[6];
  uint8_t  addr2[6];
  uint8_t  addr3[6];
  uint16_t seq_ctrl;
};

// Verify structure size at compile time
_Static_assert(sizeof(struct ieee80211_hdr) == 24,
               "ieee80211_hdr size mismatch");
```

### Architecture-Specific Optimizations

```c
// Bit manipulation with architecture-specific intrinsics
static inline int count_leading_zeros(uint32_t x) {
#ifdef __aarch64__
  // ARM has CLZ instruction
  return __builtin_clz(x);
#elif defined(__x86_64__)
  // x86 uses BSR (bit scan reverse)
  return __builtin_clz(x);  // GCC handles translation
#else
  // Fallback
  int n = 0;
  if (x == 0) return 32;
  while (!(x & 0x80000000)) { n++; x <<= 1; }
  return n;
#endif
}

// CRC32 with hardware acceleration
static inline uint32_t crc32c_hw(uint32_t crc, uint8_t data) {
#ifdef __ARM_FEATURE_CRC32
  return __crc32cb(crc, data);
#elif defined(__SSE4_2__)
  return _mm_crc32_u8(crc, data);
#else
  return crc32c_table[(crc ^ data) & 0xFF] ^ (crc >> 8);
#endif
}
```

### Pointer Size Independence

```c
// Avoid assuming pointer size
// BAD:
uint32_t ptr_value = (uint32_t)some_pointer;  // Truncates on 64-bit

// GOOD:
uintptr_t ptr_value = (uintptr_t)some_pointer;  // Correct on both

// For kernel code:
unsigned long ptr_value = (unsigned long)some_pointer;
```

---

## Summary Comparison

| Dimension | ARM (Target) | x86_64 (Dev Machine) |
|-----------|--------------|----------------------|
| **Use Case** | Embedded AP hardware | Development workstation |
| **Power** | 2-10W | 35-125W |
| **ISA Type** | RISC (simple, fixed-length) | CISC (complex, variable) |
| **GP Registers** | 31 × 64-bit | 16 × 64-bit |
| **SIMD Registers** | 32 × 128-bit (NEON) | 16-32 × 256/512-bit (AVX) |
| **Endianness** | Bi-endian (uses LE) | Little-endian only |
| **Memory Ordering** | Weakly ordered | Strongly ordered (TSO) |
| **Memory Barriers** | Explicit required | Often implicit |
| **Privilege Levels** | EL0-EL3 | Ring 0-3 |
| **Virtualization** | EL2 (native) | VT-x (extension) |
| **Secure World** | TrustZone | SGX/TDX |
| **Boot Config** | Device Tree | ACPI |
| **Integration** | Full SoC | Discrete components |
| **Binaries** | ELF aarch64 | ELF x86-64 |
| **Debug** | CoreSight/JTAG | Intel DCI/JTAG |

---

## Quick Reference Tables

### Calling Conventions

| | ARM64 (AAPCS64) | x86_64 (System V) |
|---|-----------------|-------------------|
| **Args 1-8** | X0-X7 | RDI, RSI, RDX, RCX, R8, R9 |
| **Return** | X0 (and X1) | RAX (and RDX) |
| **Callee-saved** | X19-X28 | RBX, RBP, R12-R15 |
| **Stack Align** | 16 bytes | 16 bytes |

### Common Instructions Mapping

| Operation | ARM64 | x86_64 |
|-----------|-------|--------|
| Move | `MOV X0, X1` | `MOV RAX, RBX` |
| Add | `ADD X0, X1, X2` | `ADD RAX, RBX` |
| Load | `LDR X0, [X1]` | `MOV RAX, [RBX]` |
| Store | `STR X0, [X1]` | `MOV [RBX], RAX` |
| Branch | `B label` | `JMP label` |
| Call | `BL func` | `CALL func` |
| Return | `RET` | `RET` |
| Compare | `CMP X0, X1` | `CMP RAX, RBX` |
| Cond. Branch | `B.EQ label` | `JE label` |
| Atomic Inc | `LDADD X0, X1, [X2]` | `LOCK INC [RAX]` |

### Compiler Flags Reference

| Purpose | ARM64 Flag | x86_64 Flag |
|---------|------------|-------------|
| Architecture | `-march=armv8-a` | `-march=x86-64` |
| Tune | `-mtune=cortex-a73` | `-mtune=skylake` |
| Little-endian | `-mlittle-endian` | (default) |
| Position-indep | `-fPIC` | `-fPIC` |
| No strict alias | `-fno-strict-aliasing` | `-fno-strict-aliasing` |
| Large code model | `-mcmodel=large` | `-mcmodel=large` |

---

## References

### ARM Documentation
- ARM Architecture Reference Manual ARMv8-A (ARM DDI 0487)
- ARM Cortex-A73 Technical Reference Manual
- ARM Cortex-A53 Technical Reference Manual
- ARM Procedure Call Standard for ARM 64-bit Architecture (AAPCS64)
- ARM CoreSight Architecture Specification

### x86 Documentation
- Intel 64 and IA-32 Architectures Software Developer's Manual
- AMD64 Architecture Programmer's Manual
- System V Application Binary Interface AMD64

### QCA/Platform Specific
- Qualcomm IPQ9574 Technical Reference Manual
- Qualcomm IPQ5332 Technical Reference Manual
- OpenWrt Documentation for QCA platforms

### Linux Kernel
- Documentation/arm64/ in Linux kernel source
- Documentation/memory-barriers.txt
- Documentation/DMA-API.txt

### Codebase Files
- `ap/scripts/tools_vars.mk` - Toolchain configuration
- `ap/scripts/meson-aarch64-cross-compilation.txt` - Meson cross-compile
- `ap/platform/cvendors/QCA/SOC/*/common/config/config.platform` - Platform configs
- `ap/src/wlan-drivers/QCA/licensed/*/os/linux/public/*.inc` - Build includes

