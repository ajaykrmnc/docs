# Interview Experiences

I applied to various companies for a full-time role (mostly in systems), and here are some of my `On-Campus @ IITD` as
well as `Off-Campus` Online Assessment (OA) and Interview experiences:

- [Stripe](#stripe)
- [Hudson River Trading](#hudson-river-trading)
- [Squarepoint Capital](#squarepoint-capital)
- [DRW](#drw)
- [Graviton](#graviton)
- [QuantBox](#quantbox)

---

## Stripe

### Online Assessment

It was a 60-minute test on HackerRank. The problem wasn't algorithmic, but rather implementation-heavy.
I had to parse a command string and execute the commands, which simulated transactions between users’ bank accounts.
It wasn't very difficult, but the implementation was fairly long.

### Phone Screening

The next round was a 45-minute phone screening on Zoom with one of the engineers.
This was a live coding round, which I could attempt either on my local IDE or in their HackerRank sandbox.

Again, it involved an implementation-based problem with 2–3 subparts. Each subpart built upon the previous one.

### Programming Round

This round had one programming question (with multiple subparts), which I attempted in C++.

### Bug-Squash Round

I was given access to an open-source C++ repository and asked to fix two bugs within an hour. I used a debugger and
breakpoints to trace and fix the issues.

### Manager Chat Round

This was a final, non-technical, 30-minute round with an Engineering Manager.
Some of the questions I recall:

- A deep dive into my internship experience (both technical and non-technical)
- Questions about how I approached my project, its impact, and follow-ups
- My goals as a software engineer for the next two years
- A technically challenging past experience and how I handled it
- Why I believe Stripe is the right career fit for me

---

## Hudson River Trading

**Role:** C++ Software Engineer

### Online Assessment

A 90-minute online assessment on CodeSignal, consisting of four easy CP questions.

### Phone Screening

A 45-minute in-depth systems interview, primarily on OS and C++.
Questions included:

- Use of `inline` functions in C++: pros and cons
- `vector` vs `list`: trade-offs and internal details
- Internal working of `malloc`, demand paging, etc.
- How the kernel allocates memory to user processes
- System calls like `sbrk` and `mmap`

---

## Squarepoint Capital

**Role:** C++ Software Engineer

### Online Assessment

Two CP questions — one on two pointers (CF 1600 level) and the other was a tricky implementation problem.

### Technical Screening R1 (1 hour)

- First 10 minutes: resume deep dive and basic project discussion
- Next 20 minutes: CS trivia (virtual memory, process management, page tables, real-time systems, TCP vs UDP,
  dangling pointers)
- Last 30 minutes: live coding round on HackerRank I had to debug a dummy `vector` implementation — missing
  destructor, needed a custom copy constructor, fixed memory leaks, added out-of-range checks, etc.

### Technical Screening R2 (1 hour)

- First 5–10 minutes: CV discussion
- Then, questions on TCP's internal state machine handling
- Given a code snippet, asked how many times constructors (copy/move/assignment) would be called
- Code exercise related to `char**` pointers
- Final 20 minutes: Live coding round

### Technical Screening R3 (1 hour)

- Given a thread-safe queue implementation and benchmark on HackerRank, I had to suggest some optimizations:
- Some of the optimizations:
  - Replace copies with move semantics
  - Use a condition variable instead of busy waiting
  - Make the queue bounded
  - Use RAII for locking/unlocking
  - Discuss cache friendliness of the underlying container
- Finished in ~45 minutes

---

## DRW

### Online Assessment

Three C++ questions in 120 minutes. One involved finding a bug in a given code snippet; the other two were Leetcode medium-to-hard level.

### Technical Round

A 1-hour interview with a senior engineer.
I had to write pseudocode to serialize a `struct` in binary format and write it to a file.
Follow-up questions included endianness and how to handle it.

---

## Graviton

**Role:** Software Engineer

### Pen-and-Paper Test

Two CP questions and two systems questions:

- Implement concurrent transactions between two bank accounts using locks
- Remove branching from a given code snippet
  The CP problems were roughly CF 1700 level.

### Technical Rounds

2–3 rounds, each focused on CP questions.

---

## QuantBox

### Online Assessment

15 CS fundamentals MCQs in 20 minutes.
Followed by three non-CP C++ coding questions in 25 minutes.

### Technical Round

A long, in-depth systems interview (3–4 hours) covering OS, C++, and parallel programming.
Topics included:

- Smart pointer (`shared_ptr`) implementation
- `String` class implementation
- Memory pool implementation
- Internal workings of virtual functions
- Lock-free data structures (multi-threaded linked list, producer-consumer buffer)
- Endianness detection
- Virtual dispatch
- Memory reordering (hardware/compiler level)
- Lazy allocation and `malloc` internals
- Spinlock and contention optimization
- Read-Copy-Update (RCU)
- And several open-ended follow-ups

# Preperation Resources

I made some notes while preparing for these interviews.
They can be accessed at [this](https://github.com/Shivam5022/Knowledgebase-SV) link.
