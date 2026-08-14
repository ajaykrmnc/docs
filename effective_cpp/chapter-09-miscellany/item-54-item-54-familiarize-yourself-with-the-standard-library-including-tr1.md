# Item 54: Familiarize Yourself with the Standard Library, Including TR1

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│  ITEM 54: FAMILIARIZE YOURSELF WITH THE STANDARD LIBRARY, INCLUDING TR1   │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Need common data structure/algorithm/utility -> check standard         │
│ library first.                                                            │
│ 2. Containers, algorithms, iterators, function objects, smart pointers    │
│ solve common patterns.                                                    │
│ 3. Library code is portable, tested, and idiomatic.                       │
│ 4. Custom code remains for domain-specific behavior.                      │
│ 5. Meaning: standard components reduce bugs and make intent               │
│ recognizable.                                                             │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                           STANDARD LIBRARY MAP                            │
├───────────────────────────────────────────────────────────────────────────┤
│ Containers -> vector, map, unordered_map, set, deque                      │
│ Algorithms -> sort, find, transform, accumulate                           │
│ Utilities -> smart pointers, function objects, bind/function              │
│ Iterators -> uniform access between containers and algorithms             │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                                REUSE FLOW                                 │
├───────────────────────────────────────────────────────────────────────────┤
│ Need common structure or operation                                        │
│                                     ▼                                     │
│ Check standard library first                                              │
│                                     ▼                                     │
│ Use tested idiomatic component                                            │
│                                     ▼                                     │
│ Write custom code only for domain-specific behavior                       │
└───────────────────────────────────────────────────────────────────────────┘
```

### Core Concept

When Meyers wrote this item, TR1 (Technical Report 1) was a preview of features that would eventually be incorporated into C++11. Today, everything from TR1 and much more is part of the standard library. This item is a comprehensive tour of the standard library as it exists through C++20, noting which components originated in TR1 and which were added later.

### Historical Context: TR1 to C++20

TR1 (2005) previewed these components under `std::tr1::`. All of them are now in `std::`:

| TR1 Component | Modern Standard | Header |
|---|---|---|
| `shared_ptr`, `weak_ptr` | C++11 | `<memory>` |
| `function` | C++11 | `<functional>` |
| `bind` | C++11 (largely replaced by lambdas) | `<functional>` |
| `tuple` | C++11 | `<tuple>` |
| `array` | C++11 | `<array>` |
| `unordered_set`, `unordered_map` | C++11 | `<unordered_set>`, `<unordered_map>` |
| `regex` | C++11 | `<regex>` |
| `type_traits` | C++11 (greatly expanded) | `<type_traits>` |
| `random` | C++11 | `<random>` |
| `reference_wrapper`, `ref`, `cref` | C++11 | `<functional>` |
| `result_of` | C++11 (deprecated C++17, removed C++20) | `<type_traits>` |

### Smart Pointers

TR1 introduced `shared_ptr` and `weak_ptr`. C++11 added `unique_ptr` (replacing the deprecated `auto_ptr`). C++14 added `make_unique`.

```cpp
#include <memory>

// BAD: Raw owning pointers
class ResourceManager {
public:
    ResourceManager() {
        db_ = new DatabaseConnection("localhost:5432");
        cache_ = new Cache(1024);
    }

    ~ResourceManager() {
        delete cache_;
        delete db_;  // If Cache destructor throws, db_ leaks
    }

private:
    DatabaseConnection* db_;
    Cache* cache_;
};

// GOOD: Smart pointers (C++14)
class ResourceManager {
public:
    ResourceManager()
        : db_(std::make_unique<DatabaseConnection>("localhost:5432"))
        , cache_(std::make_unique<Cache>(1024))
    {
        // If Cache constructor throws, db_ is automatically cleaned up
    }

    // No destructor needed — smart pointers handle cleanup
    // Implicitly deleted copy constructor/assignment (unique_ptr is move-only)

private:
    std::unique_ptr<DatabaseConnection> db_;
    std::unique_ptr<Cache> cache_;
};
```

```cpp
// shared_ptr: Shared ownership with reference counting
class TextureCache {
public:
    std::shared_ptr<Texture> getTexture(const std::string& path) {
        auto it = cache_.find(path);
        if (it != cache_.end()) {
            // Try to lock the weak_ptr — texture may have been evicted
            if (auto sp = it->second.lock()) {
                return sp;  // Cache hit
            }
        }
        // Cache miss — load and cache
        auto texture = std::make_shared<Texture>(path);
        cache_[path] = texture;  // Store as weak_ptr
        return texture;
    }

private:
    // weak_ptr avoids preventing texture destruction when no one is using it
    std::unordered_map<std::string, std::weak_ptr<Texture>> cache_;
};

// unique_ptr with custom deleter
auto fileDeleter = [](FILE* f) { if (f) std::fclose(f); };
std::unique_ptr<FILE, decltype(fileDeleter)> file(std::fopen("data.txt", "r"), fileDeleter);
```

### Containers

The standard library provides a rich set of containers. Here is the complete landscape:

```cpp
#include <vector>
#include <deque>
#include <list>
#include <forward_list>    // C++11
#include <array>           // C++11 (from TR1)
#include <set>
#include <map>
#include <unordered_set>   // C++11 (from TR1)
#include <unordered_map>   // C++11 (from TR1)
#include <stack>
#include <queue>
#include <span>            // C++20

// --- Sequence Containers ---

// std::array — fixed-size array with STL interface (TR1 -> C++11)
std::array<int, 5> scores = {95, 87, 92, 78, 88};
// Advantages over C arrays: knows its size, can be copied, works with algorithms
auto it = std::find(scores.begin(), scores.end(), 92);
std::sort(scores.begin(), scores.end());

// std::vector — dynamic array, the default container
std::vector<std::string> names;
names.reserve(1000);  // Pre-allocate to avoid reallocations
names.emplace_back("Alice");  // C++11: construct in-place

// std::deque — double-ended queue
std::deque<int> dq;
dq.push_front(1);  // O(1)
dq.push_back(2);   // O(1)

// std::list — doubly-linked list
std::list<int> lst = {3, 1, 4, 1, 5};
lst.sort();           // Member function sort (can't use std::sort — no random access)
lst.unique();         // Remove consecutive duplicates
lst.merge(otherList); // Merge two sorted lists

// std::forward_list — singly-linked list (C++11)
std::forward_list<int> fl = {1, 2, 3};
fl.push_front(0);
// Minimal overhead — no size() member, insert_after instead of insert

// --- Associative Containers ---

// std::set / std::multiset — sorted unique/non-unique keys (red-black tree)
std::set<std::string> uniqueWords;
uniqueWords.insert("hello");
uniqueWords.insert("world");
uniqueWords.insert("hello");  // Ignored — already present
// uniqueWords.size() == 2

// std::map / std::multimap — sorted key-value pairs (red-black tree)
std::map<std::string, int> wordCount;
wordCount["hello"]++;
wordCount["world"]++;
wordCount["hello"]++;
// wordCount["hello"] == 2

// C++17: Structured bindings for map iteration
for (const auto& [word, count] : wordCount) {
    std::cout << word << ": " << count << "\n";
}

// C++17: try_emplace and insert_or_assign
wordCount.try_emplace("new_word", 1);         // Only inserts if key doesn't exist
wordCount.insert_or_assign("hello", 100);     // Inserts or overwrites

// C++17: extract and merge nodes between maps
auto node = wordCount.extract("hello");
node.key() = "greeting";  // Change the key without reallocating the value!
wordCount.insert(std::move(node));

// --- Unordered (Hash) Containers (TR1 -> C++11) ---

// std::unordered_set / std::unordered_multiset — hash-based unique/non-unique keys
std::unordered_set<std::string> fastLookup;
fastLookup.insert("alpha");
fastLookup.count("alpha");   // O(1) average
fastLookup.contains("alpha"); // C++20 — cleaner than count()

// std::unordered_map / std::unordered_multimap — hash-based key-value pairs
std::unordered_map<std::string, std::vector<int>> index;
index["chapter1"] = {1, 5, 12, 47};

// Custom hash for user-defined types:
struct Point { int x, y; };

struct PointHash {
    std::size_t operator()(const Point& p) const noexcept {
        auto h1 = std::hash<int>{}(p.x);
        auto h2 = std::hash<int>{}(p.y);
        return h1 ^ (h2 << 1);
    }
};

struct PointEqual {
    bool operator()(const Point& a, const Point& b) const noexcept {
        return a.x == b.x && a.y == b.y;
    }
};

std::unordered_set<Point, PointHash, PointEqual> pointSet;

// --- Container Adaptors ---

// std::stack — LIFO (default: backed by deque)
std::stack<int> callStack;
callStack.push(42);
int top = callStack.top();
callStack.pop();

// std::queue — FIFO (default: backed by deque)
std::queue<std::string> messageQueue;
messageQueue.push("first");
std::string msg = messageQueue.front();
messageQueue.pop();

// std::priority_queue — max-heap (default: backed by vector)
std::priority_queue<int> maxHeap;
maxHeap.push(3);
maxHeap.push(1);
maxHeap.push(4);
int highest = maxHeap.top();  // 4

// Min-heap:
std::priority_queue<int, std::vector<int>, std::greater<int>> minHeap;

// --- C++20: std::span ---
void processData(std::span<const int> data) {
    // Non-owning view of contiguous data — works with vector, array, C arrays
    for (int val : data) {
        std::cout << val << " ";
    }
}

std::vector<int> v = {1, 2, 3, 4, 5};
int arr[] = {10, 20, 30};
processData(v);    // Works
processData(arr);  // Also works
processData(std::span(v).subspan(1, 3));  // View of elements [1..3]
```

### Algorithms

The `<algorithm>` header is one of the most powerful parts of the standard library:

```cpp
#include <algorithm>
#include <numeric>     // accumulate, iota, etc.
#include <execution>   // C++17 parallel algorithms

std::vector<int> data = {5, 3, 8, 1, 9, 2, 7, 4, 6};

// --- Sorting and Ordering ---
std::sort(data.begin(), data.end());                          // Ascending
std::sort(data.begin(), data.end(), std::greater<int>{});     // Descending
std::stable_sort(data.begin(), data.end());                   // Preserves relative order of equal elements
std::partial_sort(data.begin(), data.begin() + 3, data.end()); // Top 3 elements sorted
std::nth_element(data.begin(), data.begin() + 4, data.end()); // Median (5th element in correct position)

// --- Searching ---
auto it = std::find(data.begin(), data.end(), 7);
auto it2 = std::find_if(data.begin(), data.end(), [](int x) { return x > 5; });
bool found = std::binary_search(data.begin(), data.end(), 7); // Requires sorted range
auto [lo, hi] = std::equal_range(data.begin(), data.end(), 5); // Range of equal elements

// --- Modifying ---
std::transform(data.begin(), data.end(), data.begin(),
               [](int x) { return x * 2; });  // Double each element

std::replace_if(data.begin(), data.end(),
                [](int x) { return x < 0; }, 0);  // Replace negatives with 0

data.erase(
    std::remove_if(data.begin(), data.end(), [](int x) { return x % 2 == 0; }),
    data.end()
);  // Erase-remove idiom: delete all even numbers

// C++20: std::erase_if simplifies this
std::erase_if(data, [](int x) { return x % 2 == 0; });

// --- Aggregation ---
int sum = std::accumulate(data.begin(), data.end(), 0);
int product = std::accumulate(data.begin(), data.end(), 1, std::multiplies<int>{});
auto [minIt, maxIt] = std::minmax_element(data.begin(), data.end());

// --- Set Operations (on sorted ranges) ---
std::vector<int> a = {1, 2, 3, 4, 5};
std::vector<int> b = {3, 4, 5, 6, 7};
std::vector<int> result;

std::set_intersection(a.begin(), a.end(), b.begin(), b.end(),
                      std::back_inserter(result));  // {3, 4, 5}

result.clear();
std::set_union(a.begin(), a.end(), b.begin(), b.end(),
               std::back_inserter(result));  // {1, 2, 3, 4, 5, 6, 7}

result.clear();
std::set_difference(a.begin(), a.end(), b.begin(), b.end(),
                    std::back_inserter(result));  // {1, 2}

// --- Permutations ---
std::vector<int> perm = {1, 2, 3};
do {
    // Process each permutation: {1,2,3}, {1,3,2}, {2,1,3}, ...
} while (std::next_permutation(perm.begin(), perm.end()));

// --- C++17 Parallel Algorithms ---
std::vector<double> bigData(10000000);
std::sort(std::execution::par, bigData.begin(), bigData.end());  // Parallel sort
auto total = std::reduce(std::execution::par, bigData.begin(), bigData.end());
std::for_each(std::execution::par_unseq, bigData.begin(), bigData.end(),
              [](double& x) { x = std::sin(x); });

// --- C++20 Ranges ---
#include <ranges>

// Composable, lazy algorithm pipelines
auto evens = data | std::views::filter([](int x) { return x % 2 == 0; });
auto squares = data | std::views::transform([](int x) { return x * x; });
auto firstThreeSquaredEvens = data
    | std::views::filter([](int x) { return x % 2 == 0; })
    | std::views::transform([](int x) { return x * x; })
    | std::views::take(3);

for (int val : firstThreeSquaredEvens) {
    std::cout << val << " ";
}

// Ranges-based algorithms (take ranges directly, not iterator pairs)
std::ranges::sort(data);
auto found_it = std::ranges::find(data, 42);
bool all_positive = std::ranges::all_of(data, [](int x) { return x > 0; });
```

### Iterators

```cpp
#include <iterator>

// Iterator categories (from weakest to strongest):
// InputIterator       -> read-once, forward-only (e.g., istream_iterator)
// OutputIterator      -> write-once, forward-only (e.g., ostream_iterator)
// ForwardIterator     -> read/write, multi-pass forward (e.g., forward_list::iterator)
// BidirectionalIterator -> + backward movement (e.g., list::iterator, set::iterator)
// RandomAccessIterator  -> + O(1) jumps (e.g., vector::iterator, deque::iterator)
// ContiguousIterator    -> + contiguous memory (C++20) (e.g., vector::iterator, array::iterator)

// Stream iterators — treat I/O as ranges
std::vector<int> readFromInput() {
    std::vector<int> result;
    std::copy(std::istream_iterator<int>(std::cin),
              std::istream_iterator<int>(),
              std::back_inserter(result));
    return result;
}

void writeToOutput(const std::vector<int>& data) {
    std::copy(data.begin(), data.end(),
              std::ostream_iterator<int>(std::cout, ", "));
}

// Insert iterators
std::vector<int> src = {1, 2, 3};
std::vector<int> dst;
std::copy(src.begin(), src.end(), std::back_inserter(dst));     // push_back
std::copy(src.begin(), src.end(), std::front_inserter(dst));    // push_front (deque, list)
std::copy(src.begin(), src.end(), std::inserter(dst, dst.begin())); // insert at position

// Reverse iterators
std::vector<int> v = {1, 2, 3, 4, 5};
for (auto rit = v.rbegin(); rit != v.rend(); ++rit) {
    std::cout << *rit << " ";  // 5 4 3 2 1
}

// Move iterators (C++11) — convert copy operations to moves
std::vector<std::string> source = {"hello", "world"};
std::vector<std::string> target;
std::move(source.begin(), source.end(), std::back_inserter(target));
// source strings are now in moved-from state
```

### Function Objects and Callables

```cpp
#include <functional>

// --- std::function (TR1 -> C++11) ---
// Type-erased callable wrapper — can hold functions, lambdas, functors, member pointers

std::function<int(int, int)> operation;

operation = [](int a, int b) { return a + b; };
std::cout << operation(3, 4) << "\n";  // 7

operation = std::multiplies<int>{};
std::cout << operation(3, 4) << "\n";  // 12

int divide(int a, int b) { return a / b; }
operation = divide;
std::cout << operation(12, 4) << "\n";  // 3

// BAD: Using std::function when a template parameter would suffice
// std::function has overhead: heap allocation, virtual dispatch
void sortWithComparator(std::vector<int>& v, std::function<bool(int, int)> comp) {
    std::sort(v.begin(), v.end(), comp);
}

// GOOD: Use template parameter for zero-overhead
template<typename Comparator>
void sortWithComparator(std::vector<int>& v, Comparator comp) {
    std::sort(v.begin(), v.end(), comp);
}

// GOOD: Use std::function when you NEED type erasure (e.g., storing in a container)
std::map<std::string, std::function<double(double, double)>> operations = {
    {"add", [](double a, double b) { return a + b; }},
    {"sub", [](double a, double b) { return a - b; }},
    {"mul", [](double a, double b) { return a * b; }},
    {"div", [](double a, double b) { return a / b; }},
};

double result = operations["add"](3.0, 4.0);  // 7.0

// --- std::bind (TR1 -> C++11) — largely superseded by lambdas ---

// BAD: std::bind is harder to read
auto bound = std::bind(divide, std::placeholders::_1, 2);
bound(10);  // divide(10, 2) = 5

// GOOD: Lambda is clearer
auto divideByTwo = [](int x) { return divide(x, 2); };
divideByTwo(10);  // 5

// --- std::reference_wrapper (TR1 -> C++11) ---
// Allows references to be stored in containers and used with std::bind/function

void increment(int& x) { ++x; }

int value = 10;
auto ref = std::ref(value);  // Creates reference_wrapper<int>

// Store references in a vector (vector<int&> is illegal, but vector<reference_wrapper<int>> works)
std::vector<std::reference_wrapper<int>> refs;
int a = 1, b = 2, c = 3;
refs.push_back(std::ref(a));
refs.push_back(std::ref(b));
refs.push_back(std::ref(c));
for (auto& r : refs) {
    r.get() *= 10;  // Modifies original variables
}
// a == 10, b == 20, c == 30

// --- std::invoke (C++17) — unified call syntax ---
struct Foo {
    int value = 42;
    int getValue() const { return value; }
};

Foo foo;
int v1 = std::invoke(&Foo::getValue, foo);  // Member function call
int v2 = std::invoke(&Foo::value, foo);     // Member access
int v3 = std::invoke([](int x) { return x + 1; }, 41);  // Lambda
```

### Tuples

```cpp
#include <tuple>

// std::tuple (TR1 -> C++11)
std::tuple<std::string, int, double> person("Alice", 30, 5.6);

// Access
std::string name = std::get<0>(person);
int age = std::get<1>(person);

// C++14: std::get by type (if types are unique)
std::string name2 = std::get<std::string>(person);

// C++17: Structured bindings — the modern way
auto [name3, age2, height] = person;

// C++17: std::apply — call a function with tuple elements as arguments
int add(int a, int b, int c) { return a + b + c; }
auto args = std::make_tuple(1, 2, 3);
int sum = std::apply(add, args);  // add(1, 2, 3) = 6

// Returning multiple values
std::tuple<bool, std::string, int> parseConfig(const std::string& line) {
    // ... parsing logic ...
    return {true, "key", 42};
}

auto [success, key, value] = parseConfig("key=42");

// std::tie for comparison operators (pre-C++20)
struct Employee {
    std::string name;
    int department;
    double salary;

    bool operator<(const Employee& rhs) const {
        return std::tie(department, name, salary)
             < std::tie(rhs.department, rhs.name, rhs.salary);
    }
};

// C++20: Use the spaceship operator instead
struct EmployeeModern {
    std::string name;
    int department;
    double salary;

    auto operator<=>(const EmployeeModern&) const = default;
};
```

### Type Traits

```cpp
#include <type_traits>

// Type traits (TR1 -> C++11, massively expanded through C++20)
// Compile-time introspection and transformation of types

// --- Primary type categories ---
static_assert(std::is_integral_v<int>);              // true
static_assert(std::is_floating_point_v<double>);     // true
static_assert(std::is_pointer_v<int*>);              // true
static_assert(std::is_reference_v<int&>);            // true
static_assert(std::is_array_v<int[10]>);             // true
static_assert(std::is_class_v<std::string>);         // true
static_assert(std::is_void_v<void>);                 // true

// --- Composite type categories ---
static_assert(std::is_arithmetic_v<int>);            // true
static_assert(std::is_fundamental_v<double>);        // true
static_assert(std::is_scalar_v<int*>);               // true
static_assert(std::is_object_v<std::string>);        // true

// --- Type properties ---
static_assert(std::is_const_v<const int>);           // true
static_assert(std::is_volatile_v<volatile int>);     // true
static_assert(std::is_trivially_copyable_v<int>);    // true
static_assert(std::is_standard_layout_v<int>);       // true
static_assert(std::is_trivial_v<int>);               // true

// --- Type relationships ---
static_assert(std::is_same_v<int, int>);             // true
static_assert(std::is_convertible_v<int, double>);   // true

// --- Type transformations ---
using NoConst = std::remove_const_t<const int>;       // int
using NoRef = std::remove_reference_t<int&>;           // int
using Decayed = std::decay_t<const int&>;              // int
using Ptr = std::add_pointer_t<int>;                   // int*
using Common = std::common_type_t<int, double>;        // double

// --- Practical usage: SFINAE and if constexpr ---

// BAD: No type checking — compiles but may produce garbage for non-arithmetic types
template<typename T>
T average_bad(const std::vector<T>& v) {
    T sum = std::accumulate(v.begin(), v.end(), T{});
    return sum / v.size();
}

// GOOD: Constrained with type traits (C++17 if constexpr)
template<typename T>
auto average(const std::vector<T>& v) {
    static_assert(std::is_arithmetic_v<T>, "average() requires arithmetic types");
    if constexpr (std::is_integral_v<T>) {
        // Integer types: return double to preserve precision
        double sum = std::accumulate(v.begin(), v.end(), 0.0);
        return sum / v.size();
    } else {
        T sum = std::accumulate(v.begin(), v.end(), T{});
        return sum / static_cast<T>(v.size());
    }
}

// BEST: C++20 Concepts
template<typename T>
concept Arithmetic = std::is_arithmetic_v<T>;

template<Arithmetic T>
auto average_best(const std::vector<T>& v) {
    double sum = std::accumulate(v.begin(), v.end(), 0.0);
    return sum / v.size();
}
```

### Regular Expressions

```cpp
#include <regex>

// std::regex (TR1 -> C++11)
// NOTE: std::regex has historically had poor performance in some implementations.
// Consider third-party alternatives (RE2, CTRE) for performance-critical code.

// Basic matching
std::string email = "user@example.com";
std::regex emailPattern(R"(\w+@\w+\.\w+)");
bool isValid = std::regex_match(email, emailPattern);

// Search (find first match)
std::string text = "Call 555-1234 or 555-5678";
std::regex phonePattern(R"((\d{3})-(\d{4}))");
std::smatch match;
if (std::regex_search(text, match, phonePattern)) {
    std::cout << "Full match: " << match[0] << "\n";     // 555-1234
    std::cout << "Area code:  " << match[1] << "\n";     // 555
    std::cout << "Number:     " << match[2] << "\n";     // 1234
}

// Iterate all matches
auto matchBegin = std::sregex_iterator(text.begin(), text.end(), phonePattern);
auto matchEnd = std::sregex_iterator();
for (auto it = matchBegin; it != matchEnd; ++it) {
    std::cout << "Found: " << (*it)[0] << "\n";
}
// Output: Found: 555-1234
//         Found: 555-5678

// Replace
std::string result = std::regex_replace(text, phonePattern, "XXX-XXXX");
// "Call XXX-XXXX or XXX-XXXX"

// Splitting strings using regex
std::string csv = "field1,field2,,field4";
std::regex comma(",");
std::vector<std::string> fields(
    std::sregex_token_iterator(csv.begin(), csv.end(), comma, -1),
    std::sregex_token_iterator()
);
// fields = {"field1", "field2", "", "field4"}

// Practical example: log parser
struct LogEntry {
    std::string timestamp;
    std::string level;
    std::string message;
};

std::optional<LogEntry> parseLogLine(const std::string& line) {
    static const std::regex logPattern(
        R"(^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(\w+)\] (.+)$)"
    );

    std::smatch m;
    if (std::regex_match(line, m, logPattern)) {
        return LogEntry{m[1], m[2], m[3]};
    }
    return std::nullopt;
}
```

### Random Number Generation

```cpp
#include <random>

// BAD: Using rand() and srand() — biased, predictable, not thread-safe
int badRandom(int min, int max) {
    return min + rand() % (max - min + 1);  // Non-uniform distribution!
}

// GOOD: Modern <random> library (TR1 -> C++11)
class RandomEngine {
public:
    RandomEngine() : gen_(std::random_device{}()) {}

    // Uniform integer distribution
    int uniformInt(int min, int max) {
        std::uniform_int_distribution<int> dist(min, max);
        return dist(gen_);
    }

    // Uniform real distribution
    double uniformReal(double min, double max) {
        std::uniform_real_distribution<double> dist(min, max);
        return dist(gen_);
    }

    // Normal (Gaussian) distribution
    double normal(double mean, double stddev) {
        std::normal_distribution<double> dist(mean, stddev);
        return dist(gen_);
    }

    // Bernoulli (coin flip with probability p)
    bool bernoulli(double probability) {
        std::bernoulli_distribution dist(probability);
        return dist(gen_);
    }

    // Poisson distribution (for modeling random events over time)
    int poisson(double meanRate) {
        std::poisson_distribution<int> dist(meanRate);
        return dist(gen_);
    }

    // Discrete distribution (weighted random selection)
    int weightedChoice(std::initializer_list<double> weights) {
        std::discrete_distribution<int> dist(weights);
        return dist(gen_);
    }

    // Shuffle a container
    template<typename Container>
    void shuffle(Container& c) {
        std::shuffle(c.begin(), c.end(), gen_);
    }

private:
    std::mt19937 gen_;  // Mersenne Twister engine — good general-purpose PRNG
};

// Available engines:
// std::mt19937         — Mersenne Twister (32-bit, period 2^19937-1)
// std::mt19937_64      — Mersenne Twister (64-bit)
// std::minstd_rand     — Linear congruential (fast, lower quality)
// std::ranlux24        — Subtract-with-carry (luxury level 3)
// std::ranlux48        — Subtract-with-carry (luxury level 4)
// std::default_random_engine — Implementation-defined

// Available distributions:
// Uniform:     uniform_int_distribution, uniform_real_distribution
// Bernoulli:   bernoulli_distribution, binomial_distribution,
//              geometric_distribution, negative_binomial_distribution
// Poisson:     poisson_distribution, exponential_distribution,
//              gamma_distribution, weibull_distribution,
//              extreme_value_distribution
// Normal:      normal_distribution, lognormal_distribution,
//              chi_squared_distribution, cauchy_distribution,
//              fisher_f_distribution, student_t_distribution
// Sampling:    discrete_distribution, piecewise_constant_distribution,
//              piecewise_linear_distribution

// Usage example: Monte Carlo simulation
double estimatePi(int samples) {
    std::mt19937 gen(42);  // Fixed seed for reproducibility
    std::uniform_real_distribution<double> dist(0.0, 1.0);

    int insideCircle = 0;
    for (int i = 0; i < samples; ++i) {
        double x = dist(gen);
        double y = dist(gen);
        if (x * x + y * y <= 1.0) {
            ++insideCircle;
        }
    }
    return 4.0 * insideCircle / samples;
}
```

### String and String View

```cpp
#include <string>
#include <string_view>  // C++17
#include <charconv>     // C++17

// std::string_view (C++17) — non-owning view of character data
// Avoids copies when you only need to read a string

// BAD: Unnecessary copies
bool startsWithBad(const std::string& str, const std::string& prefix) {
    return str.substr(0, prefix.size()) == prefix;  // substr creates a copy
}

// GOOD: string_view avoids copies
bool startsWith(std::string_view str, std::string_view prefix) {
    return str.substr(0, prefix.size()) == prefix;  // substr returns a string_view — no copy
    // Or in C++20: return str.starts_with(prefix);
}

// Works with string literals, std::string, and char* — all zero-copy:
startsWith("hello world", "hello");     // No copies
std::string s = "hello world";
startsWith(s, "hello");                 // No copies

// CAUTION: string_view does not own the data — beware of dangling views
// BAD:
std::string_view dangerous() {
    std::string temp = "hello";
    return temp;  // DANGLING! temp is destroyed, view points to freed memory
}

// std::charconv (C++17) — fast, locale-independent number conversion
#include <charconv>

// BAD: stoi/stod are locale-dependent and throw exceptions
int valueSlow = std::stoi("42");

// GOOD: from_chars is fast, locale-independent, and non-allocating
int parseIntFast(std::string_view sv) {
    int result = 0;
    auto [ptr, ec] = std::from_chars(sv.data(), sv.data() + sv.size(), result);
    if (ec != std::errc{}) {
        throw std::runtime_error("Parse error");
    }
    return result;
}
```

### Chrono (Time Library)

```cpp
#include <chrono>

// C++11 chrono library — type-safe time handling

using namespace std::chrono;

// Clocks
auto now = system_clock::now();                    // Wall-clock time
auto steadyNow = steady_clock::now();              // Monotonic (for measuring intervals)
auto highResNow = high_resolution_clock::now();    // Highest available resolution

// Durations — type-safe time intervals
auto tenSeconds = seconds(10);
auto halfSecond = milliseconds(500);
auto tinyInterval = microseconds(100);
auto dur = 2h + 30min + 15s;  // C++14 duration literals

// Duration arithmetic
auto total = tenSeconds + halfSecond;  // 10500ms

// Duration casting
auto ms = duration_cast<milliseconds>(tenSeconds);  // 10000ms
auto secs = duration_cast<seconds>(milliseconds(2500)); // 2s (truncated)

// Benchmarking
auto start = steady_clock::now();
// ... code to benchmark ...
auto end = steady_clock::now();
auto elapsed = duration_cast<microseconds>(end - start);
std::cout << "Elapsed: " << elapsed.count() << " microseconds\n";

// C++20: Calendar and time zones
// Calendar types (C++20)
auto today = year_month_day{floor<days>(system_clock::now())};
auto christmas = 2024y / December / 25;
auto lastDayOfFeb = 2024y / February / last;

bool isLeapYear = year{2024}.is_leap();

// Time zones (C++20)
auto utcNow = system_clock::now();
auto localTime = zoned_time{current_zone(), utcNow};
auto tokyoTime = zoned_time{"Asia/Tokyo", utcNow};
```

### Filesystem

```cpp
#include <filesystem>  // C++17 (originated from Boost.Filesystem)
namespace fs = std::filesystem;

// Path manipulation
fs::path configPath = fs::current_path() / "config" / "settings.json";
std::cout << "Stem:      " << configPath.stem() << "\n";       // settings
std::cout << "Extension: " << configPath.extension() << "\n";  // .json
std::cout << "Parent:    " << configPath.parent_path() << "\n"; // .../config

// File operations
if (fs::exists(configPath)) {
    auto size = fs::file_size(configPath);
    auto modified = fs::last_write_time(configPath);
    std::cout << "Size: " << size << " bytes\n";
}

// Directory iteration
for (const auto& entry : fs::directory_iterator("/tmp")) {
    if (entry.is_regular_file()) {
        std::cout << entry.path().filename() << " ("
                  << entry.file_size() << " bytes)\n";
    }
}

// Recursive directory iteration
for (const auto& entry : fs::recursive_directory_iterator("src")) {
    if (entry.path().extension() == ".cpp") {
        std::cout << entry.path() << "\n";
    }
}

// Create directories
fs::create_directories("output/logs/2024");  // Creates all intermediate directories

// Copy, rename, delete
fs::copy("src/main.cpp", "backup/main.cpp.bak",
         fs::copy_options::overwrite_existing);
fs::rename("old_name.txt", "new_name.txt");
fs::remove("temp_file.txt");
fs::remove_all("temp_directory");  // Recursive delete

// Permissions
fs::permissions("script.sh",
    fs::perms::owner_exec | fs::perms::group_exec,
    fs::perm_options::add);

// Space information
auto space = fs::space("/");
std::cout << "Capacity:  " << space.capacity / (1024*1024*1024) << " GB\n";
std::cout << "Available: " << space.available / (1024*1024*1024) << " GB\n";
```

### Optional, Variant, Any (C++17)

```cpp
#include <optional>   // C++17
#include <variant>    // C++17
#include <any>        // C++17

// --- std::optional: a value that may or may not be present ---

// BAD: Using special sentinel values
int findIndexBad(const std::vector<int>& v, int target) {
    for (int i = 0; i < v.size(); ++i) {
        if (v[i] == target) return i;
    }
    return -1;  // Magic number meaning "not found"
}

// GOOD: std::optional makes absence explicit
std::optional<int> findIndex(const std::vector<int>& v, int target) {
    for (int i = 0; i < v.size(); ++i) {
        if (v[i] == target) return i;
    }
    return std::nullopt;
}

auto idx = findIndex(data, 42);
if (idx) {
    std::cout << "Found at index " << *idx << "\n";
} else {
    std::cout << "Not found\n";
}

// value_or provides a default
int index = findIndex(data, 42).value_or(-1);

// --- std::variant: type-safe union ---

// BAD: C-style union with type tag
struct ShapeOld {
    enum Type { CircleT, RectangleT, TriangleT };
    Type type;
    union {
        struct { double radius; } circle;
        struct { double width, height; } rect;
        struct { double base, height; } tri;
    };
};

// GOOD: std::variant
using Shape = std::variant<Circle, Rectangle, Triangle>;

// Pattern matching with std::visit
double area(const Shape& shape) {
    return std::visit([](const auto& s) -> double {
        using T = std::decay_t<decltype(s)>;
        if constexpr (std::is_same_v<T, Circle>) {
            return 3.14159 * s.radius * s.radius;
        } else if constexpr (std::is_same_v<T, Rectangle>) {
            return s.width * s.height;
        } else if constexpr (std::is_same_v<T, Triangle>) {
            return 0.5 * s.base * s.height;
        }
    }, shape);
}

// Overloaded visitor pattern (common C++17 idiom)
template<class... Ts> struct overloaded : Ts... { using Ts::operator()...; };
template<class... Ts> overloaded(Ts...) -> overloaded<Ts...>;  // C++17 CTAD

double areaVisitor(const Shape& shape) {
    return std::visit(overloaded{
        [](const Circle& c)    { return 3.14159 * c.radius * c.radius; },
        [](const Rectangle& r) { return r.width * r.height; },
        [](const Triangle& t)  { return 0.5 * t.base * t.height; },
    }, shape);
}

// --- std::any: type-safe void* ---
std::any value = 42;
value = std::string("hello");
value = 3.14;

try {
    double d = std::any_cast<double>(value);  // OK
    int i = std::any_cast<int>(value);        // Throws std::bad_any_cast
} catch (const std::bad_any_cast& e) {
    std::cerr << "Wrong type: " << e.what() << "\n";
}

// Check type before casting
if (value.type() == typeid(double)) {
    double d = std::any_cast<double>(value);
}
```

### Concurrency (C++11 and beyond)

```cpp
#include <thread>
#include <mutex>
#include <future>
#include <atomic>
#include <shared_mutex>    // C++17
#include <latch>           // C++20
#include <barrier>         // C++20
#include <semaphore>       // C++20

// --- Threads ---
void worker(int id) {
    std::cout << "Thread " << id << " running\n";
}

std::thread t1(worker, 1);
std::thread t2(worker, 2);
t1.join();
t2.join();

// C++20: jthread — automatically joins on destruction
{
    std::jthread jt(worker, 3);
    // No need to call join() — jt automatically joins when it goes out of scope
}

// --- Mutexes ---
std::mutex mtx;
int sharedCounter = 0;

void incrementSafely() {
    std::lock_guard<std::mutex> lock(mtx);  // RAII lock
    ++sharedCounter;
}

// C++17: std::scoped_lock — locks multiple mutexes without deadlock
std::mutex m1, m2;
void transferFunds() {
    std::scoped_lock lock(m1, m2);  // Locks both, avoids deadlock
    // ... transfer ...
}

// C++17: shared_mutex — multiple readers, single writer
std::shared_mutex rwMutex;
std::map<std::string, int> cache;

int readCache(const std::string& key) {
    std::shared_lock lock(rwMutex);  // Shared (read) lock — multiple readers OK
    return cache[key];
}

void writeCache(const std::string& key, int value) {
    std::unique_lock lock(rwMutex);  // Exclusive (write) lock
    cache[key] = value;
}

// --- Futures and Promises ---
std::future<int> result = std::async(std::launch::async, []() {
    return 42;  // expensiveComputation()
});
int value = result.get();  // Blocks until ready

// --- Atomics ---
std::atomic<int> counter{0};

void incrementAtomic() {
    counter.fetch_add(1, std::memory_order_relaxed);
}

// --- C++20 Synchronization Primitives ---

// std::latch — one-shot barrier
std::latch startLatch(1);
std::latch doneLatch(4);

void workerWithLatch(int id) {
    startLatch.wait();     // Wait for the start signal
    // ... do work ...
    doneLatch.count_down(); // Signal completion
}

// std::barrier — reusable synchronization point
std::barrier syncPoint(4, []() noexcept {
    // Completion function runs when all threads arrive
    std::cout << "All threads synchronized\n";
});

void iterativeWorker() {
    for (int i = 0; i < 10; ++i) {
        // ... do iteration work ...
        syncPoint.arrive_and_wait();  // Sync between iterations
    }
}

// std::counting_semaphore
std::counting_semaphore<4> connectionPool(4);  // Max 4 concurrent connections

void useConnection() {
    connectionPool.acquire();  // Wait for a slot
    // ... use connection ...
    connectionPool.release();  // Return the slot
}
```

### Concepts (C++20)

```cpp
#include <concepts>

// Concepts replace SFINAE and enable_if with clear, readable constraints

// BAD: SFINAE (pre-C++20)
template<typename T, typename = std::enable_if_t<std::is_arithmetic_v<T>>>
T addSFINAE(T a, T b) { return a + b; }

// GOOD: Concepts (C++20)
template<std::integral T>
T add(T a, T b) { return a + b; }

// Custom concepts
template<typename T>
concept Printable = requires(T t) {
    { std::cout << t } -> std::same_as<std::ostream&>;
};

template<typename T>
concept Hashable = requires(T t) {
    { std::hash<T>{}(t) } -> std::convertible_to<std::size_t>;
};

template<typename T>
concept Container = requires(T c) {
    typename T::value_type;
    typename T::iterator;
    { c.begin() } -> std::same_as<typename T::iterator>;
    { c.end() } -> std::same_as<typename T::iterator>;
    { c.size() } -> std::convertible_to<std::size_t>;
};

// Using concepts
template<Container C>
void printAll(const C& container) {
    for (const auto& item : container) {
        std::cout << item << " ";
    }
    std::cout << "\n";
}

// Standard library concepts:
// std::same_as, std::derived_from, std::convertible_to
// std::integral, std::floating_point, std::signed_integral, std::unsigned_integral
// std::equality_comparable, std::totally_ordered
// std::movable, std::copyable, std::semiregular, std::regular
// std::invocable, std::predicate
// std::ranges::range, std::ranges::input_range, std::ranges::forward_range, etc.
```

### Things to Remember

- The C++ standard library is vast and covers containers, algorithms, iterators, function objects, smart pointers, regular expressions, random numbers, time, filesystem, concurrency, and more. Knowing what's available prevents you from reinventing it.

- Everything from TR1 has been incorporated into the C++ standard (C++11 and later). If you see legacy code using `std::tr1::`, update it to `std::`.

- Modern C++ (C++11 through C++20) has added transformative features: move semantics, lambda expressions, `constexpr`, `auto`, structured bindings, `optional`/`variant`/`any`, ranges, concepts, coroutines, and modules. Each release substantially improves what you can express.

- Know the performance characteristics of your containers: `vector` for contiguous storage and cache locality, `unordered_map`/`unordered_set` for O(1) average lookup, `map`/`set` for ordered access, `deque` for front/back operations.

- Prefer standard library facilities over hand-written alternatives. They are tested, optimized, portable, and familiar to other C++ programmers.

---
