## Appendix T: Debug Commands Reference

### T.1 hostapd Debug Commands

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HOSTAPD DEBUG COMMANDS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  # Connect to hostapd control interface                                      │
│  hostapd_cli -i wlan0                                                        │
│                                                                              │
│  # Status commands                                                           │
│  > status                    # Show AP status                                │
│  > status-driver             # Show driver status                            │
│  > get_config                # Show current configuration                    │
│                                                                              │
│  # Station commands                                                          │
│  > sta <MAC>                 # Show station info                             │
│  > all_sta                   # Show all stations                             │
│  > list_sta                  # List station MACs                             │
│  > deauthenticate <MAC>      # Disconnect station                            │
│  > disassociate <MAC>        # Disassociate station                          │
│                                                                              │
│  # Security commands                                                         │
│  > wps_pbc                   # Start WPS push button                         │
│  > wps_pin <PIN>             # Start WPS with PIN                            │
│  > wps_cancel                # Cancel WPS                                    │
│  > pmksa                     # Show PMKSA cache                              │
│  > pmksa_flush               # Flush PMKSA cache                             │
│                                                                              │
│  # Channel commands                                                          │
│  > chan_switch <count> <freq> [options]  # Channel switch                    │
│  > dfs_radar_detected        # Simulate radar detection                      │
│                                                                              │
│  # Logging                                                                   │
│  > log_level <module> <level>  # Set log level                               │
│  > log_level                   # Show current log levels                     │
│                                                                              │
│  # BSS Transition (802.11v)                                                  │
│  > bss_tm_req <MAC> [options]  # Send BTM request                            │
│                                                                              │
│  # Neighbor Report (802.11k)                                                 │
│  > set_neighbor <BSSID> <SSID> <NR>  # Add neighbor                          │
│  > remove_neighbor <BSSID>           # Remove neighbor                       │
│  > show_neighbor                     # Show neighbors                        │
│                                                                              │
│  # Debug                                                                     │
│  > level <0-4>               # Set debug level                               │
│  > mib                       # Show MIB                                      │
│  > help                      # Show all commands                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### T.2 wpa_supplicant Debug Commands

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WPA_SUPPLICANT DEBUG COMMANDS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  # Connect to wpa_supplicant control interface                               │
│  wpa_cli -i wlan0                                                            │
│                                                                              │
│  # Status commands                                                           │
│  > status                    # Show connection status                        │
│  > status verbose            # Detailed status                               │
│  > signal_poll               # Show signal strength                          │
│                                                                              │
│  # Scanning                                                                  │
│  > scan                      # Trigger scan                                  │
│  > scan_results              # Show scan results                             │
│  > bss <BSSID>               # Show BSS details                              │
│                                                                              │
│  # Network management                                                        │
│  > list_networks             # List configured networks                      │
│  > add_network               # Add new network                               │
│  > remove_network <id>       # Remove network                                │
│  > set_network <id> <param> <value>  # Set network parameter                 │
│  > enable_network <id>       # Enable network                                │
│  > disable_network <id>      # Disable network                               │
│  > select_network <id>       # Select network                                │
│                                                                              │
│  # Connection                                                                │
│  > reassociate               # Reconnect                                     │
│  > reconnect                 # Reconnect if disconnected                     │
│  > disconnect                # Disconnect                                    │
│                                                                              │
│  # Roaming                                                                   │
│  > roam <BSSID>              # Roam to specific AP                           │
│  > ft_ds <BSSID>             # FT over DS to AP                              │
│                                                                              │
│  # Security                                                                  │
│  > pmksa                     # Show PMKSA cache                              │
│  > pmksa_flush               # Flush PMKSA cache                             │
│                                                                              │
│  # Debug                                                                     │
│  > log_level <level>         # Set log level                                 │
│  > dump                      # Dump state                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### T.3 iw Debug Commands

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    IW DEBUG COMMANDS                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  # Device information                                                        │
│  iw dev                      # List wireless devices                         │
│  iw dev wlan0 info           # Show device info                              │
│  iw phy phy0 info            # Show PHY capabilities                         │
│                                                                              │
│  # Scanning                                                                  │
│  iw dev wlan0 scan           # Trigger and show scan                         │
│  iw dev wlan0 scan dump      # Show cached scan results                      │
│                                                                              │
│  # Station info                                                              │
│  iw dev wlan0 station dump   # Show all connected stations                   │
│  iw dev wlan0 station get <MAC>  # Show specific station                     │
│                                                                              │
│  # Link info                                                                 │
│  iw dev wlan0 link           # Show current link                             │
│                                                                              │
│  # Survey (channel utilization)                                              │
│  iw dev wlan0 survey dump    # Show channel survey                           │
│                                                                              │
│  # Regulatory                                                                │
│  iw reg get                  # Show regulatory domain                        │
│  iw reg set US               # Set regulatory domain                         │
│                                                                              │
│  # Channel                                                                   │
│  iw dev wlan0 set channel 36 # Set channel                                   │
│  iw dev wlan0 set freq 5180  # Set frequency                                 │
│                                                                              │
│  # Power                                                                     │
│  iw dev wlan0 set power_save on   # Enable power save                        │
│  iw dev wlan0 set power_save off  # Disable power save                       │
│  iw dev wlan0 get power_save      # Show power save state                    │
│                                                                              │
│  # Events                                                                    │
│  iw event                    # Monitor events                                │
│  iw event -f                 # Monitor with frame dumps                      │
│  iw event -t                 # Monitor with timestamps                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### T.4 tcpdump Filters for WiFi

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TCPDUMP FILTERS FOR WIFI                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  # Capture all management frames                                             │
│  tcpdump -i wlan0 'type mgt'                                                 │
│                                                                              │
│  # Capture specific frame types                                              │
│  tcpdump -i wlan0 'type mgt subtype beacon'                                  │
│  tcpdump -i wlan0 'type mgt subtype probe-req'                               │
│  tcpdump -i wlan0 'type mgt subtype probe-resp'                              │
│  tcpdump -i wlan0 'type mgt subtype auth'                                    │
│  tcpdump -i wlan0 'type mgt subtype assoc-req'                               │
│  tcpdump -i wlan0 'type mgt subtype assoc-resp'                              │
│  tcpdump -i wlan0 'type mgt subtype deauth'                                  │
│  tcpdump -i wlan0 'type mgt subtype disassoc'                                │
│                                                                              │
│  # Capture EAPOL frames                                                      │
│  tcpdump -i wlan0 'ether proto 0x888e'                                       │
│                                                                              │
│  # Capture from/to specific MAC                                              │
│  tcpdump -i wlan0 'wlan addr1 00:11:22:33:44:55'                             │
│  tcpdump -i wlan0 'wlan addr2 00:11:22:33:44:55'                             │
│                                                                              │
│  # Capture DHCP                                                              │
│  tcpdump -i wlan0 'port 67 or port 68'                                       │
│                                                                              │
│  # Capture DNS                                                               │
│  tcpdump -i wlan0 'port 53'                                                  │
│                                                                              │
│  # Capture HTTP                                                              │
│  tcpdump -i wlan0 'port 80 or port 443'                                      │
│                                                                              │
│  # Capture RADIUS                                                            │
│  tcpdump -i eth0 'port 1812 or port 1813 or port 3799'                       │
│                                                                              │
│  # Write to file with rotation                                               │
│  tcpdump -i wlan0 -w capture.pcap -C 100 -W 10                               │
│                                                                              │
│  # Read and filter from file                                                 │
│  tcpdump -r capture.pcap 'type mgt subtype auth'                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

