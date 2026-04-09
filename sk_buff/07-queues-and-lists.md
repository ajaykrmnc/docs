# Chapter 7: Queues and Lists

Packet processing is fundamentally a queuing discipline. Packets arrive
faster than any single consumer can process them, multiple subsystems contend
for the same buffers, and ordering guarantees must be preserved across
concurrent CPU cores. The Linux kernel addresses this with a family of
queue data structures built around the `sk_buff_head` sentinel and
circular doubly-linked lists. This chapter covers the queue abstraction,
its operations, and every major queue in the network stack.

---

## 1. sk_buff_head — The Queue Header

### 1.1 Structure Definition

Every queue of `sk_buff` structures is managed by an `sk_buff_head`:

```c
struct sk_buff_head {
    struct sk_buff  *next;    /* pointer to first sk_buff (or self)  */
    struct sk_buff  *prev;    /* pointer to last sk_buff (or self)   */
    __u32            qlen;    /* number of sk_buffs in the queue     */
    spinlock_t       lock;    /* protects concurrent access          */
};
```

The structure serves as a **sentinel node** (dummy head) in a circular
doubly-linked list. When the queue is empty, both `next` and `prev` point
back to the `sk_buff_head` itself.

### 1.2 Relationship to sk_buff

Each `sk_buff` contains `next` and `prev` pointers that link it into the
queue:

```c
struct sk_buff {
    struct sk_buff  *next;    /* next buffer in the list   */
    struct sk_buff  *prev;    /* previous buffer           */
    /* ... hundreds of other fields ... */
};
```

The `sk_buff_head` is type-compatible with the `next`/`prev` pair in
`sk_buff`, allowing the sentinel and the data nodes to form a single
uniform circular list.

### 1.3 Circular Doubly-Linked List

The queue forms a ring: the sentinel's `next` points to the first element,
the sentinel's `prev` points to the last element, and each element's `prev`
and `next` chain through to form a closed loop.

```
┌───────────────────────────────────────────────────────────────────┐
│           Circular Doubly-Linked List (3 elements)                │
│                                                                   │
│                     sk_buff_head (sentinel)                        │
│                    ┌──────────────────┐                            │
│           ┌───────►│ next ──────────┐ │◄──────────┐               │
│           │        │ prev ────────┐ │ │           │               │
│           │        │ qlen = 3    │ │ │           │               │
│           │        │ lock        │ │ │           │               │
│           │        └─────────────┼─┼─┘           │               │
│           │                      │ │             │               │
│           │                      │ ▼             │               │
│           │               ┌──────┴──────┐        │               │
│           │               │  sk_buff A  │        │               │
│           │               │  next ──────┼───┐    │               │
│           │          ┌────┤  prev       │   │    │               │
│           │          │    └─────────────┘   │    │               │
│           │          │                      │    │               │
│           │          │                      ▼    │               │
│           │          │               ┌──────────────┐            │
│           │          │               │  sk_buff B  │            │
│           │          │               │  next ──────┼───┐        │
│           │          │          ┌────┤  prev       │   │        │
│           │          │          │    └─────────────┘   │        │
│           │          │          │                      │        │
│           │          │          │                      ▼        │
│           │          │          │               ┌──────────────┐│
│           │          │          │               │  sk_buff C  ││
│           │          │          │               │  next ───────┼┘
│           └──────────┼──────────┼───────────────┤  prev       │
│                      │          │               └─────────────┘
│                      │          │                      ▲
│                      ▼          ▼                      │
│                   sentinel   sentinel               sentinel
│                   (prev)     (prev)                  (next)
│                                                                   │
│  Path: sentinel ──► A ──► B ──► C ──► sentinel  (forward)        │
│  Path: sentinel ──► C ──► B ──► A ──► sentinel  (backward)       │
└───────────────────────────────────────────────────────────────────┘
```

### 1.4 Empty Queue

An empty queue is a degenerate ring where the sentinel points to itself:

```
┌───────────────────────────────────┐
│       Empty Queue                  │
│                                    │
│   sk_buff_head                     │
│  ┌──────────────────┐              │
│  │ next ──────┐     │              │
│  │ prev ──────┤     │              │
│  │ qlen = 0   │     │              │
│  │ lock       │     │              │
│  └────────────┼─────┘              │
│               │                    │
│               └──► (points to      │
│                     itself)        │
└───────────────────────────────────┘
```

The emptiness check is simply:

```c
static inline int skb_queue_empty(const struct sk_buff_head *list)
{
    return list->next == (const struct sk_buff *)list;
}
```

---

## 2. Queue Operations

The kernel provides a comprehensive set of operations for manipulating
`sk_buff` queues. Each operation exists in two variants:

1. **Locked** (`skb_queue_*`) — acquires `list->lock` automatically.
2. **Unlocked** (`__skb_queue_*`) — caller must hold the lock or guarantee
   exclusion by other means.

### 2.1 Initialization

```c
/**
 * skb_queue_head_init - initialize an empty sk_buff queue
 * @list: the queue to initialize
 *
 * Sets next and prev to point to the sentinel, qlen to 0,
 * and initializes the spinlock.
 */
static inline void skb_queue_head_init(struct sk_buff_head *list)
{
    spin_lock_init(&list->lock);
    __skb_queue_head_init(list);
}

static inline void __skb_queue_head_init(struct sk_buff_head *list)
{
    list->prev = list->next = (struct sk_buff *)list;
    list->qlen = 0;
}
```

### 2.2 Adding to the Queue

#### 2.2.1 skb_queue_head() — Add to Front

Inserts `skb` immediately after the sentinel (i.e., at the head of the
queue). The new element becomes the first to be dequeued by `skb_dequeue()`.

```c
void skb_queue_head(struct sk_buff_head *list, struct sk_buff *newsk)
{
    unsigned long flags;

    spin_lock_irqsave(&list->lock, flags);
    __skb_queue_head(list, newsk);
    spin_unlock_irqrestore(&list->lock, flags);
}

static inline void __skb_queue_head(struct sk_buff_head *list,
                                    struct sk_buff *newsk)
{
    __skb_queue_after(list, (struct sk_buff *)list, newsk);
}
```

```
┌──────────────────────────────────────────────┐
│  Before: sentinel ──► A ──► B ──► sentinel   │
│  After:  sentinel ──► NEW ──► A ──► B ──►    │
│          sentinel                             │
└──────────────────────────────────────────────┘
```

#### 2.2.2 skb_queue_tail() — Add to Back

Inserts `skb` immediately before the sentinel (i.e., at the tail of the
queue). This is the most common enqueue operation.

```c
void skb_queue_tail(struct sk_buff_head *list, struct sk_buff *newsk)
{
    unsigned long flags;

    spin_lock_irqsave(&list->lock, flags);
    __skb_queue_tail(list, newsk);
    spin_unlock_irqrestore(&list->lock, flags);
}

static inline void __skb_queue_tail(struct sk_buff_head *list,
                                    struct sk_buff *newsk)
{
    __skb_queue_before(list, (struct sk_buff *)list, newsk);
}
```

```
┌──────────────────────────────────────────────┐
│  Before: sentinel ──► A ──► B ──► sentinel   │
│  After:  sentinel ──► A ──► B ──► NEW ──►    │
│          sentinel                             │
└──────────────────────────────────────────────┘
```

#### 2.2.3 skb_insert() — Insert Before

Insert `newsk` before `old` in the list:

```c
static inline void __skb_insert(struct sk_buff *newsk,
                                struct sk_buff *prev,
                                struct sk_buff *next,
                                struct sk_buff_head *list)
{
    newsk->next  = next;
    newsk->prev  = prev;
    next->prev   = newsk;
    prev->next   = newsk;
    list->qlen++;
}

void skb_insert(struct sk_buff *old, struct sk_buff *newsk,
                struct sk_buff_head *list)
{
    unsigned long flags;

    spin_lock_irqsave(&list->lock, flags);
    __skb_insert(newsk, old->prev, old, list);
    spin_unlock_irqrestore(&list->lock, flags);
}
```

```
┌──────────────────────────────────────────────────┐
│  Before: ... ──► X ──► old ──► Y ──► ...         │
│  After:  ... ──► X ──► NEW ──► old ──► Y ──► ... │
└──────────────────────────────────────────────────┘
```

#### 2.2.4 skb_append() — Insert After

Insert `newsk` after `old` in the list:

```c
void skb_append(struct sk_buff *old, struct sk_buff *newsk,
                struct sk_buff_head *list)
{
    unsigned long flags;

    spin_lock_irqsave(&list->lock, flags);
    __skb_insert(newsk, old, old->next, list);
    spin_unlock_irqrestore(&list->lock, flags);
}
```

```
┌──────────────────────────────────────────────────┐
│  Before: ... ──► old ──► Y ──► ...               │
│  After:  ... ──► old ──► NEW ──► Y ──► ...       │
└──────────────────────────────────────────────────┘
```

### 2.3 Removing from the Queue

#### 2.3.1 skb_dequeue() — Remove from Front

Removes and returns the first sk_buff in the queue. Returns `NULL` if
the queue is empty.

```c
struct sk_buff *skb_dequeue(struct sk_buff_head *list)
{
    unsigned long flags;
    struct sk_buff *result;

    spin_lock_irqsave(&list->lock, flags);
    result = __skb_dequeue(list);
    spin_unlock_irqrestore(&list->lock, flags);

    return result;
}

static inline struct sk_buff *__skb_dequeue(struct sk_buff_head *list)
{
    struct sk_buff *skb = skb_peek(list);
    if (skb)
        __skb_unlink(skb, list);
    return skb;
}
```

#### 2.3.2 skb_dequeue_tail() — Remove from Back

Removes and returns the last sk_buff in the queue:

```c
struct sk_buff *skb_dequeue_tail(struct sk_buff_head *list)
{
    unsigned long flags;
    struct sk_buff *result;

    spin_lock_irqsave(&list->lock, flags);
    result = __skb_dequeue_tail(list);
    spin_unlock_irqrestore(&list->lock, flags);

    return result;
}

static inline struct sk_buff *__skb_dequeue_tail(struct sk_buff_head *list)
{
    struct sk_buff *skb = skb_peek_tail(list);
    if (skb)
        __skb_unlink(skb, list);
    return skb;
}
```

#### 2.3.3 skb_unlink() — Remove Specific Element

Removes a known sk_buff from its queue:

```c
void skb_unlink(struct sk_buff *skb, struct sk_buff_head *list)
{
    unsigned long flags;

    spin_lock_irqsave(&list->lock, flags);
    __skb_unlink(skb, list);
    spin_unlock_irqrestore(&list->lock, flags);
}

static inline void __skb_unlink(struct sk_buff *skb,
                                struct sk_buff_head *list)
{
    struct sk_buff *next, *prev;

    next       = skb->next;
    prev       = skb->prev;
    skb->next  = skb->prev = NULL;
    next->prev = prev;
    prev->next = next;
    list->qlen--;
}
```

### 2.4 Queue Purge

`skb_queue_purge()` removes and frees every sk_buff in the queue:

```c
void skb_queue_purge(struct sk_buff_head *list)
{
    struct sk_buff *skb;
    while ((skb = skb_dequeue(list)) != NULL)
        kfree_skb(skb);
}
```

The unlocked variant `__skb_queue_purge()` is used when the caller already
holds the lock or exclusion is guaranteed:

```c
void __skb_queue_purge(struct sk_buff_head *list)
{
    struct sk_buff *skb;
    while ((skb = __skb_dequeue(list)) != NULL)
        kfree_skb(skb);
}
```

### 2.5 Queue Length

```c
static inline __u32 skb_queue_len(const struct sk_buff_head *list)
{
    return list->qlen;   /* O(1): maintained by insert/remove */
}
```

The `qlen` field is incremented on every insert and decremented on every
remove, so this is always O(1).

### 2.6 Peeking

#### 2.6.1 skb_peek() — Examine Front

Returns a pointer to the first sk_buff without removing it:

```c
static inline struct sk_buff *skb_peek(const struct sk_buff_head *list)
{
    struct sk_buff *skb = list->next;
    if (skb == (struct sk_buff *)list)
        skb = NULL;   /* queue is empty */
    return skb;
}
```

#### 2.6.2 skb_peek_tail() — Examine Back

Returns a pointer to the last sk_buff without removing it:

```c
static inline struct sk_buff *skb_peek_tail(const struct sk_buff_head *list)
{
    struct sk_buff *skb = list->prev;
    if (skb == (struct sk_buff *)list)
        skb = NULL;   /* queue is empty */
    return skb;
}
```

### 2.7 Locked vs Unlocked Variants

The dual-variant pattern applies to all operations:

```
┌───────────────────────┬──────────────────────────────────────────┐
│ Locked (safe)         │ Unlocked (caller provides exclusion)     │
├───────────────────────┼──────────────────────────────────────────┤
│ skb_queue_head()      │ __skb_queue_head()                       │
│ skb_queue_tail()      │ __skb_queue_tail()                       │
│ skb_dequeue()         │ __skb_dequeue()                          │
│ skb_dequeue_tail()    │ __skb_dequeue_tail()                     │
│ skb_insert()          │ __skb_insert()                           │
│ skb_append()          │ __skb_append()                           │
│ skb_unlink()          │ __skb_unlink()                           │
│ skb_queue_purge()     │ __skb_queue_purge()                      │
│ skb_queue_splice()    │ __skb_queue_splice()                     │
└───────────────────────┴──────────────────────────────────────────┘
```

**When to use which:**

- **Locked variants** — default choice. Use in contexts where multiple CPUs
  or softirqs might access the queue concurrently.
- **Unlocked variants** — use only when:
  - The caller already holds `list->lock`.
  - The queue is per-CPU and preemption/softirqs are disabled.
  - The code is in an initialization path with no concurrent access.

### 2.8 Queue Splicing

Splicing moves all elements from one queue to another atomically:

```c
/**
 * skb_queue_splice - join two queues
 * @list: source queue (emptied after call)
 * @head: destination queue (elements prepended)
 */
static inline void skb_queue_splice(const struct sk_buff_head *list,
                                    struct sk_buff_head *head)
{
    if (!skb_queue_empty(list))
        __skb_queue_splice(list, (struct sk_buff *)head, head->next);
}

/**
 * skb_queue_splice_tail - join, appending to destination
 * @list: source queue (emptied after call)
 * @head: destination queue (elements appended)
 */
static inline void skb_queue_splice_tail(const struct sk_buff_head *list,
                                         struct sk_buff_head *head)
{
    if (!skb_queue_empty(list))
        __skb_queue_splice(list, head->prev, (struct sk_buff *)head);
}
```

The `_init` variants also reinitialize the source queue:

```c
void skb_queue_splice_init(struct sk_buff_head *list,
                           struct sk_buff_head *head);
void skb_queue_splice_tail_init(struct sk_buff_head *list,
                                struct sk_buff_head *head);
```

---

## 3. Queue Iteration

### 3.1 skb_queue_walk() — Forward Iteration

Iterates through every sk_buff in the queue from front to back:

```c
/**
 * skb_queue_walk - iterate over a queue
 * @queue: sk_buff_head to iterate
 * @skb:   loop cursor (struct sk_buff *)
 *
 * WARNING: Do not modify the queue during iteration.
 *          Use skb_queue_walk_safe() for removal.
 */
#define skb_queue_walk(queue, skb) \
    for (skb = (queue)->next;     \
         skb != (struct sk_buff *)(queue); \
         skb = skb->next)
```

**Usage example:**

```c
struct sk_buff_head *q = &sk->sk_receive_queue;
struct sk_buff *skb;

skb_queue_walk(q, skb) {
    /* Process each sk_buff in receive order.      */
    /* Do NOT remove skb from the queue here.      */
    pr_info("skb len=%u\n", skb->len);
}
```

### 3.2 skb_queue_walk_safe() — Safe Removal During Iteration

Uses a temporary variable to allow removing the current element:

```c
/**
 * skb_queue_walk_safe - iterate, safe against removal
 * @queue: sk_buff_head to iterate
 * @skb:   loop cursor
 * @tmp:   temporary sk_buff * for safe iteration
 */
#define skb_queue_walk_safe(queue, skb, tmp) \
    for (skb = (queue)->next, tmp = skb->next; \
         skb != (struct sk_buff *)(queue);     \
         skb = tmp, tmp = skb->next)
```

**Usage example:**

```c
struct sk_buff *skb, *tmp;

skb_queue_walk_safe(&sk->sk_receive_queue, skb, tmp) {
    if (should_drop(skb)) {
        __skb_unlink(skb, &sk->sk_receive_queue);
        kfree_skb(skb);       /* safe: tmp holds next element */
    }
}
```

### 3.3 skb_queue_walk_from() — Start from a Specific Element

Begins iteration from a known sk_buff rather than the queue head:

```c
/**
 * skb_queue_walk_from - iterate from a specific sk_buff
 * @queue: sk_buff_head
 * @skb:   starting sk_buff (must be in the queue)
 */
#define skb_queue_walk_from(queue, skb) \
    for (; skb != (struct sk_buff *)(queue); \
         skb = skb->next)
```

**Usage example:**

```c
struct sk_buff *start = find_starting_point(queue);

skb_queue_walk_from(queue, start) {
    /* Process from 'start' to the end of the queue */
    process(skb);
}
```

A safe variant also exists:

```c
#define skb_queue_walk_from_safe(queue, skb, tmp) \
    for (tmp = skb->next;                         \
         skb != (struct sk_buff *)(queue);         \
         skb = tmp, tmp = skb->next)
```

### 3.4 skb_queue_reverse_walk() — Backward Iteration

Iterates from the tail toward the head:

```c
/**
 * skb_queue_reverse_walk - iterate backward through queue
 * @queue: sk_buff_head
 * @skb:   loop cursor
 */
#define skb_queue_reverse_walk(queue, skb) \
    for (skb = (queue)->prev;              \
         skb != (struct sk_buff *)(queue); \
         skb = skb->prev)
```

**Usage example** (find the most recent packet matching a condition):

```c
struct sk_buff *skb;

skb_queue_reverse_walk(&sk->sk_write_queue, skb) {
    if (TCP_SKB_CB(skb)->seq <= target_seq)
        break;   /* found the segment covering target_seq */
}
```

A safe variant for removal during backward iteration:

```c
#define skb_queue_reverse_walk_safe(queue, skb, tmp) \
    for (skb = (queue)->prev, tmp = skb->prev;       \
         skb != (struct sk_buff *)(queue);            \
         skb = tmp, tmp = skb->prev)
```

### 3.5 Iteration Diagram

```
┌──────────────────────────────────────────────────────────────┐
│               Queue Iteration Directions                      │
│                                                               │
│  sentinel ──► skb_A ──► skb_B ──► skb_C ──► sentinel         │
│     ▲                                           │             │
│     └───────────────────────────────────────────┘             │
│                                                               │
│  skb_queue_walk():         A → B → C  (stop at sentinel)     │
│  skb_queue_reverse_walk(): C → B → A  (stop at sentinel)     │
│  skb_queue_walk_from(B):   B → C      (stop at sentinel)     │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Socket Queue Hierarchy

Every socket (`struct sock`) maintains several queues that buffer packets
at different stages of processing. Understanding these queues is essential
for diagnosing performance issues and understanding flow control.

### 4.1 Per-Socket Queues Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                   Socket Queue Architecture                          │
│                                                                      │
│  struct sock (sk)                                                    │
│  │                                                                   │
│  ├── sk_receive_queue ──► [skb] ──► [skb] ──► [skb]                │
│  │   (data ready for userspace read())                               │
│  │                                                                   │
│  ├── sk_write_queue ──► [skb] ──► [skb]                             │
│  │   (TCP: data queued for transmission)                             │
│  │                                                                   │
│  ├── sk_error_queue ──► [skb]                                       │
│  │   (ICMP errors, timestamps, etc.)                                 │
│  │                                                                   │
│  └── sk_backlog                                                      │
│      ├── head ──► [skb] ──► [skb]                                   │
│      └── tail ──► [skb]                                              │
│      (packets received while socket is locked by userspace)          │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 sk_receive_queue

This is the primary receive buffer. When data arrives for a socket and the
socket is not locked, the transport layer (TCP, UDP, etc.) places sk_buffs
here. Userspace `read()`, `recv()`, and `recvmsg()` consume from this queue.

```c
struct sock {
    /* ... */
    struct sk_buff_head sk_receive_queue;
    /* ... */
};
```

**TCP**: Stores in-order, reassembled data segments. The TCP receive path
places data here only after sequence number ordering and ACK processing.

**UDP**: Stores individual datagrams. Each `recvmsg()` call returns one
complete datagram.

Queue depth is bounded by `sk->sk_rcvbuf` (the receive buffer size, tunable
via `SO_RCVBUF` or autotuning). When the queue fills, the transport protocol
applies backpressure (TCP window shrinks; UDP drops packets).

### 4.3 sk_write_queue

The write queue holds outbound data that has been accepted from userspace but
not yet transmitted or acknowledged.

**TCP**: This is the TCP write queue. It contains segments that:
- Have been formed but not yet sent (waiting for congestion window).
- Have been sent but not yet acknowledged (may need retransmission).

```c
/* TCP enqueues segments to the write queue */
static inline void tcp_add_write_queue_tail(struct sock *sk,
                                            struct sk_buff *skb)
{
    __skb_queue_tail(&sk->sk_write_queue, skb);
}
```

The write queue and the retransmit queue were historically the same structure.
In modern kernels (5.x+), TCP uses a separate red-black tree
(`tcp_rtx_queue`) for retransmission tracking, but the write queue still
holds segments awaiting initial transmission.

### 4.4 sk_error_queue

Error notifications are queued here for retrieval via `recvmsg()` with
`MSG_ERRQUEUE`:

```c
/* Enqueue an error notification */
void sock_queue_err_skb(struct sock *sk, struct sk_buff *skb)
{
    skb_queue_tail(&sk->sk_error_queue, skb);
    sk->sk_error_report(sk);   /* wake up userspace */
}
```

Common sources:
- ICMP errors (Destination Unreachable, Time Exceeded).
- TX timestamps (`SO_TIMESTAMPING`).
- `MSG_ZEROCOPY` completion notifications.

### 4.5 sk_backlog

The backlog handles a race condition: what happens when a packet arrives
for a socket that is currently locked by userspace (e.g., in the middle of
`sendmsg()`)?

```c
struct sock {
    /* ... */
    struct {
        struct sk_buff *head;
        struct sk_buff *tail;
        int             len;    /* total bytes in backlog */
    } sk_backlog;
    /* ... */
};
```

The backlog is **not** an `sk_buff_head` — it uses a simpler singly-linked
list via `skb->next` for performance.

The flow:

```
┌────────────────────────────────────────────────────────────────┐
│                 Backlog Processing Flow                         │
│                                                                │
│  Packet arrives (softirq context)                              │
│  └── tcp_v4_rcv() / udp_rcv()                                 │
│      └── Is sock locked by user?                               │
│          ├── NO  ──► Process immediately                       │
│          │           └── Enqueue to sk_receive_queue            │
│          └── YES ──► sk_add_backlog(sk, skb)                   │
│                      └── Link to sk_backlog list               │
│                                                                │
│  User releases sock lock                                       │
│  └── release_sock(sk)                                          │
│      └── __release_sock(sk)                                    │
│          └── Process all backlog packets:                       │
│              while (sk->sk_backlog.head) {                     │
│                  skb = sk->sk_backlog.head;                    │
│                  sk->sk_backlog.head = skb->next;              │
│                  sk->sk_backlock_rcv(sk, skb);  /* process */  │
│              }                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.6 TCP-Specific Queues

TCP maintains additional queues beyond the generic socket queues:

#### 4.6.1 Retransmit Queue (tcp_rtx_queue)

In modern kernels, TCP uses an `rb_root` (red-black tree) indexed by
sequence number for retransmission:

```c
struct tcp_sock {
    /* ... */
    struct rb_root tcp_rtx_queue;   /* retransmit queue (rb-tree) */
    /* ... */
};
```

Segments are inserted when first transmitted and removed upon ACK. The
tree allows efficient lookup by sequence number for selective ACK (SACK)
processing.

```
┌──────────────────────────────────────────────────────────────┐
│            TCP Retransmit Queue (Red-Black Tree)              │
│                                                               │
│                     [seq=5000]                                 │
│                    /          \                                │
│              [seq=2000]    [seq=8000]                          │
│              /      \         \                               │
│         [seq=1000] [seq=3000] [seq=10000]                     │
│                                                               │
│  Each node is an sk_buff with TCP_SKB_CB(skb)->seq as key    │
│  Allows O(log n) lookup for SACK processing                  │
└──────────────────────────────────────────────────────────────┘
```

#### 4.6.2 Out-of-Order Queue (ooo_queue)

When TCP receives segments out of order, they are held in the OOO queue
until the gaps are filled:

```c
struct tcp_sock {
    /* ... */
    struct rb_root ooo_last_skb;     /* cache for OOO insertion */
    struct rb_root out_of_order_queue; /* rb-tree of OOO segments */
    /* ... */
};
```

```
┌──────────────────────────────────────────────────────────────┐
│             TCP Out-of-Order Queue                            │
│                                                               │
│  Expected next seq: 1000                                      │
│                                                               │
│  Received:  [1000-1460]  [2920-4380]  [5840-7300]            │
│             (in order)   (gap!)       (gap!)                  │
│                                                               │
│  sk_receive_queue: [1000-1460]                                │
│  ooo_queue:        [2920-4380] ──► [5840-7300]               │
│                                                               │
│  When [1460-2920] arrives:                                    │
│    ├── Deliver [1460-2920] to receive queue                   │
│    └── Move [2920-4380] from ooo to receive queue            │
│        (gap at 4380 still exists, [5840-7300] stays in OOO)  │
└──────────────────────────────────────────────────────────────┘
```

#### 4.6.3 Prequeue (Historical)

Older kernels (< 4.x) had a prequeue mechanism that deferred TCP processing
from softirq to process context for cache efficiency. It was removed in
Linux 4.14 (commit `e7942d0`) because the backlog mechanism provides
similar benefits with less complexity.

### 4.7 Complete TCP Socket Queue Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                  All Queues for a TCP Socket                         │
│                                                                      │
│  struct sock / tcp_sock                                              │
│  │                                                                   │
│  ├── sk_receive_queue ─────────────────────────────────────────┐     │
│  │   [seq=0..1460] → [seq=1460..2920] → [seq=2920..4380]      │     │
│  │   In-order data ready for recv()                            │     │
│  │                                                             │     │
│  ├── sk_write_queue ───────────────────────────────────────┐   │     │
│  │   [seq=0..1460] → [seq=1460..2920]                      │   │     │
│  │   Data from send() not yet transmitted                   │   │     │
│  │                                                         │   │     │
│  ├── tcp_rtx_queue (rb_root) ──────────────────────────┐   │   │     │
│  │        [seq=0..1460]                                │   │   │     │
│  │       /             \                               │   │   │     │
│  │   (left)          [seq=1460..2920]                  │   │   │     │
│  │   Sent but not ACK'd, indexed by seq               │   │   │     │
│  │                                                     │   │   │     │
│  ├── out_of_order_queue (rb_root) ─────────────────┐   │   │   │     │
│  │   [seq=5840..7300] → [seq=8760..10220]          │   │   │   │     │
│  │   Received out of order, waiting for gap fill   │   │   │   │     │
│  │                                                 │   │   │   │     │
│  ├── sk_error_queue ───────────────────────────┐   │   │   │   │     │
│  │   [ICMP err] → [TX timestamp]               │   │   │   │   │     │
│  │                                             │   │   │   │   │     │
│  └── sk_backlog ───────────────────────────┐   │   │   │   │   │     │
│      [pending skb] → [pending skb]         │   │   │   │   │   │     │
│      Arrived while socket was user-locked  │   │   │   │   │   │     │
│                                            │   │   │   │   │   │     │
└────────────────────────────────────────────┴───┴───┴───┴───┴───┘     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 5. Device Queues

### 5.1 netdev_queue — Per-TX-Queue Structure

Modern NICs expose multiple transmit queues for parallelism. Each is
represented by `struct netdev_queue`:

```c
struct netdev_queue {
    struct net_device   *dev;           /* owning device          */
    int                  numa_node;     /* NUMA locality          */
    struct Qdisc __rcu  *qdisc;        /* queueing discipline    */
    struct Qdisc        *qdisc_sleeping; /* qdisc when down      */
    unsigned long        tx_maxrate;    /* rate limit (bytes/s)   */
    unsigned long        trans_start;   /* last TX timestamp      */
    unsigned long        state;         /* queue state flags      */
    /* ... */
};
```

Access is via the `dev->_tx[]` array:

```c
struct net_device {
    /* ... */
    struct netdev_queue *_tx;           /* array of TX queues       */
    unsigned int         num_tx_queues; /* number of TX queues      */
    unsigned int         real_num_tx_queues; /* currently active     */
    /* ... */
};
```

### 5.2 Multi-Queue NIC Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                Multi-Queue NIC TX Architecture                    │
│                                                                  │
│  net_device                                                      │
│  ├── num_tx_queues = 4                                           │
│  └── _tx[]                                                       │
│      ├── _tx[0]: netdev_queue                                    │
│      │   └── qdisc ──► fq_codel ──► [skb][skb][skb]            │
│      │                                                           │
│      ├── _tx[1]: netdev_queue                                    │
│      │   └── qdisc ──► fq_codel ──► [skb][skb]                 │
│      │                                                           │
│      ├── _tx[2]: netdev_queue                                    │
│      │   └── qdisc ──► fq_codel ──► [skb]                      │
│      │                                                           │
│      └── _tx[3]: netdev_queue                                    │
│          └── qdisc ──► fq_codel ──► [skb][skb][skb][skb]       │
│                                                                  │
│  TX queue selection: netdev_pick_tx()                             │
│  └── Uses XPS, flow hash, or sk->sk_tx_queue_mapping            │
│                                                                  │
│  Each queue ──► separate NIC TX ring ──► separate DMA channel    │
└──────────────────────────────────────────────────────────────────┘
```

### 5.3 TX Queue States

A TX queue has state flags that control flow:

```c
enum netdev_queue_state_t {
    __QUEUE_STATE_DRV_XOFF,     /* driver stopped the queue      */
    __QUEUE_STATE_STACK_XOFF,   /* stack stopped the queue       */
    __QUEUE_STATE_FROZEN,       /* queue frozen (during reset)   */
};
```

Drivers use these to implement flow control:

```c
/* Driver: stop queue when TX ring is full */
netif_tx_stop_queue(txq);

/* Driver: restart queue when TX ring has space */
netif_tx_wake_queue(txq);

/* Stack: check if queue is stopped */
bool stopped = netif_tx_queue_stopped(txq);
```

### 5.4 softnet_data — Per-CPU Receive Processing

Each CPU has a `struct softnet_data` that manages receive-side processing:

```c
struct softnet_data {
    struct list_head     poll_list;       /* NAPI devices to poll     */
    struct sk_buff_head  input_pkt_queue; /* backlog RX queue         */
    struct sk_buff_head  process_queue;   /* being processed          */
    struct sk_buff       *completion_queue; /* TX completion freelist */
    /* ... */
    unsigned int         input_queue_head;
    unsigned int         input_queue_tail;
    unsigned int         processed;
    unsigned int         time_squeeze;   /* ran out of NAPI budget    */
    unsigned int         received_rps;   /* packets steered via RPS   */
    struct softnet_data  *rps_ipi_list;  /* CPUs needing IPI for RPS  */
    /* ... */
    unsigned int         dropped;        /* packets dropped           */
    /* ... */
};

DECLARE_PER_CPU_ALIGNED(struct softnet_data, softnet_data);
```

### 5.5 softnet_data Queue Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│              Per-CPU softnet_data (CPU 0)                        │
│                                                                  │
│  softnet_data                                                    │
│  │                                                               │
│  ├── poll_list ──► [napi_A] ──► [napi_B]                        │
│  │   NAPI instances with pending work                            │
│  │                                                               │
│  ├── input_pkt_queue ──► [skb] ──► [skb] ──► [skb]             │
│  │   Packets enqueued via netif_rx() (backlog mode)              │
│  │   Also: packets steered here by RPS from other CPUs           │
│  │                                                               │
│  ├── process_queue ──► [skb] ──► [skb]                          │
│  │   Packets currently being processed by process_backlog()      │
│  │                                                               │
│  └── completion_queue ──► [skb] ──► [skb]                       │
│      TX sk_buffs waiting to be freed (deferred free)             │
│                                                                  │
│  NET_RX_SOFTIRQ triggers processing:                             │
│  1. net_rx_action() iterates poll_list                           │
│  2. Each NAPI poll() delivers packets up the stack               │
│  3. process_backlog() drains input_pkt_queue                     │
└──────────────────────────────────────────────────────────────────┘
```

### 5.6 Queueing Disciplines (qdisc)

Each TX queue has an associated queueing discipline that controls the order
and rate at which packets are transmitted. The qdisc sits between the
network layer and the driver.

```c
struct Qdisc {
    int                  (*enqueue)(struct sk_buff *skb,
                                    struct Qdisc *sch,
                                    struct sk_buff **to_free);
    struct sk_buff      *(*dequeue)(struct Qdisc *sch);
    unsigned int         flags;
    /* ... */
    struct sk_buff_head  gso_skb;     /* GSO requeue list       */
    struct sk_buff_head  skb_bad_txq; /* rejected packets       */
    /* ... */
    atomic_t             refcnt;
    /* ... */
};
```

#### 5.6.1 Common Queueing Disciplines

```
┌───────────────┬──────────────────────────────────────────────────┐
│ Qdisc         │ Description                                      │
├───────────────┼──────────────────────────────────────────────────┤
│ pfifo_fast    │ Default: 3-band priority FIFO (legacy)           │
│ fq_codel      │ Fair Queuing + Controlled Delay (modern default) │
│ htb           │ Hierarchical Token Bucket (traffic shaping)      │
│ tbf           │ Token Bucket Filter (simple rate limiting)       │
│ sfq           │ Stochastic Fairness Queuing                      │
│ prio          │ Priority scheduler (configurable bands)          │
│ red           │ Random Early Detection (congestion avoidance)    │
│ netem         │ Network Emulator (delay, loss, reorder)          │
│ mq            │ Multi-queue wrapper (default for multi-queue NIC)│
│ noqueue       │ No queuing (loopback, virtual devices)           │
│ clsact        │ Classifier-action only (BPF/TC programs)        │
└───────────────┴──────────────────────────────────────────────────┘
```

#### 5.6.2 Qdisc in the TX Path

```
┌──────────────────────────────────────────────────────────────────┐
│                  TX Path Through Qdisc                            │
│                                                                  │
│  dev_queue_xmit(skb)                                             │
│  └── __dev_queue_xmit()                                          │
│      ├── 1. Select TX queue: netdev_pick_tx()                    │
│      ├── 2. Get qdisc: txq->qdisc                               │
│      ├── 3. Enqueue: qdisc->enqueue(skb, qdisc)                 │
│      │       └── qdisc applies scheduling/shaping rules          │
│      └── 4. Dequeue + transmit: __qdisc_run()                   │
│              └── while (skb = qdisc->dequeue(qdisc)) {           │
│                      sch_direct_xmit(skb, ...)                   │
│                      └── dev->netdev_ops->ndo_start_xmit(skb)    │
│                  }                                                │
│                                                                  │
│  Special case: noqueue (e.g., loopback)                          │
│  └── Bypasses qdisc, calls ndo_start_xmit() directly            │
└──────────────────────────────────────────────────────────────────┘
```

### 5.7 Device Queue vs Socket Queue Flow

The complete path from socket to wire traverses multiple queues:

```
┌──────────────────────────────────────────────────────────────────────┐
│          Complete TX Queue Path: Socket to Wire                      │
│                                                                      │
│  Application                                                         │
│  └── sendmsg(fd, data, len)                                          │
│                                                                      │
│  Socket Layer                                                        │
│  └── tcp_sendmsg() / udp_sendmsg()                                   │
│      └── Enqueue to sk->sk_write_queue                               │
│                                                                      │
│  Transport Layer                                                     │
│  └── tcp_write_xmit()                                                │
│      └── Dequeue from sk_write_queue                                 │
│          └── ip_queue_xmit(skb)                                      │
│                                                                      │
│  Network Layer                                                       │
│  └── ip_output() → ip_finish_output()                                │
│      └── dst_output() → neigh_output()                               │
│                                                                      │
│  Neighbor/ARP Layer                                                  │
│  └── dev_queue_xmit(skb)                                             │
│                                                                      │
│  Qdisc Layer                                                         │
│  ├── Enqueue to qdisc (e.g., fq_codel)                               │
│  └── Dequeue from qdisc                                              │
│                                                                      │
│  Driver                                                              │
│  └── ndo_start_xmit(skb, dev)                                       │
│      └── Place in NIC TX ring (DMA descriptor)                       │
│                                                                      │
│  NIC Hardware                                                        │
│  └── DMA data from ring → transmit on wire                           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 6. Backlog Processing

### 6.1 netif_rx() — Legacy Receive Path

`netif_rx()` is the traditional (non-NAPI) function for delivering received
packets. It enqueues the sk_buff onto the current CPU's
`softnet_data.input_pkt_queue`:

```c
int netif_rx(struct sk_buff *skb)
{
    struct softnet_data *sd = this_cpu_ptr(&softnet_data);

    /* Enqueue to per-CPU backlog */
    if (skb_queue_len(&sd->input_pkt_queue) <= netdev_budget) {
        __skb_queue_tail(&sd->input_pkt_queue, skb);
        /* Schedule NET_RX_SOFTIRQ if not already pending */
        napi_schedule_irqoff(&sd->backlog);
        return NET_RX_SUCCESS;
    }

    /* Queue full — drop */
    kfree_skb(skb);
    return NET_RX_DROP;
}
```

Modern drivers use NAPI directly and bypass `netif_rx()`. However, it remains
used by:
- Virtual devices (tun, veth).
- Loopback.
- Legacy drivers.
- RPS packet steering (enqueue to remote CPU).

### 6.2 process_backlog()

`process_backlog()` is a NAPI poll function registered for the per-CPU
backlog. When `NET_RX_SOFTIRQ` fires, `net_rx_action()` calls it to drain
the backlog:

```c
static int process_backlog(struct napi_struct *napi, int quota)
{
    struct softnet_data *sd = container_of(napi,
                                           struct softnet_data,
                                           backlog);
    int work = 0;

    while (work < quota) {
        struct sk_buff *skb;

        /* Move packets from input_pkt_queue to process_queue */
        /* (under lock, then process lock-free) */
        local_irq_disable();
        skb_queue_splice_tail_init(&sd->input_pkt_queue,
                                   &sd->process_queue);
        local_irq_enable();

        /* Process from process_queue */
        while ((skb = __skb_dequeue(&sd->process_queue))) {
            __netif_receive_skb(skb);   /* deliver up the stack */
            if (++work >= quota)
                break;
        }
    }

    return work;
}
```

The two-queue design (input → process) minimizes lock contention: the
input queue is locked only briefly during the splice, and processing
proceeds without holding any lock.

```
┌──────────────────────────────────────────────────────────────────┐
│              process_backlog() Flow                               │
│                                                                  │
│  input_pkt_queue (receives packets from netif_rx / RPS)          │
│  ┌───────────────────────────────────────┐                       │
│  │ [skb_1] ──► [skb_2] ──► [skb_3]      │                       │
│  └──────────────────┬────────────────────┘                       │
│                     │ splice_tail_init()                          │
│                     │ (atomic move under irq-off)                 │
│                     ▼                                             │
│  process_queue (drained by process_backlog)                       │
│  ┌───────────────────────────────────────┐                       │
│  │ [skb_1] ──► [skb_2] ──► [skb_3]      │                       │
│  └──────────────────┬────────────────────┘                       │
│                     │ __skb_dequeue() one by one                  │
│                     ▼                                             │
│  __netif_receive_skb(skb) → protocol handlers → socket           │
└──────────────────────────────────────────────────────────────────┘
```

### 6.3 RPS (Receive Packet Steering)

RPS distributes received packets across CPUs in software, similar to RSS
(Receive Side Scaling) done in hardware. When a packet arrives on CPU A
but should be processed by CPU B (for cache locality with the owning socket),
RPS enqueues it on CPU B's `input_pkt_queue`.

```c
/*
 * RPS flow:
 * 1. NIC delivers packet to CPU A (interrupt handler)
 * 2. get_rps_cpu() computes target CPU B based on flow hash
 * 3. enqueue_to_backlog() places skb on CPU B's input_pkt_queue
 * 4. Send IPI to CPU B if needed to trigger NET_RX_SOFTIRQ
 * 5. CPU B's process_backlog() processes the packet
 */
```

```
┌──────────────────────────────────────────────────────────────────┐
│                   RPS Packet Steering                             │
│                                                                  │
│  CPU 0 (NIC interrupt)          CPU 2 (target)                   │
│  ┌────────────────────┐         ┌────────────────────────┐       │
│  │ napi_poll()        │         │ softnet_data            │       │
│  │ └── skb received   │         │ ├── input_pkt_queue     │       │
│  │     └── hash = 42  │────────►│ │   └── [skb]           │       │
│  │     └── rps_cpu = 2│  IPI    │ └── process_backlog()   │       │
│  └────────────────────┘         │     └── delivers to TCP │       │
│                                 └────────────────────────┘       │
│                                                                  │
│  Why CPU 2? Socket's last-processing CPU was 2.                  │
│  Processing on the same CPU improves cache hit rate.             │
└──────────────────────────────────────────────────────────────────┘
```

### 6.4 RFS (Receive Flow Steering)

RFS extends RPS by considering which CPU the application thread is running
on, rather than using a static hash. It steers packets to the CPU where the
consuming thread was last scheduled, maximizing cache efficiency.

```c
struct rps_sock_flow_table {
    u32  mask;
    u32  ents[];    /* indexed by flow hash; stores CPU+counter */
};
```

### 6.5 Backlog Queue Limits

The backlog queue size is controlled by:

```c
/* Per-CPU backlog queue limit */
int netdev_budget = 300;        /* max packets per NAPI poll round  */
int netdev_max_backlog = 1000;  /* max packets in input_pkt_queue   */
```

Tunable via `/proc/sys/net/core/netdev_budget` and
`/proc/sys/net/core/netdev_max_backlog`.

When the backlog queue exceeds `netdev_max_backlog`, incoming packets are
dropped and the `softnet_data.dropped` counter increments. This counter is
visible in `/proc/net/softnet_stat`.

---

## 7. Locking and Synchronization

### 7.1 sk_buff_head.lock

Every `sk_buff_head` contains a `spinlock_t` that protects concurrent access:

```c
struct sk_buff_head {
    /* ... */
    spinlock_t lock;
};
```

The locked queue operations (`skb_queue_tail()`, `skb_dequeue()`, etc.)
acquire this lock with `spin_lock_irqsave()`, which disables interrupts
locally to prevent deadlocks between process context and softirq context.

```c
void skb_queue_tail(struct sk_buff_head *list, struct sk_buff *newsk)
{
    unsigned long flags;

    spin_lock_irqsave(&list->lock, flags);   /* disable IRQs + lock */
    __skb_queue_tail(list, newsk);
    spin_unlock_irqrestore(&list->lock, flags); /* restore + unlock */
}
```

### 7.2 Why IRQ-Safe Locking?

The same queue may be accessed from:
- **Process context** — `recvmsg()` dequeues from `sk_receive_queue`.
- **Softirq context** — TCP/UDP enqueues to `sk_receive_queue`.
- **Hardirq context** — rare, but some fast-path code runs here.

Without IRQ-safe locking, a softirq could preempt process context while the
lock is held, attempt to acquire the same lock, and deadlock.

```
┌──────────────────────────────────────────────────────────────────┐
│              Deadlock Scenario Without IRQ-Safe Lock              │
│                                                                  │
│  Process context (CPU 0):                                        │
│  1. spin_lock(&list->lock)         ← holds lock                 │
│  2. --- softirq preempts ---                                     │
│                                                                  │
│  Softirq context (CPU 0):                                        │
│  3. spin_lock(&list->lock)         ← DEADLOCK! Same CPU,        │
│                                       lock already held          │
│                                                                  │
│  Solution: spin_lock_irqsave() disables local IRQs,             │
│            preventing softirq preemption while lock is held.     │
└──────────────────────────────────────────────────────────────────┘
```

### 7.3 BH-Safe Locking

Some paths use `spin_lock_bh()` (bottom-half disabling) instead of the
full `spin_lock_irqsave()`. This disables softirqs but not hardirqs,
which is sufficient when the lock is never taken from hardirq context:

```c
/* BH-safe variant: cheaper than irqsave */
spin_lock_bh(&sk->sk_lock.slock);
/* ... critical section ... */
spin_unlock_bh(&sk->sk_lock.slock);
```

### 7.4 Lock-Free Fast Paths

Certain high-frequency operations avoid locking entirely:

#### 7.4.1 skb_peek() Without Locking

`skb_peek()` reads `list->next` and checks against the sentinel. On
architectures with atomic pointer reads, this is safe without locking
(the pointer is either the old value or the new value, never a torn read).
However, the returned skb might be removed between the peek and use, so
callers must handle this race.

#### 7.4.2 Per-CPU Queues

Per-CPU data structures (like `softnet_data`) avoid locking by ensuring only
the owning CPU modifies the queue. Preemption or softirq disabling provides
the necessary exclusion:

```c
local_irq_disable();
/* Safe: no other code on this CPU can run */
__skb_queue_tail(&sd->input_pkt_queue, skb);
local_irq_enable();
```

#### 7.4.3 Socket Lock Protocol

The socket uses a two-level locking scheme:

```c
struct sock {
    /* ... */
    struct socket_lock_t {
        spinlock_t   slock;     /* fast spinlock                     */
        int          owned;     /* 1 if locked by user process       */
        wait_queue_head_t wq;   /* waiters                           */
    } sk_lock;
    /* ... */
};
```

```
┌──────────────────────────────────────────────────────────────────┐
│              Socket Lock Protocol                                │
│                                                                  │
│  User process (e.g., recvmsg):                                   │
│  └── lock_sock(sk)                                               │
│      ├── spin_lock_bh(&sk->sk_lock.slock)                        │
│      ├── sk->sk_lock.owned = 1                                   │
│      └── spin_unlock_bh(&sk->sk_lock.slock)                      │
│                                                                  │
│  Softirq (e.g., tcp_v4_rcv):                                    │
│  └── bh_lock_sock(sk)                                            │
│      └── spin_lock(&sk->sk_lock.slock)                           │
│          ├── if (sk->sk_lock.owned)                              │
│          │   └── sk_add_backlog(sk, skb)  /* defer to backlog */ │
│          └── else                                                │
│              └── process immediately                             │
│          spin_unlock(&sk->sk_lock.slock)                         │
│                                                                  │
│  User process releases:                                          │
│  └── release_sock(sk)                                            │
│      ├── spin_lock_bh(&sk->sk_lock.slock)                        │
│      ├── sk->sk_lock.owned = 0                                   │
│      ├── __release_sock(sk)  /* process backlog */               │
│      └── spin_unlock_bh(&sk->sk_lock.slock)                      │
└──────────────────────────────────────────────────────────────────┘
```

This protocol ensures that:
1. The user process has exclusive access while it holds the socket lock.
2. Softirqs never block; they defer to the backlog instead.
3. Backlog is drained under the socket lock, serialized with user processing.

### 7.5 RCU for Read-Side Access

Some queue-like structures use RCU (Read-Copy-Update) for read-side
performance. The qdisc pointer in `netdev_queue` is RCU-protected:

```c
struct netdev_queue {
    struct Qdisc __rcu *qdisc;   /* RCU-protected qdisc pointer */
    /* ... */
};

/* Read-side access (no lock needed) */
rcu_read_lock();
struct Qdisc *q = rcu_dereference(txq->qdisc);
/* use q safely */
rcu_read_unlock();

/* Write-side update (must hold RTNL or other exclusion) */
rcu_assign_pointer(txq->qdisc, new_qdisc);
synchronize_rcu();
/* old qdisc can now be freed */
```

### 7.6 Locking Summary

```
┌────────────────────────────┬────────────────────────────────────────┐
│ Context                    │ Locking Mechanism                      │
├────────────────────────────┼────────────────────────────────────────┤
│ sk_buff_head operations    │ spin_lock_irqsave() per queue          │
│ Socket receive/write queue │ Socket lock (owned flag + backlog)     │
│ Per-CPU softnet_data       │ local_irq_disable() (per-CPU)          │
│ Qdisc modification         │ RTNL lock + RCU                        │
│ Qdisc TX path              │ __netif_tx_lock() per TX queue         │
│ NAPI poll list             │ local_irq_disable() (per-CPU)          │
│ frag_list traversal        │ Reference count (dataref)              │
└────────────────────────────┴────────────────────────────────────────┘
```

---

## Appendix A: Queue Operation Complexity

```
┌─────────────────────────┬──────────┬──────────────────────────────┐
│ Operation               │ Time     │ Notes                        │
├─────────────────────────┼──────────┼──────────────────────────────┤
│ skb_queue_head()        │ O(1)     │ Insert at sentinel->next     │
│ skb_queue_tail()        │ O(1)     │ Insert at sentinel->prev     │
│ skb_dequeue()           │ O(1)     │ Remove sentinel->next        │
│ skb_dequeue_tail()      │ O(1)     │ Remove sentinel->prev        │
│ skb_unlink()            │ O(1)     │ Remove known element         │
│ skb_queue_len()         │ O(1)     │ Read qlen field              │
│ skb_peek()              │ O(1)     │ Read sentinel->next          │
│ skb_peek_tail()         │ O(1)     │ Read sentinel->prev          │
│ skb_queue_purge()       │ O(n)     │ Dequeue + free all           │
│ skb_queue_splice()      │ O(1)     │ Pointer manipulation only    │
│ skb_queue_walk()        │ O(n)     │ Full traversal               │
└─────────────────────────┴──────────┴──────────────────────────────┘
```

---

## Appendix B: Monitoring Queue State

### B.1 /proc/net/softnet_stat

Each line corresponds to one CPU and contains (in hex):

```
Column 1: total packets processed
Column 2: packets dropped (backlog overflow)
Column 3: time_squeeze (ran out of budget)
Column 4-8: (varies by kernel version)
```

```c
/* Reading programmatically */
static void dump_softnet_stats(void)
{
    int cpu;
    for_each_online_cpu(cpu) {
        struct softnet_data *sd = &per_cpu(softnet_data, cpu);
        pr_info("CPU %d: processed=%u dropped=%u squeeze=%u "
                "backlog_len=%u\n",
                cpu, sd->processed, sd->dropped,
                sd->time_squeeze,
                skb_queue_len(&sd->input_pkt_queue));
    }
}
```

### B.2 Socket Queue Depth

Userspace can inspect socket queue depths via:

```
/proc/net/tcp   — columns show tx_queue and rx_queue sizes (hex)
/proc/net/udp   — same format
```

The `ss` tool provides a more readable view:

```bash
# Show socket queue depths
ss -tnm
#  Recv-Q  Send-Q
#  0       0          ← sk_receive_queue len, sk_write_queue len
```

### B.3 Qdisc Statistics

```bash
# Show qdisc queue lengths and drop counts
tc -s qdisc show dev eth0
#  qdisc fq_codel 0: root ...
#   Sent 1234567 bytes 8901 pkt (dropped 0, overlimits 0)
#   backlog 0b 0p requeues 12
```

### B.4 Kernel Debug: Dumping a Queue

```c
/* Debug helper: dump all sk_buffs in a queue */
static void skb_queue_dump(const char *name,
                           const struct sk_buff_head *list)
{
    const struct sk_buff *skb;
    int i = 0;

    pr_info("Queue '%s': len=%u\n", name, skb_queue_len(list));

    skb_queue_walk(list, skb) {
        pr_info("  [%d] skb=%p len=%u data_len=%u protocol=0x%04x\n",
                i++, skb, skb->len, skb->data_len,
                ntohs(skb->protocol));
    }
}
```

---

## Appendix C: Queue-Related Tunables

```
┌─────────────────────────────────────┬──────────────────────────────────┐
│ Sysctl / Parameter                  │ Effect                           │
├─────────────────────────────────────┼──────────────────────────────────┤
│ net.core.netdev_max_backlog         │ Max pkts in per-CPU backlog      │
│                                     │ (default: 1000)                  │
├─────────────────────────────────────┼──────────────────────────────────┤
│ net.core.netdev_budget              │ Max pkts per softirq round       │
│                                     │ (default: 300)                   │
├─────────────────────────────────────┼──────────────────────────────────┤
│ net.core.netdev_budget_usecs        │ Max time per softirq round       │
│                                     │ (default: 2000 usecs)            │
├─────────────────────────────────────┼──────────────────────────────────┤
│ net.core.rmem_default               │ Default socket receive buffer    │
├─────────────────────────────────────┼──────────────────────────────────┤
│ net.core.rmem_max                   │ Max socket receive buffer        │
├─────────────────────────────────────┼──────────────────────────────────┤
│ net.core.wmem_default               │ Default socket send buffer       │
├─────────────────────────────────────┼──────────────────────────────────┤
│ net.core.wmem_max                   │ Max socket send buffer           │
├─────────────────────────────────────┼──────────────────────────────────┤
│ net.ipv4.tcp_rmem                   │ TCP auto-tune: min default max   │
├─────────────────────────────────────┼──────────────────────────────────┤
│ net.ipv4.tcp_wmem                   │ TCP send auto-tune               │
├─────────────────────────────────────┼──────────────────────────────────┤
│ net.core.dev_weight                 │ NAPI poll weight (backlog)       │
│                                     │ (default: 64)                    │
├─────────────────────────────────────┼──────────────────────────────────┤
│ /sys/class/net/<dev>/queues/        │ Per-queue configuration:         │
│   tx-N/xps_cpus                     │   XPS CPU mapping                │
│   rx-N/rps_cpus                     │   RPS CPU mapping                │
│   rx-N/rps_flow_cnt                 │   RFS flow table size            │
└─────────────────────────────────────┴──────────────────────────────────┘
```

---

*Previous: [Chapter 6: Scatter-Gather and Fragments](06-scatter-gather-and-fragments.md)*
