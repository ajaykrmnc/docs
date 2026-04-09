import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Technical Documentation",
  description: "Comprehensive technical documentation covering systems programming, distributed systems, databases, networking, and more",
  base: '/docs/', // GitHub Pages base path: https://ajaykrmnc.github.io/docs/
  ignoreDeadLinks: true,

  srcExclude: [
    'aristadocs/**',
    'libstdcpp-guide/**'
  ],
  
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Architecture', link: '/architecture/cdn-architecture-guide' },
      { text: 'Database', link: '/database/01-introduction-and-overview' },
      { text: 'Distributed Systems', link: '/distributed-systems/01-cap-theorem-and-foundations' },
      { text: 'Java', link: '/java/01-jvm-internals-memory-model' },
      { text: 'Networking', link: '/networking/socket-internals' },
      { text: 'Kernel & System', link: '/kernel-and-system/process-control' },
      { text: 'DDIA', link: '/ddia/01-reliable-scalable-maintainable' },
      { text: 'HLD', link: '/hld/01-url-shortener' },
      { text: 'LLD', link: '/lld/01-rate-limiter' }
    ],

    sidebar: {
      '/architecture/': [
        {
          text: 'Architecture',
          items: [
            { text: 'CDN Architecture', link: '/architecture/cdn-architecture-guide' },
            { text: 'Client-Server Architecture', link: '/architecture/client-server-architecture' },
            { text: 'Nginx Architecture', link: '/architecture/nginx-architecture' },
            { text: 'Internet Business Ownership', link: '/architecture/internet-business-ownership-guide' },
            { text: 'Blob Storage', link: '/architecture/blob' }
          ]
        }
      ],
      '/build-and-tooling/': [
        {
          text: 'Build & Tooling',
          items: [
            { text: 'clangd TCP Setup', link: '/build-and-tooling/CLANGD_TCP_SETUP_GUIDE' },
            { text: 'Docker Guide', link: '/build-and-tooling/docker-comprehensive-guide' },
            { text: 'Git Concepts', link: '/build-and-tooling/git-concepts-guide' },
            { text: 'Git Internals', link: '/build-and-tooling/git-internals-deep-dive' },
            { text: 'Git Push Comparison', link: '/build-and-tooling/git-push-comparison' },
            { text: 'Git Topo Order', link: '/build-and-tooling/git-topo-order-analysis' },
            { text: 'Tar File Optimization', link: '/build-and-tooling/tar-file-optimization-guide' },
            { text: 'Telescope Live Grep', link: '/build-and-tooling/telescope-live-grep-glob-patterns' }
          ]
        }
      ],
      '/database/': [
        {
          text: 'Database Internals',
          items: [
            { text: '01. Introduction & Overview', link: '/database/01-introduction-and-overview' },
            { text: '02. B-Tree Basics', link: '/database/02-b-tree-basics' },
            { text: '03. B-Tree Variants', link: '/database/03-b-tree-variants' },
            { text: '04. B-Tree Implementation', link: '/database/04-b-tree-implementation' },
            { text: '05. Transaction Processing', link: '/database/05-transaction-processing-recovery' },
            { text: '06. B-Tree Concurrency', link: '/database/06-b-tree-concurrency' },
            { text: '07. Log-Structured Storage', link: '/database/07-log-structured-storage' },
            { text: '08. Distributed Systems Intro', link: '/database/08-distributed-systems-intro' },
            { text: '09. Failure Detection', link: '/database/09-failure-detection' },
            { text: '10. Leader Election', link: '/database/10-leader-election' },
            { text: '11. Replication & Consistency', link: '/database/11-replication-consistency' },
            { text: '12. Distributed Transactions', link: '/database/12-distributed-transactions' },
            { text: '13. Consensus Algorithms', link: '/database/13-consensus-algorithms' }
          ]
        }
      ],
      '/distributed-systems/': [
        {
          text: 'Distributed Systems',
          items: [
            { text: '01. CAP Theorem & Foundations', link: '/distributed-systems/01-cap-theorem-and-foundations' },
            { text: '02. Consensus Algorithms', link: '/distributed-systems/02-consensus-algorithms' },
            { text: '03. Storage & Replication', link: '/distributed-systems/03-distributed-storage-and-replication' },
            { text: '04. Distributed Transactions', link: '/distributed-systems/04-distributed-transactions' },
            { text: '05. Clocks & Time Sync', link: '/distributed-systems/05-clocks-and-time-synchronization' },
            { text: '06. Fault Tolerance', link: '/distributed-systems/06-fault-tolerance-and-resilience' },
            { text: '07. Distributed Messaging', link: '/distributed-systems/07-distributed-messaging' },
            { text: '08. Service Discovery', link: '/distributed-systems/08-service-discovery-and-coordination' },
            { text: '09. Distributed Caching', link: '/distributed-systems/09-distributed-caching' }
          ]
        }
      ],
      '/java/': [
        {
          text: 'Java Internals',
          items: [
            { text: '01. JVM Internals & Memory', link: '/java/01-jvm-internals-memory-model' },
            { text: '02. Collections Framework', link: '/java/02-collections-framework-internals' },
            { text: '03. Concurrency & Multithreading', link: '/java/03-concurrency-multithreading' },
            { text: '04. Data Structures & Algorithms', link: '/java/04-data-structures-algorithms' },
            { text: '05. OOP & Design Patterns', link: '/java/05-oop-design-patterns' },
            { text: '06. Generics & Reflection', link: '/java/06-generics-reflection-annotations' },
            { text: '07. IO, NIO & Networking', link: '/java/07-io-nio-networking' },
            { text: '08. Exception Handling', link: '/java/08-exception-handling' },
            { text: '09. Performance Optimization', link: '/java/09-performance-optimization' },
            { text: '10. Interview & Competitive', link: '/java/10-interview-competitive-programming' },
            { text: '11. Blocking/Non-blocking IO', link: '/java/11-blocking-nonblocking-io' },
            { text: '12. JIT Compilation', link: '/java/12-jit-compilation' }
          ]
        }
      ],
      '/networking/': [
        {
          text: 'Networking',
          items: [
            { text: 'DNS & SSH Deep Dive', link: '/networking/DNS_SSH_Connection_Deep_Dive' },
            { text: 'Network Interfaces', link: '/networking/NETWORK_INTERFACE_EXPLAINED' },
            { text: 'TLS', link: '/networking/TLS' },
            { text: 'Blocking/Non-blocking IO', link: '/networking/blocking-nonblocking-io' },
            { text: 'Interprocess Communication', link: '/networking/interprocess-communication' },
            { text: 'IP Categorisation', link: '/networking/ip-categorisation' },
            { text: 'Network Virtualization', link: '/networking/network-virtualization-guide' },
            { text: 'OSI Layers & Packet Flow', link: '/networking/osi_layers_packet_flow' },
            { text: 'Socket Internals', link: '/networking/socket-internals' },
            { text: 'Unix Pipes & IPC', link: '/networking/unix-pipes-and-ipc' },
            { text: 'Unix Sockets', link: '/networking/unix-sockets' },
            { text: 'WebSockets', link: '/networking/websockets' },
            { text: 'Zero-Copy Mechanisms', link: '/networking/zero-copy-mechanisms' }
          ]
        }
      ],
      '/kernel-and-system/': [
        {
          text: 'Kernel & System',
          items: [
            { text: 'File Modes & GID', link: '/kernel-and-system/file-modes-and-gid-guide' },
            { text: 'Interactive vs Non-interactive', link: '/kernel-and-system/interactive-vs-noninteractive-terminals' },
            { text: 'Interrupts', link: '/kernel-and-system/interrupts' },
            { text: 'IO Subsystem', link: '/kernel-and-system/io-subsystem' },
            { text: 'Man Pages Guide', link: '/kernel-and-system/man-pages-comprehensive-guide' },
            { text: 'Memory Management', link: '/kernel-and-system/memory-management-policies' },
            { text: 'Process Control', link: '/kernel-and-system/process-control' },
            { text: 'Process Kill Commands', link: '/kernel-and-system/process-kill-commands' },
            { text: 'Process Scheduling', link: '/kernel-and-system/process-scheduling-and-time' },
            { text: 'Process Structure', link: '/kernel-and-system/process-structure' },
            { text: 'Semaphores', link: '/kernel-and-system/semaphores' },
            { text: 'Signals', link: '/kernel-and-system/signals' },
            { text: 'strace Guide', link: '/kernel-and-system/strace-comprehensive-guide' },
            { text: 'systemd Guide', link: '/kernel-and-system/systemd-guide' },
            { text: 'UID/GID Essentials', link: '/kernel-and-system/uid-gid-essentials' }
          ]
        }
      ],

      '/ddia/': [
        {
          text: 'Designing Data-Intensive Applications',
          items: [
            { text: '01. Reliable, Scalable, Maintainable', link: '/ddia/01-reliable-scalable-maintainable' },
            { text: '02. Data Models & Query Languages', link: '/ddia/02-data-models-and-query-languages' },
            { text: '03. Storage & Retrieval', link: '/ddia/03-storage-and-retrieval' },
            { text: '04. Encoding & Evolution', link: '/ddia/04-encoding-and-evolution' },
            { text: '05. Replication', link: '/ddia/05-replication' },
            { text: '06. Partitioning', link: '/ddia/06-partitioning' },
            { text: '07. Transactions', link: '/ddia/07-transactions' },
            { text: '08. Trouble with Distributed Systems', link: '/ddia/08-trouble-with-distributed-systems' },
            { text: '09. Consistency & Consensus', link: '/ddia/09-consistency-and-consensus' },
            { text: '10. Batch Processing', link: '/ddia/10-batch-processing' },
            { text: '11. Stream Processing', link: '/ddia/11-stream-processing' },
            { text: '12. Future of Data Systems', link: '/ddia/12-future-of-data-systems' }
          ]
        }
      ],
      '/hld/': [
        {
          text: 'High-Level Design',
          items: [
            { text: '01. URL Shortener', link: '/hld/01-url-shortener' },
            { text: '02. Rate Limiter', link: '/hld/02-rate-limiter' },
            { text: '03. Chat Messaging', link: '/hld/03-chat-messaging' },
            { text: '04. News Feed', link: '/hld/04-news-feed' },
            { text: '05. Video Streaming', link: '/hld/05-video-streaming' },
            { text: '06. Notification System', link: '/hld/06-notification-system' },
            { text: '07. Search Engine', link: '/hld/07-search-engine' },
            { text: '08. Distributed Cache', link: '/hld/08-distributed-cache' },
            { text: '09. Object Storage', link: '/hld/09-object-storage' },
            { text: '10. Ride Sharing', link: '/hld/10-ride-sharing' },
            { text: '11. Payment System', link: '/hld/11-payment-system' },
            { text: '12. Ticket Booking', link: '/hld/12-ticket-booking' },
            { text: '13. Typeahead Suggestion', link: '/hld/13-typeahead-suggestion' },
            { text: '14. Key-Value Store', link: '/hld/14-key-value-store' },
            { text: '15. Metrics & Monitoring', link: '/hld/15-metrics-monitoring' }
          ]
        }
      ],
      '/lld/': [
        {
          text: 'Low-Level Design',
          items: [
            { text: '01. Rate Limiter', link: '/lld/01-rate-limiter' },
            { text: '02. In-Memory Cache', link: '/lld/02-in-memory-cache' },
            { text: '03. Pub-Sub System', link: '/lld/03-pub-sub-system' },
            { text: '04. Task Scheduler', link: '/lld/04-task-scheduler' },
            { text: '05. File System', link: '/lld/05-file-system' },
            { text: '06. Connection Pool', link: '/lld/06-connection-pool' },
            { text: '07. Logging Framework', link: '/lld/07-logging-framework' },
            { text: '08. Elevator System', link: '/lld/08-elevator-system' },
            { text: '09. Parking Lot', link: '/lld/09-parking-lot' },
            { text: '10. Library Management', link: '/lld/10-library-management' },
            { text: '11. Online Chess', link: '/lld/11-online-chess' },
            { text: '12. Notification System', link: '/lld/12-notification-system' },
            { text: '13. API Gateway', link: '/lld/13-api-gateway' },
            { text: '14. Search Autocomplete', link: '/lld/14-search-autocomplete' },
            { text: '15. URL Shortener', link: '/lld/15-url-shortener' },
            { text: '16. Order Management', link: '/lld/16-order-management' },
            { text: '17. Movie Ticket Booking', link: '/lld/17-movie-ticket-booking' },
            { text: '18. Vending Machine', link: '/lld/18-vending-machine' },
            { text: '19. Distributed Lock', link: '/lld/19-distributed-lock' },
            { text: '20. Collaborative Editor', link: '/lld/20-collaborative-editor' }
          ]
        }
      ],
      '/programming-languages/': [
        {
          text: 'Programming Languages',
          items: [
            { text: 'C Language for Systems', link: '/programming-languages/c_language_for_systems_programming' },
            { text: 'C++ VTables', link: '/programming-languages/cpp-vtables-guide' },
            { text: 'Header Files & Libraries', link: '/programming-languages/header-files-and-binary-libraries-guide' },
            { text: 'JVM Internals', link: '/programming-languages/jvm-internals' },
            { text: 'Python Path Setup', link: '/programming-languages/python-path-setup' }
          ]
        }
      ],
      '/rpi/': [
        {
          text: 'Raspberry Pi Projects',
          items: [
            { text: 'Overview', link: '/rpi/README' },
            { text: 'Distributed Sync Learning', link: '/rpi/distributed-sync-learning' }
          ]
        }
      ],
      '/testing/': [
        {
          text: 'Testing',
          items: [
            { text: 'Playwright Deep Dive', link: '/testing/playwright-deep-dive-architecture' },
            { text: 'Playwright Stubbing', link: '/testing/playwright-stubbing-deep-dive' },
            { text: 'Playwright Presentation', link: '/testing/playwrightpresentation' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/ajaykrmnc/docs' }
    ],

    search: {
      provider: 'local'
    },

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2024-present Ajay Kumar'
    }
  }
})

