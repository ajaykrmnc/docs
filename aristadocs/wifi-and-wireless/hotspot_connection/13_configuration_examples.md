## Configuration Examples

### 14.1 Basic WPA2-PSK Hotspot

```conf
# /etc/hostapd/hostapd.conf

interface=wlan0
driver=nl80211
ssid=MyHotspot
hw_mode=g
channel=6
ieee80211n=1

# Security
wpa=2
wpa_passphrase=MySecurePassword123
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP

# Optional: Enable WMM
wmm_enabled=1
```

### 14.2 WPA3-SAE Hotspot

```conf
# /etc/hostapd/hostapd.conf

interface=wlan0
driver=nl80211
ssid=SecureHotspot
hw_mode=a
channel=36
ieee80211n=1
ieee80211ac=1

# WPA3-SAE
wpa=2
wpa_key_mgmt=SAE
rsn_pairwise=CCMP
ieee80211w=2
sae_password=MySecurePassword123
sae_require_mfp=1
```

### 14.3 WPA2-Enterprise Hotspot

```conf
# /etc/hostapd/hostapd.conf

interface=wlan0
driver=nl80211
ssid=EnterpriseHotspot
hw_mode=a
channel=36

# WPA2-Enterprise
wpa=2
wpa_key_mgmt=WPA-EAP
rsn_pairwise=CCMP
ieee8021x=1

# RADIUS
auth_server_addr=192.168.1.100
auth_server_port=1812
auth_server_shared_secret=RadiusSecret123
acct_server_addr=192.168.1.100
acct_server_port=1813
acct_server_shared_secret=RadiusSecret123
```

### 14.4 Hotspot 2.0 Configuration

```conf
# /etc/hostapd/hostapd.conf

interface=wlan0
driver=nl80211
ssid=Passpoint-Hotspot
hw_mode=a
channel=36

# WPA2-Enterprise (required for HS2.0)
wpa=2
wpa_key_mgmt=WPA-EAP
rsn_pairwise=CCMP
ieee8021x=1

# Hotspot 2.0
hs20=1
interworking=1
access_network_type=2
internet=1
venue_group=2
venue_type=8
hessid=00:11:22:33:44:55

# Roaming Consortium
roaming_consortium=001122
roaming_consortium=334455667788

# NAI Realm
nai_realm=0,example.com,13[5:6],21[2:4][5:7]

# Domain Name
domain_name=example.com

# RADIUS
auth_server_addr=192.168.1.100
auth_server_port=1812
auth_server_shared_secret=RadiusSecret123
```

### 14.5 Fast Transition (802.11r) Configuration

```conf
# /etc/hostapd/hostapd.conf

interface=wlan0
driver=nl80211
ssid=FastRoamHotspot
hw_mode=a
channel=36

# WPA2-PSK with FT
wpa=2
wpa_passphrase=MySecurePassword123
wpa_key_mgmt=FT-PSK WPA-PSK
rsn_pairwise=CCMP

# 802.11r Fast Transition
mobility_domain=a1b2
ft_over_ds=1
ft_psk_generate_local=1
r0_key_lifetime=10000
r1_key_holder=000102030405
pmk_r1_push=1
nasid=ap1.example.com
```

### 14.6 Captive Portal Configuration

```conf
# /etc/hostapd/hostapd.conf

interface=wlan0
driver=nl80211
ssid=GuestHotspot
hw_mode=g
channel=6

# Open network (portal handles auth)
wpa=0

# Captive portal
# (Configured via portal daemon, not hostapd)
```

```yaml
# /etc/portal/portal.yaml

portal:
  mode: internal
  listen_ip: 192.0.2.254
  listen_port: 80

  authentication:
    method: click-through
    terms_url: /terms.html

  walled_garden:
    - captive.apple.com
    - connectivitycheck.gstatic.com
    - www.msftconnecttest.com

  session:
    timeout: 3600
    idle_timeout: 600
```

---

