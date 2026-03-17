# Design a Vending Machine
**Difficulty:** Medium | **Companies:** Google, Amazon, Microsoft

---

## Problem Statement

Design a vending machine using the State pattern, supporting multiple payment methods, inventory management, and optimal change calculation.

---

## Requirements

### Functional Requirements
1. Display available products with prices
2. Accept multiple payment methods (Cash, Card, UPI)
3. Dispense selected product
4. Return correct change (optimal coin selection)
5. Handle refunds
6. Admin interface for restocking and collecting money
7. Track inventory levels with alerts

### Non-Functional Requirements
1. Clean state machine implementation
2. Thread-safe operations
3. Extensible for new products/payment methods

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      VendingMachine                             │
├─────────────────────────────────────────────────────────────────┤
│ - state: VendingState                                           │
│ - inventory: Inventory                                          │
│ - coinDispenser: CoinDispenser                                  │
│ - display: Display                                              │
│ - currentBalance: Money                                         │
│ - selectedProduct: Product                                      │
├─────────────────────────────────────────────────────────────────┤
│ + selectProduct(code: String): void                             │
│ + insertMoney(amount: Money): void                              │
│ + dispense(): Product                                           │
│ + refund(): Money                                               │
│ + getState(): VendingState                                      │
│ + setState(state: VendingState): void                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  <<interface>> VendingState                     │
├─────────────────────────────────────────────────────────────────┤
│ + selectProduct(machine: VendingMachine, code: String): void    │
│ + insertMoney(machine: VendingMachine, amount: Money): void     │
│ + dispense(machine: VendingMachine): Product                    │
│ + refund(machine: VendingMachine): Money                        │
└─────────────────────────────────────────────────────────────────┘
         △
    ┌────┴────┬──────────────┬──────────────┬───────────┐
    │         │              │              │           │
  Idle   HasMoney     Dispensing      OutOfStock    Error
  State   State        State           State        State
```

---

## Class Implementations

### 1. Product and Inventory
```java
public class Product {
    private final String code;
    private final String name;
    private final Money price;
    private final ProductCategory category;
    
    public Product(String code, String name, Money price, ProductCategory category) {
        this.code = code;
        this.name = name;
        this.price = price;
        this.category = category;
    }
}

public class Inventory {
    private final Map<String, ProductSlot> slots;
    private final List<InventoryObserver> observers;
    
    public Inventory(int numSlots) {
        this.slots = new LinkedHashMap<>();
        this.observers = new ArrayList<>();
    }
    
    public boolean isAvailable(String code) {
        ProductSlot slot = slots.get(code);
        return slot != null && slot.getQuantity() > 0;
    }
    
    public Product dispense(String code) {
        ProductSlot slot = slots.get(code);
        if (slot == null || slot.getQuantity() <= 0) {
            throw new OutOfStockException(code);
        }
        
        slot.decrementQuantity();
        
        if (slot.getQuantity() <= slot.getLowStockThreshold()) {
            notifyLowStock(slot);
        }
        
        return slot.getProduct();
    }
    
    public void restock(String code, int quantity) {
        ProductSlot slot = slots.get(code);
        if (slot != null) {
            slot.addQuantity(quantity);
        }
    }
    
    public List<ProductInfo> getAvailableProducts() {
        return slots.values().stream()
            .filter(slot -> slot.getQuantity() > 0)
            .map(slot -> new ProductInfo(
                slot.getProduct().getCode(),
                slot.getProduct().getName(),
                slot.getProduct().getPrice(),
                slot.getQuantity()
            ))
            .collect(Collectors.toList());
    }
}

class ProductSlot {
    private final Product product;
    private int quantity;
    private final int maxCapacity;
    private final int lowStockThreshold;
}
```

### 2. State Implementations
```java
public interface VendingState {
    void selectProduct(VendingMachine machine, String code);
    void insertMoney(VendingMachine machine, Money amount);
    Product dispense(VendingMachine machine);
    Money refund(VendingMachine machine);
}

public class IdleState implements VendingState {
    @Override
    public void selectProduct(VendingMachine machine, String code) {
        if (!machine.getInventory().isAvailable(code)) {
            machine.getDisplay().show("Product out of stock");
            return;
        }
        
        Product product = machine.getInventory().getProduct(code);
        machine.setSelectedProduct(product);
        machine.getDisplay().show("Selected: " + product.getName() + 
                                  " Price: " + product.getPrice());
        machine.setState(new HasMoneyState());
    }
    
    @Override
    public void insertMoney(VendingMachine machine, Money amount) {
        machine.getDisplay().show("Please select a product first");
    }
    
    @Override
    public Product dispense(VendingMachine machine) {
        throw new InvalidOperationException("No product selected");
    }
    
    @Override
    public Money refund(VendingMachine machine) {
        return Money.ZERO;
    }
}

public class HasMoneyState implements VendingState {
    @Override
    public void selectProduct(VendingMachine machine, String code) {
        // Allow changing selection
        Product product = machine.getInventory().getProduct(code);
        machine.setSelectedProduct(product);
        machine.getDisplay().show("Changed to: " + product.getName());
    }
    
    @Override
    public void insertMoney(VendingMachine machine, Money amount) {
        Money newBalance = machine.getCurrentBalance().add(amount);
        machine.setCurrentBalance(newBalance);
        
        Money price = machine.getSelectedProduct().getPrice();
        if (newBalance.compareTo(price) >= 0) {
            machine.getDisplay().show("Press dispense to get your product");
            machine.setState(new DispensingState());
        } else {
            Money remaining = price.subtract(newBalance);
            machine.getDisplay().show("Insert " + remaining + " more");
        }
    }
    
    @Override
    public Product dispense(VendingMachine machine) {
        throw new InsufficientFundsException("Please insert more money");
    }
    
    @Override
    public Money refund(VendingMachine machine) {
        Money balance = machine.getCurrentBalance();
        machine.setCurrentBalance(Money.ZERO);
        machine.setSelectedProduct(null);
        machine.setState(new IdleState());
        return balance;
    }
}

public class DispensingState implements VendingState {
    @Override
    public Product dispense(VendingMachine machine) {
        Product product = machine.getSelectedProduct();
        Money price = product.getPrice();
        Money balance = machine.getCurrentBalance();
        
        // Dispense product
        machine.getInventory().dispense(product.getCode());
        
        // Calculate and dispense change
        Money change = balance.subtract(price);
        if (change.isPositive()) {
            machine.getCoinDispenser().dispenseChange(change);
        }
        
        // Reset machine
        machine.setCurrentBalance(Money.ZERO);
        machine.setSelectedProduct(null);
        machine.setState(new IdleState());
        machine.getDisplay().show("Thank you! Enjoy your " + product.getName());
        
        return product;
    }
    
    @Override
    public void selectProduct(VendingMachine machine, String code) {
        machine.getDisplay().show("Please collect your product first");
    }
    
    @Override
    public void insertMoney(VendingMachine machine, Money amount) {
        machine.getDisplay().show("Please collect your product first");
    }
    
    @Override
    public Money refund(VendingMachine machine) {
        return new HasMoneyState().refund(machine);
    }
}
```

### 3. Coin Dispenser with Optimal Change
```java
public class CoinDispenser {
    private final Map<Denomination, Integer> coinInventory;
    
    public CoinDispenser() {
        this.coinInventory = new TreeMap<>(Comparator.reverseOrder());
        // Initialize with coins
        for (Denomination d : Denomination.values()) {
            coinInventory.put(d, 100);  // 100 of each
        }
    }
    
    public List<Denomination> dispenseChange(Money amount) {
        List<Denomination> change = new ArrayList<>();
        int remaining = amount.getCents();
        
        for (Map.Entry<Denomination, Integer> entry : coinInventory.entrySet()) {
            Denomination denom = entry.getKey();
            int available = entry.getValue();
            
            int needed = remaining / denom.getValue();
            int toDispense = Math.min(needed, available);
            
            for (int i = 0; i < toDispense; i++) {
                change.add(denom);
            }
            
            remaining -= toDispense * denom.getValue();
            coinInventory.put(denom, available - toDispense);
        }
        
        if (remaining > 0) {
            throw new InsufficientChangeException("Cannot dispense exact change");
        }
        
        return change;
    }
    
    public void addCoins(Denomination denom, int count) {
        coinInventory.merge(denom, count, Integer::sum);
    }
}

public enum Denomination {
    DOLLAR(100), QUARTER(25), DIME(10), NICKEL(5), PENNY(1);
    
    private final int value;  // in cents
}
```

