# Item 26: Postpone Variable Definitions as Long as Possible

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│        ITEM 26: POSTPONE VARIABLE DEFINITIONS AS LONG AS POSSIBLE         │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Define variable early -> constructor/destructor cost paid even if      │
│ unused.                                                                   │
│ 2. Early definition before validation -> exceptions/returns waste work.   │
│ 3. Define at first meaningful value -> avoids default construction plus   │
│ assignment.                                                               │
│ 4. Loops -> choose inside or outside based on cost and needed lifetime.   │
│ 5. Meaning: give variables the smallest useful lifetime and best initial  │
│ value.                                                                    │
└───────────────────────────────────────────────────────────────────────────┘
```

Whenever you define a variable of a type with a constructor and destructor, you incur
the cost of construction when control reaches the variable's definition, and the cost
of destruction when the variable leaves scope. This cost is wasted if the variable is
never used -- and that happens more often than you might think.

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                            EARLY VARIABLE COST                            │
├───────────────────────────────────────────────────────────────────────────┤
│ Variable constructed before it is needed                                  │
│                                     ▼                                     │
│ Validation fails or branch returns early                                  │
│                                     ▼                                     │
│ Constructor/destructor work was wasted                                    │
│                                     ▼                                     │
│ Default construction plus assignment may also occur                       │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                         LATE INITIALIZATION FLOW                          │
├───────────────────────────────────────────────────────────────────────────┤
│ Reach point where value is actually needed                                │
│                                     ▼                                     │
│ Construct with final intended value                                       │
│                                     ▼                                     │
│ Keep lifetime narrow                                                      │
│                                     ▼                                     │
│ Reduce cost and accidental misuse                                         │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Obvious Case: Variables Before Early Returns

```cpp
// BAD: encrypted is constructed even if the password is too short
std::string encryptPassword(const std::string& password) {
    using namespace std;
    string encrypted;  // Constructed here -- default constructor

    if (password.length() < MinimumPasswordLength) {
        throw logic_error("Password is too short");
        // If we throw, 'encrypted' was constructed and destroyed for nothing.
    }

    encrypted = password;  // Assignment operator (second cost!)
    encrypt(encrypted);
    return encrypted;
}
```

```cpp
// BETTER: postpone until after the check
std::string encryptPassword(const std::string& password) {
    using namespace std;

    if (password.length() < MinimumPasswordLength) {
        throw logic_error("Password is too short");
    }

    string encrypted;      // Not constructed if we threw above
    encrypted = password;  // But still: default construction + assignment
    encrypt(encrypted);
    return encrypted;
}
```

```cpp
// BEST: postpone AND initialize directly -- skip the default construction
std::string encryptPassword(const std::string& password) {
    using namespace std;

    if (password.length() < MinimumPasswordLength) {
        throw logic_error("Password is too short");
    }

    string encrypted(password);  // Copy constructor -- one operation instead of two!
    encrypt(encrypted);
    return encrypted;
}
```

The final version avoids both the unnecessary default construction and the assignment.
It directly initializes `encrypted` with `password` using the copy constructor.

### The General Rule

You should postpone a variable's definition until:
1. You can give it an initial value, AND
2. You're certain the variable will actually be used.

```cpp
// BAD: defining variables long before they're needed
void processData(const std::vector<int>& data) {
    int sum = 0;             // Defined here...
    double average = 0.0;    // ...and here...
    std::string report;      // ...and here...

    if (data.empty()) {
        return;  // sum, average, and report were never used!
    }

    // ... 50 lines of validation code ...

    for (int x : data) {
        sum += x;            // First use of sum -- 60 lines after definition!
    }
    average = static_cast<double>(sum) / data.size();  // First use of average
    report = generateReport(average);                   // First use of report
}

// GOOD: define each variable at the point of first use
void processData(const std::vector<int>& data) {
    if (data.empty()) {
        return;
    }

    // ... 50 lines of validation code ...

    int sum = 0;               // Right where it's needed
    for (int x : data) {
        sum += x;
    }

    double average = static_cast<double>(sum) / data.size();  // Right here
    std::string report = generateReport(average);              // Right here
}
```

### Variables in Loops

What about variables used only inside a loop? There are two approaches:

```cpp
// Approach A: Define outside the loop
Widget w;
for (int i = 0; i < n; ++i) {
    w = some_value_dependent_on_i;
    // ... use w ...
}
// Cost: 1 constructor + 1 destructor + n assignments

// Approach B: Define inside the loop
for (int i = 0; i < n; ++i) {
    Widget w(some_value_dependent_on_i);
    // ... use w ...
}
// Cost: n constructors + n destructors
```

The costs are:

| Approach | Cost |
|----------|------|
| A (outside) | 1 construction + 1 destruction + n assignments |
| B (inside) | n constructions + n destructions |

Approach A is more efficient **if** an assignment is cheaper than a constructor-destructor pair.
Otherwise, Approach B is better.

**The recommendation: default to Approach B** (define inside the loop) unless:
1. You know that the assignment is significantly cheaper than a construction-destruction pair, **AND**
2. You are dealing with a performance-sensitive part of your code.

Approach B is preferred because:
- It limits the variable's scope to the loop body (better readability, fewer bugs).
- The variable can't be accidentally used after the loop.
- It's easier to reason about correctness.

```cpp
// GOOD (default choice): define inside the loop
for (int i = 0; i < n; ++i) {
    std::string s = computeString(i);  // Fresh string each iteration
    processString(s);
    // s is destroyed here -- can't leak into the next iteration or beyond the loop
}

// ACCEPTABLE (performance-critical path with expensive construction):
std::string s;
for (int i = 0; i < n; ++i) {
    s = computeString(i);  // Reuse s's memory allocation
    processString(s);
}
// But now s is visible after the loop -- wider scope, more potential for bugs.
```

### Real-World Example: Database Query Processing

```cpp
// BAD: premature definitions
void processQuery(Database& db, const std::string& queryStr) {
    Connection conn = db.getConnection();        // Expensive! Opens a connection.
    PreparedStatement stmt = conn.prepare(queryStr); // Expensive! Parses SQL.
    ResultSet results;                             // Default-constructed.

    if (!db.isAvailable()) {
        throw DatabaseException("Database unavailable");
        // conn, stmt, and results were all constructed for nothing!
        // The connection was opened and must now be closed in the destructor.
    }

    if (!isValidQuery(queryStr)) {
        throw QueryException("Invalid query");
        // conn was opened for nothing!
    }

    results = stmt.execute();  // Assignment, not initialization
    processResults(results);
}

// GOOD: postpone everything
void processQuery(Database& db, const std::string& queryStr) {
    if (!db.isAvailable()) {
        throw DatabaseException("Database unavailable");
        // No resources acquired yet
    }

    if (!isValidQuery(queryStr)) {
        throw QueryException("Invalid query");
        // Still no resources acquired
    }

    Connection conn = db.getConnection();              // NOW open the connection
    PreparedStatement stmt = conn.prepare(queryStr);   // NOW parse the SQL
    ResultSet results = stmt.execute();                 // Direct initialization!
    processResults(results);
}
```

### Real-World Example: File Processing with Multiple Error Paths

```cpp
// BAD: all variables at the top
bool convertFile(const std::string& inputPath, const std::string& outputPath) {
    std::ifstream input;
    std::ofstream output;
    std::string line;
    std::vector<std::string> processedLines;
    size_t lineCount = 0;
    bool success = false;

    input.open(inputPath);
    if (!input.is_open()) return false;

    output.open(outputPath);
    if (!output.is_open()) return false;  // input constructed, output default-constructed
                                           // then opened -- wasteful

    while (std::getline(input, line)) {
        processedLines.push_back(transformLine(line));
        ++lineCount;
    }

    for (const auto& pl : processedLines) {
        output << pl << "\n";
    }

    success = true;
    return success;
}

// GOOD: each variable defined at the point of first use
bool convertFile(const std::string& inputPath, const std::string& outputPath) {
    std::ifstream input(inputPath);         // Open immediately via constructor
    if (!input.is_open()) return false;

    std::ofstream output(outputPath);       // Only open if input succeeded
    if (!output.is_open()) return false;

    std::vector<std::string> processedLines;
    std::string line;
    while (std::getline(input, line)) {     // 'line' reused in the loop (Approach A)
        processedLines.push_back(transformLine(line));
    }

    for (const auto& pl : processedLines) {
        output << pl << "\n";
    }

    return true;                            // No need for a 'success' variable
}
```

### The Relationship to const

Postponing definitions also enables more uses of `const`:

```cpp
// BAD: can't make x const because it's defined before the value is known
int x;
// ... lots of code ...
x = computeValue();
// x is non-const even though it never changes after this point.

// GOOD: define at the point of initialization -- now it can be const
// ... lots of code ...
const int x = computeValue();
// x is const, which communicates intent and enables optimizations.
```

### Things to Remember

- Postpone variable definitions as long as possible. It increases program clarity and
  improves program efficiency.

---

## Summary

Chapter 4 covers the core design decisions in C++ software:

| Item | Key Principle |
|------|--------------|
| 18 | Design interfaces that are easy to use correctly and hard to misuse |
| 19 | Treat class design as type design -- ask the right questions |
| 20 | Pass by reference-to-const by default; avoid the slicing problem |
| 21 | Return objects by value when you must; don't return dangling references |
| 22 | Make data members private for encapsulation and flexibility |
| 23 | Prefer non-member non-friend functions for better encapsulation |
| 24 | Use non-member functions when type conversions should apply to all parameters |
| 25 | Implement efficient, non-throwing swap for your types |
| 26 | Define variables at the latest possible point, initialized with their real values |

These principles work together: good type design (Item 19) leads to interfaces that are
hard to misuse (Item 18), with private data members (Item 22) accessed through well-designed
functions that are members only when necessary (Items 23, 24), passed by reference (Item 20),
returned by value when needed (Item 21), with efficient swap support (Item 25) and minimal
variable lifetimes (Item 26).
