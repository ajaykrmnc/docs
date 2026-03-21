# Hotspot Connection Pathway Documentation

This folder contains the comprehensive documentation for the WiFi hotspot connection pathway, split into logical sections for easier navigation.

## Document Structure

### Main Phases

| File | Description |
|------|-------------|
| [00_README.md](00_README.md) | Overview and connection pathway diagram |
| [01_phase1_ap_initialization.md](01_phase1_ap_initialization.md) | AP Initialization and Hotspot Enabling |
| [02_phase2_client_discovery.md](02_phase2_client_discovery.md) | Client Discovery (Scanning) |
| [03_phase3_authentication.md](03_phase3_authentication.md) | Authentication (Open, SAE/WPA3) |
| [04_phase4_association.md](04_phase4_association.md) | Association Process |
| [05_phase5_key_exchange.md](05_phase5_key_exchange.md) | 4-Way Handshake (WPA/WPA2/WPA3) |
| [06_phase6_dhcp.md](06_phase6_dhcp.md) | IP Address Assignment (DHCP) |
| [07_phase7_captive_portal.md](07_phase7_captive_portal.md) | Captive Portal (Optional) |
| [08_phase8_connected.md](08_phase8_connected.md) | Connected State |

### Advanced Topics

| File | Description |
|------|-------------|
| [09_hotspot_2.0_passpoint.md](09_hotspot_2.0_passpoint.md) | Hotspot 2.0 (Passpoint) Connection |
| [10_roaming.md](10_roaming.md) | Roaming Between APs |
| [11_troubleshooting.md](11_troubleshooting.md) | Troubleshooting Connection Issues |
| [12_related_tests.md](12_related_tests.md) | Related Tests |
| [13_configuration_examples.md](13_configuration_examples.md) | Configuration Examples |
| [14_references.md](14_references.md) | References |

### Appendices

All appendices are located in the `appendices/` subfolder:

#### Core Appendices (A-Z)

| File | Description |
|------|-------------|
| [A_frame_formats.md](appendices/A_frame_formats.md) | 802.11 Frame Formats |
| [B_key_derivation.md](appendices/B_key_derivation.md) | Key Derivation Functions |
| [C_timing_diagrams.md](appendices/C_timing_diagrams.md) | Protocol Timing Diagrams |
| [D_source_code_refs.md](appendices/D_source_code_refs.md) | Source Code References |
| [E_glossary.md](appendices/E_glossary.md) | Glossary |
| [F_security_analysis.md](appendices/F_security_analysis.md) | Security Analysis |
| [G_performance_optimization.md](appendices/G_performance_optimization.md) | Performance Optimization |
| [H_protocol_state_machines.md](appendices/H_protocol_state_machines.md) | Protocol State Machines |
| [I_vendor_specific_ies.md](appendices/I_vendor_specific_ies.md) | Vendor-Specific Information Elements |
| [J_wifi6_6e_7_enhancements.md](appendices/J_wifi6_6e_7_enhancements.md) | WiFi 6/6E/7 Enhancements |
| [K_packet_capture.md](appendices/K_packet_capture.md) | Packet Capture Analysis |
| [L_regulatory_domains.md](appendices/L_regulatory_domains.md) | Regulatory Domains |
| [M_client_compatibility.md](appendices/M_client_compatibility.md) | Client Compatibility Matrix |
| [N_common_config_mistakes.md](appendices/N_common_config_mistakes.md) | Common Configuration Mistakes |
| [O_eap_methods.md](appendices/O_eap_methods.md) | EAP Method Deep Dive |
| [P_band_steering.md](appendices/P_band_steering.md) | Band Steering and Load Balancing |
| [Q_mesh_networking.md](appendices/Q_mesh_networking.md) | Mesh Networking (802.11s) |
| [R_power_save.md](appendices/R_power_save.md) | Power Save Mechanisms |
| [S_radius_attributes.md](appendices/S_radius_attributes.md) | RADIUS Attribute Reference |
| [T_debug_commands.md](appendices/T_debug_commands.md) | Debug Commands Reference |
| [U_failure_flowchart.md](appendices/U_failure_flowchart.md) | Connection Failure Flowchart |
| [V_quick_reference.md](appendices/V_quick_reference.md) | Quick Reference Card |
| [W_wifi7_features.md](appendices/W_wifi7_features.md) | WiFi 7 (802.11be) Features |
| [X_hotspot2_deep_dive.md](appendices/X_hotspot2_deep_dive.md) | Hotspot 2.0 Deep Dive |
| [Y_glossary_terms.md](appendices/Y_glossary_terms.md) | Glossary of Terms |
| [Z_standards_reference.md](appendices/Z_standards_reference.md) | Standards Reference |

#### Extended Appendices (AA+)

| File | Description |
|------|-------------|
| [AA_security_attacks.md](appendices/AA_security_attacks.md) | Security Attack Vectors and Mitigations |
| [AC_hostapd_config_ref.md](appendices/AC_hostapd_config_ref.md) | Complete hostapd Configuration Reference |
| [AD_frame_format_ref.md](appendices/AD_frame_format_ref.md) | Frame Format Reference |
| [AE_ie_catalog.md](appendices/AE_ie_catalog.md) | Information Element Catalog |
| [AF_status_reason_codes.md](appendices/AF_status_reason_codes.md) | Status and Reason Codes |
| [AG_vendor_extensions.md](appendices/AG_vendor_extensions.md) | Vendor-Specific Extensions |
| [AH_debugging_logging.md](appendices/AH_debugging_logging.md) | Debugging and Logging |
| [AI_test_cases.md](appendices/AI_test_cases.md) | Test Case Reference |

#### Extended Content (Consolidated)

| File | Description |
|------|-------------|
| [extended_appendices_part1.md](appendices/extended_appendices_part1.md) | AJ-AZ: Regulatory, Actions, Errors, Wireshark |
| [extended_appendices_part2.md](appendices/extended_appendices_part2.md) | BA-BZ: Client Config, VLAN, IoT, Captive Portal |
| [extended_appendices_part3.md](appendices/extended_appendices_part3.md) | CA-CZ: WiFi 6E, OFDMA, MU-MIMO, Power Management |
| [extended_appendices_part4.md](appendices/extended_appendices_part4.md) | DA-DZ: CLI, API, Automation, Site Survey |
| [extended_appendices_part5.md](appendices/extended_appendices_part5.md) | EA-EZ: Location, Monitoring, Zero Trust |
| [extended_appendices_part6.md](appendices/extended_appendices_part6.md) | FA-FZ: VoWiFi, QoS, Mesh, RADIUS, PKI |
| [extended_appendices_part7.md](appendices/extended_appendices_part7.md) | GA-GZ: ML, Edge Computing, WiFi Sensing, Summary |

## Quick Navigation

### By Topic

**Getting Started:**
- [Overview](00_README.md) → [Phase 1: Init](01_phase1_ap_initialization.md) → [Phase 2: Discovery](02_phase2_client_discovery.md)

**Security:**
- [Phase 3: Auth](03_phase3_authentication.md) → [Phase 5: 4-Way Handshake](05_phase5_key_exchange.md) → [Security Analysis](appendices/F_security_analysis.md)

**Troubleshooting:**
- [Troubleshooting](11_troubleshooting.md) → [Failure Flowchart](appendices/U_failure_flowchart.md) → [Debug Commands](appendices/T_debug_commands.md)

**Advanced Features:**
- [Hotspot 2.0](09_hotspot_2.0_passpoint.md) → [Roaming](10_roaming.md) → [WiFi 6/7](appendices/J_wifi6_6e_7_enhancements.md)

## Original Document

The original monolithic document is preserved at:
- [HOTSPOT_CONNECTION_PATHWAY.md](../HOTSPOT_CONNECTION_PATHWAY.md)

## Related Documentation

- [DRIVERS.md](../DRIVERS.md) - Driver documentation
- [QCA_ARISTA_INTEGRATION.md](../QCA_ARISTA_INTEGRATION.md) - QCA integration
- [ASAN_MEMORY_DEBUGGING.md](../ASAN_MEMORY_DEBUGGING.md) - Memory debugging

