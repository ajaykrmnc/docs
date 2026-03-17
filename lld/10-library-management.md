# Design a Library Management System
**Difficulty:** Medium | **Companies:** Amazon, Microsoft, Google

---

## Problem Statement

Design a comprehensive library management system for managing books, members, reservations, and fines.

---

## Requirements

### Functional Requirements
1. Book catalog with search (title, author, ISBN, subject)
2. Multiple copies of each book with tracking
3. Member registration and management
4. Book lending with configurable limits
5. Reservation and waitlist system
6. Fine calculation for overdue books
7. Notification system for due dates

### Non-Functional Requirements
1. Concurrent access handling
2. Efficient search
3. Audit trail for all operations

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Library                                  │
├─────────────────────────────────────────────────────────────────┤
│ - catalog: BookCatalog                                          │
│ - members: Map<String, Member>                                  │
│ - loans: Map<String, Loan>                                      │
│ - reservations: Map<String, Queue<Reservation>>                 │
│ - notificationService: NotificationService                      │
├─────────────────────────────────────────────────────────────────┤
│ + searchBooks(query: SearchQuery): List<Book>                   │
│ + checkoutBook(memberId: String, isbn: String): Loan            │
│ + returnBook(loanId: String): Fine                              │
│ + reserveBook(memberId: String, isbn: String): Reservation      │
│ + registerMember(member: Member): void                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          Book                                   │
├─────────────────────────────────────────────────────────────────┤
│ - isbn: String                                                  │
│ - title: String                                                 │
│ - authors: List<Author>                                         │
│ - publisher: String                                             │
│ - publicationDate: LocalDate                                    │
│ - subjects: List<String>                                        │
│ - copies: List<BookItem>                                        │
├─────────────────────────────────────────────────────────────────┤
│ + getAvailableCopies(): List<BookItem>                          │
│ + getTotalCopies(): int                                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        BookItem                                 │
├─────────────────────────────────────────────────────────────────┤
│ - barcode: String                                               │
│ - book: Book                                                    │
│ - status: BookStatus                                            │
│ - rack: Rack                                                    │
│ - condition: BookCondition                                      │
│ - dateAdded: LocalDate                                          │
├─────────────────────────────────────────────────────────────────┤
│ + checkout(): void                                              │
│ + checkin(): void                                               │
│ + isAvailable(): boolean                                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         Member                                  │
├─────────────────────────────────────────────────────────────────┤
│ - memberId: String                                              │
│ - name: String                                                  │
│ - email: String                                                 │
│ - phone: String                                                 │
│ - membershipType: MembershipType                                │
│ - activeLoans: List<Loan>                                       │
│ - totalFinesDue: BigDecimal                                     │
├─────────────────────────────────────────────────────────────────┤
│ + canBorrow(): boolean                                          │
│ + getBorrowLimit(): int                                         │
│ + addLoan(loan: Loan): void                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Class Implementations

### 1. Book and BookItem
```java
public class Book {
    private final String isbn;
    private String title;
    private List<Author> authors;
    private String publisher;
    private LocalDate publicationDate;
    private List<String> subjects;
    private final List<BookItem> copies;
    
    public Book(String isbn, String title, List<Author> authors) {
        this.isbn = isbn;
        this.title = title;
        this.authors = authors;
        this.copies = new ArrayList<>();
        this.subjects = new ArrayList<>();
    }
    
    public List<BookItem> getAvailableCopies() {
        return copies.stream()
            .filter(BookItem::isAvailable)
            .collect(Collectors.toList());
    }
    
    public void addCopy(BookItem item) {
        copies.add(item);
    }
}

public class BookItem {
    private final String barcode;
    private final Book book;
    private BookStatus status;
    private Rack rack;
    private BookCondition condition;
    private LocalDate dateAdded;
    
    public BookItem(String barcode, Book book, Rack rack) {
        this.barcode = barcode;
        this.book = book;
        this.rack = rack;
        this.status = BookStatus.AVAILABLE;
        this.condition = BookCondition.GOOD;
        this.dateAdded = LocalDate.now();
    }
    
    public synchronized boolean checkout() {
        if (status != BookStatus.AVAILABLE) return false;
        status = BookStatus.LOANED;
        return true;
    }
    
    public synchronized void checkin() {
        status = BookStatus.AVAILABLE;
    }
    
    public boolean isAvailable() {
        return status == BookStatus.AVAILABLE;
    }
}

public enum BookStatus {
    AVAILABLE, LOANED, RESERVED, LOST, DAMAGED
}
```

### 2. Member and MembershipType
```java
public class Member {
    private final String memberId;
    private String name;
    private String email;
    private String phone;
    private MembershipType membershipType;
    private List<Loan> activeLoans;
    private BigDecimal totalFinesDue;
    private LocalDate memberSince;
    
    public Member(String name, String email, MembershipType type) {
        this.memberId = generateMemberId();
        this.name = name;
        this.email = email;
        this.membershipType = type;
        this.activeLoans = new ArrayList<>();
        this.totalFinesDue = BigDecimal.ZERO;
        this.memberSince = LocalDate.now();
    }
    
    public boolean canBorrow() {
        if (totalFinesDue.compareTo(BigDecimal.valueOf(10)) > 0) {
            return false;  // Too much fine
        }
        return activeLoans.size() < getBorrowLimit();
    }
    
    public int getBorrowLimit() {
        return membershipType.getBorrowLimit();
    }
    
    public int getLoanPeriodDays() {
        return membershipType.getLoanPeriodDays();
    }
}

public enum MembershipType {
    BASIC(3, 14, BigDecimal.valueOf(0.50)),
    STANDARD(5, 21, BigDecimal.valueOf(0.30)),
    PREMIUM(10, 30, BigDecimal.valueOf(0.20));
    
    private final int borrowLimit;
    private final int loanPeriodDays;
    private final BigDecimal dailyFineRate;
    
    MembershipType(int limit, int days, BigDecimal rate) {
        this.borrowLimit = limit;
        this.loanPeriodDays = days;
        this.dailyFineRate = rate;
    }
}
```

### 3. Loan and Fine
```java
public class Loan {
    private final String loanId;
    private final Member member;
    private final BookItem bookItem;
    private final LocalDate checkoutDate;
    private final LocalDate dueDate;
    private LocalDate returnDate;
    private LoanStatus status;
    
    public Loan(Member member, BookItem bookItem) {
        this.loanId = UUID.randomUUID().toString();
        this.member = member;
        this.bookItem = bookItem;
        this.checkoutDate = LocalDate.now();
        this.dueDate = checkoutDate.plusDays(member.getLoanPeriodDays());
        this.status = LoanStatus.ACTIVE;
    }
    
    public Fine returnBook() {
        this.returnDate = LocalDate.now();
        this.status = LoanStatus.RETURNED;
        bookItem.checkin();
        
        if (isOverdue()) {
            return calculateFine();
        }
        return null;
    }
    
    public boolean isOverdue() {
        LocalDate checkDate = returnDate != null ? returnDate : LocalDate.now();
        return checkDate.isAfter(dueDate);
    }
    
    private Fine calculateFine() {
        long daysOverdue = ChronoUnit.DAYS.between(dueDate, returnDate);
        BigDecimal amount = member.getMembershipType().getDailyFineRate()
            .multiply(BigDecimal.valueOf(daysOverdue));
        return new Fine(this, amount);
    }
}
```

### 4. Search and Catalog
```java
public class BookCatalog {
    private final Map<String, Book> booksByIsbn;
    private final Map<String, Set<Book>> booksByTitle;
    private final Map<String, Set<Book>> booksByAuthor;
    private final Map<String, Set<Book>> booksBySubject;
    
    public List<Book> search(SearchQuery query) {
        Set<Book> results = new HashSet<>();
        
        if (query.getIsbn() != null) {
            Book book = booksByIsbn.get(query.getIsbn());
            if (book != null) results.add(book);
        }
        
        if (query.getTitle() != null) {
            results.addAll(searchByTitle(query.getTitle()));
        }
        
        if (query.getAuthor() != null) {
            results.addAll(searchByAuthor(query.getAuthor()));
        }
        
        return new ArrayList<>(results);
    }
    
    private Set<Book> searchByTitle(String title) {
        return booksByTitle.entrySet().stream()
            .filter(e -> e.getKey().toLowerCase().contains(title.toLowerCase()))
            .flatMap(e -> e.getValue().stream())
            .collect(Collectors.toSet());
    }
}

public class SearchQuery {
    private String isbn;
    private String title;
    private String author;
    private String subject;
    private boolean availableOnly;
    
    // Builder pattern
    public static class Builder {
        private SearchQuery query = new SearchQuery();
        public Builder isbn(String isbn) { query.isbn = isbn; return this; }
        public Builder title(String title) { query.title = title; return this; }
        public Builder author(String author) { query.author = author; return this; }
        public SearchQuery build() { return query; }
    }
}
```

