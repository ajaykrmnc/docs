# Network Data Boundaries: How Protocols and SKBs Ensure Proper Data Recognition

## Table of Contents

1. [Introduction](#introduction)
2. [The Fundamental Problem](#the-fundamental-problem)
3. [Layer-by-Layer Boundary Mechanisms](#layer-by-layer-boundary-mechanisms)
4. [Linux Kernel sk_buff Structure](#linux-kernel-sk_buff-structure)
5. [Protocol-Specific Framing](#protocol-specific-framing)
6. [Complete Data Flow Example](#complete-data-flow-example)
7. [Advanced Topics](#advanced-topics)

---

## 1. Introduction

When two devices communicate over a network, they face a fundamental challenge: **how to recognize where data starts and ends in a continuous stream of bits**. This document explains the multi-layered approach used by network protocols and the Linux kernel to solve this problem.

### Key Concepts

- **Framing**: The process of delimiting data boundaries
- **Protocol Data Unit (PDU)**: Data at each layer with its own boundaries
  - **Layer 2**: Frame
  - **Layer 3**: Packet
  - **Layer 4**: Segment (TCP) or Datagram (UDP)
- **sk_buff**: Linux kernel's primary data structure for network packets

---

## 2. The Fundamental Problem

### The Challenge

Network communication involves transmitting data as a stream of bits. Without proper boundary markers:
- Receivers cannot distinguish where one message ends and another begins
- Data corruption cannot be detected
- Protocol headers cannot be separated from payload
- Reassembly of fragmented data is impossible

### The Solution: Multi-Layer Boundary Mechanisms

The networking stack uses **multiple independent boundary mechanisms** at different layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  Boundary: Application-defined (HTTP headers, JSON, etc.)   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Transport Layer (TCP/UDP)                 │
│  Boundary: Sequence numbers, length fields, port numbers    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Network Layer (IP)                        │
│  Boundary: Total length, fragmentation fields, checksum     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Link Layer (Ethernet)                │
│  Boundary: Preamble, SFD, length/type, FCS                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Physical Layer                            │
│  Boundary: Electrical signals, bit timing, encoding         │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Layer-by-Layer Boundary Mechanisms

### 3.1 Physical Layer (Layer 1)

**Mechanism**: Bit synchronization and encoding

- **Clock synchronization**: Receiver synchronizes with sender's clock
- **Encoding schemes**: Manchester, 4B/5B, 8B/10B provide bit boundaries
- **Idle patterns**: Special patterns indicate no data transmission

**Example**: Ethernet uses Manchester encoding where each bit has a transition, allowing the receiver to synchronize.

---

### 3.2 Data Link Layer (Layer 2) - Ethernet

**Mechanism**: Frame delimiters and checksums

#### Ethernet Frame Structure

```
┌──────────┬─────┬──────────┬──────────┬─────────────┬──────────┬─────┐
│ Preamble │ SFD │ Dest MAC │ Src MAC  │ Type/Length │ Payload  │ FCS │
│ (7 bytes)│(1 B)│ (6 bytes)│ (6 bytes)│  (2 bytes)  │(46-1500B)│(4 B)│
└──────────┴─────┴──────────┴──────────┴─────────────┴──────────┴─────┘
```

#### Boundary Mechanisms

1. **Preamble (7 bytes)**: `10101010` repeated 7 times
   - Purpose: Clock synchronization
   - Allows receiver to lock onto bit timing

2. **Start Frame Delimiter (SFD) (1 byte)**: `10101011`
   - Purpose: **Marks the exact start of the frame**
   - Pattern: Last two bits are `11` (different from preamble)
   - Receiver knows: "Frame data starts NOW"

3. **Type/Length Field (2 bytes)**:
   - If value ≤ 1500: Indicates payload length
   - If value ≥ 1536: Indicates protocol type (EtherType)
   - Examples:
     - `0x0800`: IPv4
     - `0x86DD`: IPv6
     - `0x0806`: ARP

4. **Frame Check Sequence (FCS) (4 bytes)**:
   - CRC-32 checksum over entire frame
   - Purpose: **Marks the end of the frame** and detects corruption
   - Receiver calculates CRC and compares with FCS
   - Mismatch = corrupted frame → discard

5. **Inter-Frame Gap (IFG)**:
   - 12 bytes (96 bit times) of idle between frames
   - Purpose: **Separates consecutive frames**
   - Allows receiver to process previous frame

#### How Ethernet Recognizes Boundaries

```
Bit stream: ...idle...10101010101010101010101010101011[FRAME DATA]CRC...idle...

Step 1: Detect end of idle (carrier sense)
Step 2: Synchronize on preamble pattern
Step 3: Detect SFD (10101011) → FRAME STARTS HERE
Step 4: Read destination MAC (6 bytes)
Step 5: Read source MAC (6 bytes)
Step 6: Read Type/Length (2 bytes) → know payload size or type
Step 7: Read payload (length from step 6 or until FCS)
Step 8: Read FCS (4 bytes) → FRAME ENDS HERE
Step 9: Verify CRC
Step 10: Wait for IFG → ready for next frame
```

---

### 3.3 Network Layer (Layer 3) - IP

**Mechanism**: Header length fields and fragmentation identifiers

#### IPv4 Header Structure

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version|  IHL  |Type of Service|          Total Length         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Identification        |Flags|      Fragment Offset    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Time to Live |    Protocol   |         Header Checksum       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source Address                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Destination Address                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options                    |    Padding    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

#### Boundary Mechanisms

1. **Internet Header Length (IHL) (4 bits)**:
   - Specifies header length in 32-bit words
   - Range: 5-15 (20-60 bytes)
   - Purpose: **Marks where IP header ends and payload begins**
   - Calculation: `Header Length = IHL × 4 bytes`

2. **Total Length (16 bits)**:
   - Total packet size (header + data) in bytes
   - Maximum: 65,535 bytes
   - Purpose: **Marks where IP packet ends**
   - Payload length = Total Length - (IHL × 4)

3. **Protocol (8 bits)**:
   - Identifies next layer protocol
   - Examples:
     - `6`: TCP
     - `17`: UDP
     - `1`: ICMP
   - Purpose: **Tells receiver how to parse payload**

4. **Header Checksum (16 bits)**:
   - Checksum of IP header only (not payload)
   - Purpose: Detect header corruption
   - Recalculated at each hop (TTL changes)

#### IP Fragmentation: Handling Large Packets

When a packet is too large for the network MTU (Maximum Transmission Unit), IP fragments it:

**Fragmentation Fields**:

1. **Identification (16 bits)**:
   - Unique ID for the original packet
   - **All fragments of the same packet share this ID**
   - Purpose: Group fragments for reassembly

2. **Flags (3 bits)**:
   - Bit 0: Reserved (must be 0)
   - Bit 1: **Don't Fragment (DF)** - if set, packet must not be fragmented
   - Bit 2: **More Fragments (MF)** - if set, more fragments follow
   - Purpose: **Last fragment has MF=0, all others have MF=1**

3. **Fragment Offset (13 bits)**:
   - Position of fragment in original packet (in 8-byte units)
   - Range: 0 to 8,191 (0 to 65,528 bytes)
   - Purpose: **Tells receiver where to place this fragment**

**Fragmentation Example**:

```
Original packet: 4000 bytes
MTU: 1500 bytes
IP header: 20 bytes
Max payload per fragment: 1480 bytes (must be multiple of 8)

Fragment 1:
  Identification: 12345
  Flags: MF=1 (more fragments)
  Fragment Offset: 0 (bytes 0-1479)
  Total Length: 1500

Fragment 2:
  Identification: 12345
  Flags: MF=1 (more fragments)
  Fragment Offset: 185 (1480/8 = 185, bytes 1480-2959)
  Total Length: 1500

Fragment 3:
  Identification: 12345
  Flags: MF=0 (last fragment)
  Fragment Offset: 370 (2960/8 = 370, bytes 2960-3999)
  Total Length: 1060
```

**Reassembly Process**:

```c
// Pseudo-code for IP reassembly
struct fragment_queue {
    uint16_t identification;
    uint32_t src_addr;
    uint32_t dst_addr;
    uint8_t protocol;
    struct fragment *fragments;
    bool complete;
};

// Receiver logic
on_receive_ip_packet(packet) {
    if (is_fragmented(packet)) {
        queue = find_or_create_queue(packet.id, packet.src, packet.dst);
        insert_fragment(queue, packet, packet.offset);

        if (all_fragments_received(queue)) {
            reassembled = reassemble(queue);
            deliver_to_transport_layer(reassembled);
            delete_queue(queue);
        }
    } else {
        deliver_to_transport_layer(packet);
    }
}

bool all_fragments_received(queue) {
    // Check if we have fragment with MF=0 (last fragment)
    // Check if all offsets from 0 to last are present
    // No gaps in fragment offset sequence
}
```

---

### 3.4 Transport Layer (Layer 4)

#### 3.4.1 TCP - Transmission Control Protocol

**Mechanism**: Sequence numbers and acknowledgments (byte-stream protocol)

**TCP Header Structure**:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Sequence Number                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Acknowledgment Number                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Data |       |C|E|U|A|P|R|S|F|                               |
| Offset| Rsrvd |W|C|R|C|S|S|Y|I|            Window             |
|       |       |R|E|G|K|H|T|N|N|                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Checksum            |         Urgent Pointer        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options                    |    Padding    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Boundary Mechanisms**:

1. **Sequence Number (32 bits)**:
   - **Byte offset of first data byte in this segment**
   - NOT a segment counter - it's a byte counter
   - Purpose: **Identifies position in byte stream**
   - Example:
     - Segment 1: SEQ=1000, Length=500 → bytes 1000-1499
     - Segment 2: SEQ=1500, Length=300 → bytes 1500-1799
     - Segment 3: SEQ=1800, Length=200 → bytes 1800-1999

2. **Acknowledgment Number (32 bits)**:
   - **Next expected byte** (cumulative ACK)
   - Purpose: **Tells sender which bytes were received**
   - Example: ACK=2000 means "I received all bytes up to 1999"

3. **Data Offset (4 bits)**:
   - TCP header length in 32-bit words
   - Range: 5-15 (20-60 bytes)
   - Purpose: **Marks where TCP header ends and data begins**

4. **Flags (9 bits)**:
   - SYN: Synchronize sequence numbers (connection setup)
   - FIN: Finish, no more data (connection teardown)
   - ACK: Acknowledgment field is valid
   - PSH: Push data to application immediately
   - RST: Reset connection
   - Purpose: **Control connection state and data flow**

**TCP Does NOT Preserve Message Boundaries**:

```
Application sends:
  write(sock, "Hello", 5);
  write(sock, "World", 5);

TCP may deliver as:
  Segment 1: "HelloWorld" (combined)
  OR
  Segment 1: "Hel"
  Segment 2: "loWor"
  Segment 3: "ld"

Receiver gets: byte stream "HelloWorld"
Application must parse boundaries itself!
```

**How TCP Recognizes Data Boundaries**:

```c
// TCP receiver logic (simplified)
struct tcp_connection {
    uint32_t next_expected_seq;  // Next byte we expect
    uint8_t *receive_buffer;
    uint32_t buffer_size;
};

on_receive_tcp_segment(segment) {
    // Extract sequence number and data length
    seq = segment.sequence_number;
    len = segment.total_length - (segment.data_offset * 4);

    if (seq == connection.next_expected_seq) {
        // In-order segment
        copy_to_buffer(segment.data, len);
        connection.next_expected_seq += len;
        send_ack(connection.next_expected_seq);
        deliver_to_application();
    } else if (seq > connection.next_expected_seq) {
        // Out-of-order segment - buffer it
        store_in_out_of_order_queue(segment);
        send_ack(connection.next_expected_seq); // Duplicate ACK
    } else {
        // Old segment (already received) - ignore
        send_ack(connection.next_expected_seq);
    }
}
```

#### 3.4.2 UDP - User Datagram Protocol

**Mechanism**: Length field (datagram protocol)

**UDP Header Structure**:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|            Length             |           Checksum            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Boundary Mechanisms**:

1. **Length (16 bits)**:
   - Total datagram size (header + data) in bytes
   - Minimum: 8 bytes (header only)
   - Maximum: 65,535 bytes
   - Purpose: **Marks exact datagram boundary**
   - Data length = Length - 8

2. **Checksum (16 bits)**:
   - Optional in IPv4 (mandatory in IPv6)
   - Covers pseudo-header + UDP header + data
   - Purpose: Detect corruption

**UDP DOES Preserve Message Boundaries**:

```
Application sends:
  sendto(sock, "Hello", 5);
  sendto(sock, "World", 5);

UDP delivers:
  Datagram 1: "Hello" (5 bytes)
  Datagram 2: "World" (5 bytes)

Receiver gets: Two separate datagrams
Application receives exact message boundaries!
```

---

## 4. Linux Kernel sk_buff Structure

The Linux kernel uses `struct sk_buff` (socket buffer) to represent network packets in memory. This structure is crucial for tracking data boundaries throughout the network stack.

### 4.1 sk_buff Basic Structure

```c
struct sk_buff {
    /* Linked list pointers */
    struct sk_buff      *next;
    struct sk_buff      *prev;

    /* Socket and device */
    struct sock         *sk;
    struct net_device   *dev;

    /* Timestamp */
    ktime_t             tstamp;

    /* DATA POINTERS - THE MOST CRITICAL FIELDS */
    unsigned char       *head;    // Start of allocated buffer
    unsigned char       *data;    // Start of actual data
    unsigned int        tail;     // End of actual data (offset from head)
    unsigned int        end;      // End of allocated buffer (offset from head)

    /* Length fields */
    unsigned int        len;      // Total data length
    unsigned int        data_len; // Length in fragments (paged data)

    /* Header offsets */
    __u16               transport_header;  // Offset to L4 header
    __u16               network_header;    // Offset to L3 header
    __u16               mac_header;        // Offset to L2 header
    __u16               mac_len;           // MAC header length

    /* Protocol and type */
    __be16              protocol;          // Packet protocol (ETH_P_*)
    __u8                pkt_type;

    /* Checksum info */
    __u8                ip_summed;
    __wsum              csum;
    __u16               csum_start;
    __u16               csum_offset;

    /* Control block - 48 bytes for protocol-private data */
    char                cb[48] __aligned(8);

    /* Reference counting */
    refcount_t          users;

    /* ... many more fields ... */
};
```

### 4.2 sk_buff Memory Layout

The sk_buff structure doesn't contain the actual packet data - it points to it:

```
┌─────────────────────────────────────────────────────────────┐
│                    struct sk_buff                            │
│  (metadata: ~200 bytes)                                      │
│  - next, prev, sk, dev, tstamp                              │
│  - head, data, tail, end                                    │
│  - len, data_len, protocol                                  │
│  - transport_header, network_header, mac_header             │
│  - cb[48], users, etc.                                      │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ head pointer
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Buffer                               │
│                                                              │
│  head                  data              tail           end  │
│  │                     │                 │              │    │
│  ▼                     ▼                 ▼              ▼    │
│  ┌─────────────────────┬─────────────────┬──────────────┬──┐│
│  │     HEADROOM        │   PACKET DATA   │   TAILROOM   │SI││
│  │  (for adding hdrs)  │ (actual packet) │(for adding)  │  ││
│  └─────────────────────┴─────────────────┴──────────────┴──┘│
│                                                          ▲   │
│                                                          │   │
│                                              skb_shared_info │
└─────────────────────────────────────────────────────────────┘
```

**Key Pointer Relationships**:

```
head:     Points to start of allocated buffer (never changes)
data:     Points to start of actual packet data (changes as headers added/removed)
tail:     Offset from head to end of packet data
end:      Offset from head to end of allocated buffer

Calculations:
  Headroom = data - head
  Data length = tail - data  (also stored in skb->len)
  Tailroom = end - tail
  Total buffer size = end - head
```

### 4.3 Header Offset Tracking

The sk_buff tracks where each protocol layer's header is located:

```
Memory layout of packet in buffer:

head                                                        end
│                                                           │
▼                                                           ▼
┌────────┬──────────┬─────────┬──────────┬─────────┬───────┐
│Headroom│ Ethernet │   IP    │   TCP    │ Payload │Tailrm │
│        │  Header  │ Header  │  Header  │  Data   │       │
└────────┴──────────┴─────────┴──────────┴─────────┴───────┘
         ▲          ▲         ▲          ▲
         │          │         │          │
         │          │         │          └─ transport_header (offset from head)
         │          │         └──────────── network_header (offset from head)
         │          └────────────────────── mac_header (offset from head)
         └───────────────────────────────── data (pointer)

Access functions:
  skb_mac_header(skb)       → returns (skb->head + skb->mac_header)
  skb_network_header(skb)   → returns (skb->head + skb->network_header)
  skb_transport_header(skb) → returns (skb->head + skb->transport_header)

  eth_hdr(skb)  → returns (struct ethhdr *)skb_mac_header(skb)
  ip_hdr(skb)   → returns (struct iphdr *)skb_network_header(skb)
  tcp_hdr(skb)  → returns (struct tcphdr *)skb_transport_header(skb)
  udp_hdr(skb)  → returns (struct udphdr *)skb_transport_header(skb)
```

### 4.4 sk_buff Manipulation Functions

The kernel provides functions to add/remove headers and data:

#### 4.4.1 skb_reserve() - Reserve Headroom

```c
// Reserve space at the beginning for headers
void skb_reserve(struct sk_buff *skb, int len);

// Usage: Reserve space for all headers before adding data
skb = alloc_skb(1500, GFP_KERNEL);
skb_reserve(skb, MAX_HEADER);  // Reserve ~128 bytes for headers

Before:
head/data/tail                                            end
│                                                         │
▼                                                         ▼
┌─────────────────────────────────────────────────────────┐
│                     Available Space                     │
└─────────────────────────────────────────────────────────┘

After skb_reserve(skb, 128):
head              data/tail                               end
│                 │                                        │
▼                 ▼                                        ▼
┌─────────────────┬────────────────────────────────────────┐
│    Headroom     │         Available Space                │
│   (128 bytes)   │                                        │
└─────────────────┴────────────────────────────────────────┘
```

#### 4.4.2 skb_put() - Add Data to Tail

```c
// Add data at the end (extends tail pointer)
unsigned char *skb_put(struct sk_buff *skb, unsigned int len);

// Usage: Add payload data
data_ptr = skb_put(skb, 100);  // Add 100 bytes
memcpy(data_ptr, payload, 100);

Before:
head              data                  tail               end
│                 │                     │                  │
▼                 ▼                     ▼                  ▼
┌─────────────────┬─────────────────────┬──────────────────┐
│    Headroom     │    Existing Data    │    Tailroom      │
└─────────────────┴─────────────────────┴──────────────────┘

After skb_put(skb, 100):
head              data                           tail      end
│                 │                              │         │
▼                 ▼                              ▼         ▼
┌─────────────────┬──────────────────────────────┬─────────┐
│    Headroom     │    Existing + New Data       │Tailroom │
│                 │         (extended)           │(reduced)│
└─────────────────┴──────────────────────────────┴─────────┘
```

#### 4.4.3 skb_push() - Add Header to Front

```c
// Add header at the beginning (moves data pointer backward)
unsigned char *skb_push(struct sk_buff *skb, unsigned int len);

// Usage: Add TCP header
tcphdr = (struct tcphdr *)skb_push(skb, sizeof(struct tcphdr));
tcphdr->source = htons(src_port);
tcphdr->dest = htons(dst_port);

Before:
head              data                           tail      end
│                 │                              │         │
▼                 ▼                              ▼         ▼
┌─────────────────┬──────────────────────────────┬─────────┐
│    Headroom     │         Payload Data         │Tailroom │
└─────────────────┴──────────────────────────────┴─────────┘

After skb_push(skb, 20):  // Add 20-byte TCP header
head         data                                tail      end
│            │                                   │         │
▼            ▼                                   ▼         ▼
┌────────────┬──────┬──────────────────────────┬──────────┐
│ Headroom   │ TCP  │      Payload Data        │ Tailroom │
│ (reduced)  │Header│                          │          │
└────────────┴──────┴──────────────────────────┴──────────┘
```

#### 4.4.4 skb_pull() - Remove Header from Front

```c
// Remove header from the beginning (moves data pointer forward)
unsigned char *skb_pull(struct sk_buff *skb, unsigned int len);

// Usage: Remove Ethernet header during receive processing
skb_pull(skb, ETH_HLEN);  // Remove 14-byte Ethernet header

Before:
head         data                                tail      end
│            │                                   │         │
▼            ▼                                   ▼         ▼
┌────────────┬──────┬──────────────────────────┬──────────┐
│ Headroom   │ ETH  │      IP + Payload        │ Tailroom │
│            │Header│                          │          │
└────────────┴──────┴──────────────────────────┴──────────┘

After skb_pull(skb, 14):
head                data                        tail      end
│                   │                           │         │
▼                   ▼                           ▼         ▼
┌───────────────────┬───────────────────────────┬─────────┐
│    Headroom       │      IP + Payload         │Tailroom │
│   (increased)     │                           │         │
└───────────────────┴───────────────────────────┴─────────┘
```

### 4.5 Control Block (cb) - Protocol-Private Data

The 48-byte control block allows each protocol layer to store private metadata:

```c
// TCP uses cb for:
struct tcp_skb_cb {
    __u32   seq;        // Starting sequence number
    __u32   end_seq;    // Ending sequence number
    __u8    tcp_flags;  // TCP flags
    __u8    sacked;     // SACK information
    __u32   ack_seq;    // ACK sequence number
    // ... more fields
};

// IP uses cb for:
struct inet_skb_parm {
    int     iif;        // Input interface index
    __u16   flags;      // IP flags
    __u16   frag_max_size;
    // ... more fields
};

// Access:
#define TCP_SKB_CB(skb) ((struct tcp_skb_cb *)&((skb)->cb[0]))
#define IPCB(skb)       ((struct inet_skb_parm *)&((skb)->cb[0]))

// Usage:
TCP_SKB_CB(skb)->seq = sequence_number;
TCP_SKB_CB(skb)->end_seq = sequence_number + data_len;
```

**Important**: Each layer overwrites the cb with its own structure as the packet moves through the stack.

---

## 5. Protocol-Specific Framing

### 5.1 Application Layer Framing

Applications must implement their own framing over TCP (which doesn't preserve message boundaries):

#### 5.1.1 Length-Prefixed Framing

```
┌──────────┬─────────────────────┐
│ Length   │      Message        │
│ (4 bytes)│   (Length bytes)    │
└──────────┴─────────────────────┘

Example:
  0x00 0x00 0x00 0x0A "HelloWorld"
  │                   │
  └─ Length = 10      └─ 10 bytes of data

Receiver logic:
  1. Read 4 bytes → get length
  2. Read 'length' bytes → get message
  3. Repeat
```

#### 5.1.2 Delimiter-Based Framing

```
┌─────────────────────┬───────┐
│      Message        │ Delim │
│                     │ (\n)  │
└─────────────────────┴───────┘

Example: HTTP headers
  "GET /index.html HTTP/1.1\r\n"
  "Host: example.com\r\n"
  "\r\n"

Receiver logic:
  1. Read until delimiter (\r\n)
  2. Process message
  3. Repeat
```

#### 5.1.3 Fixed-Length Framing

```
┌─────────────────────┐
│      Message        │
│    (Fixed size)     │
└─────────────────────┘

Example: Binary protocol with 100-byte messages

Receiver logic:
  1. Read exactly 100 bytes
  2. Process message
  3. Repeat
```

#### 5.1.4 Type-Length-Value (TLV) Framing

```
┌──────┬──────────┬─────────────────────┐
│ Type │ Length   │       Value         │
│(1-2B)│ (2-4B)   │   (Length bytes)    │
└──────┴──────────┴─────────────────────┘

Example: Protocol Buffers, ASN.1
  Type=0x01, Length=5, Value="Hello"
  Type=0x02, Length=10, Value="0123456789"

Receiver logic:
  1. Read type
  2. Read length
  3. Read 'length' bytes of value
  4. Process based on type
  5. Repeat
```

---

## 6. Complete Data Flow Example

Let's trace a complete packet from application to wire and back.

### 6.1 Transmit Path (TX)

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Application Layer                                   │
└─────────────────────────────────────────────────────────────┘

Application calls:
  write(sockfd, "Hello, World!", 13);

┌─────────────────────────────────────────────────────────────┐
│ Step 2: Socket Layer                                        │
└─────────────────────────────────────────────────────────────┘

sock_sendmsg() → tcp_sendmsg()

┌─────────────────────────────────────────────────────────────┐
│ Step 3: TCP Layer                                           │
└─────────────────────────────────────────────────────────────┘

// Allocate sk_buff
skb = alloc_skb(MAX_TCP_HEADER + 13, GFP_KERNEL);

// Reserve space for headers
skb_reserve(skb, MAX_TCP_HEADER);  // ~128 bytes

// Add payload
data_ptr = skb_put(skb, 13);
copy_from_user(data_ptr, "Hello, World!", 13);

sk_buff state:
  head              data/tail                               end
  │                 │                                        │
  ▼                 ▼                                        ▼
  ┌─────────────────┬───────────────┬────────────────────────┐
  │    Headroom     │"Hello, World!"│      Tailroom          │
  │   (128 bytes)   │  (13 bytes)   │                        │
  └─────────────────┴───────────────┴────────────────────────┘

// Add TCP header
tcphdr = (struct tcphdr *)skb_push(skb, 20);
tcphdr->source = htons(12345);
tcphdr->dest = htons(80);
tcphdr->seq = htonl(1000);
tcphdr->ack_seq = htonl(5000);
tcphdr->doff = 5;  // 20 bytes / 4
tcphdr->flags = TCP_ACK | TCP_PSH;
tcphdr->window = htons(65535);

// Set transport header offset
skb->transport_header = skb->data - skb->head;

// Store metadata in control block
TCP_SKB_CB(skb)->seq = 1000;
TCP_SKB_CB(skb)->end_seq = 1013;  // 1000 + 13

sk_buff state:
  head         data                 tail                    end
  │            │                    │                       │
  ▼            ▼                    ▼                       ▼
  ┌────────────┬──────┬─────────────┬───────────────────────┐
  │ Headroom   │ TCP  │"Hello,World"│      Tailroom         │
  │ (108 bytes)│(20 B)│  (13 bytes) │                       │
  └────────────┴──────┴─────────────┴───────────────────────┘
               ▲
               └─ transport_header offset

┌─────────────────────────────────────────────────────────────┐
│ Step 4: IP Layer                                            │
└─────────────────────────────────────────────────────────────┘

ip_queue_xmit(skb);

// Add IP header
iphdr = (struct iphdr *)skb_push(skb, 20);
iphdr->version = 4;
iphdr->ihl = 5;  // 20 bytes / 4
iphdr->tot_len = htons(53);  // 20 + 20 + 13
iphdr->id = htons(12345);
iphdr->frag_off = 0;
iphdr->ttl = 64;
iphdr->protocol = IPPROTO_TCP;  // 6
iphdr->saddr = htonl(0xC0A80101);  // 192.168.1.1
iphdr->daddr = htonl(0xC0A80102);  // 192.168.1.2
iphdr->check = ip_fast_csum(iphdr, iphdr->ihl);

// Set network header offset
skb->network_header = skb->data - skb->head;

sk_buff state:
  head    data            tail                             end
  │       │               │                                │
  ▼       ▼               ▼                                ▼
  ┌───────┬─────┬──────┬──────────────┬────────────────────┐
  │Headrm │ IP  │ TCP  │"Hello,World!"│      Tailroom      │
  │(88 B) │(20B)│(20 B)│  (13 bytes)  │                    │
  └───────┴─────┴──────┴──────────────┴────────────────────┘
          ▲     ▲
          │     └─ transport_header offset
          └─ network_header offset

┌─────────────────────────────────────────────────────────────┐
│ Step 5: Ethernet Layer                                      │
└─────────────────────────────────────────────────────────────┘

dev_queue_xmit(skb);

// Add Ethernet header
ethhdr = (struct ethhdr *)skb_push(skb, 14);
memcpy(ethhdr->h_dest, dst_mac, 6);    // AA:BB:CC:DD:EE:FF
memcpy(ethhdr->h_source, src_mac, 6);  // 11:22:33:44:55:66
ethhdr->h_proto = htons(ETH_P_IP);     // 0x0800

// Set MAC header offset
skb->mac_header = skb->data - skb->head;

sk_buff state:
  head data       tail                                     end
  │    │          │                                        │
  ▼    ▼          ▼                                        ▼
  ┌────┬────┬─────┬──────┬──────────────┬──────────────────┐
  │Hdrm│ETH │ IP  │ TCP  │"Hello,World!"│    Tailroom      │
  │(74)│(14)│(20B)│(20 B)│  (13 bytes)  │                  │
  └────┴────┴─────┴──────┴──────────────┴──────────────────┘
       ▲    ▲     ▲
       │    │     └─ transport_header offset
       │    └─ network_header offset
       └─ mac_header offset

┌─────────────────────────────────────────────────────────────┐
│ Step 6: Network Driver                                      │
└─────────────────────────────────────────────────────────────┘

driver_xmit(skb);

// Map buffer for DMA
dma_addr = dma_map_single(dev, skb->data, skb->len, DMA_TO_DEVICE);

// Configure TX descriptor
tx_desc->addr = dma_addr;
tx_desc->length = skb->len;  // 67 bytes (14+20+20+13)
tx_desc->flags = TX_DESC_IFCS;  // Insert FCS

// Trigger transmission
writel(TX_QUEUE_START, hw_reg);

┌─────────────────────────────────────────────────────────────┐
│ Step 7: Physical Layer (NIC Hardware)                       │
└─────────────────────────────────────────────────────────────┘

NIC adds:
  - Preamble (7 bytes): 0xAA 0xAA 0xAA 0xAA 0xAA 0xAA 0xAA
  - SFD (1 byte): 0xAB
  - FCS (4 bytes): CRC-32 checksum

Final frame on wire (78 bytes):
┌────┬───┬────┬─────┬──────┬──────────────┬─────┐
│Pre │SFD│ETH │ IP  │ TCP  │"Hello,World!"│ FCS │
│(7) │(1)│(14)│(20B)│(20 B)│  (13 bytes)  │ (4) │
└────┴───┴────┴─────┴──────┴──────────────┴─────┘
```

### 6.2 Receive Path (RX)

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Physical Layer (NIC Hardware)                       │
└─────────────────────────────────────────────────────────────┘

NIC receives frame:
  - Detects carrier (end of idle)
  - Synchronizes on preamble
  - Detects SFD (0xAB) → frame starts
  - Receives frame data via DMA to memory
  - Verifies FCS checksum
  - Strips preamble, SFD, and FCS
  - Generates interrupt

┌─────────────────────────────────────────────────────────────┐
│ Step 2: Network Driver (Interrupt Handler)                  │
└─────────────────────────────────────────────────────────────┘

driver_rx_interrupt() {
    // Allocate sk_buff
    skb = netdev_alloc_skb(dev, frame_len);

    // Copy frame from DMA buffer to sk_buff
    // (or use page frags for zero-copy)
    memcpy(skb->data, dma_buffer, frame_len);

    // Set data pointers
    skb_put(skb, frame_len);  // 67 bytes

    // Set device and protocol
    skb->dev = netdev;
    skb->protocol = eth_type_trans(skb, netdev);

    // Deliver to network stack
    netif_receive_skb(skb);
}

sk_buff state after driver:
  head/data                                    tail           end
  │                                            │              │
  ▼                                            ▼              ▼
  ┌────┬─────┬──────┬──────────────┬───────────────────────────┐
  │ETH │ IP  │ TCP  │"Hello,World!"│        Tailroom           │
  │(14)│(20B)│(20 B)│  (13 bytes)  │                           │
  └────┴─────┴──────┴──────────────┴───────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Step 3: Ethernet Layer                                      │
└─────────────────────────────────────────────────────────────┘

eth_type_trans(skb, dev) {
    // Set MAC header
    skb->mac_header = skb->data - skb->head;  // Offset 0

    // Parse Ethernet header
    ethhdr = eth_hdr(skb);

    // Check destination MAC
    if (is_multicast_ether_addr(ethhdr->h_dest))
        skb->pkt_type = PACKET_MULTICAST;
    else if (!ether_addr_equal(ethhdr->h_dest, dev->dev_addr))
        skb->pkt_type = PACKET_OTHERHOST;
    else
        skb->pkt_type = PACKET_HOST;

    // Get protocol type
    protocol = ethhdr->h_proto;  // 0x0800 (ETH_P_IP)

    // Remove Ethernet header
    skb_pull(skb, ETH_HLEN);  // Remove 14 bytes

    return protocol;
}

sk_buff state after Ethernet processing:
  head         data                            tail           end
  │            │                               │              │
  ▼            ▼                               ▼              ▼
  ┌────────────┬─────┬──────┬──────────────┬──────────────────┐
  │ ETH (old)  │ IP  │ TCP  │"Hello,World!"│    Tailroom      │
  │ (headroom) │(20B)│(20 B)│  (13 bytes)  │                  │
  └────────────┴─────┴──────┴──────────────┴──────────────────┘
               ▲
               └─ mac_header still points here (offset 0)

┌─────────────────────────────────────────────────────────────┐
│ Step 4: IP Layer                                            │
└─────────────────────────────────────────────────────────────┘

ip_rcv(skb) {
    // Set network header
    skb->network_header = skb->data - skb->head;  // Offset 14

    // Parse IP header
    iphdr = ip_hdr(skb);

    // Validate header
    if (iphdr->version != 4) goto drop;
    if (iphdr->ihl < 5) goto drop;

    // Verify checksum
    if (ip_fast_csum(iphdr, iphdr->ihl) != 0) goto drop;

    // Check total length
    if (ntohs(iphdr->tot_len) > skb->len) goto drop;

    // Trim any padding
    pkt_len = ntohs(iphdr->tot_len);
    if (skb->len > pkt_len)
        skb_trim(skb, pkt_len);

    // Check if fragmented
    if (iphdr->frag_off & htons(IP_MF | IP_OFFSET)) {
        // Handle fragmentation
        skb = ip_defrag(skb);
        if (!skb) return;
    }

    // Route packet
    if (ip_route_input(skb, iphdr->daddr, iphdr->saddr,
                       iphdr->tos, dev) != 0)
        goto drop;

    // Deliver to transport layer based on protocol
    switch (iphdr->protocol) {
        case IPPROTO_TCP:  // 6
            return tcp_v4_rcv(skb);
        case IPPROTO_UDP:  // 17
            return udp_rcv(skb);
        case IPPROTO_ICMP: // 1
            return icmp_rcv(skb);
        default:
            goto drop;
    }
}

sk_buff state after IP processing:
  head              data                       tail           end
  │                 │                          │              │
  ▼                 ▼                          ▼              ▼
  ┌─────────────────┬──────┬──────────────┬───────────────────┐
  │ ETH+IP (old)    │ TCP  │"Hello,World!"│    Tailroom       │
  │   (headroom)    │(20 B)│  (13 bytes)  │                   │
  └─────────────────┴──────┴──────────────┴───────────────────┘
                    ▲
                    └─ network_header points to IP (offset 14)

┌─────────────────────────────────────────────────────────────┐
│ Step 5: TCP Layer                                           │
└─────────────────────────────────────────────────────────────┘

tcp_v4_rcv(skb) {
    // Set transport header
    skb->transport_header = skb->data - skb->head;  // Offset 34

    // Parse TCP header
    tcphdr = tcp_hdr(skb);

    // Validate header
    if (tcphdr->doff < 5) goto drop;

    // Calculate header length
    tcp_hdr_len = tcphdr->doff * 4;  // 20 bytes

    // Find connection
    sk = __inet_lookup_skb(&tcp_hashinfo, skb,
                           tcphdr->source, tcphdr->dest);
    if (!sk) goto no_tcp_socket;

    // Store metadata in control block
    TCP_SKB_CB(skb)->seq = ntohl(tcphdr->seq);      // 1000
    TCP_SKB_CB(skb)->end_seq = TCP_SKB_CB(skb)->seq +
                               (skb->len - tcp_hdr_len);  // 1013
    TCP_SKB_CB(skb)->ack_seq = ntohl(tcphdr->ack_seq);  // 5000
    TCP_SKB_CB(skb)->tcp_flags = tcphdr->flags;

    // Verify checksum
    if (tcp_v4_checksum_init(skb) < 0) goto csum_error;

    // Process TCP state machine
    tcp_v4_do_rcv(sk, skb);
}

tcp_v4_do_rcv(sk, skb) {
    // Check sequence number
    if (TCP_SKB_CB(skb)->seq != tp->rcv_nxt) {
        // Out of order - queue for later
        tcp_data_queue_ofo(sk, skb);
        return;
    }

    // In-order data
    // Remove TCP header
    __skb_pull(skb, tcp_hdr_len);  // Remove 20 bytes

    // Add to receive queue
    __skb_queue_tail(&sk->sk_receive_queue, skb);

    // Update next expected sequence
    tp->rcv_nxt = TCP_SKB_CB(skb)->end_seq;  // 1013

    // Send ACK
    tcp_send_ack(sk);

    // Wake up application
    sk->sk_data_ready(sk);
}

sk_buff state in receive queue:
  head                   data          tail                   end
  │                      │             │                      │
  ▼                      ▼             ▼                      ▼
  ┌──────────────────────┬─────────────┬──────────────────────┐
  │ ETH+IP+TCP (old)     │"Hello,World"│      Tailroom        │
  │     (headroom)       │ (13 bytes)  │                      │
  └──────────────────────┴─────────────┴──────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Step 6: Socket Layer                                        │
└─────────────────────────────────────────────────────────────┘

Application calls:
  read(sockfd, buffer, 100);

tcp_recvmsg(sk, msg, len, flags) {
    // Get sk_buff from receive queue
    skb = skb_peek(&sk->sk_receive_queue);

    // Copy data to user space
    copied = skb_copy_datagram_msg(skb, 0, msg, skb->len);
    // Copies "Hello, World!" (13 bytes) to user buffer

    // Remove from queue
    __skb_unlink(skb, &sk->sk_receive_queue);

    // Free sk_buff
    kfree_skb(skb);

    return copied;  // 13
}

┌─────────────────────────────────────────────────────────────┐
│ Step 7: Application Layer                                   │
└─────────────────────────────────────────────────────────────┘

Application receives:
  buffer = "Hello, World!"
  bytes_read = 13
```

---

## 7. Advanced Topics

### 7.1 Fragmentation and Reassembly

#### 7.1.1 IP Fragmentation

When a packet exceeds the MTU, IP fragments it:

```c
// Fragmentation logic (simplified)
ip_fragment(struct sk_buff *skb, int mtu) {
    struct iphdr *iph = ip_hdr(skb);
    int hlen = iph->ihl * 4;
    int max_frag_size = ((mtu - hlen) & ~7);  // Multiple of 8

    // Original packet
    int total_len = ntohs(iph->tot_len);
    int data_len = total_len - hlen;

    // Calculate number of fragments
    int num_frags = (data_len + max_frag_size - 1) / max_frag_size;

    for (int i = 0; i < num_frags; i++) {
        // Create fragment
        frag = skb_copy(skb, GFP_ATOMIC);

        // Calculate fragment parameters
        int offset = i * max_frag_size;
        int frag_len = min(max_frag_size, data_len - offset);

        // Set fragment fields
        frag_iph = ip_hdr(frag);
        frag_iph->tot_len = htons(hlen + frag_len);
        frag_iph->frag_off = htons(offset / 8);

        if (i < num_frags - 1)
            frag_iph->frag_off |= htons(IP_MF);  // More fragments

        // Recalculate checksum
        ip_send_check(frag_iph);

        // Send fragment
        ip_local_out(frag);
    }
}
```

#### 7.1.2 IP Reassembly

Receiver reassembles fragments:

```c
// Reassembly logic (simplified)
struct ipq {
    struct ipq      *next;
    u32             saddr;
    u32             daddr;
    u16             id;
    u8              protocol;
    struct sk_buff  *fragments;
    int             len;
    int             meat;  // Bytes received so far
    u8              last_in;  // Flags: first, last received
};

ip_defrag(struct sk_buff *skb) {
    struct iphdr *iph = ip_hdr(skb);

    // Find or create reassembly queue
    qp = ip_find(iph->saddr, iph->daddr, iph->id, iph->protocol);
    if (!qp) {
        qp = ip_frag_create(iph);
    }

    // Add fragment to queue
    offset = ntohs(iph->frag_off);
    end = offset + ntohs(iph->tot_len) - iph->ihl * 4;

    // Insert in order
    ip_frag_queue(qp, skb);

    // Check if complete
    if (qp->last_in == (FIRST_IN | LAST_IN) && qp->meat == qp->len) {
        // All fragments received - reassemble
        return ip_frag_reasm(qp);
    }

    return NULL;  // Still waiting for fragments
}

ip_frag_reasm(struct ipq *qp) {
    struct sk_buff *head = qp->fragments;
    struct sk_buff *fp, *prev;
    int len = 0;

    // Combine all fragments
    for (fp = head->next; fp; fp = fp->next) {
        // Remove IP header from fragments
        skb_pull(fp, ip_hdrlen(fp));

        // Append to head
        if (skb_try_coalesce(head, fp, &fragstolen, &delta)) {
            // Merged successfully
        } else {
            // Add to frag_list
            if (!head->frag_list)
                head->frag_list = fp;
            else
                prev->next = fp;
            prev = fp;
        }
    }

    // Update IP header
    iph = ip_hdr(head);
    iph->frag_off = 0;
    iph->tot_len = htons(len);
    ip_send_check(iph);

    return head;
}
```

### 7.2 TCP Segmentation Offload (TSO/GSO)

Modern NICs can segment large packets in hardware:

```c
// Application sends large buffer
write(sockfd, large_buffer, 64000);

// TCP creates one large sk_buff
skb = alloc_skb(64000 + headers, GFP_KERNEL);
skb_put(skb, 64000);

// Mark for GSO (Generic Segmentation Offload)
skb_shinfo(skb)->gso_size = mss;  // e.g., 1460
skb_shinfo(skb)->gso_type = SKB_GSO_TCPV4;
skb_shinfo(skb)->gso_segs = (64000 + mss - 1) / mss;  // ~44 segments

// Send to driver
dev_queue_xmit(skb);

// Driver/hardware segments into multiple frames
// Saves CPU cycles - segmentation done in hardware
```

### 7.3 Receive Side Scaling (RSS) and GRO

#### 7.3.1 Generic Receive Offload (GRO)

Combines multiple small packets into one large sk_buff:

```c
// NIC receives multiple TCP segments
// Segment 1: SEQ=1000, LEN=1460
// Segment 2: SEQ=2460, LEN=1460
// Segment 3: SEQ=3920, LEN=1460

// GRO combines them
napi_gro_receive(napi, skb1);  // SEQ=1000
napi_gro_receive(napi, skb2);  // SEQ=2460 - combined with skb1
napi_gro_receive(napi, skb3);  // SEQ=3920 - combined with skb1

// Result: One large sk_buff with 4380 bytes
// Reduces per-packet processing overhead
```

### 7.4 Zero-Copy Techniques

#### 7.4.1 Page Frags

Instead of copying data, sk_buff can reference pages:

```c
struct skb_shared_info {
    unsigned char   nr_frags;
    skb_frag_t      frags[MAX_SKB_FRAGS];
    struct sk_buff  *frag_list;
};

typedef struct skb_frag_struct {
    struct page *page;
    __u32 page_offset;
    __u32 size;
} skb_frag_t;

// Add page fragment
skb_fill_page_desc(skb, i, page, offset, size);

// sk_buff layout with frags:
┌─────────────────────────────────────────────────────────────┐
│ sk_buff                                                      │
│   head → [Linear data: headers]                             │
│   skb_shared_info:                                          │
│     frags[0] → page1 + offset (1024 bytes)                  │
│     frags[1] → page2 + offset (2048 bytes)                  │
│     frags[2] → page3 + offset (512 bytes)                   │
└─────────────────────────────────────────────────────────────┘

Total data = linear + sum(frags) = headers + 3584 bytes
```

### 7.5 Checksum Offload

#### 7.5.1 TX Checksum Offload

```c
// TCP layer
skb->ip_summed = CHECKSUM_PARTIAL;
skb->csum_start = skb_transport_header(skb) - skb->head;
skb->csum_offset = offsetof(struct tcphdr, check);

// Driver/hardware calculates checksum
// Saves CPU cycles
```

#### 7.5.2 RX Checksum Offload

```c
// Hardware verifies checksum
// Driver sets:
skb->ip_summed = CHECKSUM_UNNECESSARY;

// Stack skips checksum verification
// Saves CPU cycles
```

---

## 8. Summary

### 8.1 How Data Boundaries Are Ensured

| Layer | Mechanism | Start Marker | End Marker |
|-------|-----------|--------------|------------|
| **Physical** | Bit timing, encoding | Carrier detect | Idle pattern |
| **Ethernet** | Preamble, SFD, FCS | SFD (0xAB) | FCS + IFG |
| **IP** | Header length, total length | IHL field | Total Length field |
| **TCP** | Sequence numbers | SEQ number | SEQ + data length |
| **UDP** | Length field | Port numbers | Length field |
| **Application** | Custom framing | App-defined | App-defined |

### 8.2 sk_buff Role

The sk_buff structure provides:

1. **Pointer-based boundary tracking**: `head`, `data`, `tail`, `end`
2. **Header offset tracking**: `mac_header`, `network_header`, `transport_header`
3. **Length tracking**: `len`, `data_len`, `mac_len`
4. **Protocol identification**: `protocol` field
5. **Metadata storage**: 48-byte control block (`cb`)
6. **Efficient manipulation**: `skb_push()`, `skb_pull()`, `skb_put()`

### 8.3 Key Takeaways

1. **Multiple layers of boundaries**: Each protocol layer has its own boundary mechanism
2. **Redundancy ensures reliability**: Multiple checksums, length fields, and markers
3. **sk_buff tracks everything**: Kernel maintains precise pointers and offsets
4. **Hardware assists**: Modern NICs handle framing, checksums, and segmentation
5. **Zero-copy optimizations**: Page frags and offloads reduce CPU overhead

---

## 9. References

- Linux Kernel Documentation: https://docs.kernel.org/networking/skbuff.html
- RFC 791: Internet Protocol (IP)
- RFC 793: Transmission Control Protocol (TCP)
- RFC 768: User Datagram Protocol (UDP)
- IEEE 802.3: Ethernet Standard
- Linux Kernel Source: `include/linux/skbuff.h`, `net/core/skbuff.c`

---

**Document Version**: 1.0
**Last Updated**: 2026-03-20
**Author**: Based on Linux Kernel Documentation and Networking RFCs


