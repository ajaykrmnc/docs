# Chapter 3: Resource Management

C++ programs manage many kinds of resources: dynamically allocated memory, file descriptors,
mutex locks, database connections, network sockets, GUI fonts and brushes. Regardless of the
resource type, the fundamental challenge is the same: once you acquire a resource, you must
eventually release it. Failure to do so leads to resource leaks, which degrade performance,
cause data corruption, or crash programs.

This chapter covers five items that together form a coherent philosophy for resource management
in C++. The central idea is **RAII** (Resource Acquisition Is Initialization): bind the
lifetime of a resource to the lifetime of an object, so that C++'s deterministic destruction
guarantees cleanup even in the presence of exceptions or early returns.

---
