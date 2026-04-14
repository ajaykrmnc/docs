## Interesting Latency Numbers

The notes are taken from this [link](https://gist.github.com/hellerbarde/2843375).

### CPU Frequency (Clock Speed):
- The CPU frequency refers to the number of cycles the CPU can execute per second. It’s typically measured in Hertz (Hz), with modern CPUs operating in the range of Gigahertz (GHz) (1 GHz = 1 billion cycles per second).
- Higher frequency generally means more cycles per second, but that doesn’t directly translate to faster execution if other bottlenecks, like memory access or instruction complexity, exist.
- Example: A CPU with a frequency of 3 GHz can execute up to 3 billion cycles per second.

`On Average, 1 Clock Cycle = 0.3 ns`

```cpp
L1 cache reference ......................... 0.5 ns
Branch mispredict ............................ 5 ns
L2 cache reference ........................... 7 ns
Mutex lock/unlock ........................... 25 ns
Main memory reference ...................... 100 ns             
Compress 1K bytes with Zippy ............. 3,000 ns  =   3 µs
Send 2K bytes over 1 Gbps network ....... 20,000 ns  =  20 µs
SSD random read ........................ 150,000 ns  = 150 µs
Read 1 MB sequentially from memory ..... 250,000 ns  = 250 µs
Round trip within same datacenter ...... 500,000 ns  = 0.5 ms
Read 1 MB sequentially from SSD* ..... 1,000,000 ns  =   1 ms
Disk seek ........................... 10,000,000 ns  =  10 ms
Read 1 MB sequentially from disk .... 20,000,000 ns  =  20 ms
Send packet CA->Netherlands->CA .... 150,000,000 ns  = 150 ms
```

### Lets multiply all these durations by a billion:

Magnitudes:

#### Minute:
    L1 cache reference                  0.5 s         Blink of eye (0.5 s)
    Branch mispredict                   5 s           Sip of water
    L2 cache reference                  7 s           Long yawn
    Mutex lock/unlock                   25 s          Making a coffee

### Hour:
    Main memory reference               100 s         Brushing your teeth
    Compress 1K bytes with Zippy        50 min        One episode of a TV show (including ad breaks)

### Day:
    Send 2K bytes over 1 Gbps network   5.5 hr        From lunch to end of work day

### Week
    SSD random read                     1.7 days      A normal weekend
    Read 1 MB sequentially from memory  2.9 days      A long weekend
    Round trip within same datacenter   5.8 days      A medium vacation
    Read 1 MB sequentially from SSD    11.6 days      Waiting for almost 2 weeks for a delivery

### Year
    Disk seek                           16.5 weeks    A semester in university
    Read 1 MB sequentially from disk    7.8 months    Almost producing a new human being
    The above 2 together                1 year

### Decade
    Send packet CA->Netherlands->CA     4.8 years     CS5 degree at IITD