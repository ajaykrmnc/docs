# Chapter 8: Network Namespaces and Routing

This chapter examines how `sk_buff` integrates with three of the most architecturally
significant subsystems in the Linux networking stack: **network namespaces**, **routing**,
and **netfilter**. Together, these subsystems determine which network stack processes a
packet, where it is delivered, and what transformations it undergoes in transit. Every
field on `sk_buff` discussed here exists because the kernel must carry per-packet metadata
through a pipeline that spans isolation boundaries, routing decisions, firewall rules,
connection tracking, and hardware offload negotiations.

---

## 1. Network Namespaces

### 1.1 What Network Namespaces Are

A network namespace is a complete, isolated copy of the Linux network stack. Each
namespace has its own:

- Routing tables (FIB)
- Firewall rules (iptables / nftables)
- Network interfaces
- Socket hash tables
- ARP / NDP caches
- `/proc/net` and `/sys/class/net` entries
- Netfilter connection tracking tables

The initial namespace (`init_net`) is created at boot. Additional namespaces are created
via `clone(CLONE_NEWNET)`, `unshare(CLONE_NEWNET)`, or the `ip netns add` command.

```
 ┌──────────────────────────────────────────────────────────┐
 │                      Host Kernel                         │
 │                                                          │
 │  ┌────────────────────┐    ┌────────────────────┐        │
 │  │   init_net (NS 0)  │    │   netns "red"      │        │
 │  │                    │    │                    │        │
 │  │  eth0  10.0.0.1    │    │  eth0  192.168.1.1 │        │
 │  │  lo    127.0.0.1   │    │  lo    127.0.0.1   │        │
 │  │  iptables rules A  │    │  iptables rules B  │        │
 │  │  routing table A   │    │  routing table B   │        │
 │  │  conntrack table A │    │  conntrack table B  │        │
 │  └────────────────────┘    └────────────────────┘        │
 └──────────────────────────────────────────────────────────┘
```

From the perspective of processes within a namespace, the network stack appears to be
the only one on the machine. This is the foundation of container networking.

### 1.2 `struct net` --- The Namespace Structure

Every network namespace is represented by a `struct net` instance, defined in
`include/net/net_namespace.h`:

```c
struct net {
    refcount_t              passive;        /* reference count                */
    spinlock_t              rules_mod_lock; /* FIB rule modification lock     */
    unsigned int            hash_mix;       /* hash randomization seed        */

    struct net_device       *loopback_dev;  /* per-ns loopback device         */
    struct list_head        dev_base_head;  /* list of all devices in this ns */
    struct hlist_head       *dev_name_head; /* device hash by name            */
    struct hlist_head       *dev_index_head;/* device hash by ifindex         */

    /* Per-namespace subsystem state */
    struct netns_ipv4       ipv4;           /* IPv4-specific: FIB, routes     */
    struct netns_ipv6       ipv6;           /* IPv6-specific: FIB, routes     */
    struct netns_nf         nf;             /* netfilter state                */
    struct netns_ct         ct;             /* conntrack state                */
    struct netns_nftables   nft;            /* nftables state                 */
    struct netns_xt         xt;             /* xtables (iptables) state       */

    struct net_generic      *gen;           /* extensible per-ns storage      */
    struct sock             *diag_nlsk;     /* netlink diagnostics socket     */

    /* ... many more fields ... */
};
```

The `init_net` global variable is the default namespace. All other namespaces are
allocated dynamically via `copy_net_ns()` during `clone()` or `unshare()`.

### 1.3 `skb->dev->nd_net` --- How sk_buff Knows Its Namespace

An `sk_buff` does not carry a direct pointer to its network namespace. Instead, the
namespace is derived from the network device associated with the packet:

```c
/* net/core/dev.c — simplified */
static inline struct net *dev_net(const struct net_device *dev)
{
    return read_pnet(&dev->nd_net);         /* returns the namespace pointer  */
}
```

Thus, given an `sk_buff *skb`, the namespace is obtained as:

```c
struct net *ns = dev_net(skb->dev);
```

This design has a critical implication: when a packet crosses a namespace boundary
(e.g., via a veth pair), `skb->dev` is updated to the receiving device, and
`dev_net(skb->dev)` automatically returns the new namespace. No explicit namespace
field on `sk_buff` needs to be modified.

```
 ┌─────────────────────────────────────────────────────┐
 │  sk_buff                                            │
 │  ┌──────────┐     ┌───────────────┐     ┌────────┐ │
 │  │ skb->dev ├────►│ net_device    │     │ struct │ │
 │  └──────────┘     │               │     │  net   │ │
 │                   │ nd_net ───────┼────►│        │ │
 │                   └───────────────┘     └────────┘ │
 └─────────────────────────────────────────────────────┘
```

### 1.4 Namespace-Aware Socket Lookup

When a packet arrives on a device, the kernel must find the socket that should receive
it. This lookup is always scoped to the namespace of the receiving device:

```c
/* net/ipv4/inet_hashtables.c — simplified */
struct sock *__inet_lookup(struct net *net,
                           struct inet_hashinfo *hashinfo,
                           struct sk_buff *skb, int doff,
                           const __be32 saddr, const __be16 sport,
                           const __be32 daddr, const __be16 dport,
                           const int dif, const int sdif,
                           bool *refcounted)
{
    /* First: try established connection hash table */
    struct sock *sk = __inet_lookup_established(net, hashinfo,
                          saddr, sport, daddr, dport, dif, sdif);
    if (sk)
        return sk;

    /* Second: try listening socket hash table */
    return __inet_lookup_listener(net, hashinfo, skb, doff,
                          saddr, sport, daddr, dport, dif, sdif);
}
```

The `net` parameter ensures that a socket in namespace A will never be matched to a
packet arriving on a device in namespace B, even if the IP addresses and ports are
identical.

### 1.5 veth Pairs for Cross-Namespace Communication

A **veth** (virtual Ethernet) pair creates two linked virtual interfaces. Each end
can be placed in a different namespace. Frames transmitted on one end are received on
the other:

```c
/* drivers/net/veth.c — simplified TX path */
static netdev_tx_t veth_xmit(struct sk_buff *skb, struct net_device *dev)
{
    struct veth_priv *priv = netdev_priv(dev);
    struct net_device *rcv  = rcu_dereference(priv->peer); /* peer device   */

    if (likely(rcv)) {
        skb->dev = rcv;                /* point skb at receiving device      */
        /* dev_net(skb->dev) now returns the PEER's namespace               */

        if (likely(dev_forward_skb(rcv, skb) == NET_RX_SUCCESS)) {
            /* packet enters the RX path of the peer namespace              */
        }
    }
    return NETDEV_TX_OK;
}
```

The function `dev_forward_skb()` re-enters the packet into the network stack as if
it had just arrived from hardware, but in the peer device's namespace.

### 1.6 Diagram: Two Namespaces Connected via veth Pair

```
 ┌──────────────────────────┐          ┌──────────────────────────┐
 │   Namespace: "blue"      │          │   Namespace: "green"     │
 │                          │          │                          │
 │  ┌─────────────────┐     │          │     ┌─────────────────┐  │
 │  │  Application    │     │          │     │  Application    │  │
 │  │  (10.0.1.1:80)  │     │          │     │  (10.0.2.1:80)  │  │
 │  └────────┬────────┘     │          │     └────────┬────────┘  │
 │           │ socket       │          │              │ socket    │
 │  ┌────────▼────────┐     │          │     ┌────────▼────────┐  │
 │  │  TCP/IP Stack   │     │          │     │  TCP/IP Stack   │  │
 │  │  (routing, nf)  │     │          │     │  (routing, nf)  │  │
 │  └────────┬────────┘     │          │     └────────┬────────┘  │
 │           │              │          │              │           │
 │  ┌────────▼────────┐     │          │     ┌────────▼────────┐  │
 │  │  veth-blue      │     │          │     │  veth-green     │  │
 │  │  10.0.1.1/24    │◄────┼──────────┼────►│  10.0.2.1/24   │  │
 │  └─────────────────┘     │  linked  │     └─────────────────┘  │
 │                          │          │                          │
 └──────────────────────────┘          └──────────────────────────┘

 When veth-blue transmits a frame:
   1. skb->dev = veth-green           (peer device)
   2. dev_net(skb->dev) = ns "green"  (namespace changes)
   3. Frame enters RX path of "green" namespace
   4. Socket lookup scoped to "green" namespace
```

### 1.7 Namespace Lifecycle and sk_buff Safety

When a namespace is being destroyed, all devices in that namespace are moved back to
`init_net` or removed. Any in-flight `sk_buff` structures referencing those devices
are safe because:

1. The `sk_buff` holds an implicit reference to the device via `skb->dev`.
2. `net_device` structures are freed only after all references are released.
3. The namespace itself is reference-counted (`refcount_t passive`).

```c
/* Incrementing namespace reference */
static inline struct net *get_net(struct net *net)
{
    refcount_inc(&net->ns.count);
    return net;
}

/* Decrementing namespace reference */
static inline void put_net(struct net *net)
{
    if (refcount_dec_and_test(&net->ns.count))
        __put_net(net);             /* schedule cleanup work                */
}
```

---

## 2. sk_buff and Socket Association

### 2.1 `skb->sk` --- Pointer to the Owning Socket

The `sk` field of `sk_buff` is a pointer to the `struct sock` that owns or is
associated with the packet:

```c
struct sk_buff {
    /* ... */
    struct sock     *sk;            /* owning socket, or NULL               */
    /* ... */
};
```

This pointer serves multiple purposes:

| Purpose                  | Description                                        |
|--------------------------|----------------------------------------------------|
| Memory accounting        | Charged against `sk->sk_wmem_alloc` (TX) or        |
|                          | `sk->sk_rmem_alloc` (RX)                           |
| Socket option lookup     | TOS, TTL, mark, priority inherit from socket       |
| Output routing           | Uses socket's cached route (`sk->sk_dst_cache`)    |
| Netfilter owner match    | `xt_owner` module checks `skb->sk->sk_uid`         |
| Congestion control       | TCP congestion state is per-socket                 |

### 2.2 When skb->sk Is Set vs. NULL

The value of `skb->sk` depends on the packet's current position in the stack:

```
 ┌─────────────────────────────────────────────────────────────────┐
 │                    TRANSMIT (TX) PATH                           │
 │                                                                 │
 │  Application calls send()/write()                               │
 │       │                                                         │
 │       ▼                                                         │
 │  tcp_sendmsg() / udp_sendmsg()                                  │
 │       │  skb->sk = sk;          ◄── set immediately             │
 │       ▼                                                         │
 │  ip_queue_xmit() / ip_push_pending_frames()                     │
 │       │  skb->sk still set      ◄── used for routing, options   │
 │       ▼                                                         │
 │  dev_queue_xmit()                                                │
 │       │  skb->sk still set      ◄── used for memory accounting  │
 │       ▼                                                         │
 │  Driver TX                                                       │
 │       │  skb_orphan(skb);       ◄── sk set to NULL, wmem freed  │
 │       ▼                                                         │
 │  Hardware                                                        │
 └─────────────────────────────────────────────────────────────────┘

 ┌─────────────────────────────────────────────────────────────────┐
 │                    RECEIVE (RX) PATH                            │
 │                                                                 │
 │  Hardware / NAPI poll                                            │
 │       │  skb->sk = NULL;        ◄── no socket known yet         │
 │       ▼                                                         │
 │  ip_rcv() → NF_INET_PRE_ROUTING                                 │
 │       │  skb->sk = NULL;        ◄── still NULL                  │
 │       ▼                                                         │
 │  ip_route_input() → routing decision                             │
 │       │                                                         │
 │       ▼                                                         │
 │  ip_local_deliver() → NF_INET_LOCAL_IN                           │
 │       │                                                         │
 │       ▼                                                         │
 │  tcp_v4_rcv() / udp_rcv()                                        │
 │       │  sk = __inet_lookup();  ◄── socket lookup performed     │
 │       │  skb->sk = sk;          ◄── set after lookup            │
 │       ▼                                                         │
 │  tcp_rcv_established() / __udp_enqueue_schedule_skb()            │
 │       │  skb added to sk->sk_receive_queue                       │
 │       ▼                                                         │
 │  Application calls recv()/read()                                 │
 └─────────────────────────────────────────────────────────────────┘
```

### 2.3 Socket Lookup Functions

The kernel provides a hierarchy of lookup functions, each increasingly specific:

```c
/* Full lookup: try established first, then listeners */
struct sock *__inet_lookup(struct net *net,
                           struct inet_hashinfo *hashinfo,
                           struct sk_buff *skb, int doff,
                           __be32 saddr, __be16 sport,
                           __be32 daddr, __be16 dport,
                           int dif, int sdif,
                           bool *refcounted);

/* Established connections only (exact 5-tuple match) */
struct sock *__inet_lookup_established(struct net *net,
                           struct inet_hashinfo *hashinfo,
                           __be32 saddr, __be16 sport,
                           __be32 daddr, __be16 dport,
                           int dif, int sdif);

/* Listening sockets only (match on local addr:port) */
struct sock *__inet_lookup_listener(struct net *net,
                           struct inet_hashinfo *hashinfo,
                           struct sk_buff *skb, int doff,
                           __be32 saddr, __be16 sport,
                           __be32 daddr, __be16 dport,
                           int dif, int sdif);
```

The lookup uses a hash table indexed by the 5-tuple `(saddr, sport, daddr, dport,
protocol)`. For established connections, the hash is computed over all five fields.
For listeners, only the local address and port are used.

### 2.4 Socket Types: `sk_fullsock()`, `sk_listener()`, `mini_sock()`

During connection establishment, the kernel uses lightweight socket representations
to minimize memory consumption:

```c
/* Check if sk is a full socket (not a request socket or timewait) */
static inline bool sk_fullsock(const struct sock *sk)
{
    return (1 << sk->sk_state) & ~(TCPF_TIME_WAIT | TCPF_NEW_SYN_RECV);
}

/* Check if sk is a listening socket */
static inline bool sk_listener(const struct sock *sk)
{
    return (1 << sk->sk_state) & (TCPF_LISTEN);
}
```

The socket lifecycle during TCP connection establishment:

```
 ┌──────────────────────────────────────────────────────────────┐
 │  SYN arrives                                                 │
 │       │                                                      │
 │       ▼                                                      │
 │  Lookup finds listening socket (sk_listener = true)          │
 │       │                                                      │
 │       ▼                                                      │
 │  Create request_sock (mini socket)                           │
 │  ┌─────────────────────────────────────┐                     │
 │  │  struct request_sock                │                     │
 │  │    rsk_listener  → listening sock   │                     │
 │  │    ir_rmt_addr   = client IP        │                     │
 │  │    ir_loc_addr   = server IP        │                     │
 │  │    ir_rmt_port   = client port      │                     │
 │  │    ir_num        = server port      │                     │
 │  └─────────────────────────────────────┘                     │
 │       │                                                      │
 │       ▼  (SYN-ACK sent, ACK received)                        │
 │                                                              │
 │  Create full struct sock (sk_fullsock = true)                │
 │  Move from SYN_RECV → ESTABLISHED                            │
 │  Hash into established table                                 │
 │  Free request_sock                                           │
 └──────────────────────────────────────────────────────────────┘
```

### 2.5 Connection Tracking and the 5-Tuple

The 5-tuple `(protocol, src_ip, src_port, dst_ip, dst_port)` is the fundamental
identifier for both socket lookup and connection tracking. However, these two systems
operate independently:

| Aspect             | Socket Lookup                  | Connection Tracking (conntrack)  |
|--------------------|--------------------------------|----------------------------------|
| Scope              | Per-namespace socket tables    | Per-namespace conntrack table    |
| Key                | 5-tuple                        | 5-tuple (+ zone)                |
| Stored on skb      | `skb->sk`                      | `skb->_nfct`                    |
| Set when           | Transport layer RX             | PREROUTING / OUTPUT hooks       |
| Purpose            | Deliver to application         | Stateful firewalling, NAT       |

---

## 3. sk_buff and Device Association

### 3.1 `skb->dev` --- The Network Device

The `dev` field points to the `struct net_device` currently associated with the packet:

```c
struct sk_buff {
    /* ... */
    struct net_device   *dev;       /* device this skb is associated with   */
    /* ... */
};
```

The meaning of `skb->dev` changes depending on context:

| Context                | `skb->dev` points to                              |
|------------------------|----------------------------------------------------|
| RX: after driver       | Input device (the NIC that received the frame)     |
| RX: after routing      | Still input device                                  |
| Forwarding: after FIB  | Output device (determined by route lookup)         |
| TX: from socket        | Output device (determined by route lookup)         |
| TX: in driver          | Output device (the NIC that will transmit)         |

### 3.2 Changes During Forwarding

When the routing subsystem determines that a packet should be forwarded (not delivered
locally), `skb->dev` is changed from the input device to the output device:

```c
/* net/ipv4/ip_forward.c — simplified */
int ip_forward(struct sk_buff *skb)
{
    struct iphdr *iph = ip_hdr(skb);
    struct rtable *rt = skb_rtable(skb);    /* routing decision from FIB    */

    /* Decrement TTL */
    ip_decrease_ttl(iph);

    /* skb->dev was the INPUT device; now change to OUTPUT device */
    skb->dev = rt->dst.dev;                 /* output device from route     */

    /* Traverse NF_INET_FORWARD hook */
    return NF_HOOK(NFPROTO_IPV4, NF_INET_FORWARD,
                   dev_net(skb->dev), NULL, skb, skb->dev,
                   rt->dst.dev, ip_forward_finish);
}
```

### 3.3 `skb->skb_iif` --- Input Interface Index

Because `skb->dev` is overwritten during forwarding, the kernel preserves the original
input interface index in a separate field:

```c
struct sk_buff {
    /* ... */
    int             skb_iif;        /* input interface index (ifindex)      */
    /* ... */
};
```

This field is set early in the receive path:

```c
/* net/core/dev.c — __netif_receive_skb_core() simplified */
static int __netif_receive_skb_core(struct sk_buff **pskb, bool pfmemalloc,
                                     struct packet_type **ppt_prev)
{
    struct sk_buff *skb = *pskb;

    skb->skb_iif = skb->dev->ifindex;      /* save input ifindex           */

    /* ... protocol dispatch ... */
}
```

Netfilter uses `skb_iif` to match on the original input interface even after
`skb->dev` has been changed to the output device.

### 3.4 Virtual Devices: Bridge Ports, VLAN, Bonding, Team

Virtual network devices add layers of indirection. As a packet traverses these
devices, `skb->dev` is updated at each layer:

```
 ┌─────────────────────────────────────────────────────────┐
 │  Physical NIC receives frame                             │
 │  skb->dev = eth0                                         │
 │       │                                                  │
 │       ▼                                                  │
 │  Bond/Team device (if eth0 is a slave)                   │
 │  skb->dev = bond0                                        │
 │       │                                                  │
 │       ▼                                                  │
 │  VLAN device (if tagged frame, VLAN ID match)            │
 │  skb->dev = bond0.100                                    │
 │       │                                                  │
 │       ▼                                                  │
 │  Bridge device (if bond0.100 is a bridge port)           │
 │  skb->dev = br0                                          │
 │       │                                                  │
 │       ▼                                                  │
 │  IP stack receives packet with skb->dev = br0            │
 │  Namespace = dev_net(br0)                                │
 └─────────────────────────────────────────────────────────┘
```

Each virtual device type implements its own `rx_handler` that is registered via
`netdev_rx_handler_register()`. The handler may consume the skb, redirect it, or
pass it up:

```c
/* net/bridge/br_input.c — simplified */
rx_handler_result_t br_handle_frame(struct sk_buff **pskb)
{
    struct sk_buff *skb = *pskb;
    struct net_bridge_port *p = br_port_get_rcu(skb->dev);

    /* skb->dev is the physical port (e.g., eth0) */
    /* Bridge logic decides: forward, flood, or deliver locally */

    if (should_deliver_locally) {
        skb->dev = p->br->dev;      /* change to bridge device (br0)       */
        return RX_HANDLER_ANOTHER;   /* re-enter __netif_receive_skb        */
    }
    /* ... */
}
```

---

## 4. Routing and Destination Cache

### 4.1 `skb->_skb_refdst` --- Cached Routing Decision

Every IP packet that enters or leaves the stack must have a routing decision. This
decision is cached on the `sk_buff` in the `_skb_refdst` field:

```c
struct sk_buff {
    /* ... */
    unsigned long       _skb_refdst;    /* destination cache entry          */
    /* ... */
};
```

The low bit of `_skb_refdst` encodes whether the reference is counted:

```c
#define SKB_DST_NOREF   1UL             /* dst is not reference-counted     */

static inline struct dst_entry *skb_dst(const struct sk_buff *skb)
{
    /* Mask off the low bit to get the pointer */
    return (struct dst_entry *)(skb->_skb_refdst & SKB_DST_PTRMASK);
}
```

### 4.2 `struct dst_entry` --- The Route Cache Entry

The `dst_entry` structure encapsulates a complete routing decision:

```c
struct dst_entry {
    struct net_device       *dev;           /* output device                 */
    struct dst_ops          *ops;           /* protocol-specific operations  */
    unsigned long           _metrics;       /* route metrics (MTU, etc.)     */
    unsigned long           expires;        /* cache expiration time         */

    int                     (*input)(struct sk_buff *skb);   /* RX handler  */
    int                     (*output)(struct net *net,
                                      struct sock *sk,
                                      struct sk_buff *skb);  /* TX handler  */

    unsigned short          flags;          /* DST_HOST, DST_NOXFRM, ...    */
    short                   error;          /* routing error code            */
    short                   obsolete;       /* cache validity state          */

    struct fib_info         *fi;            /* FIB information               */

    /* ... */
};
```

The `input` and `output` function pointers determine what happens to the packet:

| Route type     | `input`                | `output`               |
|----------------|------------------------|------------------------|
| Local delivery | `ip_local_deliver`     | N/A                    |
| Forwarding     | `ip_forward`           | `ip_output`            |
| Local TX       | N/A                    | `ip_output`            |
| Unreachable    | `ip_error`             | `ip_error`             |
| Blackhole      | `dst_discard`          | `dst_discard`          |

### 4.3 `skb_dst()` and `skb_dst_set()`

These accessor functions manage the routing cache on `sk_buff`:

```c
/* Get the dst_entry from an skb */
static inline struct dst_entry *skb_dst(const struct sk_buff *skb)
{
    /* WARN if accessed without being set */
    WARN_ON(!(skb->_skb_refdst & SKB_DST_PTRMASK));
    return (struct dst_entry *)(skb->_skb_refdst & SKB_DST_PTRMASK);
}

/* Set the dst_entry on an skb (takes a reference) */
static inline void skb_dst_set(struct sk_buff *skb, struct dst_entry *dst)
{
    skb->_skb_refdst = (unsigned long)dst;
}

/* Set without taking a reference (caller guarantees lifetime) */
static inline void skb_dst_set_noref(struct sk_buff *skb,
                                      struct dst_entry *dst)
{
    skb->_skb_refdst = (unsigned long)dst | SKB_DST_NOREF;
}

/* Drop the dst_entry reference */
static inline void skb_dst_drop(struct sk_buff *skb)
{
    if (!(skb->_skb_refdst & SKB_DST_NOREF))
        dst_release(skb_dst(skb));
    skb->_skb_refdst = 0UL;
}
```

### 4.4 `ip_route_input()` --- RX Routing Lookup

For incoming packets, `ip_route_input()` performs the FIB lookup and attaches the
result to the skb:

```c
/* net/ipv4/route.c — simplified */
int ip_route_input_noref(struct sk_buff *skb,
                          __be32 daddr, __be32 saddr,
                          u8 tos,
                          struct net_device *dev)
{
    struct net *net = dev_net(dev);
    struct fib_result res;
    struct rtable *rth;
    int err;

    /* Step 1: Check for multicast/broadcast */
    if (ipv4_is_multicast(daddr))
        return ip_route_input_mc(skb, daddr, saddr, tos, dev);

    /* Step 2: FIB lookup */
    err = fib_lookup(net, &fl4, &res, 0);
    if (err)
        return err;

    /* Step 3: Based on FIB result, create appropriate dst_entry */
    switch (res.type) {
    case RTN_LOCAL:
        rth = rt_dst_alloc(net->loopback_dev, tos,
                           res.fi, /* ... */);
        rth->dst.input = ip_local_deliver;  /* deliver to local socket     */
        break;

    case RTN_UNICAST:
        rth = rt_dst_alloc(res.fi->fib_dev, tos,
                           res.fi, /* ... */);
        rth->dst.input = ip_forward;        /* forward to another host     */
        break;

    case RTN_UNREACHABLE:
        rth->dst.input = ip_error;          /* send ICMP unreachable       */
        break;
    }

    /* Step 4: Attach route to skb */
    skb_dst_set_noref(skb, &rth->dst);

    return 0;
}
```

### 4.5 `ip_route_output_flow()` --- TX Routing Lookup

For locally generated packets, `ip_route_output_flow()` determines the output path:

```c
/* net/ipv4/route.c — simplified */
struct rtable *ip_route_output_flow(struct net *net,
                                     struct flowi4 *flp4,
                                     const struct sock *sk)
{
    struct rtable *rt;

    /* Step 1: FIB lookup for output route */
    rt = __ip_route_output_key(net, flp4);
    if (IS_ERR(rt))
        return rt;

    /* Step 2: Apply XFRM (IPsec) policy if needed */
    if (flp4->flowi4_proto)
        rt = (struct rtable *)xfrm_lookup_route(net, &rt->dst, flp4, sk, 0);

    return rt;
}
```

The caller then attaches the result to the skb:

```c
/* Example: TCP output path */
struct rtable *rt = ip_route_output_flow(net, &fl4, sk);
skb_dst_set(skb, &rt->dst);
skb->dev = rt->dst.dev;            /* set output device from route         */
```

### 4.6 FIB Lookup Process

The Forwarding Information Base (FIB) is the kernel's routing table. A lookup traverses
the following structures:

```
 ┌────────────────────────────────────────────────────────────────┐
 │  FIB Lookup Process                                            │
 │                                                                │
 │  ┌──────────────────┐                                          │
 │  │  fib_lookup()    │                                          │
 │  └────────┬─────────┘                                          │
 │           │                                                    │
 │           ▼                                                    │
 │  ┌──────────────────┐     ┌──────────────────┐                 │
 │  │  FIB Rules       │     │  ip rule list:   │                 │
 │  │  (policy routing)│────►│  0:  lookup local│                 │
 │  │                  │     │  32766: lookup    │                 │
 │  │                  │     │        main       │                 │
 │  │                  │     │  32767: lookup    │                 │
 │  │                  │     │        default    │                 │
 │  └────────┬─────────┘     └──────────────────┘                 │
 │           │                                                    │
 │           ▼  (for each matching rule)                          │
 │  ┌──────────────────┐                                          │
 │  │  fib_table       │     Uses LC-Trie (Level Compressed       │
 │  │  _lookup()       │     Trie) for O(log n) prefix matching   │
 │  └────────┬─────────┘                                          │
 │           │                                                    │
 │           ▼                                                    │
 │  ┌──────────────────┐                                          │
 │  │  fib_result      │     Contains:                            │
 │  │                  │     - type: RTN_LOCAL, RTN_UNICAST, ...  │
 │  │                  │     - fi: fib_info (next hop, device)    │
 │  │                  │     - prefixlen: matched prefix length   │
 │  └──────────────────┘                                          │
 └────────────────────────────────────────────────────────────────┘
```

### 4.7 Routing Decision Flowchart

```
 ┌─────────────────────────────────────────────────────────────────┐
 │                    Routing Decision Flowchart                    │
 └─────────────────────────────────────────────────────────────────┘

                      Packet arrives on NIC
                              │
                              ▼
                    ┌───────────────────┐
                    │  eth_type_trans() │
                    │  Set skb->protocol│
                    │  Set skb->pkt_type│
                    └────────┬──────────┘
                             │
                             ▼
                    ┌───────────────────┐
                    │  ip_rcv()         │
                    │  Basic IP checks  │
                    └────────┬──────────┘
                             │
                             ▼
                    ┌───────────────────┐
                    │  NF_INET_        │
                    │  PRE_ROUTING     │
                    └────────┬──────────┘
                             │
                             ▼
                    ┌───────────────────┐
                    │  ip_route_input() │
                    │  FIB lookup       │
                    └────────┬──────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
               ┌────▼─────┐    ┌─────▼──────┐
               │ RTN_LOCAL │    │RTN_UNICAST │
               │           │    │            │
               │ dst.input │    │ dst.input  │
               │ = ip_local│    │ = ip_      │
               │ _deliver  │    │   forward  │
               └────┬──────┘    └─────┬──────┘
                    │                 │
                    ▼                 ▼
           ┌──────────────┐  ┌──────────────┐     ┌──────────────┐
           │NF_INET_      │  │ TTL check    │     │ RTN_         │
           │LOCAL_IN      │  │ TTL-- == 0?  │     │ UNREACHABLE  │
           └──────┬───────┘  └──────┬───────┘     └──────┬───────┘
                  │                 │                     │
                  ▼            ┌────┴────┐               ▼
           ┌──────────────┐   │         │        ┌──────────────┐
           │ Transport    │   ▼         ▼        │ ICMP         │
           │ layer (TCP,  │  Yes       No        │ Unreachable  │
           │ UDP, etc.)   │   │         │        └──────────────┘
           └──────────────┘   │    ┌────▼─────┐
                              │    │NF_INET_  │
                    ┌─────────▼┐   │FORWARD   │
                    │ICMP Time │   └────┬─────┘
                    │Exceeded  │        │
                    └──────────┘        ▼
                                 ┌──────────────┐
                                 │NF_INET_      │
                                 │POST_ROUTING  │
                                 └──────┬───────┘
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │ dev_queue_   │
                                 │ xmit()       │
                                 └──────────────┘
```

---

## 5. Netfilter Hooks and sk_buff

### 5.1 The Five Netfilter Hook Points

Netfilter defines five hook points in the IPv4 packet path. Every IP packet traverses
exactly two or three of these hooks:

```
 ┌──────────────────────────────────────────────────────────────────┐
 │                  Netfilter Hook Points (IPv4)                    │
 │                                                                  │
 │                                                                  │
 │     Incoming                                                     │
 │     Packet ──────────►┌──────────────────┐                       │
 │                       │  NF_INET_        │  Hook 0               │
 │                       │  PRE_ROUTING     │  (conntrack, DNAT,    │
 │                       │                  │   mangle, raw)        │
 │                       └────────┬─────────┘                       │
 │                                │                                 │
 │                         Routing Decision                         │
 │                       ┌────────┴────────┐                        │
 │                       │                 │                        │
 │                  For local?        For forwarding?               │
 │                       │                 │                        │
 │              ┌────────▼───────┐  ┌──────▼──────────┐             │
 │              │  NF_INET_     │  │  NF_INET_       │             │
 │              │  LOCAL_IN     │  │  FORWARD        │  Hook 2     │
 │              │               │  │                 │             │
 │              │  Hook 1       │  │  (filter,       │             │
 │              │  (filter,     │  │   mangle,       │             │
 │              │   mangle,     │  │   security)     │             │
 │              │   security,   │  │                 │             │
 │              │   conntrack)  │  └──────┬──────────┘             │
 │              └────────┬──────┘         │                        │
 │                       │                │                        │
 │              ┌────────▼──────┐         │                        │
 │              │  Local        │         │                        │
 │              │  Process      │         │                        │
 │              └────────┬──────┘         │                        │
 │                       │                │                        │
 │              ┌────────▼───────┐        │                        │
 │              │  NF_INET_     │        │                        │
 │              │  LOCAL_OUT    │        │                        │
 │              │               │        │                        │
 │              │  Hook 3       │        │                        │
 │              │  (filter,     │        │                        │
 │              │   mangle,     │        │                        │
 │              │   DNAT, raw,  │        │                        │
 │              │   security,   │        │                        │
 │              │   conntrack)  │        │                        │
 │              └────────┬──────┘        │                        │
 │                       │               │                        │
 │                       └───────┬───────┘                        │
 │                               │                                │
 │                      ┌────────▼────────┐                       │
 │                      │  NF_INET_      │  Hook 4               │
 │                      │  POST_ROUTING  │  (SNAT, mangle,       │
 │                      │               │   conntrack-confirm)   │
 │                      └────────┬───────┘                       │
 │                               │                                │
 │                               ▼                                │
 │                        Outgoing Packet                          │
 └──────────────────────────────────────────────────────────────────┘
```

The five hooks, enumerated in `include/uapi/linux/netfilter.h`:

```c
enum nf_inet_hooks {
    NF_INET_PRE_ROUTING  = 0,  /* After NIC, before routing decision       */
    NF_INET_LOCAL_IN     = 1,  /* After routing, destined for local socket  */
    NF_INET_FORWARD      = 2,  /* After routing, being forwarded            */
    NF_INET_LOCAL_OUT    = 3,  /* Locally generated, before routing         */
    NF_INET_POST_ROUTING = 4,  /* After routing, about to leave the host   */
    NF_INET_NUMHOOKS     = 5
};
```

### 5.2 Packet Paths Through Hooks

Different packet types traverse different combinations of hooks:

| Packet type         | Hooks traversed                                     |
|---------------------|-----------------------------------------------------|
| Received locally    | PRE_ROUTING -> LOCAL_IN                             |
| Forwarded           | PRE_ROUTING -> FORWARD -> POST_ROUTING              |
| Locally generated   | LOCAL_OUT -> POST_ROUTING                           |
| Locally generated   |                                                     |
|   and forwarded     | LOCAL_OUT -> POST_ROUTING (same path as generated)  |

### 5.3 Hook Function Signature

Every netfilter hook callback conforms to the `nf_hookfn` type:

```c
/* include/linux/netfilter.h */
typedef unsigned int nf_hookfn(void *priv,
                                struct sk_buff *skb,
                                const struct nf_hook_state *state);
```

The `nf_hook_state` provides context about where the hook is being invoked:

```c
struct nf_hook_state {
    unsigned int        hook;       /* which hook (NF_INET_PRE_ROUTING, ..) */
    u_int8_t            pf;         /* protocol family (NFPROTO_IPV4, ...)  */
    struct net_device   *in;        /* input device (may be NULL)           */
    struct net_device   *out;       /* output device (may be NULL)          */
    struct sock         *sk;        /* socket (may be NULL)                 */
    struct net          *net;       /* network namespace                    */
    int                 (*okfn)(struct net *, struct sock *,
                                struct sk_buff *);  /* continuation func   */
};
```

### 5.4 Hook Return Values

```c
/* include/uapi/linux/netfilter.h */
#define NF_DROP     0   /* Discard the packet                               */
#define NF_ACCEPT   1   /* Continue traversal; packet passes this hook      */
#define NF_STOLEN   2   /* Hook took ownership; do NOT free or continue     */
#define NF_QUEUE    3   /* Queue packet to userspace (via NFQUEUE)          */
#define NF_REPEAT   4   /* Call this hook function again                    */
#define NF_STOP     5   /* Accept and skip remaining hooks at this point    */
```

The semantics of each return value:

```
 ┌──────────────────────────────────────────────────────────────┐
 │  Hook returns NF_ACCEPT                                      │
 │  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────────┐            │
 │  │Hook 1├───►│Hook 2├───►│Hook 3├───►│ Continue │            │
 │  │ACCEPT│    │ACCEPT│    │ACCEPT│    │ to okfn  │            │
 │  └──────┘    └──────┘    └──────┘    └──────────┘            │
 ├──────────────────────────────────────────────────────────────┤
 │  Hook returns NF_DROP                                        │
 │  ┌──────┐    ┌──────┐    ┌──────┐                            │
 │  │Hook 1├───►│Hook 2├──X │      │  Packet freed (kfree_skb) │
 │  │ACCEPT│    │ DROP │    │      │                            │
 │  └──────┘    └──────┘    └──────┘                            │
 ├──────────────────────────────────────────────────────────────┤
 │  Hook returns NF_STOLEN                                      │
 │  ┌──────┐    ┌──────┐                                        │
 │  │Hook 1├───►│Hook 2│  Hook took ownership of skb;          │
 │  │ACCEPT│    │STOLEN│  neither freed nor continued           │
 │  └──────┘    └──────┘                                        │
 ├──────────────────────────────────────────────────────────────┤
 │  Hook returns NF_QUEUE                                       │
 │  ┌──────┐    ┌──────┐    ┌──────────────────┐                │
 │  │Hook 1├───►│Hook 2├───►│ Userspace queue  │                │
 │  │ACCEPT│    │QUEUE │    │ (nfnetlink_queue) │                │
 │  └──────┘    └──────┘    └──────────────────┘                │
 └──────────────────────────────────────────────────────────────┘
```

### 5.5 `nf_hook()` --- Traversing the Hook Chain

The kernel invokes all registered hooks at a given point via `nf_hook()`:

```c
/* include/linux/netfilter.h — simplified */
static inline int nf_hook(u_int8_t pf, unsigned int hook,
                           struct net *net, struct sock *sk,
                           struct sk_buff *skb,
                           struct net_device *indev,
                           struct net_device *outdev,
                           int (*okfn)(struct net *, struct sock *,
                                       struct sk_buff *))
{
    struct nf_hook_entries *e = rcu_dereference(net->nf.hooks_ipv4[hook]);

    if (e) {
        struct nf_hook_state state;
        nf_hook_state_init(&state, hook, pf, indev, outdev, sk, net, okfn);
        return nf_hook_slow(skb, &state, e, 0);  /* walk the hook list     */
    }
    return 1;                       /* no hooks registered; continue        */
}
```

The `NF_HOOK()` macro is the common entry point used throughout the IP stack:

```c
/* Convenience macro: invoke hooks, then call okfn if all accept */
static inline int NF_HOOK(uint8_t pf, unsigned int hook,
                           struct net *net, struct sock *sk,
                           struct sk_buff *skb,
                           struct net_device *in,
                           struct net_device *out,
                           int (*okfn)(struct net *, struct sock *,
                                       struct sk_buff *))
{
    int ret = nf_hook(pf, hook, net, sk, skb, in, out, okfn);
    if (ret == 1)
        ret = okfn(net, sk, skb);   /* all hooks accepted; continue        */
    return ret;
}
```

### 5.6 Registering a Netfilter Hook

Kernel modules register hooks using `nf_register_net_hook()`:

```c
/* Example: a simple packet logging hook */
static unsigned int my_hook_fn(void *priv,
                                struct sk_buff *skb,
                                const struct nf_hook_state *state)
{
    struct iphdr *iph = ip_hdr(skb);

    pr_info("Packet: %pI4 -> %pI4 proto=%u hook=%u\n",
            &iph->saddr, &iph->daddr,
            iph->protocol, state->hook);

    return NF_ACCEPT;                       /* let the packet continue      */
}

static struct nf_hook_ops my_hook_ops = {
    .hook     = my_hook_fn,
    .pf       = NFPROTO_IPV4,
    .hooknum  = NF_INET_PRE_ROUTING,
    .priority = NF_IP_PRI_FIRST,            /* run before other hooks       */
};

static int __init my_module_init(void)
{
    return nf_register_net_hook(&init_net, &my_hook_ops);
}

static void __exit my_module_exit(void)
{
    nf_unregister_net_hook(&init_net, &my_hook_ops);
}
```

### 5.7 Complete Netfilter Packet Flow Diagram

```
                        ┌─────────────────────────────────┐
        Incoming        │         PREROUTING              │
        Packet ────────►│  (DNAT, conntrack, mangle)      │
                        └──────────┬──────────────────────┘
                                   │
                            Routing Decision
                           ┌───────┴───────┐
                           │               │
                      Local?           Forward?
                           │               │
                  ┌────────▼───┐    ┌──────▼──────┐
                  │  INPUT      │    │  FORWARD     │
                  │ (filter)    │    │  (filter)    │
                  └────────┬───┘    └──────┬──────┘
                           │               │
                  Local Process      ┌─────▼──────┐
                           │         │ POSTROUTING │
                  ┌────────▼───┐    │  (SNAT)     │
                  │  OUTPUT     │    └─────┬──────┘
                  │ (filter,    │          │
                  │  DNAT)      │          ▼
                  └────────┬───┘     Outgoing
                           │         Packet
                  ┌────────▼──────┐
                  │  POSTROUTING  │
                  │  (SNAT)       │
                  └────────┬─────┘
                           │
                           ▼
                     Outgoing Packet
```

---

## 6. Connection Tracking (conntrack)

### 6.1 `skb->_nfct` --- Connection Tracking Entry

The `_nfct` field on `sk_buff` stores the connection tracking entry associated with
the packet:

```c
struct sk_buff {
    /* ... */
    unsigned long       _nfct;      /* conntrack entry + ctinfo in low bits */
    /* ... */
};
```

The low 3 bits encode the `enum ip_conntrack_info` value (the relationship of the
packet to the connection), while the remaining bits are a pointer to the
`struct nf_conn`:

```c
/* Extract the nf_conn pointer */
static inline struct nf_conn *nf_ct_get(const struct sk_buff *skb,
                                         enum ip_conntrack_info *ctinfo)
{
    unsigned long nfct = skb->_nfct;

    *ctinfo = nfct & NFCT_INFOMASK;         /* low 3 bits = ctinfo         */
    return (struct nf_conn *)(nfct & NFCT_PTRMASK);  /* pointer           */
}

/* Set the conntrack entry on an skb */
static inline void nf_ct_set(struct sk_buff *skb,
                              struct nf_conn *ct,
                              enum ip_conntrack_info ctinfo)
{
    skb->_nfct = (unsigned long)ct | ctinfo;
}
```

### 6.2 `struct nf_conn` --- The Connection Entry

```c
struct nf_conn {
    /* Tuple hash: original and reply direction */
    struct nf_conntrack_tuple_hash tuplehash[IP_CT_DIR_MAX];

    unsigned long       status;         /* IPS_EXPECTED, IPS_SEEN_REPLY, ...*/
    u32                 mark;           /* connmark (CONNMARK target)       */
    u16                 zone_id;        /* conntrack zone                   */

    possible_net_t      ct_net;         /* owning namespace                 */

    struct nf_ct_ext    *ext;           /* extensions: NAT, helper, etc.    */
    struct timer_list   timeout;        /* expiration timer                 */

    /* Reference count */
    struct nf_conntrack ct_general;
    /* ... */
};
```

Each connection is identified by a tuple in each direction:

```c
struct nf_conntrack_tuple {
    struct nf_conntrack_man src;    /* source: IP, port, L3/L4 proto       */
    struct {
        union nf_inet_addr u3;     /* destination IP                       */
        union {
            __be16 all;
            struct { __be16 port; } tcp;
            struct { __be16 port; } udp;
        } u;
        u_int8_t protonum;         /* L4 protocol (IPPROTO_TCP, ...)       */
        u_int8_t dir;              /* direction: original or reply         */
    } dst;
};
```

### 6.3 Connection States

Conntrack classifies each packet into a state relative to its connection:

```c
enum ip_conntrack_info {
    IP_CT_ESTABLISHED,          /* Part of an established connection        */
    IP_CT_RELATED,              /* Related to an established connection     */
    IP_CT_NEW,                  /* Starting a new connection                */
    IP_CT_IS_REPLY = 3,        /* Flag: packet is in the reply direction   */
    IP_CT_ESTABLISHED_REPLY = IP_CT_ESTABLISHED + IP_CT_IS_REPLY,
    IP_CT_RELATED_REPLY     = IP_CT_RELATED + IP_CT_IS_REPLY,
};
```

The state machine for a TCP connection:

```
 ┌──────────────────────────────────────────────────────────────────┐
 │  TCP Connection Tracking State Machine                           │
 │                                                                  │
 │  SYN packet (original direction)                                 │
 │       │                                                          │
 │       ▼                                                          │
 │  ┌─────────────────┐                                             │
 │  │  NEW             │  No reply seen yet                          │
 │  │  status: 0       │                                             │
 │  └────────┬────────┘                                             │
 │           │  SYN-ACK (reply direction)                           │
 │           ▼                                                      │
 │  ┌─────────────────┐                                             │
 │  │  ESTABLISHED     │  Reply seen; bidirectional flow             │
 │  │  status:         │                                             │
 │  │  IPS_SEEN_REPLY  │                                             │
 │  └────────┬────────┘                                             │
 │           │  ACK (original direction)                            │
 │           ▼                                                      │
 │  ┌─────────────────┐                                             │
 │  │  ESTABLISHED     │  Fully established; assured                 │
 │  │  status:         │                                             │
 │  │  IPS_SEEN_REPLY  │                                             │
 │  │  IPS_ASSURED     │  (won't be dropped when table is full)     │
 │  └────────┬────────┘                                             │
 │           │  FIN / RST                                           │
 │           ▼                                                      │
 │  ┌─────────────────┐                                             │
 │  │  Timeout starts  │  Awaiting final cleanup                     │
 │  │  (configurable)  │                                             │
 │  └────────┬────────┘                                             │
 │           │  Timer expires                                       │
 │           ▼                                                      │
 │  ┌─────────────────┐                                             │
 │  │  DESTROYED       │  Entry removed from hash table              │
 │  │  nf_ct_put()     │                                             │
 │  └─────────────────┘                                             │
 └──────────────────────────────────────────────────────────────────┘
```

The INVALID state is not a conntrack state per se but rather a classification for
packets that cannot be associated with any valid connection:

```c
/* In iptables: -m conntrack --ctstate INVALID */
/* These packets have skb->_nfct == 0 (no conntrack entry) */
```

### 6.4 NAT and How It Modifies sk_buff

NAT (Network Address Translation) operates through conntrack. When a NAT rule matches,
the connection's reply tuple is modified. Subsequent packets in the same connection
are translated automatically:

```c
/* net/netfilter/nf_nat_core.c — simplified */
unsigned int nf_nat_packet(struct nf_conn *ct,
                            enum ip_conntrack_info ctinfo,
                            unsigned int hooknum,
                            struct sk_buff *skb)
{
    enum nf_ct_dir dir = CTINFO2DIR(ctinfo);
    unsigned long statusbit;

    if (hooknum == NF_INET_PRE_ROUTING || hooknum == NF_INET_LOCAL_IN)
        statusbit = IPS_DST_NAT;            /* DNAT at PRE_ROUTING         */
    else
        statusbit = IPS_SRC_NAT;            /* SNAT at POST_ROUTING        */

    /* Modify the packet headers according to the NAT mapping */
    if (dir == IP_CT_DIR_ORIGINAL) {
        /* Original direction: apply NAT transformation */
        nf_nat_manip_pkt(skb, ct, NF_NAT_MANIP_SRC or _DST);
    } else {
        /* Reply direction: apply reverse transformation */
        nf_nat_manip_pkt(skb, ct, reverse_manip);
    }

    return NF_ACCEPT;
}
```

The `nf_nat_manip_pkt()` function modifies the following `sk_buff` data:

```
 ┌──────────────────────────────────────────────────────────┐
 │  Fields modified by NAT on sk_buff's packet data:        │
 │                                                          │
 │  For SNAT (Source NAT):                                  │
 │  ├── IP header: saddr  →  new source IP                  │
 │  ├── TCP/UDP header: sport  →  new source port           │
 │  ├── IP header checksum: recalculated                    │
 │  └── TCP/UDP checksum: updated incrementally             │
 │                                                          │
 │  For DNAT (Destination NAT):                             │
 │  ├── IP header: daddr  →  new destination IP             │
 │  ├── TCP/UDP header: dport  →  new destination port      │
 │  ├── IP header checksum: recalculated                    │
 │  └── TCP/UDP checksum: updated incrementally             │
 └──────────────────────────────────────────────────────────┘
```

Checksum updates use incremental checksum adjustment (RFC 1624) to avoid recomputing
the entire checksum:

```c
/* net/netfilter/nf_nat_proto.c — simplified */
static void nf_nat_ipv4_csum_update(struct sk_buff *skb,
                                      __be32 oldip, __be32 newip)
{
    struct iphdr *iph = ip_hdr(skb);

    inet_proto_csum_replace4(&iph->check, skb, oldip, newip, true);
}
```

### 6.5 Conntrack Zones

Conntrack zones allow multiple independent conntrack tables within the same namespace.
This is essential for scenarios like transparent proxies where the same 5-tuple may
appear in different contexts:

```c
struct nf_conntrack_zone {
    u16     id;             /* zone identifier (0 = default zone)           */
    u8      flags;          /* NF_CT_FLAG_MARK                              */
    u8      dir;            /* NF_CT_ZONE_DIR_ORIG, _REPL, or _DEFAULT     */
};
```

A packet's zone is determined by the `CT --zone` target in iptables/nftables or by
a `ct zone` assignment in nftables. The zone ID is included in the conntrack hash
lookup, so two connections with the same 5-tuple but different zones are treated as
separate entries.

```
 ┌──────────────────────────────────────────────────────────────┐
 │  Zone 0 (default)              Zone 1                        │
 │  ┌──────────────────────┐     ┌──────────────────────┐       │
 │  │ 10.0.0.1:1234 →      │     │ 10.0.0.1:1234 →      │       │
 │  │   8.8.8.8:53  (UDP)  │     │   8.8.8.8:53  (UDP)  │       │
 │  │                      │     │                      │       │
 │  │ (different conntrack │     │ (different conntrack │       │
 │  │  entry, different    │     │  entry, may have     │       │
 │  │  NAT mappings)       │     │  different NAT)      │       │
 │  └──────────────────────┘     └──────────────────────┘       │
 └──────────────────────────────────────────────────────────────┘
```

---

## 7. The Mark Field

### 7.1 `skb->mark` --- 32-bit Packet Mark

The `mark` field is a 32-bit unsigned integer on `sk_buff` that carries no inherent
semantic meaning. It exists solely as a metadata tag for policy decisions:

```c
struct sk_buff {
    /* ... */
    __u32       mark;               /* packet mark (set by netfilter, etc.) */
    /* ... */
};
```

The mark is never transmitted on the wire. It is a local, kernel-internal annotation
that persists for the lifetime of the `sk_buff`.

### 7.2 Setting the Mark via iptables/nftables

```bash
# iptables: set mark on packets from a specific source
iptables -t mangle -A PREROUTING -s 10.0.0.0/8 -j MARK --set-mark 0x100

# nftables equivalent
nft add rule ip mangle prerouting ip saddr 10.0.0.0/8 meta mark set 0x100
```

In the kernel, the `MARK` target simply assigns the value:

```c
/* net/netfilter/xt_MARK.c — simplified */
static unsigned int mark_tg(struct sk_buff *skb,
                             const struct xt_action_param *par)
{
    const struct xt_mark_tginfo2 *info = par->targinfo;

    skb->mark = (skb->mark & ~info->mask) | info->mark;
    return XT_CONTINUE;
}
```

### 7.3 Policy Routing with fwmark

The mark field is used by policy routing (`ip rule`) to select different routing
tables based on the packet's mark:

```bash
# Route marked packets through a different table
ip rule add fwmark 0x100 table 100
ip route add default via 10.0.1.1 table 100
```

In the kernel, the FIB rule matching function checks the mark:

```c
/* net/ipv4/fib_rules.c — simplified */
static int fib4_rule_match(struct fib_rule *rule,
                            struct flowi *fl, int flags)
{
    struct fib4_rule *r = container_of(rule, struct fib4_rule, common);

    /* Match on fwmark */
    if (r->common.mark && (r->common.mark != fl->flowi_mark))
        return 0;                   /* mark doesn't match this rule        */

    /* ... other match criteria ... */
    return 1;
}
```

The flow key's mark (`fl->flowi_mark`) is populated from `skb->mark`:

```c
/* net/ipv4/route.c — building the flow key for routing */
static void ip_route_input_fill_fl4(struct flowi4 *fl4,
                                      const struct sk_buff *skb,
                                      __be32 daddr, __be32 saddr)
{
    fl4->flowi4_mark = skb->mark;   /* copy skb mark into flow key         */
    /* ... */
}
```

### 7.4 Traffic Classification with tc

The `tc` (traffic control) subsystem can match and act on `skb->mark`:

```bash
# tc filter matching on skb->mark
tc filter add dev eth0 parent 1:0 protocol ip \
    handle 0x100 fw classid 1:10
```

This `fw` classifier reads `skb->mark` and classifies the packet into the
appropriate traffic class.

### 7.5 Socket Mark: `SO_MARK`

The `SO_MARK` socket option sets a default mark on all outgoing packets from that
socket:

```c
/* Application code */
int mark = 0x100;
setsockopt(fd, SOL_SOCKET, SO_MARK, &mark, sizeof(mark));
```

In the kernel, the mark is propagated from socket to sk_buff during packet construction:

```c
/* net/ipv4/ip_output.c — simplified */
static int __ip_queue_xmit(struct sock *sk, struct sk_buff *skb, ...)
{
    /* ... */
    skb->mark = sk->sk_mark;       /* inherit mark from socket             */
    /* ... */
}
```

The reverse direction also works: when a packet is received, its mark can be
propagated to the socket via `SO_INCOMING_MARK` or `IP_RECVMARK`.

### 7.6 Mark Propagation Summary

```
 ┌──────────────────────────────────────────────────────────────┐
 │  Mark Propagation Paths                                      │
 │                                                              │
 │  Socket → sk_buff (TX path):                                 │
 │  ┌────────┐     sk->sk_mark     ┌──────────┐                │
 │  │ Socket ├────────────────────►│ sk_buff  │                │
 │  │ (sk)   │  set during         │ .mark    │                │
 │  └────────┘  ip_queue_xmit()    └──────────┘                │
 │                                                              │
 │  Netfilter → sk_buff (any path):                             │
 │  ┌──────────────┐  MARK target  ┌──────────┐                │
 │  │ iptables/nft ├──────────────►│ sk_buff  │                │
 │  │ rule         │               │ .mark    │                │
 │  └──────────────┘               └──────────┘                │
 │                                                              │
 │  Conntrack → sk_buff:                                        │
 │  ┌──────────────┐  CONNMARK     ┌──────────┐                │
 │  │ nf_conn      │  --restore-   │ sk_buff  │                │
 │  │ .mark        ├──mark────────►│ .mark    │                │
 │  └──────────────┘               └──────────┘                │
 │                                                              │
 │  sk_buff → Conntrack:                                        │
 │  ┌──────────┐  CONNMARK         ┌──────────────┐            │
 │  │ sk_buff  │  --save-          │ nf_conn      │            │
 │  │ .mark    ├──mark────────────►│ .mark        │            │
 │  └──────────┘                   └──────────────┘            │
 └──────────────────────────────────────────────────────────────┘
```

### 7.7 `skb->priority` --- QoS Priority

The `priority` field influences the packet's placement in the output queue:

```c
struct sk_buff {
    /* ... */
    __u32       priority;           /* QoS priority                         */
    /* ... */
};
```

Priority is set from multiple sources:

```c
/* From the socket (SO_PRIORITY) */
skb->priority = sk->sk_priority;

/* From the IP TOS/DSCP field */
skb->priority = rt_tos2priority(iph->tos);

/* The mapping (simplified): */
static inline int rt_tos2priority(u8 tos)
{
    /*
     * TOS field to Linux priority mapping:
     *   0x00 (Normal)       → TC_PRIO_BESTEFFORT (0)
     *   0x08 (Minimize Delay) → TC_PRIO_INTERACTIVE (6)
     *   0x04 (Maximize Throughput) → TC_PRIO_BULK (2)
     *   0x02 (Maximize Reliability) → TC_PRIO_BESTEFFORT (0)
     *   0x10 (Minimize Cost) → TC_PRIO_FILLER (1)
     */
    return ip_tos2prio[IPTOS_TOS(tos) >> 1];
}
```

### 7.8 `skb->tc_index` --- Traffic Control Classifier Index

The `tc_index` field is used by the traffic control subsystem for internal
classification:

```c
struct sk_buff {
    /* ... */
    __u16       tc_index;           /* traffic control index                */
    /* ... */
};
```

This field is set by the `CLASSIFY` iptables target or by `tc` actions, and it is
read by the `tcindex` classifier in the queueing discipline:

```bash
# Set tc_index via iptables
iptables -t mangle -A POSTROUTING -p tcp --dport 80 \
    -j CLASSIFY --set-class 1:10

# Use tc_index in tc filter
tc filter add dev eth0 parent 1:0 tcindex \
    hash 64 mask 0xff pass_on
```

---

## 8. Protocol and Packet Type Fields

### 8.1 `skb->protocol` --- Layer 3 Protocol

The `protocol` field identifies the Layer 3 (network layer) protocol encapsulated in
the frame:

```c
struct sk_buff {
    /* ... */
    __be16      protocol;           /* L3 protocol in network byte order   */
    /* ... */
};
```

Common values defined in `include/uapi/linux/if_ether.h`:

```c
#define ETH_P_IP        0x0800      /* Internet Protocol (IPv4)            */
#define ETH_P_IPV6      0x86DD      /* IPv6                                */
#define ETH_P_ARP       0x0806      /* Address Resolution Protocol         */
#define ETH_P_8021Q     0x8100      /* 802.1Q VLAN tagged frame            */
#define ETH_P_8021AD    0x88A8      /* 802.1ad Service VLAN (QinQ)         */
#define ETH_P_LLDP      0x88CC      /* Link Layer Discovery Protocol       */
#define ETH_P_SLOW      0x8809      /* LACP / Marker                       */
#define ETH_P_ALL       0x0003      /* Capture all protocols (raw socket)  */
```

### 8.2 `skb->pkt_type` --- Packet Type Classification

The `pkt_type` field classifies how the packet relates to the receiving host:

```c
struct sk_buff {
    /* ... */
    __u8        pkt_type:3;         /* 3-bit field                         */
    /* ... */
};
```

Possible values:

```c
#define PACKET_HOST         0   /* Destined for this host (our MAC addr)   */
#define PACKET_BROADCAST    1   /* Broadcast frame (ff:ff:ff:ff:ff:ff)     */
#define PACKET_MULTICAST    2   /* Multicast frame (group address)         */
#define PACKET_OTHERHOST    3   /* Not for us (promiscuous mode capture)   */
#define PACKET_OUTGOING     4   /* Locally originated (seen on TX path)    */
#define PACKET_LOOPBACK     5   /* Sent to ourselves via loopback          */
#define PACKET_USER         6   /* To userspace (unused in modern kernels) */
#define PACKET_KERNEL       7   /* To kernel space (unused in most paths)  */
```

### 8.3 `eth_type_trans()` --- Setting Protocol and Packet Type

The function `eth_type_trans()` is called by every Ethernet NIC driver immediately
after receiving a frame. It parses the Ethernet header and sets both `skb->protocol`
and `skb->pkt_type`:

```c
/* net/ethernet/eth.c — simplified */
__be16 eth_type_trans(struct sk_buff *skb, struct net_device *dev)
{
    const struct ethhdr *eth;
    unsigned short ethertype;

    skb->dev = dev;                         /* set the receiving device     */
    eth = (struct ethhdr *)skb->data;

    /* Step 1: Determine pkt_type from destination MAC */
    if (unlikely(!ether_addr_equal_64bits(eth->h_dest,
                                          dev->dev_addr))) {
        if (is_multicast_ether_addr(eth->h_dest)) {
            if (ether_addr_equal_64bits(eth->h_dest, dev->broadcast))
                skb->pkt_type = PACKET_BROADCAST;
            else
                skb->pkt_type = PACKET_MULTICAST;
        } else {
            skb->pkt_type = PACKET_OTHERHOST;  /* not our MAC address     */
        }
    }
    /* else: pkt_type remains PACKET_HOST (default = 0) */

    /* Step 2: Determine protocol from EtherType */
    ethertype = ntohs(eth->h_proto);

    if (ethertype >= ETH_P_802_3_MIN) {
        /* Standard EtherType: use directly */
        skb->protocol = eth->h_proto;       /* e.g., ETH_P_IP             */
    } else {
        /* 802.2 LLC frame: need further parsing */
        skb->protocol = htons(ETH_P_802_2);
    }

    /* Step 3: Advance data pointer past Ethernet header */
    skb_pull_inline(skb, ETH_HLEN);

    return skb->protocol;
}
```

### 8.4 The Relationship Between pkt_type and Processing

```
 ┌──────────────────────────────────────────────────────────────┐
 │  pkt_type determines initial packet disposition:             │
 │                                                              │
 │  PACKET_HOST                                                 │
 │  └── Normal processing: IP stack, socket lookup, etc.        │
 │                                                              │
 │  PACKET_BROADCAST                                            │
 │  └── Delivered to all matching sockets                       │
 │  └── Also subject to ip_rcv() processing                    │
 │                                                              │
 │  PACKET_MULTICAST                                            │
 │  └── Delivered via multicast routing / IGMP                  │
 │  └── Requires multicast group membership                    │
 │                                                              │
 │  PACKET_OTHERHOST                                            │
 │  └── Normally dropped by ip_rcv()                            │
 │  └── Captured by tcpdump / raw sockets in promisc mode       │
 │  └── NOT forwarded unless bridge or macvlan                  │
 │                                                              │
 │  PACKET_LOOPBACK                                             │
 │  └── Packets sent to localhost                               │
 │  └── Never reach a physical device                           │
 └──────────────────────────────────────────────────────────────┘
```

### 8.5 VLAN Handling: `skb->vlan_tci` and `skb_vlan_tag_present()`

802.1Q VLAN tags are handled through dedicated fields on `sk_buff`:

```c
struct sk_buff {
    /* ... */
    __u16       vlan_tci;           /* VLAN Tag Control Information         */
    __be16      vlan_proto;         /* VLAN protocol (ETH_P_8021Q, etc.)   */
    /* ... */
};
```

The `vlan_tci` field layout (16 bits):

```
 ┌───────────────────────────────────────────────────────┐
 │  15  14  13  12  11  10   9   8   7   6   5   4   3  │
 │ ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬──┐│
 │ │PCP│DEI│        VLAN ID (VID) — 12 bits            ││
 │ │3b │1b │                                           ││
 │ └───┴───┴───────────────────────────────────────────┘│
 │                                                       │
 │  PCP: Priority Code Point (802.1p priority, 0-7)      │
 │  DEI: Drop Eligible Indicator                         │
 │  VID: VLAN Identifier (0-4095)                        │
 └───────────────────────────────────────────────────────┘
```

The VLAN tag may be present in two ways:

1. **In-band**: The tag is in the Ethernet header (4 extra bytes). The driver parses
   it and stores it in `skb->vlan_tci`.

2. **Hardware-stripped**: The NIC strips the tag via hardware offload and provides it
   via the descriptor. The driver calls `__vlan_hwaccel_put_tag()`.

```c
/* Called by NIC driver when hardware strips the VLAN tag */
static inline void __vlan_hwaccel_put_tag(struct sk_buff *skb,
                                           __be16 vlan_proto,
                                           u16 vlan_tci)
{
    skb->vlan_proto = vlan_proto;
    skb->vlan_tci   = VLAN_TAG_PRESENT | vlan_tci;
}

/* Check if VLAN tag is present (hardware-accelerated) */
static inline bool skb_vlan_tag_present(const struct sk_buff *skb)
{
    return skb->vlan_tci & VLAN_TAG_PRESENT;
}

/* Get the VLAN ID (strip the PRESENT flag) */
static inline u16 skb_vlan_tag_get_id(const struct sk_buff *skb)
{
    return skb->vlan_tci & VLAN_VID_MASK;   /* mask = 0x0FFF               */
}
```

### 8.6 VLAN Processing Flow

```
 ┌──────────────────────────────────────────────────────────────────┐
 │  VLAN Processing on RX Path                                      │
 │                                                                  │
 │  NIC receives tagged frame                                       │
 │       │                                                          │
 │       ├── Hardware VLAN offload enabled?                         │
 │       │           │                                              │
 │       │      ┌────┴────┐                                         │
 │       │      │         │                                         │
 │       │     Yes        No                                        │
 │       │      │         │                                         │
 │       │      ▼         ▼                                         │
 │       │  NIC strips   Tag remains                                │
 │       │  tag; driver   in frame data                             │
 │       │  calls:        │                                         │
 │       │  __vlan_       ▼                                         │
 │       │  hwaccel_   skb->protocol                                │
 │       │  put_tag()  = ETH_P_8021Q                                │
 │       │      │         │                                         │
 │       │      ▼         ▼                                         │
 │       │  skb->vlan_ __vlan_get_tag()                             │
 │       │  tci set    parses inline tag                            │
 │       │      │         │                                         │
 │       │      └────┬────┘                                         │
 │       │           │                                              │
 │       │           ▼                                              │
 │       │  vlan_do_receive()                                       │
 │       │  ├── Find VLAN device for VID                            │
 │       │  ├── skb->dev = vlan_dev (e.g., eth0.100)               │
 │       │  ├── skb->protocol = inner protocol (ETH_P_IP)         │
 │       │  └── Re-enter netif_receive_skb()                        │
 │       │                                                          │
 └──────────────────────────────────────────────────────────────────┘
```

---

## 9. Checksum Offload Fields

### 9.1 `skb->ip_summed` --- Checksum Status

The `ip_summed` field describes the current checksum state of the packet. Its meaning
differs between the RX and TX paths:

```c
struct sk_buff {
    /* ... */
    __u8    ip_summed:2;            /* checksum status (2-bit field)        */
    /* ... */
};
```

The four possible values:

```c
#define CHECKSUM_NONE           0   /* No checksum information available   */
#define CHECKSUM_UNNECESSARY    1   /* Checksum verified by hardware/lower */
#define CHECKSUM_COMPLETE       2   /* Hardware computed raw checksum      */
#define CHECKSUM_PARTIAL        3   /* Hardware should compute on TX       */
```

### 9.2 Checksum States on the RX Path

```
 ┌──────────────────────────────────────────────────────────────────┐
 │  RX Checksum States                                              │
 │                                                                  │
 │  CHECKSUM_NONE                                                   │
 │  ├── NIC did NOT verify or compute any checksum                  │
 │  ├── Software must verify the checksum                           │
 │  └── Common on older NICs or for unsupported protocols           │
 │                                                                  │
 │  CHECKSUM_UNNECESSARY                                            │
 │  ├── NIC (or a lower layer) verified the checksum is correct     │
 │  ├── Software can skip checksum verification                     │
 │  ├── skb->csum is NOT meaningful                                 │
 │  └── Most common for modern NICs with checksum offload           │
 │                                                                  │
 │  CHECKSUM_COMPLETE                                               │
 │  ├── NIC computed the raw checksum over the packet payload       │
 │  ├── skb->csum contains the raw checksum value                   │
 │  ├── Software must fold in pseudo-header and verify              │
 │  └── Used by some NICs that compute but don't verify             │
 └──────────────────────────────────────────────────────────────────┘
```

### 9.3 Checksum States on the TX Path

```
 ┌──────────────────────────────────────────────────────────────────┐
 │  TX Checksum States                                              │
 │                                                                  │
 │  CHECKSUM_NONE                                                   │
 │  ├── Software has already computed the checksum                  │
 │  ├── The checksum field in the packet header is correct          │
 │  └── NIC should NOT modify the checksum                         │
 │                                                                  │
 │  CHECKSUM_PARTIAL                                                │
 │  ├── Software has computed the pseudo-header checksum            │
 │  ├── NIC should compute the rest (over payload)                  │
 │  ├── skb->csum_start = offset from skb->head to start of        │
 │  │   checksum computation                                       │
 │  ├── skb->csum_offset = offset from csum_start to the           │
 │  │   checksum field in the header                                │
 │  └── Most common for TCP/UDP on modern NICs                     │
 │                                                                  │
 │  CHECKSUM_UNNECESSARY                                            │
 │  ├── Loopback and certain virtual devices                        │
 │  └── Checksum is not needed (e.g., local delivery)              │
 └──────────────────────────────────────────────────────────────────┘
```

### 9.4 `skb->csum`, `skb->csum_start`, `skb->csum_offset`

These fields work together for TX checksum offload:

```c
struct sk_buff {
    /* ... */
    union {
        __wsum      csum;           /* RX: raw checksum from hardware      */
        struct {
            __u16   csum_start;     /* TX: offset from head to csum start  */
            __u16   csum_offset;    /* TX: offset from csum_start to field */
        };
    };
    /* ... */
};
```

The layout in memory during TX checksum offload:

```
 ┌──────────────────────────────────────────────────────────────────┐
 │  sk_buff data during TX with CHECKSUM_PARTIAL                    │
 │                                                                  │
 │  skb->head                                                       │
 │  │                                                               │
 │  ▼  ┌──────────────┬──────────────┬──────────────────────┐       │
 │     │  Ethernet    │  IP Header   │  TCP Header + Data   │       │
 │     │  Header      │              │                      │       │
 │     └──────────────┴──────────────┴──────────────────────┘       │
 │     │              │              │    │                          │
 │     │              │              │    └── checksum field         │
 │     │              │              │        (pre-filled with      │
 │     │              │              │         pseudo-header csum)  │
 │     │              │              │                              │
 │     │◄─────────────┼──────────────┤                              │
 │     │              │  csum_start  │                              │
 │     │              │  (offset from head to TCP header start)    │
 │     │              │              │                              │
 │     │              │              │◄──►│                          │
 │     │              │              │csum_offset                   │
 │     │              │              │(offset from TCP hdr start   │
 │     │              │              │ to the checksum field)       │
 │     │              │              │                              │
 │     │              │              │ For TCP: csum_offset = 16    │
 │     │              │              │ For UDP: csum_offset = 6     │
 └──────────────────────────────────────────────────────────────────┘
```

### 9.5 How the Stack Sets Up TX Checksum Offload

```c
/* net/ipv4/tcp_output.c — simplified */
static int __tcp_transmit_skb(struct sock *sk, struct sk_buff *skb, ...)
{
    struct tcphdr *th;
    /* ... */

    th = (struct tcphdr *)skb->data;

    /* Step 1: Compute pseudo-header checksum */
    th->check = ~tcp_v4_check(skb->len, inet->inet_saddr,
                               inet->inet_daddr, 0);

    /* Step 2: Tell NIC where to compute the checksum */
    skb->ip_summed  = CHECKSUM_PARTIAL;
    skb->csum_start = skb_transport_header(skb) - skb->head;
    skb->csum_offset = offsetof(struct tcphdr, check);  /* = 16          */

    /* NIC will sum from csum_start to end of packet, add to th->check,
       and write the result back to th->check */
}
```

### 9.6 Checksum Offload Flow Diagram

```
 ┌──────────────────────────────────────────────────────────────────┐
 │                RX Checksum Offload Flow                          │
 │                                                                  │
 │  NIC receives frame                                              │
 │       │                                                          │
 │       ├── NIC supports RX checksum offload?                     │
 │       │           │                                              │
 │       │      ┌────┴────┐                                         │
 │       │      │         │                                         │
 │       │     Yes        No                                        │
 │       │      │         │                                         │
 │       │      ▼         ▼                                         │
 │       │  NIC verifies  ip_summed =                               │
 │       │  checksum      CHECKSUM_NONE                             │
 │       │      │         │                                         │
 │       │      ├── OK?   ▼                                         │
 │       │      │    │    Software computes                         │
 │       │      │   Yes   and verifies checksum                     │
 │       │      │    │    in tcp_v4_rcv()                           │
 │       │      │    ▼                                              │
 │       │      │  ip_summed =                                      │
 │       │      │  CHECKSUM_UNNECESSARY                             │
 │       │      │    │                                              │
 │       │      │    ▼                                              │
 │       │      │  tcp_v4_rcv() skips                               │
 │       │      │  checksum verification                            │
 │       │      │                                                   │
 │       │      ├── Partial?                                        │
 │       │      │    │                                              │
 │       │      │    ▼                                              │
 │       │      │  ip_summed =                                      │
 │       │      │  CHECKSUM_COMPLETE                                │
 │       │      │  skb->csum = raw sum                              │
 │       │      │    │                                              │
 │       │      │    ▼                                              │
 │       │      │  Software adds pseudo-header                      │
 │       │      │  and verifies                                     │
 │       │      │                                                   │
 └──────────────────────────────────────────────────────────────────┘

 ┌──────────────────────────────────────────────────────────────────┐
 │                TX Checksum Offload Flow                          │
 │                                                                  │
 │  tcp_sendmsg() builds skb                                        │
 │       │                                                          │
 │       ▼                                                          │
 │  Pseudo-header checksum stored in th->check                      │
 │  ip_summed = CHECKSUM_PARTIAL                                    │
 │  csum_start = transport header offset                            │
 │  csum_offset = 16 (TCP) or 6 (UDP)                              │
 │       │                                                          │
 │       ▼                                                          │
 │  dev_queue_xmit()                                                │
 │       │                                                          │
 │       ├── NIC supports TX checksum offload?                     │
 │       │           │                                              │
 │       │      ┌────┴────┐                                         │
 │       │      │         │                                         │
 │       │     Yes        No                                        │
 │       │      │         │                                         │
 │       │      ▼         ▼                                         │
 │       │  Pass skb     skb_checksum_help(skb)                     │
 │       │  to NIC       ├── Compute checksum in software           │
 │       │  as-is        ├── Write result to header                 │
 │       │      │        ├── ip_summed = CHECKSUM_NONE              │
 │       │      │        └── Pass to NIC                            │
 │       │      ▼                                                   │
 │       │  NIC reads csum_start, csum_offset                       │
 │       │  Computes checksum over payload                          │
 │       │  Adds to pseudo-header checksum                          │
 │       │  Writes final checksum to th->check                      │
 │       │  Transmits frame on wire                                 │
 │       │                                                          │
 └──────────────────────────────────────────────────────────────────┘
```

### 9.7 Software Fallback: `skb_checksum_help()`

When a NIC does not support TX checksum offload (or the packet is being redirected to
a device that does not), the kernel falls back to software computation:

```c
/* net/core/dev.c — simplified */
int skb_checksum_help(struct sk_buff *skb)
{
    __wsum csum;
    int offset = skb_checksum_start_offset(skb);

    /* Compute checksum from csum_start to end of packet */
    csum = skb_checksum(skb, offset, skb->len - offset, 0);

    /* Add pseudo-header checksum (already in the checksum field) */
    offset += skb->csum_offset;
    *(__sum16 *)(skb->data + offset) = csum_fold(csum);

    /* Mark as fully computed */
    skb->ip_summed = CHECKSUM_NONE;

    return 0;
}
```

---

## 10. Security and Labeling

### 10.1 `skb->secmark` --- SELinux Security Mark

The `secmark` field is a 32-bit value used by Linux Security Modules (primarily
SELinux) to associate a security context with a packet:

```c
struct sk_buff {
    /* ... */
#ifdef CONFIG_NETWORK_SECMARK
    __u32       secmark;            /* security mark (SELinux, etc.)        */
#endif
    /* ... */
};
```

The secmark is set by the `SECMARK` iptables target:

```bash
# Set SELinux context on HTTP traffic
iptables -t security -A INPUT -p tcp --dport 80 \
    -j SECMARK --selctx system_u:object_r:httpd_packet_t:s0
```

In the kernel:

```c
/* net/netfilter/xt_SECMARK.c — simplified */
static unsigned int secmark_tg(struct sk_buff *skb,
                                const struct xt_action_param *par)
{
    const struct xt_secmark_target_info *info = par->targinfo;

    skb->secmark = info->secid;     /* set the security ID on the packet   */
    return XT_CONTINUE;
}
```

SELinux then uses `skb->secmark` during access control decisions:

```c
/* security/selinux/hooks.c — simplified */
static int selinux_socket_sock_rcv_skb(struct sock *sk,
                                        struct sk_buff *skb)
{
    u32 sk_sid = sksec->sid;        /* socket's security context           */
    u32 pkt_sid;

    if (skb->secmark)
        pkt_sid = skb->secmark;     /* use packet's security mark          */
    else
        pkt_sid = SECINITSID_UNLABELED;

    /* Check if socket is allowed to receive this packet */
    return avc_has_perm(sk_sid, pkt_sid, SECCLASS_PACKET, PACKET__RECV);
}
```

### 10.2 IPsec Security Path

The IPsec subsystem uses the XFRM (transform) framework to associate security
associations with packets. On the RX path, the security path records which transforms
have been applied:

```c
struct sec_path {
    int                 len;        /* number of transforms applied         */
    int                 olen;       /* original length before transforms    */
    struct xfrm_state   *xvec[XFRM_MAX_DEPTH]; /* transform states        */
};
```

Access to the security path from sk_buff uses an extension mechanism:

```c
/* Get security path from skb (may be NULL) */
static inline struct sec_path *skb_sec_path(const struct sk_buff *skb)
{
#ifdef CONFIG_XFRM
    return skb_ext_find(skb, SKB_EXT_SEC_PATH);
#else
    return NULL;
#endif
}
```

### 10.3 XFRM (Transform) Framework and sk_buff

The XFRM framework implements IPsec ESP, AH, and IPComp transforms. Each transform
modifies the sk_buff in a specific way:

```
 ┌──────────────────────────────────────────────────────────────────┐
 │  XFRM Processing on RX Path                                     │
 │                                                                  │
 │  Encrypted ESP packet arrives                                    │
 │       │                                                          │
 │       ▼                                                          │
 │  ┌──────────────────────────────────┐                            │
 │  │  xfrm4_rcv() / xfrm6_rcv()     │                            │
 │  │  Lookup Security Association (SA)│                            │
 │  │  by SPI + destination address    │                            │
 │  └──────────┬───────────────────────┘                            │
 │             │                                                    │
 │             ▼                                                    │
 │  ┌──────────────────────────────────┐                            │
 │  │  xfrm_input()                   │                            │
 │  │  For each transform in SA:       │                            │
 │  │  ├── Verify authentication hash  │                            │
 │  │  ├── Decrypt payload             │                            │
 │  │  ├── Remove ESP/AH header        │                            │
 │  │  ├── Update skb->data pointers   │                            │
 │  │  └── sec_path->xvec[n] = state   │                            │
 │  └──────────┬───────────────────────┘                            │
 │             │                                                    │
 │             ▼                                                    │
 │  ┌──────────────────────────────────┐                            │
 │  │  Inner packet (cleartext)        │                            │
 │  │  Re-enter ip_rcv() for routing   │                            │
 │  │  sec_path records transform      │                            │
 │  └──────────────────────────────────┘                            │
 └──────────────────────────────────────────────────────────────────┘
```

On the TX path, XFRM applies transforms before the packet reaches the NIC:

```c
/* net/xfrm/xfrm_output.c — simplified */
static int xfrm_output2(struct net *net, struct sock *sk,
                          struct sk_buff *skb)
{
    /* Walk the bundle of transforms */
    while (xfrm_state) {
        /* Apply ESP/AH/IPComp transform */
        err = xfrm_state->outer_mode.afinfo->output(net, sk, skb);

        /* The transform:
         * 1. Expands skb (headroom for ESP header)
         * 2. Encrypts payload
         * 3. Appends authentication hash
         * 4. Updates IP header (protocol, length)
         */
    }

    return 0;
}
```

The `struct xfrm_state` holds the cryptographic keys and algorithms:

```c
struct xfrm_state {
    struct xfrm_id          id;         /* SPI + protocol + dst address    */
    struct xfrm_selector    sel;        /* traffic selector (what to match)*/

    struct xfrm_algo_auth   *aalg;      /* authentication algorithm (HMAC) */
    struct xfrm_algo        *ealg;      /* encryption algorithm (AES, etc.)*/
    struct xfrm_algo        *calg;      /* compression algorithm           */

    u32                     reqid;      /* request ID for policy matching   */
    u8                      props_mode; /* transport or tunnel mode         */

    /* ... lifetime, replay protection, etc. ... */
};
```

### 10.4 `skb->nf_bridge` --- Bridge Netfilter Information

When netfilter operates on bridged traffic (via `br_netfilter`), additional state is
stored in an `sk_buff` extension:

```c
struct nf_bridge_info {
    u32                         mask;           /* state flags              */
    struct net_device           *physindev;      /* physical input device   */
    struct net_device           *physoutdev;     /* physical output device  */
    union {
        __be32                  ipv4_daddr;     /* saved destination IP     */
        struct in6_addr         ipv6_daddr;
    };
};
```

This structure is necessary because bridge netfilter "pretends" that bridged frames
go through the IP netfilter hooks. The physical devices must be preserved separately
from the logical bridge device:

```c
/* Get the nf_bridge_info from skb */
static inline struct nf_bridge_info *nf_bridge_info_get(
    const struct sk_buff *skb)
{
    return skb_ext_find(skb, SKB_EXT_BRIDGE_NF);
}
```

```
 ┌──────────────────────────────────────────────────────────────────┐
 │  Bridge Netfilter Flow                                           │
 │                                                                  │
 │  Frame arrives on bridge port (eth0)                             │
 │  skb->dev = eth0                                                 │
 │       │                                                          │
 │       ▼                                                          │
 │  br_handle_frame()                                               │
 │  ├── physindev = eth0           (saved in nf_bridge_info)       │
 │  ├── skb->dev = br0             (bridge device)                 │
 │  │                                                               │
 │  │   br_netfilter intercepts:                                    │
 │  │   ├── NF_INET_PRE_ROUTING    (as if IP packet on br0)       │
 │  │   ├── Routing decision       (bridge forwarding)             │
 │  │   ├── NF_INET_FORWARD        (filter bridged traffic)       │
 │  │   ├── NF_INET_POST_ROUTING   (SNAT on bridged traffic)      │
 │  │                                                               │
 │  │   physoutdev = eth1          (saved in nf_bridge_info)       │
 │  │   skb->dev = eth1            (output bridge port)            │
 │  │                                                               │
 │  └── Frame forwarded out eth1                                    │
 └──────────────────────────────────────────────────────────────────┘
```

### 10.5 Security Field Interactions Summary

The following diagram summarizes how security-related fields on `sk_buff` interact
with various kernel subsystems:

```
 ┌──────────────────────────────────────────────────────────────────┐
 │  sk_buff Security Fields and Their Consumers                     │
 │                                                                  │
 │  ┌─────────────────┐                                             │
 │  │    sk_buff       │                                             │
 │  │                  │                                             │
 │  │  .secmark ───────┼──────► SELinux / AppArmor                  │
 │  │                  │        (access control decisions)           │
 │  │                  │                                             │
 │  │  .mark ──────────┼──────► Netfilter (matching)                │
 │  │                  │        Policy routing (fwmark)             │
 │  │                  │        Traffic control (tc)                 │
 │  │                  │                                             │
 │  │  ._nfct ─────────┼──────► Connection tracking                 │
 │  │                  │        NAT (address translation)           │
 │  │                  │        Stateful firewalling                │
 │  │                  │                                             │
 │  │  sec_path ───────┼──────► IPsec / XFRM                       │
 │  │  (extension)     │        ESP/AH verification                 │
 │  │                  │        Security policy enforcement         │
 │  │                  │                                             │
 │  │  nf_bridge ──────┼──────► Bridge netfilter                    │
 │  │  (extension)     │        Physical device tracking            │
 │  │                  │        Bridged IP filtering                │
 │  └─────────────────┘                                             │
 └──────────────────────────────────────────────────────────────────┘
```

---

## Appendix A: Key Data Structure Relationships

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                                                                          │
 │  ┌──────────┐                                                            │
 │  │ sk_buff  │                                                            │
 │  │          │                                                            │
 │  │  .sk ────┼───────────────────────────►┌──────────┐                    │
 │  │          │                            │ struct   │                    │
 │  │          │                            │ sock     │                    │
 │  │          │                            │          │                    │
 │  │          │                            │ .sk_mark │                    │
 │  │          │                            │ .sk_prio │                    │
 │  │  .dev ───┼────────►┌──────────────┐   │ .sk_dst  │                    │
 │  │          │         │ net_device   │   └──────────┘                    │
 │  │          │         │              │                                   │
 │  │          │         │ .nd_net ─────┼───►┌──────────┐                   │
 │  │          │         │              │    │ struct   │                   │
 │  │          │         │ .ifindex     │    │ net      │                   │
 │  │  ._skb   │         └──────────────┘    │          │                   │
 │  │  refdst─┼────►┌──────────────┐         │ .ipv4   │                   │
 │  │          │     │ dst_entry    │         │ .nf     │                   │
 │  │          │     │              │         │ .ct     │                   │
 │  │          │     │ .dev (output)│         └──────────┘                   │
 │  │          │     │ .input()     │                                       │
 │  │          │     │ .output()    │                                       │
 │  │  ._nfct─┼──►┌──────────────┐ │                                       │
 │  │          │   │ nf_conn      │ │                                       │
 │  │          │   │              │ │                                       │
 │  │          │   │ .tuplehash[] │ │                                       │
 │  │          │   │ .status      │ │                                       │
 │  │          │   │ .mark        │ │                                       │
 │  │  .mark   │   └──────────────┘ │                                       │
 │  │  .secmark│                    │                                       │
 │  │  .prior  │   └──────────────┘                                        │
 │  │  .protcl │                                                            │
 │  │  .pkt_ty │                                                            │
 │  │  .ip_sum │                                                            │
 │  │  .vlan   │                                                            │
 │  │  .skb_iif│                                                            │
 │  └──────────┘                                                            │
 │                                                                          │
 └──────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix B: Field Quick Reference

| Field              | Type           | Set by                    | Used by                         |
|--------------------|----------------|---------------------------|---------------------------------|
| `skb->sk`          | `struct sock *`| Transport TX / RX lookup  | Memory accounting, options      |
| `skb->dev`         | `net_device *` | Driver RX / routing TX    | Namespace lookup, TX path       |
| `skb->skb_iif`     | `int`          | `__netif_receive_skb`     | Netfilter input interface match |
| `skb->_skb_refdst` | `unsigned long`| `ip_route_input/output`   | Forwarding, output path         |
| `skb->_nfct`       | `unsigned long`| Conntrack hooks           | NAT, stateful firewall          |
| `skb->mark`        | `__u32`        | Netfilter, socket         | Policy routing, tc, matching    |
| `skb->priority`    | `__u32`        | Socket, TOS mapping       | Queueing disciplines            |
| `skb->tc_index`    | `__u16`        | tc actions, CLASSIFY      | tcindex classifier              |
| `skb->protocol`    | `__be16`       | `eth_type_trans()`        | Protocol handler dispatch       |
| `skb->pkt_type`    | `__u8` (3-bit) | `eth_type_trans()`        | Delivery decisions              |
| `skb->vlan_tci`    | `__u16`        | Driver / VLAN code        | VLAN device selection           |
| `skb->vlan_proto`  | `__be16`       | Driver / VLAN code        | VLAN protocol identification    |
| `skb->ip_summed`   | `__u8` (2-bit) | Driver RX / transport TX  | Checksum verification/offload   |
| `skb->csum`        | `__wsum`       | Hardware / software       | Checksum computation            |
| `skb->csum_start`  | `__u16`        | Transport layer TX        | TX checksum offload             |
| `skb->csum_offset` | `__u16`        | Transport layer TX        | TX checksum offload             |
| `skb->secmark`     | `__u32`        | SECMARK target            | SELinux access control          |

---

## Appendix C: Namespace and Routing Interaction Example

The following annotated walkthrough traces a packet from a container through veth,
across namespaces, through routing and netfilter, to an external NIC:

```c
/*
 * Scenario: Container in netns "ctr1" sends a TCP SYN to 8.8.8.8:53
 *
 * Container has:  veth-ctr1 (10.0.0.2/24) in netns "ctr1"
 * Host has:       veth-host (10.0.0.1/24) in init_net
 *                 eth0      (192.168.1.10/24) in init_net
 *
 * NAT rule in init_net: MASQUERADE on eth0
 */

/* === STEP 1: Container's TCP stack builds the skb === */
/* In netns "ctr1" */
skb->sk       = container_socket;           /* TCP socket in ctr1          */
skb->dev      = NULL;                       /* not yet determined          */
skb->mark     = sk->sk_mark;               /* inherit from socket         */
skb->priority = sk->sk_priority;            /* inherit from socket         */

/* TCP sets up checksum offload */
skb->ip_summed  = CHECKSUM_PARTIAL;
skb->csum_start = transport_header_offset;
skb->csum_offset = offsetof(struct tcphdr, check);

/* === STEP 2: ip_route_output_flow() in ctr1's namespace === */
/* FIB lookup in ctr1: 8.8.8.8 → default route via 10.0.0.1 dev veth-ctr1 */
skb_dst_set(skb, &rt->dst);
skb->dev = veth_ctr1;                      /* output device in ctr1       */
/* dev_net(skb->dev) = netns "ctr1" */

/* === STEP 3: NF_INET_LOCAL_OUT in ctr1 === */
/* Conntrack: NEW connection */
/* nf_ct_set(skb, ct, IP_CT_NEW) */
skb->_nfct = (unsigned long)ct | IP_CT_NEW;

/* === STEP 4: NF_INET_POST_ROUTING in ctr1 === */
/* No NAT rules in ctr1 → NF_ACCEPT */

/* === STEP 5: dev_queue_xmit() → veth_xmit() === */
/* veth_xmit() on veth-ctr1:
 *   skb->dev = veth-host;                 (peer in init_net)
 *   dev_forward_skb(veth-host, skb);      (re-enter RX in init_net)
 */

/* === STEP 6: __netif_receive_skb() in init_net === */
skb->skb_iif = veth_host->ifindex;          /* save input interface        */
/* dev_net(skb->dev) = init_net */
skb->protocol = ETH_P_IP;                  /* set by eth_type_trans()     */
skb->pkt_type = PACKET_HOST;               /* destined for this host      */

/* === STEP 7: ip_rcv() → NF_INET_PRE_ROUTING in init_net === */
/* Conntrack lookup: finds the ct entry from step 3 (RELATED/ESTABLISHED) */
/* No DNAT rules → NF_ACCEPT */

/* === STEP 8: ip_route_input() in init_net === */
/* FIB lookup: 8.8.8.8 → not local → FORWARD via eth0 */
skb_dst_set(skb, &rt->dst);
/* rt->dst.input = ip_forward */
/* rt->dst.dev   = eth0 */

/* === STEP 9: ip_forward() === */
/* TTL-- */
skb->dev = eth0;                            /* change to output device     */
/* skb_iif still = veth-host->ifindex */

/* === STEP 10: NF_INET_FORWARD in init_net === */
/* Filter rules evaluated → NF_ACCEPT */

/* === STEP 11: NF_INET_POST_ROUTING in init_net === */
/* MASQUERADE rule matches:
 *   SNAT: 10.0.0.2 → 192.168.1.10
 *   Modify IP saddr in skb data
 *   Modify TCP sport (if port remap needed)
 *   Update checksums incrementally
 *   Store NAT mapping in conntrack entry
 */

/* === STEP 12: dev_queue_xmit() on eth0 === */
/* ip_summed = CHECKSUM_PARTIAL → NIC computes TCP checksum */
/* skb_orphan(skb) → skb->sk = NULL */
/* Frame transmitted on wire */
```

---

## Appendix D: Conntrack State Machine (Complete)

```
 ┌──────────────────────────────────────────────────────────────────┐
 │  UDP Conntrack States                                            │
 │                                                                  │
 │  First packet (either direction)                                 │
 │       │                                                          │
 │       ▼                                                          │
 │  ┌────────────┐   timeout: 30s                                   │
 │  │   NEW      │   (nf_conntrack_udp_timeout)                     │
 │  └─────┬──────┘                                                  │
 │        │  Reply packet seen                                      │
 │        ▼                                                         │
 │  ┌────────────┐   timeout: 180s                                  │
 │  │ ESTABLISHED│   (nf_conntrack_udp_timeout_stream)              │
 │  │ + ASSURED  │                                                  │
 │  └─────┬──────┘                                                  │
 │        │  Timeout expires                                        │
 │        ▼                                                         │
 │  ┌────────────┐                                                  │
 │  │ DESTROYED  │                                                  │
 │  └────────────┘                                                  │
 └──────────────────────────────────────────────────────────────────┘

 ┌──────────────────────────────────────────────────────────────────┐
 │  ICMP Conntrack States                                           │
 │                                                                  │
 │  ICMP Echo Request                                               │
 │       │                                                          │
 │       ▼                                                          │
 │  ┌────────────┐   timeout: 30s                                   │
 │  │   NEW      │   (nf_conntrack_icmp_timeout)                    │
 │  └─────┬──────┘                                                  │
 │        │  ICMP Echo Reply seen                                   │
 │        ▼                                                         │
 │  ┌────────────┐   short timeout (reply received = done)          │
 │  │ ESTABLISHED│                                                  │
 │  └─────┬──────┘                                                  │
 │        │  Timeout expires                                        │
 │        ▼                                                         │
 │  ┌────────────┐                                                  │
 │  │ DESTROYED  │                                                  │
 │  └────────────┘                                                  │
 │                                                                  │
 │  ICMP errors (Dest Unreachable, etc.):                           │
 │  └── Classified as RELATED to the original connection            │
 │      that triggered the error                                    │
 └──────────────────────────────────────────────────────────────────┘
```

---

## Appendix E: Netfilter Table and Chain Traversal Order

The following table shows which iptables tables are traversed at each hook point,
in priority order:

```
 ┌───────────────┬────────────────────────────────────────────────┐
 │  Hook Point   │  Tables traversed (in order of priority)      │
 ├───────────────┼────────────────────────────────────────────────┤
 │  PRE_ROUTING  │  raw → conntrack → mangle → nat (DNAT)       │
 ├───────────────┼────────────────────────────────────────────────┤
 │  LOCAL_IN     │  mangle → filter → security → nat (SNAT)     │
 │               │  → conntrack (confirm)                        │
 ├───────────────┼────────────────────────────────────────────────┤
 │  FORWARD      │  mangle → filter → security                  │
 ├───────────────┼────────────────────────────────────────────────┤
 │  LOCAL_OUT    │  raw → conntrack → mangle → nat (DNAT)       │
 │               │  → filter → security                         │
 ├───────────────┼────────────────────────────────────────────────┤
 │  POST_ROUTING │  mangle → nat (SNAT) → conntrack (confirm)   │
 └───────────────┴────────────────────────────────────────────────┘
```

Each table has a specific purpose:

| Table      | Purpose                                                       |
|------------|---------------------------------------------------------------|
| `raw`      | Bypass conntrack (`NOTRACK`/`CT --notrack`)                   |
| `mangle`   | Modify packet headers (TTL, TOS, mark)                        |
| `nat`      | Network Address Translation (SNAT, DNAT, MASQUERADE, REDIRECT)|
| `filter`   | Accept/drop decisions (the "firewall" table)                  |
| `security` | SELinux SECMARK labeling                                      |

---

## Appendix F: Kernel Configuration Options

The following `CONFIG_` options control compilation of the features discussed in this
chapter:

```
 ┌────────────────────────────────┬─────────────────────────────────────┐
 │  Config Option                 │  Feature                           │
 ├────────────────────────────────┼─────────────────────────────────────┤
 │  CONFIG_NET_NS                 │  Network namespace support          │
 │  CONFIG_VETH                   │  Virtual Ethernet pairs             │
 │  CONFIG_NETFILTER              │  Netfilter framework                │
 │  CONFIG_NF_CONNTRACK           │  Connection tracking                │
 │  CONFIG_NF_NAT                 │  NAT support                        │
 │  CONFIG_NF_TABLES              │  nftables (modern netfilter)        │
 │  CONFIG_IP_NF_IPTABLES         │  iptables (legacy netfilter)        │
 │  CONFIG_BRIDGE_NETFILTER       │  Bridge netfilter (br_netfilter)    │
 │  CONFIG_XFRM                   │  IPsec transform framework          │
 │  CONFIG_INET_ESP               │  ESP protocol                       │
 │  CONFIG_INET_AH                │  AH protocol                        │
 │  CONFIG_NETWORK_SECMARK        │  Security marking (secmark)         │
 │  CONFIG_VLAN_8021Q             │  802.1Q VLAN support                │
 │  CONFIG_BONDING                │  Link aggregation (bonding)         │
 │  CONFIG_NET_TEAM               │  Team driver                        │
 │  CONFIG_IP_ADVANCED_ROUTER     │  Policy routing (ip rule)           │
 │  CONFIG_IP_MULTIPLE_TABLES     │  Multiple routing tables            │
 └────────────────────────────────┴─────────────────────────────────────┘
```

---

*This chapter has covered the intersection of sk_buff with network namespaces,
routing, netfilter, connection tracking, packet marking, protocol identification,
checksum offload, and security labeling. These fields and subsystems form the
control plane of the Linux networking stack --- the metadata infrastructure that
determines where each packet goes and what transformations it undergoes. The next
chapter will examine performance optimization and hardware offload in greater depth.*
