# Item 37: Never redefine a function's inherited default parameter value

### The Core Issue

Virtual functions are dynamically bound, but **default parameter values are statically bound**. This mismatch leads to bizarre behavior:

```cpp
// BAD -- redefining inherited default parameter value
class Shape {
public:
    virtual ~Shape() = default;

    enum class Color { Red, Green, Blue };

    virtual void draw(Color color = Color::Red) const = 0;
};

class Circle : public Shape {
public:
    // Redefines the default parameter! BAD!
    void draw(Color color = Color::Green) const override {
        std::cout << "Circle::draw with color "
                  << static_cast<int>(color) << "\n";
    }
};

class Rectangle : public Shape {
public:
    // Also redefines the default! BAD!
    void draw(Color color = Color::Blue) const override {
        std::cout << "Rectangle::draw with color "
                  << static_cast<int>(color) << "\n";
    }
};

// The horror:
Shape* pc = new Circle;
Shape* pr = new Rectangle;

pc->draw();  // Calls Circle::draw(Color::Red)!
             // Virtual dispatch picks Circle::draw (dynamic binding)
             // BUT default parameter comes from Shape (static binding)
             // User sees Red, not Green!

pr->draw();  // Calls Rectangle::draw(Color::Red)!
             // Same issue: dynamic body, static default

Circle c;
c.draw();    // Calls Circle::draw(Color::Green)
             // When called via Circle*, uses Circle's default!
```

The same object, the same function call, but different results depending on the *declared type* of the pointer. This is exactly the kind of insanity you want to avoid.

### Why C++ Works This Way

Default parameters are statically bound for runtime efficiency. If default parameter values were dynamically bound, the runtime would need a mechanism to determine the appropriate default at each call site, which would be slower and more complex than the current approach.

### The Fix: NVI Idiom

The NVI idiom elegantly sidesteps this problem. Make the public function non-virtual (with the default parameter), and delegate to a private virtual function (without a default parameter).

```cpp
// GOOD -- NVI idiom avoids the default parameter problem entirely
class Shape {
public:
    virtual ~Shape() = default;

    enum class Color { Red, Green, Blue };

    // Non-virtual: owns the default parameter
    void draw(Color color = Color::Red) const {
        doDraw(color);  // pass explicit argument to virtual
    }

private:
    // Virtual: no default parameter to worry about
    virtual void doDraw(Color color) const = 0;
};

class Circle : public Shape {
private:
    void doDraw(Color color) const override {
        std::cout << "Circle::draw with color "
                  << static_cast<int>(color) << "\n";
    }
};

class Rectangle : public Shape {
private:
    void doDraw(Color color) const override {
        std::cout << "Rectangle::draw with color "
                  << static_cast<int>(color) << "\n";
    }
};

// Now it works correctly:
Shape* pc = new Circle;
Shape* pr = new Rectangle;

pc->draw();              // Circle::draw(Color::Red) -- always consistent!
pr->draw();              // Rectangle::draw(Color::Red) -- always consistent!
pc->draw(Shape::Color::Blue);  // Circle::draw(Color::Blue)
```

### A More Elaborate Example

```cpp
// BAD -- complex hierarchy with inconsistent defaults
class Widget {
public:
    virtual ~Widget() = default;
    virtual void render(int opacity = 255, bool shadow = true) const {
        std::cout << "Widget::render opacity=" << opacity
                  << " shadow=" << shadow << "\n";
    }
};

class Button : public Widget {
public:
    // Changes opacity default -- BAD!
    void render(int opacity = 200, bool shadow = true) const override {
        std::cout << "Button::render opacity=" << opacity
                  << " shadow=" << shadow << "\n";
    }
};

class FlatButton : public Button {
public:
    // Changes shadow default -- BAD!
    void render(int opacity = 200, bool shadow = false) const override {
        std::cout << "FlatButton::render opacity=" << opacity
                  << " shadow=" << shadow << "\n";
    }
};

Widget* w = new FlatButton;
w->render();   // FlatButton::render(255, true) -- Widget's defaults!
               // User expected opacity=200, shadow=false
```

```cpp
// GOOD -- NVI with clean defaults
class Widget {
public:
    virtual ~Widget() = default;

    void render(int opacity = 255, bool shadow = true) const {
        doRender(opacity, shadow);
    }

private:
    virtual void doRender(int opacity, bool shadow) const {
        std::cout << "Widget::render opacity=" << opacity
                  << " shadow=" << shadow << "\n";
    }
};

class Button : public Widget {
private:
    void doRender(int opacity, bool shadow) const override {
        std::cout << "Button::render opacity=" << opacity
                  << " shadow=" << shadow << "\n";
    }
};

class FlatButton : public Button {
private:
    void doRender(int opacity, bool shadow) const override {
        std::cout << "FlatButton::render opacity=" << opacity
                  << " shadow=" << shadow << "\n";
    }
};

Widget* w = new FlatButton;
w->render();   // FlatButton::doRender(255, true) -- consistent!
```

### What if the Derived Class Genuinely Needs a Different Default?

If you truly need different defaults when calling through different types, you probably have a design problem. But if you must, overload instead of changing the default:

```cpp
// ACCEPTABLE -- overloads instead of changing defaults
class Shape {
public:
    virtual ~Shape() = default;

    enum class Color { Red, Green, Blue };

    void draw() const { doDraw(defaultColor()); }
    void draw(Color c) const { doDraw(c); }

protected:
    virtual Color defaultColor() const { return Color::Red; }

private:
    virtual void doDraw(Color color) const = 0;
};

class OceanShape : public Shape {
protected:
    Color defaultColor() const override { return Color::Blue; }
private:
    void doDraw(Color color) const override {
        std::cout << "OceanShape with color " << static_cast<int>(color) << "\n";
    }
};
```

### Things to Remember

- Never redefine an inherited default parameter value, because default parameter values are statically bound, while virtual functions -- the only functions you should be overriding -- are dynamically bound.
- Use the NVI idiom (Item 35) to have the non-virtual public function specify the default, delegating to a private virtual with no default parameter.

---
