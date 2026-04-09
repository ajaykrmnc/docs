# Item 43: Know how to access names in templatized base classes

### The problem: names in dependent base classes are invisible

Consider a messaging system with compile-time selection of the transport:

```cpp
class CompanyA {
public:
    void sendCleartext(const std::string& msg) { /* ... */ }
    void sendEncrypted(const std::string& msg) { /* ... */ }
};

class CompanyB {
public:
    void sendCleartext(const std::string& msg) { /* ... */ }
    void sendEncrypted(const std::string& msg) { /* ... */ }
};

template <typename Company>
class MsgSender {
public:
    void sendClear(const std::string& info) {
        Company c;
        c.sendCleartext(info);
    }

    void sendSecret(const std::string& info) {
        Company c;
        c.sendEncrypted(info);
    }
};
```

Now a derived class that logs every message:

```cpp
template <typename Company>
class LoggingMsgSender : public MsgSender<Company> {
public:
    void sendClearMsg(const std::string& info) {
        // write "before sending" to log
        sendClear(info);  // ERROR! Won't compile!
        // write "after sending" to log
    }
};
```

This fails because the compiler refuses to look inside `MsgSender<Company>` for `sendClear`. Why? Because `Company` is a template parameter, and there could be a **total specialization** of `MsgSender` that does not have `sendClear`:

```cpp
// A company for which encrypted-only communication is mandated.
class CompanyZ {
public:
    void sendEncrypted(const std::string& msg) { /* ... */ }
    // No sendCleartext!
};

// Total specialization: MsgSender<CompanyZ> has no sendClear()
template <>
class MsgSender<CompanyZ> {
public:
    void sendSecret(const std::string& info) {
        CompanyZ c;
        c.sendEncrypted(info);
    }
    // No sendClear() here!
};
```

Because `MsgSender<CompanyZ>` does not have `sendClear`, the compiler is right to refuse to assume it exists in the general case. The standard says: **names in dependent base classes are not examined during unqualified lookup**.

### Solution 1: `this->`

Prefix the call with `this->` to make it a dependent expression, deferring lookup to instantiation time:

```cpp
template <typename Company>
class LoggingMsgSender : public MsgSender<Company> {
public:
    void sendClearMsg(const std::string& info) {
        logToFile("Before sending");
        this->sendClear(info);  // OK: defers lookup to instantiation time
        logToFile("After sending");
    }
};
```

This is the most common and recommended approach.

### Solution 2: `using` declaration

Bring the base class name into the derived class's scope:

```cpp
template <typename Company>
class LoggingMsgSender : public MsgSender<Company> {
public:
    using MsgSender<Company>::sendClear;  // Make sendClear visible

    void sendClearMsg(const std::string& info) {
        logToFile("Before sending");
        sendClear(info);  // OK: using declaration made it visible
        logToFile("After sending");
    }
};
```

### Solution 3: Explicit qualification

Qualify the call with the base class name:

```cpp
template <typename Company>
class LoggingMsgSender : public MsgSender<Company> {
public:
    void sendClearMsg(const std::string& info) {
        logToFile("Before sending");
        MsgSender<Company>::sendClear(info);  // OK but problematic
        logToFile("After sending");
    }
};
```

This works but has a significant drawback: **it suppresses virtual dispatch**. If `sendClear` were virtual, this would always call the base class version, never an overridden version. For this reason, `this->` or `using` declarations are generally preferred.

### A comprehensive real-world example

Consider a policy-based design for database operations:

```cpp
// Policy for SQL generation
template <typename Dialect>
class SQLGenerator {
public:
    std::string generateSelect(const std::string& table,
                               const std::vector<std::string>& cols) {
        return Dialect::selectPrefix() + buildColumnList(cols) + " FROM " + table;
    }

protected:
    std::string buildColumnList(const std::vector<std::string>& cols) {
        std::string result;
        for (size_t i = 0; i < cols.size(); ++i) {
            if (i > 0) result += ", ";
            result += Dialect::quoteIdentifier(cols[i]);
        }
        return result;
    }

    std::string escapeString(const std::string& s) {
        return Dialect::escapeImpl(s);
    }
};

// Extended generator that adds WHERE clause support
template <typename Dialect>
class FilteredSQLGenerator : public SQLGenerator<Dialect> {
public:
    // Must use this-> or using declarations to access base class members

    using SQLGenerator<Dialect>::generateSelect;
    using SQLGenerator<Dialect>::escapeString;

    std::string generateFilteredSelect(
            const std::string& table,
            const std::vector<std::string>& cols,
            const std::string& whereClause) {
        // Without the using declarations above, these calls would fail:
        std::string base = generateSelect(table, cols);
        return base + " WHERE " + escapeString(whereClause);
    }
};

// Even deeper inheritance -- same rules apply at every level
template <typename Dialect>
class PaginatedSQLGenerator : public FilteredSQLGenerator<Dialect> {
public:
    std::string generatePaginatedSelect(
            const std::string& table,
            const std::vector<std::string>& cols,
            const std::string& whereClause,
            int limit, int offset) {
        // this-> needed because FilteredSQLGenerator<Dialect> is a dependent base
        std::string query = this->generateFilteredSelect(table, cols, whereClause);
        return query + " LIMIT " + std::to_string(limit)
                     + " OFFSET " + std::to_string(offset);
    }
};
```

### Accessing dependent base class types

The problem extends to types as well. Accessing a typedef or nested type from a dependent base class requires both `typename` (Item 42) and one of the three solutions above:

```cpp
template <typename T>
class Base {
public:
    using value_type = T;
    using container_type = std::vector<T>;
};

template <typename T>
class Derived : public Base<T> {
public:
    // WRONG: Base<T>::value_type is not found
    // value_type getData();

    // CORRECT: use typename + full qualification
    typename Base<T>::value_type getData() {
        typename Base<T>::container_type storage;
        storage.push_back(T());
        return storage.front();
    }

    // ALTERNATIVE: bring the type in with using
    using typename Base<T>::value_type;
    // Now value_type can be used unqualified in this class
};
```

### Multiple dependent base classes

When inheriting from multiple templatized bases, you need to resolve ambiguity for each:

```cpp
template <typename T>
class Serializable {
public:
    std::string serialize() const { /* ... */ return ""; }
};

template <typename T>
class Printable {
public:
    void print() const { /* ... */ }
};

template <typename T>
class Document : public Serializable<T>, public Printable<T> {
public:
    void save() {
        std::string data = this->serialize();  // From Serializable<T>
        this->print();                          // From Printable<T>
        // store data...
    }
};
```

### Things to Remember

- In derived class templates, refer to names in base class templates via a `this->` prefix, via `using` declarations, or via an explicit base class qualification.
- The compiler does not search dependent base classes during unqualified name lookup because a specialization of the base class template might not contain the name.
- Prefer `this->` or `using` declarations over explicit qualification, because explicit qualification inhibits virtual dispatch.

---
