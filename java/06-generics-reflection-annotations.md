# Generics, Reflection, and Annotations - Deep Dive

## Table of Contents
1. [Generics Fundamentals](#generics-fundamentals)
2. [Type Erasure](#type-erasure)
3. [Bounded Type Parameters](#bounded-type-parameters)
4. [Wildcards Deep Dive](#wildcards)
5. [Reflection API](#reflection-api)
6. [Annotations](#annotations)
7. [Building a Mini Framework](#mini-framework)
8. [Interview Questions](#interview-questions)

---

## Generics Fundamentals

### Why Generics?

```java
// Before Generics (Java 1.4 and earlier)
List list = new ArrayList();
list.add("Hello");
list.add(123);  // No compile error, but dangerous!
String s = (String) list.get(1);  // ClassCastException at runtime!

// With Generics (Java 5+)
List<String> list = new ArrayList<>();
list.add("Hello");
// list.add(123);  // Compile error! Type safety enforced
String s = list.get(0);  // No cast needed
```

### Generic Class Implementation

```java
// Generic class with multiple type parameters
public class Pair<K, V> {
    private final K key;
    private final V value;
    
    public Pair(K key, V value) {
        this.key = key;
        this.value = value;
    }
    
    public K getKey() { return key; }
    public V getValue() { return value; }
    
    // Generic static factory method (type inference)
    public static <K, V> Pair<K, V> of(K key, V value) {
        return new Pair<>(key, value);
    }
    
    // Swap key and value
    public Pair<V, K> swap() {
        return new Pair<>(value, key);
    }
    
    @Override
    public String toString() {
        return "(" + key + ", " + value + ")";
    }
}

// Usage
Pair<String, Integer> pair = Pair.of("age", 25);
Pair<Integer, String> swapped = pair.swap();
```

### Generic Methods

```java
public class GenericMethods {
    // Generic method - type parameter declared before return type
    public static <T> T getFirst(List<T> list) {
        if (list == null || list.isEmpty()) {
            return null;
        }
        return list.get(0);
    }
    
    // Multiple type parameters
    public static <T, U> Pair<T, U> makePair(T first, U second) {
        return new Pair<>(first, second);
    }
    
    // Type parameter with bound
    public static <T extends Comparable<T>> T max(T a, T b) {
        return a.compareTo(b) > 0 ? a : b;
    }
    
    // Generic method in generic class
    public static <T> void copy(List<? super T> dest, List<? extends T> src) {
        for (T item : src) {
            dest.add(item);
        }
    }
}
```

---

## Type Erasure

### How Type Erasure Works

At compile time, generics are converted to raw types:

```java
// What you write:
public class Box<T> {
    private T value;
    public T getValue() { return value; }
    public void setValue(T value) { this.value = value; }
}

// After type erasure (what JVM sees):
public class Box {
    private Object value;
    public Object getValue() { return value; }
    public void setValue(Object value) { this.value = value; }
}

// With bounded type:
public class Box<T extends Number> {
    private T value;
}

// After erasure (bounded type preserved):
public class Box {
    private Number value;  // Erased to bound
}
```

### Type Erasure Implications

```java
// 1. Cannot use instanceof with parameterized types
// if (list instanceof ArrayList<String>) {}  // Compile error!
if (list instanceof ArrayList<?>) {}  // OK, unbounded wildcard

// 2. Cannot create arrays of parameterized types
// List<String>[] array = new ArrayList<String>[10];  // Compile error!
List<?>[] array = new ArrayList<?>[10];  // OK with wildcard
@SuppressWarnings("unchecked")
List<String>[] array = (List<String>[]) new ArrayList<?>[10];  // Workaround

// 3. Cannot create instances of type parameters
public class Factory<T> {
    // public T create() { return new T(); }  // Compile error!
    
    // Workaround using Class token
    private Class<T> type;
    
    public Factory(Class<T> type) {
        this.type = type;
    }
    
    public T create() throws Exception {
        return type.getDeclaredConstructor().newInstance();
    }
}

// 4. Static members cannot use class type parameters
public class Problem<T> {
    // private static T instance;  // Compile error!
    // public static T getInstance() {}  // Compile error!
    
    // Static methods can declare their own type parameters
    public static <U> U staticMethod(U param) { return param; }  // OK
}
```

---

## Bounded Type Parameters

### Upper Bounds

```java
// Single upper bound
public static <T extends Number> double sum(List<T> numbers) {
    double sum = 0;
    for (T n : numbers) {
        sum += n.doubleValue();  // Can call Number methods
    }
    return sum;
}

// Multiple bounds (class first, then interfaces)
public class SortedBox<T extends Comparable<T> & Serializable> {
    private T value;
    
    public int compareTo(SortedBox<T> other) {
        return this.value.compareTo(other.value);
    }
}

// Recursive type bound (F-bounded polymorphism)
public abstract class Builder<T extends Builder<T>> {
    protected abstract T self();
    
    private String name;
    private int id;
    
    public T withName(String name) {
        this.name = name;
        return self();
    }
    
    public T withId(int id) {
        this.id = id;
        return self();
    }
}

public class UserBuilder extends Builder<UserBuilder> {
    private String email;
    
    @Override
    protected UserBuilder self() {
        return this;
    }
    
    public UserBuilder withEmail(String email) {
        this.email = email;
        return this;
    }
    
    public User build() {
        return new User(/* ... */);
    }
}

// Usage: Fluent API without casting
User user = new UserBuilder()
    .withName("John")  // Returns UserBuilder, not Builder
    .withId(123)
    .withEmail("john@example.com")
    .build();
```

---

## Type Erasure Deep Dive

### How Type Erasure Works

```java
// Source code
public class Box<T> {
    private T value;
    public void set(T value) { this.value = value; }
    public T get() { return value; }
}

// After type erasure (what JVM sees)
public class Box {
    private Object value;
    public void set(Object value) { this.value = value; }
    public Object get() { return value; }
}

// Bounded type parameter
public class NumberBox<T extends Number> {
    private T value;
}

// After erasure (erased to bound)
public class NumberBox {
    private Number value;  // Erased to Number, not Object
}
```

### Bridge Methods

```java
// Generic parent
public class Parent<T> {
    public void process(T value) { }
}

// Concrete child
public class Child extends Parent<String> {
    @Override
    public void process(String value) { }
}

// Compiler generates bridge method
public class Child extends Parent {
    // User's method
    public void process(String value) { }

    // Bridge method (synthetic)
    public void process(Object value) {
        process((String) value);  // Delegates to typed version
    }
}
```

### Type Erasure Gotchas

```java
// 1. Cannot create generic arrays
T[] array = new T[10];  // Compile error!
// Workaround:
@SuppressWarnings("unchecked")
T[] array = (T[]) new Object[10];

// 2. Cannot use instanceof with generics
if (obj instanceof List<String>) { }  // Compile error!
// Can only check raw type:
if (obj instanceof List<?>) { }

// 3. Cannot create instances of type parameters
T instance = new T();  // Compile error!
// Workaround: Class<T> factory
public <T> T create(Class<T> clazz) throws Exception {
    return clazz.getDeclaredConstructor().newInstance();
}

// 4. Static members cannot use type parameter
public class Box<T> {
    private static T value;  // Compile error!
    private static List<T> list;  // Compile error!
}
```

---

## Wildcards

### PECS: Producer Extends, Consumer Super

```java
// ? extends T (upper bound) - Producer
// Read from the collection, don't write
public void printNumbers(List<? extends Number> list) {
    for (Number n : list) {
        System.out.println(n);  // Can read as Number
    }
    // list.add(1);  // Compile error! Don't know actual type
}

// ? super T (lower bound) - Consumer
// Write to the collection, limited reading
public void addIntegers(List<? super Integer> list) {
    list.add(1);    // Can add Integer
    list.add(2);
    // Integer n = list.get(0);  // Compile error! Only Object guaranteed
    Object o = list.get(0);  // OK
}

// Example usage
List<Integer> integers = new ArrayList<>();
List<Number> numbers = new ArrayList<>();
List<Object> objects = new ArrayList<>();

// Producer (extends)
printNumbers(integers);  // OK
printNumbers(numbers);   // OK

// Consumer (super)
addIntegers(integers);  // OK
addIntegers(numbers);   // OK
addIntegers(objects);   // OK
```

### Wildcard Capture

```java
// Wildcard capture helper pattern
public class WildcardHelper {

    // This won't compile
    public static void swap(List<?> list, int i, int j) {
        // list.set(i, list.get(j));  // Compile error!
    }

    // Solution: Capture helper
    public static void swap(List<?> list, int i, int j) {
        swapHelper(list, i, j);
    }

    private static <T> void swapHelper(List<T> list, int i, int j) {
        T temp = list.get(i);
        list.set(i, list.get(j));
        list.set(j, temp);
    }
}
```

---

## Reflection API

### Class Introspection

```java
public class ReflectionDemo {

    public void inspectClass(Class<?> clazz) {
        // Class metadata
        System.out.println("Name: " + clazz.getName());
        System.out.println("Simple name: " + clazz.getSimpleName());
        System.out.println("Package: " + clazz.getPackage());
        System.out.println("Superclass: " + clazz.getSuperclass());
        System.out.println("Interfaces: " + Arrays.toString(clazz.getInterfaces()));
        System.out.println("Modifiers: " + Modifier.toString(clazz.getModifiers()));

        // Fields
        for (Field field : clazz.getDeclaredFields()) {
            System.out.println("Field: " + field.getName() + " : " + field.getType());
        }

        // Methods
        for (Method method : clazz.getDeclaredMethods()) {
            System.out.println("Method: " + method.getName());
        }

        // Constructors
        for (Constructor<?> constructor : clazz.getDeclaredConstructors()) {
            System.out.println("Constructor: " + constructor);
        }
    }
}
```

### Dynamic Invocation

```java
public class DynamicInvocation {

    public Object invokeMethod(Object target, String methodName, Object... args)
            throws Exception {
        // Find matching method
        Class<?>[] paramTypes = Arrays.stream(args)
            .map(Object::getClass)
            .toArray(Class<?>[]::new);

        Method method = target.getClass().getMethod(methodName, paramTypes);
        method.setAccessible(true);  // Bypass access checks

        return method.invoke(target, args);
    }

    public <T> T createInstance(Class<T> clazz, Object... args) throws Exception {
        Class<?>[] paramTypes = Arrays.stream(args)
            .map(Object::getClass)
            .toArray(Class<?>[]::new);

        Constructor<T> constructor = clazz.getDeclaredConstructor(paramTypes);
        constructor.setAccessible(true);

        return constructor.newInstance(args);
    }

    public void setField(Object target, String fieldName, Object value) throws Exception {
        Field field = target.getClass().getDeclaredField(fieldName);
        field.setAccessible(true);
        field.set(target, value);
    }
}
```

### Reflection Performance

```java
// Reflection is slower - cache Method/Field objects
public class ReflectionOptimization {
    private static final Map<String, Method> methodCache = new ConcurrentHashMap<>();

    public Object invokeOptimized(Object target, String methodName) throws Exception {
        String key = target.getClass().getName() + "#" + methodName;

        Method method = methodCache.computeIfAbsent(key, k -> {
            try {
                Method m = target.getClass().getMethod(methodName);
                m.setAccessible(true);
                return m;
            } catch (NoSuchMethodException e) {
                throw new RuntimeException(e);
            }
        });

        return method.invoke(target);
    }
}
```

---

## Annotations

### Creating Custom Annotations

```java
// Marker annotation
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface Entity {
}

// Annotation with elements
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface Column {
    String name() default "";
    boolean nullable() default true;
    int length() default 255;
}

// Repeatable annotation
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@Repeatable(Schedules.class)
public @interface Schedule {
    String cron();
}

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Schedules {
    Schedule[] value();
}

// Usage
@Entity
public class User {
    @Column(name = "user_name", nullable = false, length = 100)
    private String name;

    @Schedule(cron = "0 0 * * *")
    @Schedule(cron = "0 12 * * *")
    public void backup() { }
}
```

### Processing Annotations at Runtime

```java
public class AnnotationProcessor {

    public void processEntity(Object entity) {
        Class<?> clazz = entity.getClass();

        if (!clazz.isAnnotationPresent(Entity.class)) {
            throw new IllegalArgumentException("Not an entity");
        }

        for (Field field : clazz.getDeclaredFields()) {
            if (field.isAnnotationPresent(Column.class)) {
                Column column = field.getAnnotation(Column.class);
                String columnName = column.name().isEmpty() ? field.getName() : column.name();
                System.out.println("Column: " + columnName +
                    ", nullable=" + column.nullable() +
                    ", length=" + column.length());
            }
        }
    }
}
```

---

## Building a Mini Framework

### Simple Dependency Injection Container

```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface Inject { }

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface Component { }

public class DIContainer {
    private Map<Class<?>, Object> instances = new HashMap<>();

    public void register(Class<?> clazz) throws Exception {
        if (!clazz.isAnnotationPresent(Component.class)) {
            throw new IllegalArgumentException("Class must be annotated with @Component");
        }

        Object instance = clazz.getDeclaredConstructor().newInstance();
        instances.put(clazz, instance);
    }

    public void autowire() throws Exception {
        for (Object instance : instances.values()) {
            for (Field field : instance.getClass().getDeclaredFields()) {
                if (field.isAnnotationPresent(Inject.class)) {
                    Object dependency = instances.get(field.getType());
                    if (dependency != null) {
                        field.setAccessible(true);
                        field.set(instance, dependency);
                    }
                }
            }
        }
    }

    @SuppressWarnings("unchecked")
    public <T> T get(Class<T> clazz) {
        return (T) instances.get(clazz);
    }
}

// Usage
@Component
public class UserRepository {
    public User findById(int id) { return new User(); }
}

@Component
public class UserService {
    @Inject
    private UserRepository repository;

    public User getUser(int id) {
        return repository.findById(id);
    }
}

// Bootstrap
DIContainer container = new DIContainer();
container.register(UserRepository.class);
container.register(UserService.class);
container.autowire();

UserService service = container.get(UserService.class);
```

---

## Interview Questions

### Q1: Why can't you create generic arrays?

```java
// Arrays are covariant, generics are invariant
// This is legal:
Object[] objects = new String[10];
objects[0] = 123;  // ArrayStoreException at runtime

// If generic arrays were allowed:
List<String>[] lists = new List<String>[10];  // Hypothetically
Object[] objects = lists;  // Covariance
objects[0] = new ArrayList<Integer>();  // No exception!
String s = lists[0].get(0);  // ClassCastException - type safety broken!
```

### Q2: What is reification?

**Reification** means type information is available at runtime.
- Arrays ARE reified: `String[]` knows it holds Strings
- Generics are NOT reified: `List<String>` becomes just `List` at runtime

### Q3: Difference between getClass() and instanceof?

```java
// instanceof checks for IS-A relationship (includes subclasses)
if (obj instanceof Number) { }  // True for Integer, Double, etc.

// getClass() checks exact type
if (obj.getClass() == Integer.class) { }  // Only true for Integer

// With generics
if (obj instanceof List<?>) { }  // OK
// if (obj instanceof List<String>) { }  // Compile error!
```
