# Chapter 5: Implementations

Most of the time, coming up with appropriate definitions for your classes and
declarations for your functions is the lion's share of the battle. Once you have
those right, the corresponding implementations are largely straightforward. Still,
there are things to watch out for. Defining variables too soon can cause a drag on
performance. Overuse of casts can lead to code that is slow, hard to maintain, and
infected with subtle bugs. Returning handles to an object's internals can defeat
encapsulation and leave clients with dangling handles. Failure to consider the
impact of exceptions can lead to leaked resources and corrupted data structures.
Overzealous inlining can cause code bloat. And excessive coupling can result in
unacceptably long build times.

Each of these problems is addressed in the Items that follow.

---
