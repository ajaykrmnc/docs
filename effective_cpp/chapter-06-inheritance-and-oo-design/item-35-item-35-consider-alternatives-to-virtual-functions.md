# Item 35: Consider alternatives to virtual functions

## Visual Summary

```text
┌───────────────────────────────────────────────────────────────────────────┐
│            ITEM 35: CONSIDER ALTERNATIVES TO VIRTUAL FUNCTIONS            │
├───────────────────────────────────────────────────────────────────────────┤
│ 1. Need customizable behavior -> virtual function is one option.          │
│ 2. NVI -> public non-virtual wrapper enforces invariants around private   │
│ virtual hook.                                                             │
│ 3. Strategy/function object -> behavior supplied by composition.          │
│ 4. Templates -> compile-time customization without runtime dispatch.      │
│ 5. Meaning: dynamic polymorphism is useful, but not the only variation    │
│ point.                                                                    │
└───────────────────────────────────────────────────────────────────────────┘
```

## Visual Deep Dive

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                           CUSTOMIZATION OPTIONS                           │
├───────────────────────────────────────────────────────────────────────────┤
│ Technique                         | Best when                             │
│ ----------------------------------+-------------------------------------  │
│ virtual function                  | runtime subtype behavior              │
│ NVI                               | base enforces wrapper rules           │
│ strategy object                   | behavior is replaceable data          │
│ template                          | compile-time variation                │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                                 NVI FLOW                                  │
├───────────────────────────────────────────────────────────────────────────┤
│ Public non-virtual function called                                        │
│                                     ▼                                     │
│ Base checks preconditions/invariants                                      │
│                                     ▼                                     │
│ Private virtual hook customizes step                                      │
│                                     ▼                                     │
│ Base checks postconditions/logging                                        │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Problem with a Straightforward Virtual Function Design

Consider a simple health computation for game characters:

```cpp
// Straightforward but rigid approach
class GameCharacter {
public:
    virtual ~GameCharacter() = default;
    virtual int healthValue() const {
        // default algorithm for computing health
        return baseHealth_ - damage_;
    }
private:
    int baseHealth_ = 100;
    int damage_ = 0;
};
```

This works, but there are several alternatives that offer greater flexibility. Meyers presents four alternatives, each with different tradeoffs.

### Alternative 1: The Template Method Pattern via the Non-Virtual Interface (NVI) Idiom

The NVI idiom wraps virtual functions with non-virtual public functions. The non-virtual wrapper does "before" and "after" work, while the virtual function is private or protected.

```cpp
// GOOD -- NVI idiom (Template Method Pattern)
class GameCharacter {
public:
    virtual ~GameCharacter() = default;

    // Non-virtual interface: the public entry point
    int healthValue() const {
        // "before" work: lock mutex, log, validate invariants, etc.
        logHealthQuery();

        int result = doHealthValue();  // delegate to virtual

        // "after" work: unlock mutex, verify postconditions, etc.
        assert(result >= 0 && result <= maxHealth_);
        return result;
    }

private:
    virtual int doHealthValue() const {
        // default health calculation
        return baseHealth_ - damage_;
    }

    void logHealthQuery() const {
        std::cout << "[LOG] Health queried for character\n";
    }

    int baseHealth_ = 100;
    int damage_ = 0;
    int maxHealth_ = 100;
};

class Warrior : public GameCharacter {
private:
    int doHealthValue() const override {
        // Warriors get bonus health from armor
        return GameCharacter::doHealthValue() + armorBonus_;
    }
    int armorBonus_ = 20;
};

class Mage : public GameCharacter {
private:
    int doHealthValue() const override {
        // Mages have lower base health but get mana shield
        return GameCharacter::doHealthValue() + manaShield_;
    }
    int manaShield_ = 15;
};
```

Key advantages of NVI:
- Pre-conditions and post-conditions are always enforced.
- Logging, locking, and instrumentation happen in one place.
- Derived classes customize *what* is done, while the base class controls *when* and *how* it's done.

### Alternative 2: The Strategy Pattern via Function Pointers

Decouple the health calculation entirely from the class hierarchy by using a function pointer:

```cpp
// GOOD -- Strategy Pattern via function pointers
class GameCharacter;  // forward declaration

// Health calculation is a free function (a "strategy")
int defaultHealthCalc(const GameCharacter& gc);
int conservativeHealthCalc(const GameCharacter& gc);
int aggressiveHealthCalc(const GameCharacter& gc);

class GameCharacter {
public:
    using HealthCalcFunc = int (*)(const GameCharacter&);

    explicit GameCharacter(HealthCalcFunc hcf = defaultHealthCalc)
        : healthFunc_(hcf) {}

    int healthValue() const {
        return healthFunc_(*this);
    }

    // Can change strategy at runtime!
    void setHealthCalculator(HealthCalcFunc hcf) {
        healthFunc_ = hcf;
    }

    int getBaseHealth() const { return baseHealth_; }
    int getDamage() const { return damage_; }

private:
    HealthCalcFunc healthFunc_;
    int baseHealth_ = 100;
    int damage_ = 0;
};

int defaultHealthCalc(const GameCharacter& gc) {
    return gc.getBaseHealth() - gc.getDamage();
}

int conservativeHealthCalc(const GameCharacter& gc) {
    return static_cast<int>((gc.getBaseHealth() - gc.getDamage()) * 0.8);
}

int aggressiveHealthCalc(const GameCharacter& gc) {
    return static_cast<int>((gc.getBaseHealth() - gc.getDamage()) * 1.2);
}

// Usage
GameCharacter warrior(aggressiveHealthCalc);
GameCharacter healer(conservativeHealthCalc);

// Switch strategies at runtime
warrior.setHealthCalculator(conservativeHealthCalc);
```

Key advantages:
- Different instances of the *same* class can have different health strategies.
- Strategies can be swapped at runtime.
- Health calculation is fully decoupled from the class hierarchy.

Key disadvantage:
- The function pointer has no access to private/protected members. You may need to weaken encapsulation (provide public accessors or declare friends).

### Alternative 3: The Strategy Pattern via `std::function`

`std::function` generalizes function pointers to accept any callable: regular functions, lambdas, functors, bound member functions, etc.

```cpp
// GOOD -- Strategy Pattern via std::function (most flexible)
#include <functional>

class GameCharacter {
public:
    using HealthCalcFunc = std::function<int(const GameCharacter&)>;

    explicit GameCharacter(HealthCalcFunc hcf = defaultHealthCalc)
        : healthFunc_(std::move(hcf)) {}

    int healthValue() const {
        return healthFunc_(*this);
    }

    void setHealthCalculator(HealthCalcFunc hcf) {
        healthFunc_ = std::move(hcf);
    }

    int getBaseHealth() const { return baseHealth_; }
    int getDamage() const { return damage_; }

private:
    HealthCalcFunc healthFunc_;
    int baseHealth_ = 100;
    int damage_ = 0;

    static int defaultHealthCalc(const GameCharacter& gc) {
        return gc.baseHealth_ - gc.damage_;
    }
};

// Now we can use ANYTHING callable:

// 1. Regular function
int heroCalc(const GameCharacter& gc) {
    return gc.getBaseHealth() * 2 - gc.getDamage();
}

// 2. Lambda
auto timidCalc = [](const GameCharacter& gc) -> int {
    return std::max(0, gc.getBaseHealth() / 2 - gc.getDamage());
};

// 3. Functor
struct LevelAdjustedCalc {
    int level;
    int operator()(const GameCharacter& gc) const {
        return gc.getBaseHealth() + level * 10 - gc.getDamage();
    }
};

// 4. Bound member function of another class
class GameLevel {
public:
    int environmentalHealthAdjust(const GameCharacter& gc) const {
        // Poison swamp reduces health
        return gc.getBaseHealth() - gc.getDamage() - poisonDamage_;
    }
private:
    int poisonDamage_ = 15;
};

// Usage:
GameCharacter c1(heroCalc);                          // function pointer
GameCharacter c2(timidCalc);                         // lambda
GameCharacter c3(LevelAdjustedCalc{5});              // functor

GameLevel swamp;
GameCharacter c4(std::bind(&GameLevel::environmentalHealthAdjust,
                           &swamp, std::placeholders::_1));  // bound member
// Or with a lambda (preferred over std::bind in modern C++):
GameCharacter c5([&swamp](const GameCharacter& gc) {
    return swamp.environmentalHealthAdjust(gc);
});
```

### Alternative 4: The Classic Strategy Pattern

Extract the strategy into its own class hierarchy:

```cpp
// GOOD -- Classic Strategy Pattern with its own hierarchy
class GameCharacter;  // forward declaration

class HealthCalcStrategy {
public:
    virtual ~HealthCalcStrategy() = default;
    virtual int calc(const GameCharacter& gc) const = 0;
};

class DefaultHealthCalc : public HealthCalcStrategy {
public:
    int calc(const GameCharacter& gc) const override;
};

class SlowRegenHealthCalc : public HealthCalcStrategy {
public:
    int calc(const GameCharacter& gc) const override {
        // Regenerates slowly over time
        return gc.getBaseHealth() - gc.getDamage() + regenRate_ * turnCount_;
    }
private:
    int regenRate_ = 2;
    int turnCount_ = 0;
};

class PoisonedHealthCalc : public HealthCalcStrategy {
public:
    int calc(const GameCharacter& gc) const override {
        return gc.getBaseHealth() - gc.getDamage() - poisonPerTurn_ * turns_;
    }
private:
    int poisonPerTurn_ = 5;
    int turns_ = 3;
};

class GameCharacter {
public:
    explicit GameCharacter(std::shared_ptr<HealthCalcStrategy> strategy
                           = std::make_shared<DefaultHealthCalc>())
        : strategy_(std::move(strategy)) {}

    int healthValue() const {
        return strategy_->calc(*this);
    }

    void setStrategy(std::shared_ptr<HealthCalcStrategy> s) {
        strategy_ = std::move(s);
    }

    int getBaseHealth() const { return baseHealth_; }
    int getDamage() const { return damage_; }

private:
    std::shared_ptr<HealthCalcStrategy> strategy_;
    int baseHealth_ = 100;
    int damage_ = 0;
};

int DefaultHealthCalc::calc(const GameCharacter& gc) const {
    return gc.getBaseHealth() - gc.getDamage();
}
```

This is the most elaborate approach but offers the greatest extensibility: new strategies can be added as new classes without modifying existing code. Strategies can carry their own state, be configured independently, and be shared among multiple characters.

### Comparison of Approaches

| Approach | Flexibility | Complexity | Encapsulation Impact |
|---|---|---|---|
| Virtual functions | Low | Low | None |
| NVI (Template Method) | Low-Medium | Low | None |
| Function pointers | Medium | Low | May need public accessors |
| `std::function` | High | Medium | May need public accessors |
| Classic Strategy | High | High | May need public accessors |

### Things to Remember

- Alternatives to virtual functions include the NVI idiom and various forms of the Strategy design pattern. The NVI idiom is the Template Method design pattern; it wraps public non-virtual member functions around less accessible virtual functions.
- Moving functionality from a member function to a function outside the class means the non-member function has no special access to non-public members.
- `std::function` objects act like generalized function pointers. They accept any callable entity compatible with the target signature.
- The classic Strategy pattern replaces virtual functions in the primary hierarchy with a separate hierarchy of strategy objects.

---
