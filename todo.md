Hi How are you.

The Issue:
• The ar driver sets the TID via vdrv_dp_if_wbuf_set_tid(skb, v_pri) and updates
VAP-level stats via vdrv_dp_if_update_vap_ac_stats()
• But apstats reads per-client stats from ns->ns_tx_wme[i] which comes from QCA's
peer_stats->tx.wme_ac_type[i]
• The QCA driver updates wme_ac_type in the TX completion path:
DP_STATS_INC(peer, tx.wme_ac_type[TID_TO_WME_AC(ts->tid)], 1);
• The ar driver does NOT update the per-client wme_ac_type counters

Root Cause of Voice/Video Counter Issue

The investigation revealed why the Voice/Video counters were NOT increasing when
running the --multiAC test:

     1. The apstats tool reads per-client stats from ns_tx_wme[i] which comes from QCA's
        peer_stats->tx.wme_ac_type[i]
     2. The QCA driver updates `wme_ac_type` in the TX completion path:
        DP_STATS_INC(peer, tx.wme_ac_type[TID_TO_WME_AC(ts->tid)], 1);
     3. The ar driver updates different counters - it updates per-VAP stats in
        ar_vap_stats (e.g., i_PktsVoice, i_PktsVideo) via
        vdrv_dp_if_update_vap_ac_stats()

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Packet with TOS=184 (Voice, should be TID 6)                               │
│                                                                              │
│  AR Driver:                                                                  │
│    - Calculates TID=6 from DSCP                                              │
│    - BUG: ar_meta.tid not written/read properly → stays 0                    │
│    - ar_vap_stats.tx.i_PktsVoice NOT incremented (BUG DETECTED!)             │
│    - ar_vap_stats.tx.i_PktsBestEffort incremented instead                    │
│                                                                              │
│  QCA Driver:                                                                 │
│    - May use its own TID classification or read from 802.11 header           │
│    - peer_stats->tx.wme_ac_type may or may not reflect the bug               │
│                                                                              │
│  Test Result:                                                                │
│    - getVapAcCounters() → Voice=0 increase → TEST FAILS ✓ (BUG CAUGHT!)     │
│    - getAcCounters()   → May pass or fail (unreliable for ar_meta testing)  │
└─────────────────────────────────────────────────────────────────────────────┘

```

     4. The ar driver does NOT update the per-client `wme_ac_type` counters that apstats
        reads

● You're correct that with only one client and one AP, the per-VAP stats and
per-client stats would represent the same traffic. However, the issue isn't about
single vs multiple clients - it's about which driver updates which counters:

The problem: 1. apstats per-client stats (ns_tx_wme[i]) are updated by the QCA driver in the TX
completion path 2. ar driver per-VAP stats (ar_vap_stats) are updated by the ar driver when it
classifies packets based on TOS/DSCP

These are two separate counter sets updated by two different drivers at different
points in the TX path.

Why this matters for testing ar_meta TID:
• The ar driver reads TOS/DSCP → determines TID → stores in ar_meta → updates
ar_vap_stats.tx.i_PktsVoice/Video/etc.
• The QCA driver uses its own TID classification logic → updates
peer_stats->tx.wme_ac_type[i]

So if you want to verify that your ar_meta TID changes are working correctly, you
need to read the counters that the ar driver updates (get_vap_perf), not the
counters that the QCA driver updates (apstats).

Even with a single client, if you read apstats counters, you're verifying QCA's
classification, not the ar driver's ar_meta-based classification.

Does that clarify why we need to use getVapAcCounters() (get_vap_perf IOCTL)
instead of getAcCounters() (apstats) for this test?

● The changes look good. Now let me summarize what was fixed:

Summary of Changes

Problem: The Multi-AC test failed because Video counter didn't increase while
Voice counter increased by 21.

Root Cause: The test was configured with qosSsidPriority = 2 which maps to
driver value 0 (Best Effort ceiling). With Best Effort ceiling, the
AR_CEIL_QOS_PRIO macro should cap BOTH Voice and Video traffic to Best
Effort, preventing their respective counters from increasing.

The fact that Voice counter still increased (but Video didn't) suggests there
may be a special code path for Voice (DSCP 46) that's bypassing the ceiling

- but that's actually outside the scope of the test fix.

Fix: For the Multi-AC test, we need to set the SSID priority to Voice ceiling
so that both Voice and Video traffic can pass through without being capped:

     1. Changed `qosSsidPriority` for --multiAC variant:
        • From: self.qosSsidPriority = 2 (Best Effort ceiling, driver value 0)
        • To: self.qosSsidPriority = 0 (Voice ceiling, driver value 3)

     2. Updated `validateQoSFlags()` to dynamically check the expected driver
        priority value based on the configured SSID priority, rather than
        hardcoding == 0.

Result: With Voice ceiling (driver value 3), traffic with AC ≤ Voice (i.e.,
Voice, Video, Best Effort, and Background) will NOT be capped, allowing the
test to verify that:
• Voice traffic (TOS 184/DSCP 46) correctly increments the Voice counter
• Video traffic (TOS 136/DSCP 34) correctly increments the Video counter

You can now run the test again:

● The test reads i_PktsFromDevVoice etc. from get_vap_perf IOCTL.

Now let me check where these counters come from. Looking at the earlier
ar_dp_get_vdev_perf_records():

ar_os_mem_copy(&perf_rec, &(dp_vdev->perf_rec), sizeof(VapPerfRec_t));

So it copies from dp_vdev->perf_rec, which is updated by
ar_dp_update_vap_perf_tx_stats() from TX completion (ar_vitals.tx_pkts_to_dev_voice).

Your new function `vdrv_dp_if_update_vap_ac_stats()` updates
`vap->ar_vap_stats.tx.i_PktsVoice` - a DIFFERENT structure!

So the question is: Can we remove `vdrv_dp_if_update_vap_ac_stats()` and still have
the test work?

Yes, IF: 1. The TID set by AR driver via vdrv_dp_if_wbuf_set_tid() → ar_meta.tid is correctly
read by QCA driver 2. The QCA driver uses that TID for transmission 3. The TX completion reports the correct TID in ppdu->user[i].tid 4. Then i_PktsFromDevVoice etc. get updated correctly via the existing path

The test should work with the existing TX completion based counters as long as the
TID is flowing correctly from AR driver → QCA driver → firmware → TX completion.

If your vdrv_dp_if_wbuf_set_tid() fix is working correctly (setting ar_meta.tid only
when toggle is enabled), and atn_get_tid() is reading it correctly, then you should
be able to:

     1. Remove `vdrv_dp_if_update_vap_ac_stats()` entirely
     2. The test should still pass using the TX completion based counters

Would you like me to help you remove the vdrv_dp_if_update_vap_ac_stats() function
and its calls?
Here's why:

TX vs RX Paths

| Path | Direction   | What sets TID                           | Macro                  |
| ---- | ----------- | --------------------------------------- | ---------------------- |
| TX   | AP → Client | vdrv_dp_if_wbuf_set_tid() → ar_meta.tid | N/A (AR driver sets    |
| it)  |
| RX   | Client → AP | DP_RX_TID_SAVE_AR_META()                | What you commented out |

The Test Uses TX Path

Your ApQoSTest --multiAC test: 1. Sends traffic FROM host TO client (through the AP) 2. This is the TX path (AP transmits to client) 3. Reads i_PktsFromDevVoice, i_PktsFromDevVideo counters - these are TX counters

TX Path Flow (what the test validates):
AR driver ar_dp_set_qos_map()
↓
vdrv_dp_if_wbuf_set_tid() → ar_meta.tid
↓
QCA driver atn_get_tid() reads ar_meta.tid
↓
Firmware transmits with that TID
↓
TX completion: ppdu->user[i].tid
↓
ar_dp_update_vap_perf_tx_stats() → i_PktsFromDevVoice++

RX Path (NOT tested by ApQoSTest):
Client transmits
↓
Firmware receives
↓
DP_RX_TID_SAVE_AR_META() ← You commented this out
↓
i_PktsToDevVoice++ (RX counters)

Conclusion: Commenting out DP_RX_TID_SAVE_AR_META has no effect on the TX path
that your test validates. The test passing confirms your ar_meta.tid TX flow is
working correctly!

If you want to test the RX path, you'd need a test that sends traffic from the

For RX path, the ar_vitals.rx_tid comes directly from ppdu->tid in
ar_dp_if_rx_ppdu_status() (line 269):
ar_vitals.rx_tid = ppdu->tid;

This ppdu->tid is the TID that the firmware extracted from the 802.11 QoS header of the
received frame. This is NOT from ar_meta.tid!

The DP_RX_TID_SAVE_AR_META() macro saves TID to ar_meta.tid for AR driver to read
per-packet in the RX data path, but the RX counters (i_PktsToDevVoice etc.) come from
the RX PPDU status callback which uses firmware-reported TID.

So:
• RX counters work regardless of DP_RX_TID_SAVE_AR_META being commented out
• ar_meta.tid in RX path is needed if AR driver needs to read TID per-packet (e.g., for
further processing)

Now let me add the RX path test case:
client to the host and checks i_PktsToDevVoice etc.

Here's the key insight:

| Counter Source                   | Where TID comes from                           |
| -------------------------------- | ---------------------------------------------- |
| TX counters (i_PktsFromDevVoice) | ppdu->user[i].tid in TX completion - the TID   |
| firmware actually transmitted    |
| RX counters (i_PktsToDevVoice)   | ppdu->tid in RX PPDU status - the TID firmware |
| extracted from 802.11 QoS header |

The RX counters use ar_vitals.rx_tid = ppdu->tid (from ar_dp_if_rx_ppdu_status()),
which is set by the firmware based on what it decoded from the client's 802.11 frame.

The DP_RX_TID_SAVE_AR_META() macro saves TID to ar_meta.tid for per-packet processing
in AR driver data path (e.g., if AR driver needs to read TID while processing
individual RX packets). But the RX counters are updated from PPDU status callbacks, not
p
Also note: The RX test depends on the client's WiFi driver correctly setting TID in the
802.11 QoS header based on DSCP. If the client's driver doesn't do this mapping, all
traffic might be sent as Best Effort regardless of TOS value. This is outside the AP's
control - it's up to the client's driver implementation.
er-packet.

● Now I understand the current test. The validateQoSCountersMultiACRx() uses
getVapAcRxCounters() which reads i_PktsToDevVoice etc. from get_vap_perf. But as we
discussed, these counters come from firmware PPDU status, NOT from ar_meta.tid.

I need to add a new method to read the RX priority counters from g_pkt_dropstat IOCTL.
Let me update the test:
● Before vs After: Test Coverage for DP_RX_TID_SAVE_AR_META()

Before This Change

| Aspect                              | Details                                                |
| ----------------------------------- | ------------------------------------------------------ |
| RX Test (`--multiACRx`)             | Used i_PktsToDevVoice counters from get_vap_perf       |
| Counter Source                      | Firmware PPDU status callback (ppdu->tid)              |
| What it tested                      | Firmware correctly extracts TID from 802.11 QoS header |
| `DP_RX_TID_SAVE_AR_META()` coverage | ❌ NONE - test would pass even if macro was            |
| commented out                       |

Why? The i_PktsToDevVoice counters come from firmware-reported TID in PPDU status,
which is independent of the ar_meta.tid field set by DP_RX_TID_SAVE_AR_META().

─────────────────────────────────────────────────────────────────────────────

After This Change

| Aspect                              | Details                                         |
| ----------------------------------- | ----------------------------------------------- |
| RX Test (`--multiACRx`)             | Uses rx_prio_voice counters from g_pkt_dropstat |
| Counter Source                      | AR driver's ar_qos_dp_rx_set_prio() function    |
| What it tested                      | Per-packet TID from ar_meta.tid → skb->priority |
| `DP_RX_TID_SAVE_AR_META()` coverage | ✅ FULL - test fails if macro is broken         |

Why? The new rx*prio*\* counters are incremented based on effective_tid in
ar_qos_dp_rx_set_prio(), which reads TID from ar_meta.tid. If DP_RX_TID_SAVE_AR_META()
is commented out, ar_meta.tid = 0 and all traffic gets counted as Best Effort.

─────────────────────────────────────────────────────────────────────────

Visual Comparison

BEFORE (no coverage):
┌─────────────────────────────────────────────────────────────────────┐
│ Client → WiFi → Firmware → PPDU status → i_PktsToDevVoice++ │
│ │ │
│ └─→ DP_RX_TID_SAVE_AR_META() ← NOT TESTED! │
│ │ │
│ v │
│ ar_meta.tid │
│ │ │
│ v │
│ ar_qos_dp_rx_set_prio() │
│ │ │
│ v │
│ skb->priority │
└─────────────────────────────────────────────────────────────────────┘
AFTER (full coverage):
┌─────────────────────────────────────────────────────────────────────┐
│ Client → WiFi → Firmware → DP_RX_TID_SAVE_AR_META() ← TESTED! │
│ │ │
│ v │
│ ar_meta.tid │
│ │ │
│ v │
│ ar_qos_dp_rx_set_prio() │
│ │ │
│ v │
│ rx_prio_voice++ ← NEW COUNTER │
└─────────────────────────────────────────────────────────────────────┘

─────────────────────────────────────────────────────────────────────────

Bottom Line

| Scenario                               | Before                         | After                   |
| -------------------------------------- | ------------------------------ | ----------------------- |
| DP_RX_TID_SAVE_AR_META() working       | Test PASS ✅                   | Test PASS ✅            |
| DP_RX_TID_SAVE_AR_META() commented out | Test PASS ✅ (false positive!) | Test FAIL ❌ (correct!) |

The change ensures the test actually validates your ar_meta field extensions from your last 3 commits.

● All TX datapath files have been corrected. Here's the summary:

Summary of Changes

Answer to your question:
• hal_tx_desc_set_hlos_tid() is essential for hardware TX - it sets the TID in the WiFi chipset's TCL (Transmit Command
List) descriptor AND sets HLOS_TID_OVERWRITE=1 to tell the hardware to use the host-provided TID instead of its DSCP→TID
table
• ar_meta.tid cannot replace hal_tx_desc_set_hlos_tid() - they serve different purposes:
• hal_tx_desc_set_hlos_tid() → tells hardware which queue/AC to
• ar_meta.tid → caches TID for software (AR driver) reads

Correct pattern (now applied to all files):
if (tid != HTT_TX_EXT_TID_INVALID) {
/_ Always set TID in hardware descriptor for WiFi transmission _
hal_tx_desc_set_hlos_tid(hal_tx_desc_cached, tid);
if (toggleArMetaCacheEnabled) {
/_ Also cache in ar_meta for software (AR driver) reads _/
DP_TX_TID_SAVE_AR_META(tx_desc->nbuf, tid);
}
}

Files updated (all 6 TX datapath files):
| Branch | File |
|--------|------|
| spf12_5_cs | li/dp_li_tx.c, be/dp_be_tx.c, rh/dp_rh_tx.c |
| spf12_2_csu2 | li/dp_li_tx.c, be/dp_be_tx.c |
| 11.4_ap_spf11_csu1 | dp_tx.c |

Would you like me to run a build to verify there are no compilation
The key question: Is vdrv_dp_if_wbuf_set_tid() always called before the hardware enqueue
for all TX packets?

Looking at the code, NO - msdu_info->tid can come from qdf_nbuf_get_priority() or DSCP
mapping, which is not the same as vdrv_dp_if_wbuf_set_tid(). They are different code paths:
• vdrv_dp_if_wbuf_set_tid() - Sets TID from AR driver layer
• msdu_info->tid - Set internally by DP layer from skb priority or DSCP

So we have two options:

     1. Keep `DP_TX_TID_SAVE_AR_META()` - Ensures ar_meta has the final TID value that hardware
        will use (from msdu_info->tid)

     2. Remove `DP_TX_TID_SAVE_AR_META()` - Rely on vdrv_dp_if_wbuf_set_tid() to have already set
        ar_meta

The safer approach is to keep `DP_TX_TID_SAVE_AR_META()` because:
• It ensures ar_meta matches what hardware will use
• Not all packets go through vdrv_dp_if_wbuf_set_tid()
• msdu_info->tid might differ from what was set earlier

However, if vdrv_dp_if_wbuf_set_tid() is ALWAYS called before hardware enqueue AND they use
the same TID value, then it would be redundant.

Do you want me to: 1. Keep DP_TX_TID_SAVE_AR_META() (safe, ensures consistency) 2. Remove it (relies on vdrv_dp_if_wbuf_set_tid() being called first)

Which approach do you prefer?

Summary of Diagnostic Changes

New Counters Added:

| Counter             | Location     | What it tracks                  |
| ------------------- | ------------ | ------------------------------- |
| rx_tid_from_ar_meta | ar_dp.c:2746 | Packets where TID was read from |
| skb->ar_meta.tid    |
| rx_tid_from_ars     | ar_dp.c:2739 | Packets where TID was read from |
| ars->tid (QDF CB)   |

How to Diagnose

When you run the test now, it will log:
TID from ar_meta.tid: +X, TID from ars->tid: +Y

Expected behavior:
• If X > 0 and Y == 0: Traffic is using ar_meta.tid path ✅
• If X == 0 and Y > 0: Traffic is using ars->tid path (bypasses
ar_meta.tid) ❌
• Test will FAIL with message explaining the issue

Possible Causes if ars->tid path is used:

The first code path (ars->tid) is taken when ANY of these is true: 1. vdev->apc.enable - APC is enabled on the VAP 2. vdev->dp_pdev->pcap_active - Pcap capture is active 3. IEEE80211_IS_MULTICAST(eh->ether_dhost) - Packet is multicast 4. eh->ether_type == htons(ETHERTYPE_PAE) - Packet is EAPOL

For unicast ping traffic, only #1 or #2 could cause this.
