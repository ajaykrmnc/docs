## Appendix S: RADIUS Attribute Reference

### S.1 Standard RADIUS Attributes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STANDARD RADIUS ATTRIBUTES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Attr#  Name                      Type        Description                   │
│  ─────  ────                      ────        ───────────                   │
│    1    User-Name                 String      Username for authentication   │
│    2    User-Password             String      User's password (encrypted)   │
│    3    CHAP-Password             String      CHAP response                 │
│    4    NAS-IP-Address            IP Addr     IP of the AP                  │
│    5    NAS-Port                  Integer     Physical port number          │
│    6    Service-Type              Integer     Type of service requested     │
│    7    Framed-Protocol           Integer     Framing protocol              │
│    8    Framed-IP-Address         IP Addr     IP to assign to user          │
│    9    Framed-IP-Netmask         IP Addr     Netmask for user              │
│   10    Framed-Routing            Integer     Routing method                │
│   11    Filter-Id                 String      Filter to apply               │
│   12    Framed-MTU                Integer     MTU for user                  │
│   13    Framed-Compression        Integer     Compression protocol          │
│   18    Reply-Message             String      Message to display            │
│   24    State                     String      State for multi-round auth    │
│   25    Class                     String      Accounting class              │
│   26    Vendor-Specific           String      Vendor-specific attributes    │
│   27    Session-Timeout           Integer     Session timeout (seconds)     │
│   28    Idle-Timeout              Integer     Idle timeout (seconds)        │
│   29    Termination-Action        Integer     Action on session end         │
│   30    Called-Station-Id         String      AP MAC:SSID                   │
│   31    Calling-Station-Id        String      Client MAC address            │
│   32    NAS-Identifier            String      AP identifier string          │
│   40    Acct-Status-Type          Integer     Start/Stop/Interim            │
│   41    Acct-Delay-Time           Integer     Delay since event             │
│   42    Acct-Input-Octets         Integer     Bytes received                │
│   43    Acct-Output-Octets        Integer     Bytes sent                    │
│   44    Acct-Session-Id           String      Unique session ID             │
│   45    Acct-Authentic            Integer     How user was authenticated    │
│   46    Acct-Session-Time         Integer     Session duration (seconds)    │
│   47    Acct-Input-Packets        Integer     Packets received              │
│   48    Acct-Output-Packets       Integer     Packets sent                  │
│   49    Acct-Terminate-Cause      Integer     Reason for session end        │
│   50    Acct-Multi-Session-Id     String      Multi-link session ID         │
│   51    Acct-Link-Count           Integer     Number of links               │
│   52    Acct-Input-Gigawords      Integer     Input octets / 2^32           │
│   53    Acct-Output-Gigawords     Integer     Output octets / 2^32          │
│   55    Event-Timestamp           Date        Time of event                 │
│   60    CHAP-Challenge            String      CHAP challenge                │
│   61    NAS-Port-Type             Integer     Type of port (Wireless)       │
│   64    Tunnel-Type               Integer     Tunnel protocol               │
│   65    Tunnel-Medium-Type        Integer     Transport medium              │
│   79    EAP-Message               String      EAP packet                    │
│   80    Message-Authenticator     String      HMAC-MD5 of packet            │
│   81    Tunnel-Private-Group-Id   String      VLAN ID                       │
│   87    NAS-Port-Id               String      Port identifier               │
│   89    Chargeable-User-Identity  String      CUI for accounting            │
│   95    NAS-IPv6-Address          IPv6 Addr   IPv6 of the AP                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### S.2 Vendor-Specific Attributes (VSA)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VENDOR-SPECIFIC ATTRIBUTES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Microsoft (Vendor ID: 311)                                                  │
│  ─────────────────────────                                                   │
│  VSA#  Name                      Description                                │
│  ────  ────                      ───────────                                │
│   10   MS-CHAP-Response          MS-CHAP response                           │
│   11   MS-CHAP-Error             Error message                              │
│   16   MS-MPPE-Send-Key          MPPE send key (for PTK)                    │
│   17   MS-MPPE-Recv-Key          MPPE receive key (for PTK)                 │
│   25   MS-MPPE-Encryption-Policy Encryption required                        │
│   26   MS-MPPE-Encryption-Types  Encryption types allowed                   │
│                                                                              │
│  Cisco (Vendor ID: 9)                                                        │
│  ────────────────────                                                        │
│  VSA#  Name                      Description                                │
│  ────  ────                      ───────────                                │
│    1   Cisco-AVPair              Attribute-value pair                       │
│  252   Cisco-Audit-Session-Id    Session ID for CoA                         │
│                                                                              │
│  Arista/Airtight (Vendor ID: 16901)                                          │
│  ──────────────────────────────────                                          │
│  VSA#  Name                      Description                                │
│  ────  ────                      ───────────                                │
│    1   Airtight-Bandwidth-Up     Upstream bandwidth limit (Kbps)            │
│    2   Airtight-Bandwidth-Down   Downstream bandwidth limit (Kbps)          │
│    3   Airtight-Role             User role assignment                       │
│    4   Airtight-VLAN             VLAN assignment                            │
│    5   Airtight-Session-Timeout  Session timeout override                   │
│                                                                              │
│  Example RADIUS Response with VSAs:                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Access-Accept                                                       │    │
│  │   User-Name = "user@example.com"                                    │    │
│  │   Class = "employee"                                                │    │
│  │   Session-Timeout = 28800                                           │    │
│  │   Tunnel-Type = VLAN                                                │    │
│  │   Tunnel-Medium-Type = IEEE-802                                     │    │
│  │   Tunnel-Private-Group-Id = "100"                                   │    │
│  │   MS-MPPE-Send-Key = 0x...                                          │    │
│  │   MS-MPPE-Recv-Key = 0x...                                          │    │
│  │   Airtight-Bandwidth-Up = 10000                                     │    │
│  │   Airtight-Bandwidth-Down = 50000                                   │    │
│  │   Airtight-Role = "standard"                                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### S.3 Acct-Terminate-Cause Values

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACCOUNTING TERMINATE CAUSES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Value  Name                      Description                               │
│  ─────  ────                      ───────────                               │
│    1    User-Request              User initiated disconnect                 │
│    2    Lost-Carrier              Connection lost                           │
│    3    Lost-Service              Service unavailable                       │
│    4    Idle-Timeout              Idle timeout expired                      │
│    5    Session-Timeout           Session timeout expired                   │
│    6    Admin-Reset               Administrator reset                       │
│    7    Admin-Reboot              System reboot                             │
│    8    Port-Error                Port error                                │
│    9    NAS-Error                 NAS error                                 │
│   10    NAS-Request               NAS initiated disconnect                  │
│   11    NAS-Reboot                NAS reboot                                │
│   12    Port-Unneeded             Port no longer needed                     │
│   13    Port-Preempted            Port preempted                            │
│   14    Port-Suspended            Port suspended                            │
│   15    Service-Unavailable       Service unavailable                       │
│   16    Callback                  Callback                                  │
│   17    User-Error                User error                                │
│   18    Host-Request              Host request                              │
│   19    Supplicant-Restart        Supplicant restarted                      │
│   20    Reauthentication-Failure  Reauth failed                             │
│   21    Port-Reinit               Port reinitialized                        │
│   22    Port-Disabled             Port disabled                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

