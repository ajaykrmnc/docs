import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Arista Documentation",
  description: "Technical documentation for Arista systems",
  base: '/docs/', // GitHub Pages base path: https://ajaykrmnc.github.io/docs/
  ignoreDeadLinks: true,
  
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Build & Tooling', link: '/build-and-tooling/' },
      { text: 'Kernel & System', link: '/kernel-and-system/' },
      { text: 'Networking', link: '/networking/' },
      { text: 'WiFi & Wireless', link: '/wifi-and-wireless/' },
      { text: 'WLAN Drivers', link: '/wlan-drivers/' }
    ],

    sidebar: {
      '/build-and-tooling/': [
        {
          text: 'Build & Tooling',
          items: [
            { text: 'ARM vs x86 Architecture', link: '/build-and-tooling/ARM_vs_x86_Architecture_Guide' },
            { text: 'Cross Compilation Guide', link: '/build-and-tooling/Cross_Compilation_Guide' },
            { text: 'Makefile Commands', link: '/build-and-tooling/MAKEFILE_COMMANDS' },
            { text: 'Repository Analysis', link: '/build-and-tooling/Repository_Analysis_Rebuild_Estimation' }
          ]
        }
      ],
      '/kernel-and-system/': [
        {
          text: 'Kernel & System',
          items: [
            { text: 'AR Meta Cache Debug', link: '/kernel-and-system/AR_META_CACHE_DEBUG_GUIDE' },
            { text: 'Kernel Userspace', link: '/kernel-and-system/KERNEL_USERSPACE' },
            { text: 'Linux Kernel Build Lifecycle', link: '/kernel-and-system/LINUX_KERNEL_BUILD_LIFECYCLE' },
            { text: 'Netlink IOCTL', link: '/kernel-and-system/NETLINK_IOCTL' },
            { text: 'AR Meta SKB Guide', link: '/kernel-and-system/ar_meta_skb_guide' },
            { text: 'Kernel Patch Management', link: '/kernel-and-system/kernel-patch-management' },
            { text: 'Kernel Debug Print Guide', link: '/kernel-and-system/kernel_debug_print_guide' },
            { text: 'Linux 5.4 Patch Workflow', link: '/kernel-and-system/linux-5.4-patch-workflow' },
            { text: 'SK Buff Modification Guide', link: '/kernel-and-system/sk_buff_modification_guide' },
            { text: 'SK Buff vs Data Packets', link: '/kernel-and-system/sk_buff_vs_data_packets' },
            { text: 'SK Buff vs QDF NBuf', link: '/kernel-and-system/sk_buff_vs_qdf_nbuf' },
            { text: 'SK Sock SK Buff', link: '/kernel-and-system/sk_sock_sk_buff_doc' },
            { text: 'SKB Field Dependencies', link: '/kernel-and-system/skb_field_dependencies' },
            { text: 'SKB TID Metadata Flow', link: '/kernel-and-system/skb_tid_metadata_flow' }
          ]
        }
      ],
      '/networking/': [
        {
          text: 'Networking',
          items: [
            { text: 'Bridges and Tunnels', link: '/networking/BRIDGES_AND_TUNNELS' },
            { text: 'DHCP Documentation', link: '/networking/DHCP_Documentation' },
            { text: 'DSCP Documentation', link: '/networking/DSCP_Documentation' },
            { text: 'Networking Interfaces', link: '/networking/Networking_Interfaces_Documentation' },
            { text: 'Proxy', link: '/networking/PROXY' },
            { text: 'QoS Downstream Traffic', link: '/networking/QoS_Downstream_Traffic_Management' },
            { text: 'TOS Documentation', link: '/networking/TOS_Documentation' },
            { text: 'Tunnel Interface and VXLAN', link: '/networking/TUNNEL_INTERFACE_AND_VXLAN' },
            { text: 'Upstream Downstream', link: '/networking/Upstream_Downstream_Documentation' }
          ]
        }
      ],
      '/wifi-and-wireless/': [
        {
          text: 'WiFi & Wireless',
          items: [
            { text: 'AP Data Generation', link: '/wifi-and-wireless/AP_DATA_GENERATION' },
            { text: 'DHCP and Beacon', link: '/wifi-and-wireless/DHCP_AND_BEACON' },
            { text: 'HostAPD', link: '/wifi-and-wireless/HOSTAPD' },
            { text: 'Hotspot Connection Pathway', link: '/wifi-and-wireless/HOTSPOT_CONNECTION_PATHWAY' },
            { text: 'Hotspot', link: '/wifi-and-wireless/Hotspot' },
            { text: 'Inter AP Communication', link: '/wifi-and-wireless/INTER_AP_COMMUNICATION' },
            { text: 'RADIUS', link: '/wifi-and-wireless/RADIUS' },
            { text: 'WiFi Standards Compliance', link: '/wifi-and-wireless/WIFI_STANDARDS_COMPLIANCE' },
            { text: 'WPA/WPA2 Security', link: '/wifi-and-wireless/WPA_WPA2_SECURITY' },
            { text: 'Ethernet vs WiFi', link: '/wifi-and-wireless/ethernet-vs-wifi' }
          ]
        }
      ],
      '/wlan-drivers/': [
        {
          text: 'WLAN Drivers',
          items: [
            { text: 'ApQoS Test Documentation', link: '/wlan-drivers/ApQoSTest_Documentation' },
            { text: 'Datapath Controlpath', link: '/wlan-drivers/DATAPATH_CONTROLPATH' },
            { text: 'Drivers', link: '/wlan-drivers/DRIVERS' },
            { text: 'QCA Arista Integration', link: '/wlan-drivers/QCA_ARISTA_INTEGRATION' },
            { text: 'QoS Configuration Guide', link: '/wlan-drivers/QoS_Configuration_Guide' },
            { text: 'TID Investigation Report', link: '/wlan-drivers/TID_Investigation_Report' },
            { text: 'VAP OSIF', link: '/wlan-drivers/VAP_OSIF' },
            { text: 'AR Meta Cache', link: '/wlan-drivers/ar_meta_cache' },
            { text: 'AR Meta Cache Patch Analysis', link: '/wlan-drivers/ar_meta_cache_patch_analysis_SPF12.2_vs_SPF12.5' },
            { text: 'Codebase Structure', link: '/wlan-drivers/codebase_structure' },
            { text: 'PDEV vs VDEV', link: '/wlan-drivers/pdev_vs_vdev_documentation' },
            { text: 'WLAN Drivers Terminology', link: '/wlan-drivers/wlan_drivers_terminology' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/ajaykrmnc/docs' }
    ],

    search: {
      provider: 'local'
    }
  }
})

