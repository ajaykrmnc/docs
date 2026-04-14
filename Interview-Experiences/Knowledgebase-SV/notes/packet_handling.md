## The Network Packet's Diary

PDF [Notes](../assets/From%20NIC%20to%20Application.pdf)

A packet consists of:

```
| Ethernet Header | IP Header | TCP Header | Data |
```
Network Interface Controller (NIC):
- Receives the packet
- Compares the MAC destination address (the address to be compared against is
programmed by the OS)
- Verifies the Ethernet (Frame) Checksum FCS
- Stores the packet to buffer programmed by the driver using DMA
- Triggers an interrupt

Interrupt:
- Top half processing:
    - Acknowledge the interrupt
    - Schedule the 'Bottom Half Processing'

- Bottom half processing:
    - It identifies the memory where the packet is stored.
    - Allocates `sk_buf` (it is a struct which contains various pointers, like 
    pointer to different headers, pointer to data and other metadata).

    ```mermaid
    graph TD;
    A[sk_buff] --> B[Memory Buffer];
    B --> C[Head Pointer];
    B --> D[Data Pointer];
    B --> E[Tail Pointer];
    B --> F[End Pointer];
    
    A --> G[Packet Headers];
    G --> H[Ethernet Header]; 
    G --> I[IP Header];
    G --> J[TCP/UDP Header];

    A --> K[Metadata];
    K --> L[Reference Counters];
    K --> M[Checksum Info];
    K --> N[Flags];
    
    B --> O[Packet Data];
    ```
    - Passes the `sk_buf` to the protocol stack.

The `sk_buf` traverses various levels, where some checksums are verified, headers
are removed and other metadata processing is done.

Eventually, it reaches TCP stack:
- TCP checksum verified
- Handles the TCP state machine
- Enqueues the data to socket's recevive queue
- Signals the fd that the data is available (for processes sleeping on `select`)

On Socket read (by user process):
- Dequeue data from socket's receive queue
- Copy to user buffer
- Release the `sk_buf`
