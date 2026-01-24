# OSI Model and Packet Encapsulation/Decapsulation

## Table of Contents

1. [Overview](#overview)
2. [The OSI Model](#the-osi-model)
3. [Protocol Data Units (PDUs)](#protocol-data-units-pdus)
4. [Encapsulation Process (Sending)](#encapsulation-process-sending)
5. [Decapsulation Process (Receiving)](#decapsulation-process-receiving)
6. [Layer-by-Layer Breakdown](#layer-by-layer-breakdown)
7. [TCP/IP Model Comparison](#tcpip-model-comparison)
8. [Packet Structure Examples](#packet-structure-examples)
9. [Inter-Layer Communication](#inter-layer-communication)
10. [Practical Examples](#practical-examples)

---

## Overview

This document explains how data is transformed as it passes through the layers of the OSI (Open Systems
Interconnection) model. As data travels down the stack (sending), each layer adds its own header (and
sometimes trailer) - a process called **encapsulation**. When receiving, each layer removes its respective
header/trailer - called **decapsulation**.

---

## The OSI Model

The OSI model consists of 7 layers, each with specific responsibilities:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        OSI Reference Model                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Layer 7  ┌─────────────────────────────────────────────────────┐  │
│           │              APPLICATION LAYER                      │  │
│           │  HTTP, FTP, SMTP, DNS, SSH, Telnet, SNMP           │  │
│           │  User interface, application services               │  │
│           └─────────────────────────────────────────────────────┘  │
│                                    ↕                                │
│  Layer 6  ┌─────────────────────────────────────────────────────┐  │
│           │              PRESENTATION LAYER                     │  │
│           │  SSL/TLS, JPEG, MPEG, ASCII, Encryption            │  │
│           │  Data format, encryption, compression               │  │
│           └─────────────────────────────────────────────────────┘  │
│                                    ↕                                │
│  Layer 5  ┌─────────────────────────────────────────────────────┐  │
│           │                SESSION LAYER                        │  │
│           │  NetBIOS, RPC, PPTP                                 │  │
│           │  Session management, dialog control                 │  │
│           └─────────────────────────────────────────────────────┘  │
│                                    ↕                                │
│  Layer 4  ┌─────────────────────────────────────────────────────┐  │
│           │               TRANSPORT LAYER                       │  │
│           │  TCP, UDP, SCTP                                     │  │
│           │  End-to-end delivery, segmentation, flow control    │  │
│           └─────────────────────────────────────────────────────┘  │
│                                    ↕                                │
│  Layer 3  ┌─────────────────────────────────────────────────────┐  │
│           │                NETWORK LAYER                        │  │
│           │  IP, ICMP, IGMP, IPsec, Routing Protocols          │  │
│           │  Logical addressing, routing, path determination    │  │
│           └─────────────────────────────────────────────────────┘  │
│                                    ↕                                │
│  Layer 2  ┌─────────────────────────────────────────────────────┐  │
│           │               DATA LINK LAYER                       │  │
│           │  Ethernet, Wi-Fi (802.11), PPP, HDLC               │  │
│           │  Physical addressing, framing, error detection      │  │
│           └─────────────────────────────────────────────────────┘  │
│                                    ↕                                │
│  Layer 1  ┌─────────────────────────────────────────────────────┐  │
│           │               PHYSICAL LAYER                        │  │
│           │  Cables, Hubs, Repeaters, Radio waves              │  │
│           │  Bit transmission, electrical/optical signals       │  │
│           └─────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Layer Summary Table

| Layer | Name         | PDU              | Function                             | Devices              |
| ----- | ------------ | ---------------- | ------------------------------------ | -------------------- |
| 7     | Application  | Data             | User interface, application services | -                    |
| 6     | Presentation | Data             | Format, encryption, compression      | -                    |
| 5     | Session      | Data             | Session establishment, maintenance   | -                    |
| 4     | Transport    | Segment/Datagram | End-to-end delivery, reliability     | -                    |
| 3     | Network      | Packet           | Routing, logical addressing          | Router, L3 Switch    |
| 2     | Data Link    | Frame            | Physical addressing, framing         | Switch, Bridge, AP   |
| 1     | Physical     | Bits             | Physical transmission                | Hub, Repeater, Cable |

---

## Protocol Data Units (PDUs)

Each layer has its own name for the data unit it handles:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Protocol Data Units (PDUs)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Layer 7-5:    ┌──────────────────────────────────────┐            │
│                │              DATA                     │            │
│                └──────────────────────────────────────┘            │
│                                                                     │
│  Layer 4:      ┌────────┬─────────────────────────────┐            │
│                │TCP/UDP │           DATA               │            │
│                │ Header │                              │            │
│                └────────┴─────────────────────────────┘            │
│                         SEGMENT (TCP) / DATAGRAM (UDP)              │
│                                                                     │
│  Layer 3:      ┌────────┬────────┬────────────────────┐            │
│                │   IP   │TCP/UDP │       DATA         │            │
│                │ Header │ Header │                    │            │
│                └────────┴────────┴────────────────────┘            │
│                              PACKET                                 │
│                                                                     │
│  Layer 2:      ┌────────┬────────┬────────┬──────────┬────────┐   │
│                │  L2    │   IP   │TCP/UDP │   DATA   │  L2    │   │
│                │ Header │ Header │ Header │          │Trailer │   │
│                └────────┴────────┴────────┴──────────┴────────┘   │
│                                 FRAME                               │
│                                                                     │
│  Layer 1:      01101001 01010110 11010010 10110101 ...             │
│                                 BITS                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Encapsulation Process (Sending)

When data is sent, it travels DOWN the OSI stack, with each layer adding its header:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ENCAPSULATION (Sending)                         │
│                     Data flows DOWN the stack                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Application    User types: "Hello World"                           │
│  Layer 7        ┌──────────────────────────────────┐               │
│                 │         "Hello World"            │               │
│                 └──────────────────────────────────┘               │
│                              │                                      │
│                              ▼ Add Application Protocol Header      │
│  Presentation   ┌─────┬────────────────────────────┐               │
│  Layer 6        │ SSL │      "Hello World"         │               │
│                 └─────┴────────────────────────────┘               │
│                              │                                      │
│                              ▼ Add Session Info                     │
│  Session        ┌─────┬─────┬──────────────────────┐               │
│  Layer 5        │ Sess│ SSL │   "Hello World"      │               │
│                 └─────┴─────┴──────────────────────┘               │
│                              │                                      │
│                              ▼ Add TCP Header (Ports, Seq#, etc.)   │
│  Transport      ┌─────┬─────────────────────────────┐              │
│  Layer 4        │ TCP │          DATA               │  = SEGMENT   │
│                 │20-60│                             │              │
│                 └─────┴─────────────────────────────┘              │
│                              │                                      │
│                              ▼ Add IP Header (Src/Dst IP, TTL)      │
│  Network        ┌─────┬─────┬───────────────────────┐              │
│  Layer 3        │ IP  │ TCP │        DATA           │  = PACKET    │
│                 │ 20  │     │                       │              │
│                 └─────┴─────┴───────────────────────┘              │
│                              │                                      │
│                              ▼ Add Ethernet Header + FCS Trailer    │
│  Data Link      ┌─────┬─────┬─────┬─────────────┬─────┐           │
│  Layer 2        │ ETH │ IP  │ TCP │    DATA     │ FCS │ = FRAME   │
│                 │ 14  │     │     │             │  4  │           │
│                 └─────┴─────┴─────┴─────────────┴─────┘           │
│                              │                                      │
│                              ▼ Convert to electrical/radio signals  │
│  Physical       0110100101011011010010101101010011010110...         │
│  Layer 1        Transmitted over wire, fiber, or radio             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

```

## Decapsulation Process (Receiving)

When data is received, it travels UP the OSI stack, with each layer removing its header:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DECAPSULATION (Receiving)                        │
│                     Data flows UP the stack                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Physical       0110100101011011010010101101010011010110...         │
│  Layer 1        Received from wire, fiber, or radio                │
│                              │                                      │
│                              ▼ Convert signals to digital frame     │
│  Data Link      ┌─────┬─────┬─────┬─────────────┬─────┐           │
│  Layer 2        │ ETH │ IP  │ TCP │    DATA     │ FCS │           │
│                 └─────┴─────┴─────┴─────────────┴─────┘           │
│                 ✓ Verify FCS (checksum)                            │
│                 ✓ Check destination MAC matches                     │
│                 ✗ Remove Ethernet header & FCS                      │
│                              │                                      │
│                              ▼                                      │
│  Network        ┌─────┬─────┬───────────────────────┐              │
│  Layer 3        │ IP  │ TCP │        DATA           │              │
│                 └─────┴─────┴───────────────────────┘              │
│                 ✓ Check destination IP matches                      │
│                 ✓ Verify IP header checksum                         │
│                 ✓ Decrement TTL                                     │
│                 ✗ Remove IP header                                  │
│                              │                                      │
│                              ▼                                      │
│  Transport      ┌─────┬─────────────────────────────┐              │
│  Layer 4        │ TCP │          DATA               │              │
│                 └─────┴─────────────────────────────┘              │
│                 ✓ Check destination port                           │
│                 ✓ Verify TCP checksum                              │
│                 ✓ Handle sequence numbers, ACKs                    │
│                 ✓ Reassemble segments                              │
│                 ✗ Remove TCP header                                 │
│                              │                                      │
│                              ▼                                      │
│  Session/       ┌──────────────────────────────────┐               │
│  Presentation   │         Decrypted DATA           │               │
│  Layer 5-6      └──────────────────────────────────┘               │
│                 ✓ Decrypt if encrypted (SSL/TLS)                   │
│                 ✓ Decompress if compressed                         │
│                 ✓ Convert character encoding                       │
│                              │                                      │
│                              ▼                                      │
│  Application    ┌──────────────────────────────────┐               │
│  Layer 7        │         "Hello World"            │               │
│                 └──────────────────────────────────┘               │
│                 Application receives the original data             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Layer-by-Layer Breakdown

### Layer 7: Application Layer

**Purpose**: Provides network services directly to end-user applications

**What it does to data**:

- No encapsulation header added (provides the actual data)
- Formats data according to application protocol (HTTP, FTP, etc.)

**Protocols**:
| Protocol | Port | Description |
|----------|------|-------------|
| HTTP | 80 | Web browsing |
| HTTPS | 443 | Secure web |
| FTP | 20, 21 | File transfer |
| SSH | 22 | Secure shell |
| Telnet | 23 | Remote terminal |
| SMTP | 25 | Email sending |
| DNS | 53 | Name resolution |
| DHCP | 67, 68 | IP addressing |
| POP3 | 110 | Email retrieval |
| IMAP | 143 | Email access |
| SNMP | 161 | Network management |

---

### Layer 6: Presentation Layer

**Purpose**: Data translation, encryption, and compression

**What it does to data**:

- **Encryption/Decryption**: SSL/TLS encryption
- **Compression**: Reduces data size
- **Format Conversion**: Character encoding (ASCII, Unicode)
- **Serialization**: Converting data structures

**Examples**:
| Function | Examples |
|----------|----------|
| Encryption | SSL, TLS, AES |
| Compression | GZIP, LZ4 |
| Format | JPEG, PNG, MPEG, MP3 |
| Encoding | ASCII, UTF-8, EBCDIC |

---

### Layer 5: Session Layer

**Purpose**: Manages sessions between applications

**What it does to data**:

- **Session establishment**: Creates connection
- **Session maintenance**: Keeps connection alive
- **Session termination**: Closes connection properly
- **Synchronization**: Checkpoints for recovery

**Protocols**: NetBIOS, RPC, PPTP, SIP (session management)

**Session Modes**:
| Mode | Description |
|------|-------------|
| Simplex | One-way only |
| Half-Duplex | Two-way, alternating |
| Full-Duplex | Two-way, simultaneous |

---

### Layer 4: Transport Layer

**Purpose**: End-to-end data delivery, reliability, and flow control

**Header Added**: TCP Header (20-60 bytes) or UDP Header (8 bytes)

#### TCP Header Structure (20-60 bytes)

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
|                    Options (if any)                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Field                 | Size    | Description                        |
| --------------------- | ------- | ---------------------------------- |
| Source Port           | 16 bits | Sender's port number               |
| Destination Port      | 16 bits | Receiver's port number             |
| Sequence Number       | 32 bits | Byte position in stream            |
| Acknowledgment Number | 32 bits | Next expected byte                 |
| Data Offset           | 4 bits  | Header length (in 32-bit words)    |
| Flags                 | 9 bits  | SYN, ACK, FIN, RST, PSH, URG, etc. |
| Window                | 16 bits | Receive window size                |
| Checksum              | 16 bits | Error detection                    |
| Urgent Pointer        | 16 bits | Urgent data offset                 |

#### TCP Flags

| Flag | Name                      | Purpose                   |
| ---- | ------------------------- | ------------------------- |
| SYN  | Synchronize               | Initiate connection       |
| ACK  | Acknowledge               | Acknowledge received data |
| FIN  | Finish                    | Terminate connection      |
| RST  | Reset                     | Abort connection          |
| PSH  | Push                      | Deliver data immediately  |
| URG  | Urgent                    | Urgent data present       |
| ECE  | ECN Echo                  | Congestion notification   |
| CWR  | Congestion Window Reduced | Response to ECE           |

#### UDP Header Structure (8 bytes)

```
0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|            Length             |           Checksum            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

#### TCP vs UDP Comparison

| Feature            | TCP                  | UDP                  |
| ------------------ | -------------------- | -------------------- |
| Connection         | Connection-oriented  | Connectionless       |
| Reliability        | Guaranteed delivery  | Best effort          |
| Ordering           | Ordered delivery     | No ordering          |
| Flow Control       | Yes (sliding window) | No                   |
| Congestion Control | Yes                  | No                   |
| Header Size        | 20-60 bytes          | 8 bytes              |
| Speed              | Slower               | Faster               |
| Use Cases          | HTTP, FTP, Email     | DNS, VoIP, Streaming |

---

### Layer 3: Network Layer

**Purpose**: Logical addressing and routing across networks

**Header Added**: IP Header (20-60 bytes for IPv4, 40 bytes for IPv6)

#### IPv4 Header Structure (20-60 bytes)

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
|                    Options (if IHL > 5)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Field                      | Size    | Description                              |
| -------------------------- | ------- | ---------------------------------------- |
| Version                    | 4 bits  | IP version (4 or 6)                      |
| IHL                        | 4 bits  | Header length (in 32-bit words)          |
| Type of Service (DSCP/ECN) | 8 bits  | QoS markings                             |
| Total Length               | 16 bits | Total packet size                        |
| Identification             | 16 bits | Fragment identification                  |
| Flags                      | 3 bits  | DF (Don't Fragment), MF (More Fragments) |
| Fragment Offset            | 13 bits | Fragment position                        |
| TTL                        | 8 bits  | Hop limit (decremented at each router)   |
| Protocol                   | 8 bits  | Upper layer protocol (TCP=6, UDP=17)     |
| Header Checksum            | 16 bits | Header error detection                   |
| Source Address             | 32 bits | Sender's IP address                      |
| Destination Address        | 32 bits | Receiver's IP address                    |

#### Protocol Numbers

| Number | Protocol    |
| ------ | ----------- |
| 1      | ICMP        |
| 6      | TCP         |
| 17     | UDP         |
| 47     | GRE         |
| 50     | ESP (IPsec) |
| 51     | AH (IPsec)  |
| 89     | OSPF        |

#### IP Fragmentation

When a packet exceeds the MTU (Maximum Transmission Unit):

```
Original Packet (4000 bytes payload, MTU = 1500)
┌──────────────────────────────────────────────────────────────┐
│ IP Header │              4000 bytes of data                  │
└──────────────────────────────────────────────────────────────┘
│
▼ Fragmentation
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│ IP Header │ 1480 bytes│  │ IP Header │ 1480 bytes│  │ IP Header │ 1040 bytes│
│ Offset=0  │  MF=1     │  │ Offset=185│  MF=1     │  │ Offset=370│  MF=0     │
│ ID=12345  │           │  │ ID=12345  │           │  │ ID=12345  │           │
└───────────────────────┘  └───────────────────────┘  └───────────────────────┘
Fragment 1                 Fragment 2                 Fragment 3
```

---

### Layer 2: Data Link Layer

**Purpose**: Physical addressing, framing, and local delivery

**Header Added**: Ethernet Header (14 bytes) + FCS Trailer (4 bytes)

#### Ethernet Frame Structure

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          Ethernet II Frame                                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────┬─────────┬─────────┬──────────────────────────────┬─────────┐ │
│  │Preamble │   SFD   │  Header │           Payload            │   FCS   │ │
│  │ 7 bytes │ 1 byte  │14 bytes │        46-1500 bytes         │ 4 bytes │ │
│  └─────────┴─────────┴─────────┴──────────────────────────────┴─────────┘ │
│                                                                            │
│  Header Detail:                                                            │
│  ┌──────────────────┬──────────────────┬──────────────────┐               │
│  │ Destination MAC  │   Source MAC     │   EtherType      │               │
│  │     6 bytes      │    6 bytes       │    2 bytes       │               │
│  └──────────────────┴──────────────────┴──────────────────┘               │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

| Field                       | Size          | Description                           |
| --------------------------- | ------------- | ------------------------------------- |
| Preamble                    | 7 bytes       | Synchronization pattern (10101010...) |
| SFD (Start Frame Delimiter) | 1 byte        | Marks frame start (10101011)          |
| Destination MAC             | 6 bytes       | Destination hardware address          |
| Source MAC                  | 6 bytes       | Sender hardware address               |
| EtherType/Length            | 2 bytes       | Protocol type or frame length         |
| Payload                     | 46-1500 bytes | Data from upper layers                |
| FCS (Frame Check Sequence)  | 4 bytes       | CRC-32 checksum                       |

#### EtherType Values

| Value  | Protocol       |
| ------ | -------------- |
| 0x0800 | IPv4           |
| 0x0806 | ARP            |
| 0x86DD | IPv6           |
| 0x8100 | VLAN (802.1Q)  |
| 0x88CC | LLDP           |
| 0x8847 | MPLS (unicast) |

#### 802.1Q VLAN Tag

```
┌──────────────────┬──────────────────┬─────────┬──────────────────┬──────────────────┐
│ Destination MAC  │   Source MAC     │802.1Q   │   EtherType      │     Payload      │
│     6 bytes      │    6 bytes       │ 4 bytes │    2 bytes       │                  │
└──────────────────┴──────────────────┴─────────┴──────────────────┴──────────────────┘
│
┌───────────┴───────────┐
│ TPID │ PCP│DEI│ VID   │
│0x8100│ 3b │1b │ 12b   │
└───────────────────────┘
```

| Field | Size    | Description               |
| ----- | ------- | ------------------------- |
| TPID  | 16 bits | Tag Protocol ID (0x8100)  |
| PCP   | 3 bits  | Priority Code Point (QoS) |
| DEI   | 1 bit   | Drop Eligible Indicator   |
| VID   | 12 bits | VLAN ID (0-4095)          |

---

### Layer 1: Physical Layer

**Purpose**: Physical transmission of raw bits

**What it does to data**:

- Converts frames to electrical, optical, or radio signals
- Handles bit timing and synchronization
- Defines physical media specifications

**Physical Media Types**:

| Media                     | Characteristics                      |
| ------------------------- | ------------------------------------ |
| Twisted Pair (Cat5e/6/6a) | Electrical signals, 100m max, RJ-45  |
| Fiber Optic (Single-mode) | Light, up to 40+ km, low attenuation |
| Fiber Optic (Multi-mode)  | Light, up to 2 km, higher bandwidth  |
| Coaxial                   | Electrical, legacy, cable TV         |
| Wireless (802.11)         | Radio waves, 2.4/5/6 GHz             |

**Encoding Schemes**:

| Scheme                   | Description                        |
| ------------------------ | ---------------------------------- |
| NRZ (Non-Return to Zero) | Simple binary encoding             |
| Manchester               | Transition in middle of each bit   |
| 4B/5B                    | 4 data bits encoded as 5 bits      |
| 8B/10B                   | 8 data bits encoded as 10 bits     |
| PAM-4                    | 4-level pulse amplitude modulation |

---

## TCP/IP Model Comparison

The TCP/IP model is a simplified 4-layer model that maps to the OSI model:

```
┌─────────────────────────────────────────────────────────────────────┐
│              OSI Model vs TCP/IP Model Comparison                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│     OSI Model                          TCP/IP Model                 │
│  ┌─────────────────┐                ┌─────────────────┐            │
│  │  7. Application │                │                 │            │
│  ├─────────────────┤                │   Application   │            │
│  │  6. Presentation│ ───────────▶   │   (HTTP, FTP,   │            │
│  ├─────────────────┤                │    DNS, etc.)   │            │
│  │  5. Session     │                │                 │            │
│  ├─────────────────┤                ├─────────────────┤            │
│  │  4. Transport   │ ───────────▶   │   Transport     │            │
│  │                 │                │   (TCP, UDP)    │            │
│  ├─────────────────┤                ├─────────────────┤            │
│  │  3. Network     │ ───────────▶   │   Internet      │            │
│  │                 │                │   (IP, ICMP)    │            │
│  ├─────────────────┤                ├─────────────────┤            │
│  │  2. Data Link   │                │   Network       │            │
│  ├─────────────────┤ ───────────▶   │   Access        │            │
│  │  1. Physical    │                │   (Ethernet,    │            │
│  │                 │                │    Wi-Fi)       │            │
│  └─────────────────┘                └─────────────────┘            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

| OSI Layer | TCP/IP Layer   | Protocols                 |
| --------- | -------------- | ------------------------- |
| 7, 6, 5   | Application    | HTTP, FTP, DNS, SMTP, SSH |
| 4         | Transport      | TCP, UDP                  |
| 3         | Internet       | IP, ICMP, IGMP, ARP       |
| 2, 1      | Network Access | Ethernet, Wi-Fi, PPP      |

---

## Packet Structure Examples

### Complete HTTP Request Packet

Here's what a complete packet looks like when you request a web page:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                     Complete HTTP GET Request Packet                       │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ETHERNET HEADER (14 bytes)                                                │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ Dst MAC: AA:BB:CC:DD:EE:FF                                           │ │
│  │ Src MAC: 11:22:33:44:55:66                                           │ │
│  │ EtherType: 0x0800 (IPv4)                                             │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  IP HEADER (20 bytes)                                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ Version: 4          IHL: 5              ToS: 0x00                    │ │
│  │ Total Length: 60    ID: 0x1234          Flags: DF                    │ │
│  │ TTL: 64             Protocol: 6 (TCP)   Checksum: 0xABCD             │ │
│  │ Source IP: 192.168.1.100                                             │ │
│  │ Dest IP: 93.184.216.34 (example.com)                                 │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  TCP HEADER (20 bytes)                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ Src Port: 54321     Dst Port: 80                                     │ │
│  │ Seq: 1000           Ack: 0                                           │ │
│  │ Offset: 5           Flags: SYN                                       │ │
│  │ Window: 65535       Checksum: 0x1234                                 │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  HTTP DATA (Variable)                                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ GET / HTTP/1.1                                                       │ │
│  │ Host: example.com                                                    │ │
│  │ User-Agent: Mozilla/5.0                                              │ │
│  │ Accept: text/html                                                    │ │
│  │ Connection: keep-alive                                               │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ETHERNET FCS (4 bytes)                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ CRC-32: 0xDEADBEEF                                                   │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### DNS Query Packet

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          DNS Query Packet                                  │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ETHERNET: Dst MAC | Src MAC | 0x0800                         (14 bytes)  │
│  ├────────────────────────────────────────────────────────────────────────│
│  IP HEADER: v4 | 20 | UDP | Src IP | Dst IP (DNS Server)      (20 bytes)  │
│  ├────────────────────────────────────────────────────────────────────────│
│  UDP HEADER: Src Port: 12345 | Dst Port: 53 | Length | Cksum  (8 bytes)   │
│  ├────────────────────────────────────────────────────────────────────────│
│  DNS QUERY:                                                                │
│  │  Transaction ID: 0x1234                                                │
│  │  Flags: Standard query (0x0100)                                        │
│  │  Questions: 1                                                          │
│  │  Query: www.example.com, Type: A, Class: IN                            │
│  ├────────────────────────────────────────────────────────────────────────│
│  FCS: CRC-32                                                  (4 bytes)   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Inter-Layer Communication

### Service Access Points (SAPs)

Each layer communicates with adjacent layers through Service Access Points:

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Inter-Layer Communication                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Application Layer                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│                     Port Number (SAP)                               │
│                    (e.g., 80, 443, 22)                             │
│                           │                                         │
│                           ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Transport Layer                          │   │
│  │               (TCP Socket / UDP Socket)                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│                    Protocol Number (SAP)                            │
│                    (TCP=6, UDP=17, ICMP=1)                         │
│                           │                                         │
│                           ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     Network Layer                           │   │
│  │                        (IP)                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│                     EtherType (SAP)                                 │
│                    (0x0800=IPv4, 0x86DD=IPv6)                      │
│                           │                                         │
│                           ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Data Link Layer                          │   │
│  │                      (Ethernet)                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│                      Physical Medium                                │
│                           │                                         │
│                           ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Physical Layer                           │   │
│  │              (Electrical/Optical/Radio)                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Multiplexing and Demultiplexing

**Multiplexing (Sending)**: Multiple upper-layer streams share lower-layer services

```
Application Layer:    HTTP        FTP         SSH
│          │           │
Port 80   Port 21    Port 22
│          │           │
└──────────┼───────────┘
│
Transport Layer:              TCP (Protocol 6)
│
│
Network Layer:                  IP Packet
│
│
Data Link:                   Ethernet Frame
```

**Demultiplexing (Receiving)**: Lower layer delivers to correct upper-layer service

```
Ethernet Frame arrives
│
▼
Check EtherType: 0x0800 → IPv4
│
▼
Check Protocol: 6 → TCP
│
▼
Check Dst Port: 80 → HTTP Server
```

---

## Practical Examples

### Example 1: Complete Web Request Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│     User types "http://example.com" in browser                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Step 1: DNS Resolution (if needed)                                 │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │ Application: DNS query for "example.com"                       ││
│  │ Transport:   UDP datagram, Src:12345, Dst:53                   ││
│  │ Network:     IP packet, Src:192.168.1.100, Dst:8.8.8.8         ││
│  │ Data Link:   Ethernet frame to default gateway                 ││
│  │ Physical:    Electrical signals on wire                        ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  Step 2: TCP Three-Way Handshake                                    │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │ Client → Server: SYN (Seq=100)                                 ││
│  │ Server → Client: SYN-ACK (Seq=300, Ack=101)                    ││
│  │ Client → Server: ACK (Seq=101, Ack=301)                        ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  Step 3: HTTP Request                                               │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │ Application: "GET / HTTP/1.1\r\nHost: example.com\r\n..."      ││
│  │ Transport:   TCP segment, Src:54321, Dst:80, Seq=101           ││
│  │ Network:     IP packet to 93.184.216.34                        ││
│  │ Data Link:   Ethernet frames (may traverse multiple switches)  ││
│  │ Physical:    Signals through cables, routers, internet         ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  Step 4: HTTP Response                                              │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │ Application: "HTTP/1.1 200 OK\r\n...<html>...</html>"          ││
│  │ Transport:   Multiple TCP segments (data may be split)         ││
│  │ Network:     IP packets back to client                         ││
│  │ Data Link:   Ethernet frames                                   ││
│  │ Physical:    Signals                                           ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  Step 5: TCP Connection Termination                                 │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │ Client → Server: FIN-ACK                                       ││
│  │ Server → Client: ACK                                           ││
│  │ Server → Client: FIN-ACK                                       ││
│  │ Client → Server: ACK                                           ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Example 2: Packet Journey Through a Network

```
┌─────────────────────────────────────────────────────────────────────┐
│                 Packet Journey: Host A to Host B                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Host A]                                                           │
│  192.168.1.100 ─────┐                                               │
│  MAC: AA:AA:AA      │                                               │
│                     │                                               │
│              ┌──────┴──────┐                                        │
│              │  Switch 1   │                                        │
│              └──────┬──────┘                                        │
│                     │                                               │
│              ┌──────┴──────┐     Frame at Switch:                   │
│              │  Router 1   │     Dst MAC: Router1_MAC               │
│              │ 192.168.1.1 │     Src MAC: AA:AA:AA                  │
│              └──────┬──────┘     IP Dst: 10.0.0.50                  │
│                     │            IP Src: 192.168.1.100              │
│                     │                                               │
│              [Internet]          Router rewrites:                   │
│                     │            - Decrements TTL                   │
│                     │            - New Src MAC: Router2_MAC         │
│                     │            - New Dst MAC: BB:BB:BB            │
│                     │            (IP addresses unchanged)           │
│              ┌──────┴──────┐                                        │
│              │  Router 2   │                                        │
│              │  10.0.0.1   │                                        │
│              └──────┬──────┘                                        │
│                     │                                               │
│              ┌──────┴──────┐                                        │
│              │  Switch 2   │                                        │
│              └──────┬──────┘                                        │
│                     │                                               │
│  [Host B]           │                                               │
│  10.0.0.50  ────────┘                                               │
│  MAC: BB:BB:BB                                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Key Observations:
┌─────────────────────────────────────────────────────────────────────┐
│ 1. MAC addresses change at each hop (Layer 2)                      │
│ 2. IP addresses remain constant end-to-end (Layer 3)               │
│ 3. TTL decrements at each router                                   │
│ 4. Switches forward based on MAC, routers forward based on IP      │
│ 5. ARP is used to resolve IP → MAC at each hop                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Example 3: ARP Resolution Process

When Host A needs to send to Host B on the same subnet:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ARP Resolution                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Host A: "I need to send to 192.168.1.50, but I don't know its MAC"│
│                                                                     │
│  1. ARP Request (Broadcast)                                         │
│     ┌────────────────────────────────────────────────────────────┐ │
│     │ Ethernet:                                                  │ │
│     │   Dst MAC: FF:FF:FF:FF:FF:FF (Broadcast)                   │ │
│     │   Src MAC: AA:AA:AA:AA:AA:AA                               │ │
│     │   EtherType: 0x0806 (ARP)                                  │ │
│     │ ARP:                                                       │ │
│     │   Opcode: 1 (Request)                                      │ │
│     │   Sender MAC: AA:AA:AA:AA:AA:AA                            │ │
│     │   Sender IP: 192.168.1.100                                 │ │
│     │   Target MAC: 00:00:00:00:00:00 (Unknown)                  │ │
│     │   Target IP: 192.168.1.50                                  │ │
│     └────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  2. ARP Reply (Unicast from Host B)                                 │
│     ┌────────────────────────────────────────────────────────────┐ │
│     │ Ethernet:                                                  │ │
│     │   Dst MAC: AA:AA:AA:AA:AA:AA                               │ │
│     │   Src MAC: BB:BB:BB:BB:BB:BB                               │ │
│     │   EtherType: 0x0806 (ARP)                                  │ │
│     │ ARP:                                                       │ │
│     │   Opcode: 2 (Reply)                                        │ │
│     │   Sender MAC: BB:BB:BB:BB:BB:BB                            │ │
│     │   Sender IP: 192.168.1.50                                  │ │
│     │   Target MAC: AA:AA:AA:AA:AA:AA                            │ │
│     │   Target IP: 192.168.1.100                                 │ │
│     └────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  3. Host A updates ARP cache: 192.168.1.50 → BB:BB:BB:BB:BB:BB     │
│                                                                     │
│  4. Host A can now send frames directly to Host B                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Maximum Transmission Unit (MTU) and Fragmentation

### MTU Values by Media Type

| Media Type     | Typical MTU                   |
| -------------- | ----------------------------- |
| Ethernet       | 1500 bytes                    |
| Jumbo Frames   | 9000 bytes                    |
| PPPoE          | 1492 bytes                    |
| VPN/Tunnels    | 1400-1460 bytes               |
| IPv6 Minimum   | 1280 bytes                    |
| Wi-Fi (802.11) | 2304 bytes (but usually 1500) |

### Path MTU Discovery

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Path MTU Discovery Process                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Host A                Router 1               Router 2     Host B   │
│  MTU=1500             MTU=1500               MTU=1400     MTU=1500  │
│                                                                     │
│  1. Host A sends 1500-byte packet with DF (Don't Fragment) bit set  │
│      ──────────────────────────────────────────────▶                │
│                                                                     │
│  2. Router 2 cannot forward (MTU=1400 < 1500)                       │
│      ◀─────────────────────────────────────────────                 │
│      ICMP "Fragmentation Needed" (Type 3, Code 4)                   │
│      Contains: Next-Hop MTU = 1400                                  │
│                                                                     │
│  3. Host A reduces packet size to 1400 bytes                        │
│      ──────────────────────────────────────────────▶   Success!     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Error Handling at Each Layer

### Layer-by-Layer Error Detection

| Layer           | Error Detection Method      | Action on Error          |
| --------------- | --------------------------- | ------------------------ |
| Physical        | Signal quality, bit errors  | Retransmit (if detected) |
| Data Link       | CRC-32 (FCS)                | Drop frame               |
| Network         | IP header checksum          | Drop packet              |
| Transport (TCP) | Checksum + Sequence numbers | Retransmit segment       |
| Transport (UDP) | Checksum (optional)         | Drop datagram            |
| Application     | Application-specific        | Varies                   |

### TCP Error Recovery

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TCP Retransmission Example                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Sender                                              Receiver       │
│    │                                                      │         │
│    │ ─── Segment 1 (Seq=1000, 500 bytes) ──────────────▶ │         │
│    │                                                      │         │
│    │ ◀────────────── ACK 1500 ─────────────────────────── │         │
│    │                                                      │         │
│    │ ─── Segment 2 (Seq=1500, 500 bytes) ────────X        │ (Lost!) │
│    │                                                      │         │
│    │ ─── Segment 3 (Seq=2000, 500 bytes) ──────────────▶ │         │
│    │                                                      │         │
│    │ ◀────────────── ACK 1500 ─────────────────────────── │ (Dup)   │
│    │                                                      │         │
│    │ ─── Segment 4 (Seq=2500, 500 bytes) ──────────────▶ │         │
│    │                                                      │         │
│    │ ◀────────────── ACK 1500 ─────────────────────────── │ (Dup)   │
│    │                                                      │         │
│    │ ◀────────────── ACK 1500 ─────────────────────────── │ (Dup)   │
│    │                                                      │         │
│    │ (3 duplicate ACKs = Fast Retransmit triggered)       │         │
│    │                                                      │         │
│    │ ─── Segment 2 (Seq=1500, 500 bytes) ──────────────▶ │ (Retx)  │
│    │                                                      │         │
│    │ ◀────────────── ACK 3000 ─────────────────────────── │ (All OK)│
│    │                                                      │         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quality of Service (QoS) Markings

### DSCP (Differentiated Services Code Point) - Layer 3

```
┌─────────────────────────────────────────────────────────────────────┐
│                    IP ToS/DSCP Field (8 bits)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌───┬───┬───┬───┬───┬───┬───┬───┐                               │
│   │ D │ S │ C │ P │   │   │ E │ E │                               │
│   │ S │   │   │   │   │   │ C │ C │                               │
│   │ 5 │ 4 │ 3 │ 2 │ 1 │ 0 │ N │ E │                               │
│   └───┴───┴───┴───┴───┴───┴───┴───┘                               │
│   |←─────── DSCP ────────▶|←─ECN─▶|                               │
│          (6 bits)          (2 bits)                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

| DSCP Value | Name                 | Description        |
| ---------- | -------------------- | ------------------ |
| 46 (EF)    | Expedited Forwarding | Low-latency (VoIP) |
| 34 (AF41)  | Assured Forwarding   | Video              |
| 26 (AF31)  | Assured Forwarding   | Streaming          |
| 0 (BE)     | Best Effort          | Default traffic    |

### 802.1p Priority (Layer 2)

| Priority | Traffic Type     |
| -------- | ---------------- |
| 7        | Network Control  |
| 6        | Voice            |
| 5        | Video            |
| 4        | Controlled Load  |
| 3        | Excellent Effort |
| 2        | Spare            |
| 1        | Background       |
| 0        | Best Effort      |

---

## Wireless (802.11) Specifics

### 802.11 Frame vs Ethernet Frame

```
┌─────────────────────────────────────────────────────────────────────┐
│              802.11 Frame Structure (Wireless)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────┬─────────┬───────────────────────────────────┬───────┐ │
│  │ Frame   │Duration │         Address Fields            │ Seq   │ │
│  │ Control │   ID    │  Addr1  │ Addr2 │ Addr3 │ Addr4  │Control│ │
│  │ 2 bytes │ 2 bytes │ 6 bytes │6 bytes│6 bytes│6 bytes │2 bytes│ │
│  └─────────┴─────────┴───────────────────────────────────┴───────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────┬─────────┐│
│  │                      Frame Body                      │   FCS   ││
│  │                    0-2312 bytes                      │ 4 bytes ││
│  └──────────────────────────────────────────────────────┴─────────┘│
│                                                                    │
│  Note: 802.11 has up to 4 address fields (vs 2 in Ethernet)        │
│        because of the infrastructure mode (AP involvement)          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Address Fields Based on To DS / From DS

| To DS | From DS | Addr1 | Addr2 | Addr3 | Addr4 |
| ----- | ------- | ----- | ----- | ----- | ----- |
| 0     | 0       | DA    | SA    | BSSID | N/A   |
| 0     | 1       | DA    | BSSID | SA    | N/A   |
| 1     | 0       | BSSID | SA    | DA    | N/A   |
| 1     | 1       | RA    | TA    | DA    | SA    |

---

## Summary: Encapsulation at a Glance

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Complete Encapsulation Stack                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Application Data:  "Hello, World!"                                 │
│                     ├─────────────────┤                             │
│                                                                     │
│  + TLS/SSL:        [TLS HDR][Encrypted "Hello, World!"]             │
│                    ├────────┼──────────────────────────┤            │
│                                                                     │
│  + TCP:           [TCP HDR][TLS HDR][Encrypted Data]                │
│                   ├────────┼────────┼───────────────────┤           │
│                                                                     │
│  + IP:           [IP HDR][TCP HDR][TLS HDR][Encrypted Data]         │
│                  ├───────┼────────┼────────┼───────────────┤        │
│                                                                     │
│  + Ethernet:    [ETH HDR][IP HDR][TCP HDR][TLS HDR][Data][FCS]      │
│                 ├────────┼───────┼────────┼────────┼──────┼────┤    │
│                                                                     │
│  Physical:      01101001 01010110 11010010 10110101 ...             │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  Header Sizes (typical):                                            │
│  • Ethernet Header:  14 bytes                                       │
│  • IP Header:        20 bytes (without options)                     │
│  • TCP Header:       20 bytes (without options)                     │
│  • UDP Header:       8 bytes                                        │
│  • Ethernet FCS:     4 bytes                                        │
│                                                                     │
│  Overhead for TCP over Ethernet: 14 + 20 + 20 + 4 = 58 bytes       │
│  Maximum TCP payload in 1500-byte MTU: 1500 - 40 = 1460 bytes      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Glossary

| Term           | Definition                                           |
| -------------- | ---------------------------------------------------- |
| Encapsulation  | Adding headers/trailers as data moves down the stack |
| Decapsulation  | Removing headers/trailers as data moves up the stack |
| PDU            | Protocol Data Unit - the data unit at each layer     |
| MTU            | Maximum Transmission Unit - largest packet size      |
| TTL            | Time to Live - hop limit for packets                 |
| FCS            | Frame Check Sequence - CRC checksum at Layer 2       |
| SAP            | Service Access Point - interface between layers      |
| DSCP           | Differentiated Services Code Point - QoS marking     |
| MSS            | Maximum Segment Size - largest TCP payload           |
| Fragmentation  | Splitting packets to fit MTU                         |
| Reassembly     | Combining fragments back to original packet          |
| Multiplexing   | Multiple streams sharing one connection              |
| Demultiplexing | Delivering to correct upper-layer service            |

```

```
