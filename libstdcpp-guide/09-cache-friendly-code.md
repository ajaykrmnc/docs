# Writing Cache-Friendly Code: Complete Guide

## Table of Contents
1. [What is Cache and Why Does It Matter?](#what-is-cache-and-why-does-it-matter)
2. [How CPU Cache Works](#how-cpu-cache-works)
3. [Cache Terminology Explained Simply](#cache-terminology-explained-simply)
4. [The Golden Rules of Cache-Friendly Code](#the-golden-rules-of-cache-friendly-code)
5. [Data Structure Layout](#data-structure-layout)
6. [Array Access Patterns](#array-access-patterns)
7. [Loop Optimization](#loop-optimization)
8. [Common Cache Killers](#common-cache-killers)
9. [STL Containers and Cache Performance](#stl-containers-and-cache-performance)
10. [Practical Examples and Benchmarks](#practical-examples-and-benchmarks)
11. [Advanced Techniques](#advanced-techniques)
12. [Measuring Cache Performance](#measuring-cache-performance)

---

## What is Cache and Why Does It Matter?

### The Speed Problem

Modern computers have a huge speed gap between CPU and RAM:

```
CPU Speed:        ~3 GHz (billions of operations per second)
RAM Speed:        ~100 ns per access
CPU Cache Speed:  ~1-10 ns per access

Speed Difference: Cache is 10-100x FASTER than RAM!
```

### Real-World Analogy

Think of it like working in a kitchen:

- **RAM** = Pantry in the basement (far away, slow to access)
- **Cache** = Counter next to you (close, fast to access)
- **CPU** = You (the chef)

**Scenario 1: Cache-Friendly (Fast)**
```
You need: flour, sugar, eggs
Action: All ingredients are on the counter
Result: Cook quickly! ✅
```

**Scenario 2: Cache-Unfriendly (Slow)**
```
You need: flour, sugar, eggs
Action: Run to basement for flour, back to kitchen,
        run to basement for sugar, back to kitchen,
        run to basement for eggs...
Result: Exhausted and slow! ❌
```

### The Performance Impact

```cpp
// Example: Sum array elements

// Cache-friendly version
int sum = 0;
for (int i = 0; i < n; i++) {
    sum += array[i];  // Sequential access
}
// Speed: ~1-2 ns per element

// Cache-unfriendly version
int sum = 0;
for (int i = 0; i < n; i++) {
    sum += array[random_index[i]];  // Random access
}
// Speed: ~100 ns per element (50-100x SLOWER!)
```

**Real difference:** Cache-friendly code can be **10-100x faster** than cache-unfriendly code!

---

## How CPU Cache Works

### Cache Hierarchy

Modern CPUs have multiple levels of cache:

```
┌─────────────────────────────────────────────┐
│              CPU Core                       │
│  ┌──────────────────────────────────────┐  │
│  │  L1 Cache (32-64 KB)                 │  │  ← Fastest, smallest
│  │  Access time: ~1 ns                  │  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │  L2 Cache (256-512 KB)               │  │  ← Medium speed/size
│  │  Access time: ~3-5 ns                │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│  L3 Cache (8-32 MB, shared)              │  ← Slower, larger
│  Access time: ~10-20 ns                  │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│  RAM (8-64 GB)                           │  ← Slowest, largest
│  Access time: ~100 ns                    │
└─────────────────────────────────────────────┘
```

### Cache Lines

Cache doesn't load individual bytes - it loads **cache lines** (typically 64 bytes):

```cpp
// When you access array[0], the CPU loads:
int array[1000];
int x = array[0];  // Loads array[0] through array[15] (64 bytes)

// Now accessing array[1] through array[15] is FREE!
int y = array[1];  // Already in cache! ✅
int z = array[2];  // Already in cache! ✅
```

**Visual representation:**
```
Memory:  [0][1][2][3][4][5][6][7][8][9][10][11][12][13][14][15]...
         └────────────── Cache Line (64 bytes) ──────────────┘
         
Access array[0] → Entire cache line loaded
Access array[1-15] → Already in cache (fast!)
```

### Spatial Locality

**Principle:** If you access memory location X, you'll likely access nearby locations soon.

```cpp
// Good spatial locality (cache-friendly)
for (int i = 0; i < n; i++) {
    sum += array[i];  // Sequential: i, i+1, i+2, ...
}

// Bad spatial locality (cache-unfriendly)
for (int i = 0; i < n; i++) {
    sum += array[random[i]];  // Random jumps all over memory
}
```

### Temporal Locality

**Principle:** If you access memory location X, you'll likely access it again soon.

```cpp
// Good temporal locality
int x = array[0];
// ... use x multiple times ...
int y = x + 1;
int z = x * 2;

// Bad temporal locality
int x = array[0];
// ... do lots of other stuff ...
// ... access thousands of other memory locations ...
int y = array[0];  // Might be evicted from cache by now
```

---

## Cache Terminology Explained Simply

### Cache Hit vs Cache Miss

```cpp
int array[1000];

// First access
int x = array[0];  // CACHE MISS (not in cache, load from RAM)
                   // Loads cache line: array[0-15]

// Second access
int y = array[1];  // CACHE HIT (already in cache, fast!)

// Far away access
int z = array[500]; // CACHE MISS (different cache line)
```

**Cache Hit:** Data is in cache (fast, ~1-10 ns)  
**Cache Miss:** Data not in cache, must load from RAM (slow, ~100 ns)

### Cache Line

A **cache line** is the smallest unit of data transferred between cache and RAM.

- Typical size: **64 bytes**
- Contains multiple elements (e.g., 16 ints, 8 doubles)

```cpp
// One cache line can hold:
int array[16];      // 16 ints × 4 bytes = 64 bytes
double array[8];    // 8 doubles × 8 bytes = 64 bytes
char array[64];     // 64 chars × 1 byte = 64 bytes
```

### False Sharing

When multiple threads access different variables in the same cache line:

```cpp
struct Data {
    int counter1;  // Thread 1 uses this
    int counter2;  // Thread 2 uses this
};  // Both in same cache line!

// Problem: Even though threads access different variables,
// they fight over the same cache line (slow!)
```

**Solution:** Pad to separate cache lines:

```cpp
struct Data {
    int counter1;
    char padding[60];  // Force counter2 to different cache line
    int counter2;
};
```

### Prefetching

CPU tries to predict what data you'll need next and loads it early:

```cpp
// Sequential access - CPU can prefetch
for (int i = 0; i < n; i++) {
    sum += array[i];  // CPU predicts: "Next is array[i+1]"
}

// Random access - CPU cannot prefetch
for (int i = 0; i < n; i++) {
    sum += array[random[i]];  // CPU cannot predict
}
```

---

## The Golden Rules of Cache-Friendly Code

### Rule 1: Access Memory Sequentially

```cpp
❌ BAD: Random access
for (int i = 0; i < n; i++) {
    process(array[random_index[i]]);
}

✅ GOOD: Sequential access
for (int i = 0; i < n; i++) {
    process(array[i]);
}
```

### Rule 2: Keep Data Small and Compact

```cpp
❌ BAD: Large struct with unused data
struct Player {
    int id;
    char name[256];      // 256 bytes!
    char description[1024]; // 1024 bytes!
    int score;
};
// Total: ~1300 bytes per player

✅ GOOD: Small struct with only needed data
struct Player {
    int id;
    int score;
};
// Total: 8 bytes per player (162x smaller!)
```

### Rule 3: Use Arrays Instead of Linked Structures

```cpp
❌ BAD: Linked list (pointers jump around memory)
struct Node {
    int data;
    Node* next;  // Points to random memory location
};

✅ GOOD: Array (contiguous memory)
vector<int> data;  // All elements next to each other
```

### Rule 4: Process Data in Chunks

```cpp
❌ BAD: Process one element at a time from multiple arrays
for (int i = 0; i < n; i++) {
    result[i] = array1[i] + array2[i] + array3[i];
}

✅ GOOD: Process chunks to keep data in cache
const int CHUNK = 64;
for (int chunk = 0; chunk < n; chunk += CHUNK) {
    for (int i = chunk; i < min(chunk + CHUNK, n); i++) {
        result[i] = array1[i] + array2[i] + array3[i];
    }
}
```

### Rule 5: Avoid Unpredictable Branches

```cpp
❌ BAD: Unpredictable branch
for (int i = 0; i < n; i++) {
    if (array[i] % 2 == 0) {  // Unpredictable
        sum += array[i];
    }
}

✅ GOOD: Branchless code
for (int i = 0; i < n; i++) {
    sum += array[i] * (array[i] % 2 == 0);  // No branch
}
```

---

## Data Structure Layout

### Structure of Arrays (SoA) vs Array of Structures (AoS)

#### Array of Structures (AoS) - Often Cache-Unfriendly

```cpp
struct Particle {
    float x, y, z;     // Position (12 bytes)
    float vx, vy, vz;  // Velocity (12 bytes)
    float mass;        // Mass (4 bytes)
    float charge;      // Charge (4 bytes)
};  // Total: 32 bytes per particle

vector<Particle> particles(1000);

// Update only positions
for (int i = 0; i < particles.size(); i++) {
    particles[i].x += particles[i].vx * dt;
    particles[i].y += particles[i].vy * dt;
    particles[i].z += particles[i].vz * dt;
}
// Problem: Loads entire 32-byte struct, but only uses 24 bytes
// Wastes cache space on mass and charge!
```

**Memory layout:**
```
[x,y,z,vx,vy,vz,mass,charge][x,y,z,vx,vy,vz,mass,charge]...
 └────── Particle 0 ──────┘ └────── Particle 1 ──────┘
```

#### Structure of Arrays (SoA) - Cache-Friendly

```cpp
struct Particles {
    vector<float> x, y, z;        // Positions
    vector<float> vx, vy, vz;     // Velocities
    vector<float> mass;           // Masses
    vector<float> charge;         // Charges
};

Particles particles;
particles.x.resize(1000);
particles.y.resize(1000);
// ... etc

// Update only positions
for (int i = 0; i < particles.x.size(); i++) {
    particles.x[i] += particles.vx[i] * dt;
    particles.y[i] += particles.vy[i] * dt;
    particles.z[i] += particles.vz[i] * dt;
}
// Better: Only loads position and velocity data
// No wasted cache space!
```

**Memory layout:**
```
x:  [x0][x1][x2][x3]...
y:  [y0][y1][y2][y3]...
z:  [z0][z1][z2][z3]...
vx: [vx0][vx1][vx2][vx3]...
...
```

### When to Use Each

**Use AoS when:**
- You always access all fields together
- Code clarity is more important than performance
- Working with small datasets

**Use SoA when:**
- You often access only some fields
- Processing large datasets
- Performance is critical

### Hybrid Approach: AoSoA (Array of Structures of Arrays)

```cpp
struct ParticleChunk {
    float x[16], y[16], z[16];        // 16 particles
    float vx[16], vy[16], vz[16];
    float mass[16], charge[16];
};

vector<ParticleChunk> particles;

// Good cache locality within each chunk
// Reasonable code structure
```

---

## Array Access Patterns

### Row-Major vs Column-Major Order

#### 2D Array in C++ (Row-Major)

```cpp
int matrix[1000][1000];

❌ BAD: Column-major access (cache-unfriendly)
for (int col = 0; col < 1000; col++) {
    for (int row = 0; row < 1000; row++) {
        sum += matrix[row][col];  // Jumps 1000 elements each time!
    }
}

✅ GOOD: Row-major access (cache-friendly)
for (int row = 0; row < 1000; row++) {
    for (int col = 0; col < 1000; col++) {
        sum += matrix[row][col];  // Sequential access
    }
}
```

**Memory layout:**
```
matrix[0][0], matrix[0][1], matrix[0][2], ..., matrix[0][999],
matrix[1][0], matrix[1][1], matrix[1][2], ..., matrix[1][999],
...
```

**Performance difference:** Row-major can be **10-50x faster**!

#### Benchmark Example

```cpp
#include <iostream>
#include <chrono>
using namespace std;

const int N = 1000;
int matrix[N][N];

void columnMajor() {
    long long sum = 0;
    for (int col = 0; col < N; col++) {
        for (int row = 0; row < N; row++) {
            sum += matrix[row][col];  // Cache-unfriendly
        }
    }
}

void rowMajor() {
    long long sum = 0;
    for (int row = 0; row < N; row++) {
        for (int col = 0; col < N; col++) {
            sum += matrix[row][col];  // Cache-friendly
        }
    }
}

int main() {
    // Initialize
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            matrix[i][j] = i + j;
    
    auto start = chrono::high_resolution_clock::now();
    columnMajor();
    auto end = chrono::high_resolution_clock::now();
    auto duration1 = chrono::duration_cast<chrono::milliseconds>(end - start);
    
    start = chrono::high_resolution_clock::now();
    rowMajor();
    end = chrono::high_resolution_clock::now();
    auto duration2 = chrono::duration_cast<chrono::milliseconds>(end - start);
    
    cout << "Column-major: " << duration1.count() << " ms\n";
    cout << "Row-major: " << duration2.count() << " ms\n";
    cout << "Speedup: " << (double)duration1.count() / duration2.count() << "x\n";
    
    return 0;
}

// Typical output:
// Column-major: 45 ms
// Row-major: 3 ms
// Speedup: 15x
```

### Matrix Multiplication

```cpp
// Naive implementation (cache-unfriendly)
void matmul_naive(int A[N][N], int B[N][N], int C[N][N]) {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            C[i][j] = 0;
            for (int k = 0; k < N; k++) {
                C[i][j] += A[i][k] * B[k][j];  // B[k][j] is cache-unfriendly!
            }
        }
    }
}

// Cache-friendly implementation (transpose B first)
void matmul_optimized(int A[N][N], int B[N][N], int C[N][N]) {
    // Transpose B
    int BT[N][N];
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            BT[j][i] = B[i][j];
    
    // Now multiply with transposed B
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            C[i][j] = 0;
            for (int k = 0; k < N; k++) {
                C[i][j] += A[i][k] * BT[j][k];  // Both sequential!
            }
        }
    }
}
// Can be 2-5x faster!
```

---

## Loop Optimization

### Loop Tiling (Blocking)

Break large loops into smaller chunks that fit in cache:

```cpp
❌ BAD: Process entire arrays (doesn't fit in cache)
for (int i = 0; i < N; i++) {
    for (int j = 0; j < N; j++) {
        C[i][j] = A[i][j] + B[i][j];
    }
}

✅ GOOD: Process in tiles (fits in cache)
const int TILE = 64;
for (int ii = 0; ii < N; ii += TILE) {
    for (int jj = 0; jj < N; jj += TILE) {
        // Process tile
        for (int i = ii; i < min(ii + TILE, N); i++) {
            for (int j = jj; j < min(jj + TILE, N); j++) {
                C[i][j] = A[i][j] + B[i][j];
            }
        }
    }
}
```

### Loop Unrolling

Reduce loop overhead and improve cache usage:

```cpp
❌ NORMAL: Regular loop
for (int i = 0; i < n; i++) {
    sum += array[i];
}

✅ UNROLLED: Process multiple elements per iteration
for (int i = 0; i < n; i += 4) {
    sum += array[i];
    sum += array[i + 1];
    sum += array[i + 2];
    sum += array[i + 3];
}
// Handle remainder
for (int i = (n / 4) * 4; i < n; i++) {
    sum += array[i];
}
```

### Loop Fusion

Combine multiple loops to reuse cached data:

```cpp
❌ BAD: Separate loops (load data twice)
for (int i = 0; i < n; i++) {
    a[i] = b[i] + c[i];
}
for (int i = 0; i < n; i++) {
    d[i] = a[i] * 2;
}

✅ GOOD: Fused loop (load data once)
for (int i = 0; i < n; i++) {
    a[i] = b[i] + c[i];
    d[i] = a[i] * 2;
}
```

---

## Common Cache Killers

### 1. Pointer Chasing (Linked Lists)

```cpp
❌ CACHE KILLER: Linked list traversal
struct Node {
    int data;
    Node* next;  // Pointer to random memory location
};

Node* current = head;
while (current != nullptr) {
    process(current->data);
    current = current->next;  // Cache miss likely!
}

✅ CACHE FRIENDLY: Array/vector
vector<int> data;
for (int i = 0; i < data.size(); i++) {
    process(data[i]);  // Sequential, cache-friendly
}
```

**Performance difference:** Vector can be **10-100x faster** than linked list!

### 2. Virtual Function Calls

```cpp
❌ CACHE KILLER: Virtual functions (indirect call)
class Base {
public:
    virtual void process() = 0;
};

vector<Base*> objects;
for (auto* obj : objects) {
    obj->process();  // Indirect call through vtable
}

✅ CACHE FRIENDLY: Direct calls or templates
template<typename T>
void processAll(vector<T>& objects) {
    for (auto& obj : objects) {
        obj.process();  // Direct call, can be inlined
    }
}
```

### 3. Large Structs

```cpp
❌ CACHE KILLER: Large struct
struct Entity {
    int id;
    char name[256];
    char description[1024];
    float position[3];
    // ... lots more data
};  // 1300+ bytes!

vector<Entity> entities;
for (auto& e : entities) {
    e.position[0] += velocity;  // Loads entire 1300 bytes!
}

✅ CACHE FRIENDLY: Separate hot and cold data
struct EntityHot {
    int id;
    float position[3];
};  // 16 bytes

struct EntityCold {
    char name[256];
    char description[1024];
};

vector<EntityHot> hotData;
vector<EntityCold> coldData;

for (auto& e : hotData) {
    e.position[0] += velocity;  // Only loads 16 bytes!
}
```

### 4. Hash Tables with Poor Hash Functions

```cpp
❌ CACHE KILLER: Poor hash function causes clustering
unordered_map<int, int> map;
// Bad hash: all keys map to same bucket
// Causes long linked list traversal

✅ CACHE FRIENDLY: Good hash function spreads keys evenly
// Or use flat_map (sorted vector of pairs)
vector<pair<int, int>> flat_map;
sort(flat_map.begin(), flat_map.end());
// Binary search is cache-friendly for small/medium sizes
```

### 5. Excessive Indirection

```cpp
❌ CACHE KILLER: Multiple levels of indirection
vector<vector<int*>> data;
for (auto& row : data) {
    for (auto* ptr : row) {
        process(*ptr);  // Three pointer dereferences!
    }
}

✅ CACHE FRIENDLY: Flat structure
vector<int> data;
for (int val : data) {
    process(val);  // Direct access
}
```

---

## STL Containers and Cache Performance

### Container Performance Ranking (Cache-Friendliness)

**Most Cache-Friendly:**
1. `array` / `vector` - Contiguous memory, excellent cache locality
2. `deque` - Chunked contiguous memory, good cache locality
3. `string` - Contiguous (with SSO), good cache locality

**Medium Cache-Friendliness:**
4. `unordered_map` / `unordered_set` - Hash table, moderate locality
5. `map` / `set` - Tree structure, poor locality

**Least Cache-Friendly:**
6. `list` / `forward_list` - Linked list, terrible cache locality

### Detailed Comparison

#### vector vs list

```cpp
#include <vector>
#include <list>
#include <chrono>
#include <iostream>
using namespace std;

const int N = 1000000;

void test_vector() {
    vector<int> v(N);
    for (int i = 0; i < N; i++) v[i] = i;
    
    long long sum = 0;
    for (int val : v) {
        sum += val;
    }
}

void test_list() {
    list<int> l;
    for (int i = 0; i < N; i++) l.push_back(i);
    
    long long sum = 0;
    for (int val : l) {
        sum += val;
    }
}

int main() {
    auto start = chrono::high_resolution_clock::now();
    test_vector();
    auto end = chrono::high_resolution_clock::now();
    auto duration1 = chrono::duration_cast<chrono::milliseconds>(end - start);
    
    start = chrono::high_resolution_clock::now();
    test_list();
    end = chrono::high_resolution_clock::now();
    auto duration2 = chrono::duration_cast<chrono::milliseconds>(end - start);
    
    cout << "vector: " << duration1.count() << " ms\n";
    cout << "list: " << duration2.count() << " ms\n";
    cout << "list is " << (double)duration2.count() / duration1.count() << "x slower\n";
    
    return 0;
}

// Typical output:
// vector: 2 ms
// list: 50 ms
// list is 25x slower
```

#### map vs vector (for small datasets)

```cpp
// For small datasets (< 1000 elements), sorted vector can be faster!

❌ SLOWER: map for small data
map<int, int> m;
for (int i = 0; i < 100; i++) {
    m[i] = i * 2;
}
auto it = m.find(50);  // O(log n) but poor cache locality

✅ FASTER: sorted vector for small data
vector<pair<int, int>> v;
for (int i = 0; i < 100; i++) {
    v.push_back({i, i * 2});
}
sort(v.begin(), v.end());
auto it = lower_bound(v.begin(), v.end(), make_pair(50, 0));
// O(log n) but excellent cache locality
```

### When to Use Each Container

| Container | Use When | Cache Performance |
|-----------|----------|-------------------|
| `vector` | Default choice, random access | ⭐⭐⭐⭐⭐ Excellent |
| `array` | Fixed size known at compile time | ⭐⭐⭐⭐⭐ Excellent |
| `deque` | Need fast insert/delete at both ends | ⭐⭐⭐⭐ Good |
| `string` | Text data | ⭐⭐⭐⭐ Good |
| `unordered_map` | Fast lookup, large dataset | ⭐⭐⭐ Medium |
| `map` | Need sorted keys | ⭐⭐ Poor |
| `set` | Need sorted unique values | ⭐⭐ Poor |
| `list` | Frequent insert/delete in middle | ⭐ Very Poor |

---

## Practical Examples and Benchmarks

### Example 1: Particle System

```cpp
// Cache-unfriendly version
struct Particle {
    float x, y, z;
    float vx, vy, vz;
    float mass;
    int id;
    char name[64];  // Rarely used!
};

vector<Particle> particles(10000);

void update_unfriendly(float dt) {
    for (auto& p : particles) {
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        p.z += p.vz * dt;
    }
}
// Loads 88 bytes per particle, uses only 24 bytes

// Cache-friendly version
struct ParticleData {
    vector<float> x, y, z;
    vector<float> vx, vy, vz;
};

ParticleData particles;

void update_friendly(float dt) {
    for (size_t i = 0; i < particles.x.size(); i++) {
        particles.x[i] += particles.vx[i] * dt;
        particles.y[i] += particles.vy[i] * dt;
        particles.z[i] += particles.vz[i] * dt;
    }
}
// Loads only needed data, 3-4x faster!
```

### Example 2: Image Processing

```cpp
// Process image pixels

❌ CACHE-UNFRIENDLY: Column-major
void process_columns(unsigned char image[HEIGHT][WIDTH]) {
    for (int x = 0; x < WIDTH; x++) {
        for (int y = 0; y < HEIGHT; y++) {
            image[y][x] = process_pixel(image[y][x]);
        }
    }
}

✅ CACHE-FRIENDLY: Row-major
void process_rows(unsigned char image[HEIGHT][WIDTH]) {
    for (int y = 0; y < HEIGHT; y++) {
        for (int x = 0; x < WIDTH; x++) {
            image[y][x] = process_pixel(image[y][x]);
        }
    }
}
// Can be 10-20x faster for large images!
```

### Example 3: Game Entity System

```cpp
// Cache-unfriendly: Object-oriented approach
class Entity {
public:
    virtual void update() = 0;
    virtual void render() = 0;
protected:
    float x, y, z;
    float vx, vy, vz;
    // ... lots of other data
};

vector<Entity*> entities;

void update_all() {
    for (auto* e : entities) {
        e->update();  // Virtual call + scattered memory
    }
}

// Cache-friendly: Data-oriented approach
struct TransformComponent {
    vector<float> x, y, z;
};

struct VelocityComponent {
    vector<float> vx, vy, vz;
};

void update_all(TransformComponent& transform, 
                VelocityComponent& velocity, float dt) {
    for (size_t i = 0; i < transform.x.size(); i++) {
        transform.x[i] += velocity.vx[i] * dt;
        transform.y[i] += velocity.vy[i] * dt;
        transform.z[i] += velocity.vz[i] * dt;
    }
}
// 5-10x faster!
```

---

## Advanced Techniques

### 1. Cache Line Alignment

```cpp
// Align data to cache line boundaries
struct alignas(64) CacheLineAligned {
    int data[16];  // Exactly one cache line
};

// Prevent false sharing in multithreading
struct ThreadData {
    alignas(64) int counter1;  // Own cache line
    alignas(64) int counter2;  // Own cache line
};
```

### 2. Prefetching

```cpp
// Manual prefetch (GCC/Clang)
for (int i = 0; i < n; i++) {
    // Prefetch data for next iteration
    if (i + 8 < n) {
        __builtin_prefetch(&array[i + 8], 0, 3);
    }
    process(array[i]);
}
```

### 3. SIMD with Cache-Friendly Layout

```cpp
// Process 4 floats at once with SIMD
#include <immintrin.h>

void add_arrays_simd(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; i += 4) {
        __m128 va = _mm_load_ps(&a[i]);
        __m128 vb = _mm_load_ps(&b[i]);
        __m128 vc = _mm_add_ps(va, vb);
        _mm_store_ps(&c[i], vc);
    }
}
// Requires aligned, contiguous memory (cache-friendly!)
```

### 4. Memory Pooling

```cpp
// Custom allocator for cache-friendly allocation
template<typename T, size_t ChunkSize = 1024>
class PoolAllocator {
    vector<T*> chunks;
    size_t current_chunk = 0;
    size_t current_index = 0;
    
public:
    T* allocate() {
        if (current_index >= ChunkSize) {
            chunks.push_back(new T[ChunkSize]);
            current_chunk++;
            current_index = 0;
        }
        return &chunks[current_chunk][current_index++];
    }
    
    // All objects in same chunk are contiguous (cache-friendly!)
};
```

---

## Measuring Cache Performance

### Using perf (Linux)

```bash
# Compile your program
g++ -O3 -o program program.cpp

# Measure cache misses
perf stat -e cache-references,cache-misses ./program

# Output:
# 1,234,567 cache-references
#    12,345 cache-misses  # 1% miss rate (good!)
```

### Using Valgrind Cachegrind

```bash
# Run with cachegrind
valgrind --tool=cachegrind ./program

# Analyze results
cg_annotate cachegrind.out.<pid>

# Shows cache misses per line of code!
```

### Simple Timing Benchmark

```cpp
#include <chrono>
#include <iostream>

template<typename Func>
void benchmark(const char* name, Func func) {
    auto start = std::chrono::high_resolution_clock::now();
    func();
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << name << ": " << duration.count() << " ms\n";
}

int main() {
    benchmark("Cache-friendly", []() {
        // Your cache-friendly code
    });
    
    benchmark("Cache-unfriendly", []() {
        // Your cache-unfriendly code
    });
    
    return 0;
}
```

---

## Quick Reference Checklist

### ✅ Do This (Cache-Friendly)

- ✅ Use `vector` instead of `list`
- ✅ Access arrays sequentially (row-major in C++)
- ✅ Keep structs small (< 64 bytes if possible)
- ✅ Use Structure of Arrays (SoA) for large datasets
- ✅ Process data in chunks that fit in cache
- ✅ Align data to cache line boundaries (64 bytes)
- ✅ Use contiguous memory (arrays, vectors)
- ✅ Fuse loops to reuse cached data
- ✅ Prefetch data when access pattern is predictable

### ❌ Avoid This (Cache-Unfriendly)

- ❌ Don't use linked lists for large datasets
- ❌ Don't access 2D arrays column-major
- ❌ Don't create huge structs with rarely-used fields
- ❌ Don't use Array of Structures (AoS) for selective access
- ❌ Don't chase pointers (indirection)
- ❌ Don't use virtual functions in hot loops
- ❌ Don't access memory randomly
- ❌ Don't create false sharing in multithreaded code

---

## Summary

### Key Takeaways

1. **Cache is 10-100x faster than RAM** - optimize for it!
2. **Sequential access is king** - access memory in order
3. **Keep data compact** - smaller structs = more in cache
4. **Use arrays, not linked lists** - contiguous memory wins
5. **Measure, don't guess** - profile your code

### The 80/20 Rule

**80% of cache optimization comes from:**
1. Using `vector` instead of `list`
2. Accessing arrays sequentially (row-major)
3. Keeping structs small
4. Using Structure of Arrays for large datasets

**Focus on these four things first!**

### Final Advice

- **Start simple:** Use `vector`, access sequentially
- **Measure:** Profile before and after optimization
- **Don't over-optimize:** Readability matters too
- **Know your data:** Hot paths need optimization, cold paths don't

---

**Remember: Cache-friendly code is often simpler code. Use simple data structures (arrays/vectors), access them sequentially, and you're 90% there!** 🚀

