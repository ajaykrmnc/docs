# Item 38: Model "has-a" or "is-implemented-in-terms-of" through composition

### Composition vs. Inheritance

Composition (also called layering, containment, aggregation, or embedding) is the relationship where one class *contains* an object of another class as a data member. It models two different relationships depending on the domain:

1. **"Has-a"**: in the application domain (objects modeling real-world things).
2. **"Is-implemented-in-terms-of"**: in the implementation domain (objects that are implementation artifacts).

### "Has-a" Relationship

```cpp
// GOOD -- Person "has-a" name, address, and phone numbers
class Address {
public:
    std::string street;
    std::string city;
    std::string state;
    std::string zip;
};

class PhoneNumber {
public:
    std::string areaCode;
    std::string number;
    std::string extension;
};

class Person {
public:
    const std::string& name() const { return name_; }
    const Address& address() const { return address_; }

private:
    std::string name_;             // Person has-a name
    Address address_;              // Person has-a address
    std::vector<PhoneNumber> phones_;  // Person has phone numbers
};
```

A `Person` is *not* a `string`, an `Address`, or a `PhoneNumber`. A person *has* those things. This is obvious, and nobody would use public inheritance here.

### "Is-Implemented-In-Terms-Of" Relationship

This is less obvious and is the more common source of confusion. Consider implementing a `Set` using a `std::list`:

```cpp
// BAD -- Set is NOT a list!
template <typename T>
class Set : public std::list<T> {
    // A list can contain duplicates; a set cannot.
    // A list has push_front, push_back, etc. -- inappropriate for a set.
    // This violates "is-a": a Set is NOT a list.
};
```

A set is not a list. A list allows duplicates and preserves insertion order; a set does not. Public inheritance is wrong here.

```cpp
// GOOD -- Set is-implemented-in-terms-of list
template <typename T>
class Set {
public:
    bool contains(const T& item) const {
        return std::find(rep_.begin(), rep_.end(), item) != rep_.end();
    }

    void insert(const T& item) {
        if (!contains(item)) {
            rep_.push_back(item);
        }
    }

    void remove(const T& item) {
        auto it = std::find(rep_.begin(), rep_.end(), item);
        if (it != rep_.end()) {
            rep_.erase(it);
        }
    }

    std::size_t size() const { return rep_.size(); }
    bool empty() const { return rep_.empty(); }

    // Iterators for range-based for
    auto begin() const { return rep_.begin(); }
    auto end() const { return rep_.end(); }

private:
    std::list<T> rep_;   // Set is-implemented-in-terms-of list
};
```

The `Set` *uses* a `list` for its implementation, but it is not *a kind of* list. Users of `Set` never see the `list`; it is a hidden implementation detail.

### Real-World Example: Connection Pool

```cpp
// GOOD -- ConnectionPool uses a queue internally
class Connection {
public:
    explicit Connection(const std::string& host) : host_(host) {
        std::cout << "Connected to " << host_ << "\n";
    }
    void execute(const std::string& query) {
        std::cout << "Executing on " << host_ << ": " << query << "\n";
    }
    void reset() {
        std::cout << "Resetting connection to " << host_ << "\n";
    }
private:
    std::string host_;
};

// BAD -- trying to inherit from deque
// class ConnectionPool : public std::deque<Connection> { ... };
// A pool is NOT a deque!

// GOOD -- composition (is-implemented-in-terms-of)
class ConnectionPool {
public:
    explicit ConnectionPool(const std::string& host, int poolSize)
        : host_(host)
    {
        for (int i = 0; i < poolSize; ++i) {
            pool_.push(std::make_unique<Connection>(host));
        }
    }

    std::unique_ptr<Connection> acquire() {
        if (pool_.empty()) {
            return std::make_unique<Connection>(host_);  // grow if needed
        }
        auto conn = std::move(pool_.front());
        pool_.pop();
        return conn;
    }

    void release(std::unique_ptr<Connection> conn) {
        conn->reset();
        pool_.push(std::move(conn));
    }

    std::size_t available() const { return pool_.size(); }

private:
    std::string host_;
    std::queue<std::unique_ptr<Connection>> pool_;  // implemented in terms of queue
};
```

### Real-World Example: A Timer-Based Notification System

```cpp
// BAD -- a NotificationScheduler is NOT a priority_queue
// class NotificationScheduler : public std::priority_queue<...> { };

// GOOD
struct Notification {
    std::chrono::system_clock::time_point when;
    std::string message;
    std::string recipient;

    bool operator<(const Notification& rhs) const {
        // Earlier notifications have higher priority (min-heap behavior)
        return when > rhs.when;
    }
};

class NotificationScheduler {
public:
    void schedule(Notification n) {
        queue_.push(std::move(n));
    }

    bool hasReady() const {
        if (queue_.empty()) return false;
        return queue_.top().when <= std::chrono::system_clock::now();
    }

    Notification getNext() {
        Notification n = queue_.top();
        queue_.pop();
        return n;
    }

    bool empty() const { return queue_.empty(); }

private:
    std::priority_queue<Notification> queue_;  // implemented in terms of pq
};
```

### Things to Remember

- Composition has meaning very different from that of public inheritance. It means either "has-a" (in the application domain) or "is-implemented-in-terms-of" (in the implementation domain).
- In the application domain, composition means "has-a." A `Person` has-a name, an address, phone numbers.
- In the implementation domain, composition means "is-implemented-in-terms-of." A `Set` can be implemented in terms of a `list`, but a `Set` is not a `list`.

---
