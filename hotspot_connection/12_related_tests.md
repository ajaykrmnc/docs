## Related Tests

The following tests validate the hotspot connection pathway:

### 13.1 Authentication Tests

| Test File | Description |
|-----------|-------------|
| `WpaPersonalTest.py` | WPA/WPA2-PSK authentication |
| `Wpa3PersonalTest.py` | WPA3-SAE authentication |
| `WpaEnterpriseTest.py` | WPA/WPA2-Enterprise (802.1X) |
| `Wpa3EnterpriseTest.py` | WPA3-Enterprise with Suite B |
| `OweTest.py` | Enhanced Open (OWE) |
| `DppTest.py` | Device Provisioning Protocol |
| `FilsTest.py` | Fast Initial Link Setup |

### 13.2 Roaming Tests

| Test File | Description |
|-----------|-------------|
| `OkcTest.py` | Opportunistic Key Caching |
| `FastTransitionTest.py` | 802.11r Fast BSS Transition |
| `PMKCacheSyncTest.py` | PMK synchronization between APs |
| `BssTransitionTest.py` | 802.11v BSS Transition Management |
| `RoamingTest.py` | General roaming scenarios |

### 13.3 RADIUS Tests

| Test File | Description |
|-----------|-------------|
| `RadiusAcctServerTest.py` | RADIUS accounting |
| `RadiusBwCoaTest.py` | RADIUS CoA bandwidth control |
| `RadiusFqdnTest.py` | RADIUS server FQDN resolution |
| `RadiusPoolingTest.py` | RADIUS server load balancing |
| `RadsecproxyTest.py` | RadSec (RADIUS over TLS) |

### 13.4 Hotspot 2.0 Tests

| Test File | Description |
|-----------|-------------|
| `Hs20Test.py` | Hotspot 2.0 basic functionality |
| `AnqpTest.py` | ANQP query/response |
| `GasTest.py` | GAS protocol |
| `OsenTest.py` | OSU Server-Only Authenticated L2 Encryption |

### 13.5 Captive Portal Tests

| Test File | Description |
|-----------|-------------|
| `CaptivePortalTest.py` | Captive portal redirect |
| `WalledGardenTest.py` | Walled garden access |
| `ExternalPortalTest.py` | External portal integration |

### 13.6 Running Tests


```bash
# Run a specific test
cd /garage/workspace/ap/autotest/WifiClusterTest
python -m pytest ctest/WpaPersonalTest.py -v

# Run all authentication tests
python -m pytest ctest/Wpa*.py -v

# Run with specific AP configuration
python -m pytest ctest/OkcTest.py --ap-config=config/dual_ap.yaml -v

# Run with debug output
python -m pytest ctest/FastTransitionTest.py -v --log-cli-level=DEBUG
```

---

