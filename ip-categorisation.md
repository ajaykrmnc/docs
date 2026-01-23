# IP Address Categorisation

## Overview

IP (Internet Protocol) addresses are numerical identifiers assigned to devices on a network. They can be categorized in multiple ways: by version, class, scope, and purpose.

## IPv4 vs IPv6

| Feature | IPv4 | IPv6 |
|---------|------|------|
| Address size | 32 bits | 128 bits |
| Format | Dotted decimal (192.168.1.1) | Hexadecimal colon (2001:0db8::1) |
| Total addresses | ~4.3 billion | ~340 undecillion |
| Header size | 20-60 bytes | 40 bytes (fixed) |
| Checksum | Yes | No (handled by other layers) |
| NAT required | Often yes | Rarely needed |

```
IPv4:  192.168.1.1
       └┬┘ └┬┘ └┬┘ └┬┘
        8   8   8   8  = 32 bits

IPv6:  2001:0db8:85a3:0000:0000:8a2e:0370:7334
       └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ ...
          16      16      16      16   = 128 bits
```

## IPv4 Address Classes (Classful Addressing)

```
┌───────┬─────────────────┬────────────────┬──────────────┬─────────────┐
│ Class │ First Octet     │ Range          │ Default Mask │ Purpose     │
├───────┼─────────────────┼────────────────┼──────────────┼─────────────┤
│   A   │ 0xxxxxxx (1-126)│ 1.0.0.0 -      │ 255.0.0.0    │ Large nets  │
│       │                 │ 126.255.255.255│ /8           │ (16M hosts) │
├───────┼─────────────────┼────────────────┼──────────────┼─────────────┤
│   B   │ 10xxxxxx        │ 128.0.0.0 -    │ 255.255.0.0  │ Medium nets │
│       │ (128-191)       │ 191.255.255.255│ /16          │ (65K hosts) │
├───────┼─────────────────┼────────────────┼──────────────┼─────────────┤
│   C   │ 110xxxxx        │ 192.0.0.0 -    │ 255.255.255.0│ Small nets  │
│       │ (192-223)       │ 223.255.255.255│ /24          │ (254 hosts) │
├───────┼─────────────────┼────────────────┼──────────────┼─────────────┤
│   D   │ 1110xxxx        │ 224.0.0.0 -    │ N/A          │ Multicast   │
│       │ (224-239)       │ 239.255.255.255│              │             │
├───────┼─────────────────┼────────────────┼──────────────┼─────────────┤
│   E   │ 1111xxxx        │ 240.0.0.0 -    │ N/A          │ Reserved/   │
│       │ (240-255)       │ 255.255.255.255│              │ Experimental│
└───────┴─────────────────┴────────────────┴──────────────┴─────────────┘
```

> **Note**: Classful addressing is largely replaced by CIDR (Classless Inter-Domain Routing).

## Public vs Private IP Addresses

### Private IP Ranges (RFC 1918)
These addresses are **not routable** on the public internet:

| Class | Range | CIDR | Addresses |
|-------|-------|------|-----------|
| A | 10.0.0.0 – 10.255.255.255 | 10.0.0.0/8 | 16,777,216 |
| B | 172.16.0.0 – 172.31.255.255 | 172.16.0.0/12 | 1,048,576 |
| C | 192.168.0.0 – 192.168.255.255 | 192.168.0.0/16 | 65,536 |

```
┌─────────────────────────────────────────────────────────────────┐
│                         THE INTERNET                            │
│                    (Public IP Addresses)                        │
│                                                                 │
│         203.0.113.50          198.51.100.25                    │
│              │                      │                           │
└──────────────┼──────────────────────┼───────────────────────────┘
               │                      │
         ┌─────▼─────┐          ┌─────▼─────┐
         │  Router   │          │  Router   │
         │  (NAT)    │          │  (NAT)    │
         └─────┬─────┘          └─────┬─────┘
               │                      │
    ┌──────────┼──────────┐    ┌──────┼──────┐
    │   Private Network   │    │  Private   │
    │   192.168.1.0/24    │    │ 10.0.0.0/8 │
    │  .10  .11  .12 ...  │    │ .1 .2 ...  │
    └─────────────────────┘    └────────────┘
```

## Special Purpose IP Addresses

| Address/Range | Purpose | Description |
|---------------|---------|-------------|
| `0.0.0.0/8` | This network | Represents "any" or "all" addresses |
| `127.0.0.0/8` | Loopback | localhost (127.0.0.1) |
| `169.254.0.0/16` | Link-local | Auto-assigned when DHCP fails (APIPA) |
| `224.0.0.0/4` | Multicast | One-to-many communication |
| `255.255.255.255` | Broadcast | Send to all hosts on local network |
| `100.64.0.0/10` | Carrier-grade NAT | ISP shared address space |
| `192.0.2.0/24` | Documentation | TEST-NET-1 for examples |
| `198.51.100.0/24` | Documentation | TEST-NET-2 for examples |
| `203.0.113.0/24` | Documentation | TEST-NET-3 for examples |

## Unicast, Broadcast, Multicast, Anycast

```
UNICAST (One-to-One)              BROADCAST (One-to-All)
┌────┐      ┌────┐                ┌────┐      ┌────┐
│ A  │─────►│ B  │                │ A  │─────►│ B  │
└────┘      └────┘                └────┘  │   └────┘
                                          │   ┌────┐
                                          ├──►│ C  │
                                          │   └────┘
                                          │   ┌────┐
                                          └──►│ D  │
                                              └────┘

MULTICAST (One-to-Many/Group)     ANYCAST (One-to-Nearest)
┌────┐      ┌────┐                ┌────┐      ┌────┐
│ A  │─────►│ B  │ (subscribed)   │ A  │─────►│ B  │ (nearest)
└────┘  │   └────┘                └────┘      └────┘
        │   ┌────┐                            ┌────┐
        └──►│ C  │ (subscribed)               │ C  │ (same IP, farther)
            └────┘                            └────┘
            ┌────┐
            │ D  │ (not subscribed - ignored)
            └────┘
```

## CIDR Notation (Classless Inter-Domain Routing)

CIDR replaces classful addressing with flexible prefix lengths:

```
192.168.1.0/24
└────┬────┘ └┬┘
  Network   Prefix length (bits for network portion)

/24 = 255.255.255.0 = 256 addresses (254 usable)
/16 = 255.255.0.0   = 65,536 addresses
/8  = 255.0.0.0     = 16,777,216 addresses
```

### Common CIDR Blocks

| CIDR | Subnet Mask | Hosts | Use Case |
|------|-------------|-------|----------|
| /32 | 255.255.255.255 | 1 | Single host |
| /30 | 255.255.255.252 | 2 | Point-to-point links |
| /24 | 255.255.255.0 | 254 | Small office |
| /16 | 255.255.0.0 | 65,534 | Large organization |
| /8 | 255.0.0.0 | 16,777,214 | ISP allocation |

## IPv6 Address Categories

| Type | Prefix | Example | Description |
|------|--------|---------|-------------|
| Global Unicast | 2000::/3 | 2001:db8::1 | Public, routable |
| Link-Local | fe80::/10 | fe80::1 | Single link only |
| Unique Local | fc00::/7 | fd00::1 | Private (like RFC 1918) |
| Multicast | ff00::/8 | ff02::1 | One-to-many |
| Loopback | ::1/128 | ::1 | localhost |
| Unspecified | ::/128 | :: | No address assigned |

## Geographic / Allocation Categories

IP addresses are allocated hierarchically:

```
┌─────────────────────────────────────────────────────────────┐
│                         IANA                                │
│            (Internet Assigned Numbers Authority)            │
└─────────────────────────┬───────────────────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
┌───▼───┐            ┌────▼────┐           ┌────▼────┐
│ ARIN  │            │  RIPE   │           │  APNIC  │
│(N.Am) │            │(Europe) │           │ (Asia)  │
└───┬───┘            └────┬────┘           └────┬────┘
    │                     │                     │
┌───▼───┐            ┌────▼────┐           ┌────▼────┐
│  ISP  │            │   ISP   │           │   ISP   │
└───┬───┘            └─────────┘           └─────────┘
    │
┌───▼───────────┐
│ End User/Org  │
└───────────────┘
```

### Regional Internet Registries (RIRs)

| RIR | Region |
|-----|--------|
| ARIN | North America |
| RIPE NCC | Europe, Middle East, Central Asia |
| APNIC | Asia Pacific |
| LACNIC | Latin America, Caribbean |
| AFRINIC | Africa |

