# Technical Documentation Repository

A comprehensive collection of technical documentation covering systems programming, distributed systems, databases, networking, and software engineering topics.

---

## 📁 Repository Structure

### `architecture/`
Software architecture patterns and design:
- CDN architecture
- Client-server architecture
- Internet business ownership
- Nginx architecture
- Blob storage

### `database/`
Database internals and distributed data systems:
- B-tree fundamentals and variants
- Transaction processing and recovery
- Concurrency control and locking
- Log-structured storage
- Distributed systems concepts
- Replication and consistency
- Consensus algorithms (Paxos, Raft)
- Leader election and failure detection

### `distributed-systems/`
Distributed computing concepts:
- CAP theorem and foundations
- Consensus algorithms
- Distributed storage and replication
- Distributed transactions
- Clocks and time synchronization
- Fault tolerance and resilience
- Distributed messaging
- Service discovery and coordination
- Distributed caching

### `java/`
Java programming deep dives:
- JVM internals and memory model
- Collections framework internals
- Concurrency and multithreading
- Data structures and algorithms
- OOP and design patterns
- Generics, reflection, annotations
- I/O, NIO, and networking
- Performance optimization
- JIT compilation

### `lld/` (Low-Level Design)
System design interview questions with detailed solutions:
- Rate limiter, cache, pub-sub system
- Task scheduler, file system
- Connection pool, logging framework
- Elevator system, parking lot
- Library management, online chess
- Notification system, API gateway
- URL shortener, order management
- Movie ticket booking, vending machine
- Distributed lock, collaborative editor

### `networking/`
Network protocols and concepts:
- OSI layers and packet flow
- DNS and TLS
- Sockets and IPC
- Network virtualization
- IP categorization
- Blocking/non-blocking I/O
- Zero-copy mechanisms
- WebSockets
- Unix pipes and sockets

### `kernel-and-system/`
Linux kernel and system programming:
- Process structure and control
- Process scheduling and time
- Memory management policies
- Signals and semaphores
- Interrupts and I/O subsystem
- File modes and permissions
- UID/GID essentials
- systemd guide
- strace comprehensive guide
- Man pages guide

### `build-and-tooling/`
Development tools and build systems:
- Docker comprehensive guide
- Git concepts and internals
- Git push comparison
- Git topo-order analysis
- Tar file optimization
- clangd TCP setup
- compile_commands setup
- Telescope live grep patterns

### `libstdcpp-guide/`
C++ standard library deep dive:
- Introduction and overview
- Navigating source code
- Understanding containers
- Algorithms and iterators
- Template syntax guides
- Cache-friendly code
- Competitive programming guide
- Quant dev optimization

### `programming-languages/`
Language-specific guides:
- C language for systems programming
- C++ vtables guide
- Header files and binary libraries
- JVM internals
- Python path setup

### `testing/`
Testing frameworks and methodologies:
- Playwright deep dive architecture
- Playwright stubbing
- Playwright presentation

### `threading/`
Multithreading and concurrency:
- C++ threading examples
- Python threading examples
- Threading explanations

### `rpi/` (Raspberry Pi)
Raspberry Pi projects and concepts:
- Setup guides
- Core concepts
- Project ideas
- Distributed sync learning

### `scripts/`
Utility scripts:
- clangd multi-project setup
- clangd TCP server
- Download scripts
- Markdown to PDF converter

### `docs/`
Additional documentation

---

## 🌐 Live Documentation Site

This repository is published as a documentation website using GitHub Pages:

**🔗 [View Live Site](https://ajaykrmnc.github.io/docs/)**

The site is automatically built and deployed using VitePress and GitHub Actions whenever changes are pushed to the `master` branch.

For setup instructions, see [`aristadocs/GITHUB_PAGES_SETUP.md`](aristadocs/GITHUB_PAGES_SETUP.md).

---

## 🔒 Proprietary Content

**Note:** Arista Networks proprietary documentation has been moved to the `aristadocs/` directory. This includes:
- WiFi driver development (QCA integration)
- Kernel patches (ar_meta cache)
- Arista AP-specific networking
- Internal build systems

See `aristadocs/README.md` for details.

---

## 🎯 Topics Covered

- **Systems Programming**: C/C++, kernel development, memory management
- **Distributed Systems**: Consensus, replication, fault tolerance, CAP theorem
- **Databases**: B-trees, transactions, concurrency control, distributed databases
- **Networking**: TCP/IP, sockets, protocols, network virtualization
- **Software Design**: Architecture patterns, low-level design, design patterns
- **Programming Languages**: Java, C++, Python, Go
- **DevOps**: Docker, Git, build systems, CI/CD
- **Performance**: Optimization, caching, zero-copy, JIT compilation

---

## 📚 How to Use This Repository

1. **Learning**: Use as a reference for understanding complex technical topics
2. **Interview Prep**: Review LLD questions and distributed systems concepts
3. **Development**: Reference guides for specific technologies and tools
4. **Teaching**: Share knowledge with team members

---

## 🤝 Contributing

This is a personal documentation repository. Feel free to fork and adapt for your own use.

---

**Last Updated:** March 2026

