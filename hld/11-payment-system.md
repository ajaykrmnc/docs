# Design a Payment System (Stripe / PayPal)

**Difficulty:** Hard | **Companies:** Stripe, PayPal, Square, Amazon, Google, Visa

---

## 1. Problem Statement and Scope

Design a large-scale payment processing system similar to Stripe or PayPal that enables
merchants to accept online payments from customers across the globe. The system must
handle the full lifecycle of a payment -- authorization, capture, settlement, refunds --
while guaranteeing exactly-once processing, maintaining PCI DSS compliance, supporting
multiple currencies, and performing financial reconciliation.

### In Scope

- **Payment processing:** Credit card, debit card, and bank transfer (ACH/SEPA).
- **Payment lifecycle:** Authorize, capture, settle, void, refund.
- **Merchant management:** Onboarding, configuration, dashboard, payout scheduling.
- **Multi-currency:** Accept payments in 135+ currencies, settle in merchant's local currency.
- **Recurring payments:** Subscriptions with billing cycles, retries on failure, dunning.
- **Webhooks and notifications:** Real-time event delivery to merchants.
- **Ledger and reconciliation:** Double-entry bookkeeping, daily bank reconciliation.
- **Compliance:** PCI DSS Level 1, SOC2, GDPR, PSD2 (Strong Customer Authentication).
- **Fraud detection:** Rule-based and ML-based scoring before authorization.
- **Reporting and analytics:** Payment success rates, revenue dashboards, dispute tracking.

### Out of Scope

- Physical point-of-sale (POS) terminal hardware.
- Cryptocurrency payments.
- Peer-to-peer (P2P) money transfers.
- Full banking / neobank services (loans, savings accounts).
- Issuing of payment cards.

---

## 2. Functional Requirements

| # | Requirement | Description |
|---|-------------|-------------|
| FR-1 | Process payments | Accept credit card, debit card, and bank transfer payments via API |
| FR-2 | Authorization and capture | Support separate auth/capture flows and combined auth+capture |
| FR-3 | Refunds | Full and partial refunds with automatic ledger reversal |
| FR-4 | Payment status tracking | Real-time status queries with deterministic state machine |
| FR-5 | Merchant dashboard | View transactions, revenue, chargebacks, payouts |
| FR-6 | Multi-currency | Accept 135+ currencies, auto-convert with live exchange rates |
| FR-7 | Recurring payments | Subscriptions with configurable billing intervals and retry logic |
| FR-8 | Payment history | Searchable, filterable history with export capability |
| FR-9 | Webhooks | Notify merchants of payment events with at-least-once delivery |
| FR-10 | Merchant payouts | Schedule and execute payouts to merchant bank accounts |
| FR-11 | Dispute management | Handle chargebacks, evidence submission, resolution tracking |
| FR-12 | Payment method vault | Securely store and tokenize payment methods for reuse |

---

## 3. Non-Functional Requirements

| # | Requirement | Target |
|---|-------------|--------|
| NFR-1 | Exactly-once processing | No double charges under any failure scenario |
| NFR-2 | Data consistency | ACID for payment transactions, eventual for analytics |
| NFR-3 | PCI DSS compliance | Level 1 certification, no raw PAN storage in application tier |
| NFR-4 | Latency | < 500ms for payment API response (excluding PSP round-trip) |
| NFR-5 | Availability | 99.999% uptime (< 5.26 minutes downtime per year) |
| NFR-6 | Audit trail | Every state change logged immutably with actor, timestamp, reason |
| NFR-7 | Fault tolerance | Survive single data center failure with zero data loss |
| NFR-8 | Idempotency | Every mutating API is idempotent via client-supplied key |
| NFR-9 | Throughput | Handle 100 TPS peak with ability to scale to 1,000 TPS |
| NFR-10 | Data durability | Zero tolerance for lost payment records (RPO = 0) |
| NFR-11 | Encryption | TLS 1.3 in transit, AES-256 at rest, HSM for key management |
| NFR-12 | Regulatory | GDPR-compliant data handling, PSD2 SCA support |

---

## 4. Back-of-Envelope Estimation

### Traffic Estimates

```
Daily transactions:          1,000,000
Seconds per day:             86,400

Average TPS:                 1,000,000 / 86,400 = ~12 TPS
Peak TPS (10x average):      ~120 TPS
Black Friday peak (30x):     ~360 TPS

API calls per transaction:   ~5 (create, auth, capture, status check, webhook)
Total API calls/day:         5,000,000
Peak API calls/second:       ~600

Webhook deliveries/day:      2,000,000 (2 events per transaction avg)
```

### Storage Estimates

```
Payment record size:         ~2 KB (order + metadata)
Ledger entries per payment:  2-4 entries x 500 bytes = ~1.5 KB
Audit log per payment:       ~3 KB (multiple state changes)
Total per payment:           ~6.5 KB

Daily storage:               1M x 6.5 KB = 6.5 GB/day
Monthly storage:             ~195 GB/month
Yearly storage:              ~2.4 TB/year

Payment ledger (append-only):
  - 1M transactions x 3 entries x 500B = 1.5 GB/day
  - Yearly: ~550 GB/year
  - 5-year retention: ~2.75 TB

Encrypted card vault:
  - 10M unique cards x 1 KB = 10 GB (relatively static)
```

### Compute Estimates

```
Payment service instances:   10-20 (each handles ~10-15 TPS with headroom)
Database connections:        200-400 (connection pooling)
Redis cache nodes:           3 (clustered, for idempotency + config)
Worker nodes (async):        10-15 (settlement, reconciliation, webhooks)
```

### Financial Estimates

```
Average transaction value:   $50
Daily GMV:                   $50M
Annual GMV:                  $18.25B
Revenue (2.9% + $0.30):     ~$529M + $109M = ~$638M/year

Fraud rate target:           < 0.1% of GMV = < $18.25M/year
Chargeback rate target:      < 0.5% of transactions = < 5,000/day
```

---

## 5. API Design

### 5.1 Create Payment (Auth + Capture or Auth Only)

```
POST /v1/payments
Headers:
  Authorization: Bearer {api_key}
  Idempotency-Key: {uuid}           # Required for all mutating operations
  Content-Type: application/json

Request Body:
{
  "amount": 5000,                   # Amount in smallest currency unit (cents)
  "currency": "usd",               # ISO 4217 currency code
  "payment_method": "pm_abc123",   # Tokenized payment method ID
  "merchant_id": "merch_xyz",      # Merchant identifier
  "capture": true,                  # false = auth-only, true = auth+capture
  "description": "Order #12345",
  "metadata": {                     # Arbitrary key-value pairs
    "order_id": "ord_12345",
    "customer_email": "user@example.com"
  },
  "return_url": "https://merchant.com/payment/complete",
  "statement_descriptor": "ACME CORP"  # Appears on bank statement
}

Response (201 Created):
{
  "id": "pay_a1b2c3d4e5",
  "object": "payment",
  "amount": 5000,
  "currency": "usd",
  "status": "succeeded",           # or "requires_action", "processing"
  "payment_method": "pm_abc123",
  "merchant_id": "merch_xyz",
  "capture": true,
  "created_at": "2026-04-09T10:30:00Z",
  "updated_at": "2026-04-09T10:30:01Z",
  "idempotency_key": "uuid-here",
  "metadata": { "order_id": "ord_12345" },
  "receipt_url": "https://payments.example.com/receipts/pay_a1b2c3d4e5"
}
```

### 5.2 Get Payment

```
GET /v1/payments/{payment_id}
Headers:
  Authorization: Bearer {api_key}

Response (200 OK):
{
  "id": "pay_a1b2c3d4e5",
  "object": "payment",
  "amount": 5000,
  "amount_captured": 5000,
  "amount_refunded": 0,
  "currency": "usd",
  "status": "succeeded",
  "payment_method": "pm_abc123",
  "merchant_id": "merch_xyz",
  "psp_reference": "psp_ref_xyz",   # Reference from downstream PSP
  "risk_score": 12,                  # 0-100, higher = riskier
  "created_at": "2026-04-09T10:30:00Z",
  "captured_at": "2026-04-09T10:30:01Z",
  "settled_at": null,
  "timeline": [                      # Full audit trail
    { "event": "created", "at": "2026-04-09T10:30:00Z" },
    { "event": "authorized", "at": "2026-04-09T10:30:00.5Z" },
    { "event": "captured", "at": "2026-04-09T10:30:01Z" }
  ]
}
```

### 5.3 Capture Payment (for Auth-only Flows)

```
POST /v1/payments/{payment_id}/capture
Headers:
  Authorization: Bearer {api_key}
  Idempotency-Key: {uuid}

Request Body:
{
  "amount": 4500                     # Optional: partial capture (up to authorized amount)
}

Response (200 OK):
{
  "id": "pay_a1b2c3d4e5",
  "status": "captured",
  "amount": 5000,
  "amount_captured": 4500,
  "captured_at": "2026-04-09T12:00:00Z"
}
```

### 5.4 Refund Payment

```
POST /v1/payments/{payment_id}/refund
Headers:
  Authorization: Bearer {api_key}
  Idempotency-Key: {uuid}

Request Body:
{
  "amount": 2000,                    # Partial refund; omit for full refund
  "reason": "customer_request",      # customer_request | duplicate | fraudulent
  "metadata": {
    "support_ticket": "TKT-789"
  }
}

Response (201 Created):
{
  "id": "rfnd_f6g7h8i9",
  "object": "refund",
  "payment_id": "pay_a1b2c3d4e5",
  "amount": 2000,
  "currency": "usd",
  "status": "pending",              # pending → succeeded | failed
  "reason": "customer_request",
  "created_at": "2026-04-09T14:00:00Z"
}
```

### 5.5 List Payments

```
GET /v1/payments?merchant_id=merch_xyz&status=succeeded&limit=50&starting_after=pay_xxx
Headers:
  Authorization: Bearer {api_key}

Response (200 OK):
{
  "object": "list",
  "data": [ ... ],
  "has_more": true,
  "total_count": 15234
}
```

### 5.6 Create Payment Method (Tokenization)

```
POST /v1/payment_methods
Headers:
  Authorization: Bearer {publishable_key}    # Client-side publishable key

Request Body:
{
  "type": "card",
  "card": {
    "number": "4242424242424242",       # Only handled in PCI-compliant vault
    "exp_month": 12,
    "exp_year": 2028,
    "cvc": "123"
  },
  "billing_details": {
    "name": "Jane Doe",
    "email": "jane@example.com"
  }
}

Response (201 Created):
{
  "id": "pm_abc123",
  "object": "payment_method",
  "type": "card",
  "card": {
    "brand": "visa",
    "last4": "4242",
    "exp_month": 12,
    "exp_year": 2028,
    "fingerprint": "fp_unique_hash"     # For dedup across merchants
  }
}
```

### 5.7 Webhook Registration

```
POST /v1/webhooks/endpoints
Headers:
  Authorization: Bearer {api_key}

Request Body:
{
  "url": "https://merchant.com/webhooks/payments",
  "events": ["payment.succeeded", "payment.failed", "refund.created"],
  "secret": "whsec_..."               # Auto-generated signing secret
}
```

### 5.8 Idempotency Key Handling

```
Idempotency Contract:
  1. Client sends Idempotency-Key header with every mutating request.
  2. Server stores: (idempotency_key, merchant_id) -> (status_code, response_body, created_at).
  3. If a duplicate key is received:
     a. If original request is still processing: return 409 Conflict.
     b. If original request completed: return the stored response (same status code + body).
     c. If original request failed: allow retry (key is "consumable" only on success).
  4. Idempotency records expire after 24 hours.
  5. Keys are scoped per merchant (same key from different merchants = different requests).
```

---

## 6. Data Model and Database Selection

### 6.1 Database Selection Rationale

| Data Type | Database | Rationale |
|-----------|----------|-----------|
| Payment orders | PostgreSQL (primary) | ACID transactions, strong consistency, mature ecosystem |
| Ledger entries | PostgreSQL (separate cluster) | Double-entry bookkeeping requires ACID, append-only |
| Payment methods (vault) | PostgreSQL + HSM | Encrypted at column level, tokenized references |
| Merchant config | PostgreSQL + Redis cache | Relatively static, frequently read |
| Idempotency keys | Redis (primary) + PostgreSQL (backup) | Fast lookup, 24h TTL, persistence for crash recovery |
| Webhook events | PostgreSQL + Kafka | Ordered, durable event stream for reliable delivery |
| Analytics/reporting | ClickHouse or BigQuery | Columnar, optimized for aggregation queries |
| Audit logs | Append-only PostgreSQL / S3 | Immutable, tamper-evident, long retention |

### 6.2 Core Schema

#### payments (Primary payment order table)

```sql
CREATE TABLE payments (
    id                  VARCHAR(26) PRIMARY KEY,   -- ULID (sortable, unique)
    merchant_id         VARCHAR(26) NOT NULL,       -- FK to merchants
    idempotency_key     VARCHAR(64),                -- Client-provided dedup key
    amount              BIGINT NOT NULL,            -- In smallest currency unit (cents)
    currency            CHAR(3) NOT NULL,           -- ISO 4217
    status              VARCHAR(20) NOT NULL,       -- CREATED, PROCESSING, AUTHORIZED,
                                                    -- CAPTURED, SETTLED, FAILED,
                                                    -- CANCELED, REFUNDED
    payment_method_id   VARCHAR(26) NOT NULL,       -- FK to payment_methods (token)
    capture_mode        VARCHAR(10) NOT NULL,       -- 'auto' or 'manual'
    amount_authorized   BIGINT DEFAULT 0,
    amount_captured     BIGINT DEFAULT 0,
    amount_refunded     BIGINT DEFAULT 0,
    description         TEXT,
    statement_descriptor VARCHAR(22),               -- Max 22 chars for bank statement
    metadata            JSONB,                      -- Merchant-defined key-value pairs
    risk_score          SMALLINT,                   -- 0-100
    psp_id              VARCHAR(26),                -- Which PSP processed this
    psp_reference       VARCHAR(128),               -- PSP's transaction ID
    failure_code        VARCHAR(50),                -- decline_code if failed
    failure_message     TEXT,
    ip_address          INET,                       -- Customer IP for fraud detection
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    authorized_at       TIMESTAMPTZ,
    captured_at         TIMESTAMPTZ,
    settled_at          TIMESTAMPTZ,
    version             INTEGER NOT NULL DEFAULT 1, -- Optimistic locking

    CONSTRAINT uq_idempotency UNIQUE (merchant_id, idempotency_key),
    CONSTRAINT chk_amount CHECK (amount > 0),
    CONSTRAINT chk_currency CHECK (currency ~ '^[A-Z]{3}$')
);

CREATE INDEX idx_payments_merchant_created ON payments (merchant_id, created_at DESC);
CREATE INDEX idx_payments_status ON payments (status) WHERE status IN ('PROCESSING', 'AUTHORIZED');
CREATE INDEX idx_payments_psp_reference ON payments (psp_reference);
```

#### ledger_entries (Double-entry bookkeeping)

```sql
CREATE TABLE ledger_entries (
    id                  BIGSERIAL PRIMARY KEY,
    payment_id          VARCHAR(26) NOT NULL,       -- FK to payments
    entry_type          VARCHAR(20) NOT NULL,       -- AUTHORIZATION, CAPTURE, REFUND,
                                                    -- SETTLEMENT, FEE, PAYOUT
    account_id          VARCHAR(26) NOT NULL,       -- FK to ledger_accounts
    direction           CHAR(1) NOT NULL,           -- 'D' (debit) or 'C' (credit)
    amount              BIGINT NOT NULL,            -- Always positive
    currency            CHAR(3) NOT NULL,
    balance_after       BIGINT NOT NULL,            -- Running balance after this entry
    counterpart_id      BIGINT,                     -- The matching entry (debit<->credit)
    description         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_direction CHECK (direction IN ('D', 'C')),
    CONSTRAINT chk_amount CHECK (amount > 0)
);

CREATE INDEX idx_ledger_payment ON ledger_entries (payment_id);
CREATE INDEX idx_ledger_account ON ledger_entries (account_id, created_at DESC);
```

#### ledger_accounts

```sql
CREATE TABLE ledger_accounts (
    id                  VARCHAR(26) PRIMARY KEY,
    account_type        VARCHAR(30) NOT NULL,       -- MERCHANT_RECEIVABLE, MERCHANT_PAYABLE,
                                                    -- PLATFORM_REVENUE, PROCESSING_FEE,
                                                    -- SETTLEMENT_HOLDING, PSP_CLEARING
    owner_id            VARCHAR(26),                -- merchant_id or NULL for system accounts
    currency            CHAR(3) NOT NULL,
    balance             BIGINT NOT NULL DEFAULT 0,  -- Current balance in smallest unit
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_account UNIQUE (account_type, owner_id, currency)
);
```

#### payment_methods (Tokenized vault)

```sql
CREATE TABLE payment_methods (
    id                  VARCHAR(26) PRIMARY KEY,    -- Token (e.g., pm_abc123)
    customer_id         VARCHAR(26),                -- Optional customer association
    type                VARCHAR(20) NOT NULL,       -- card, bank_account, wallet
    -- Card fields (encrypted)
    card_brand          VARCHAR(20),                -- visa, mastercard, amex
    card_last4          CHAR(4),                    -- Last 4 digits
    card_exp_month      SMALLINT,
    card_exp_year       SMALLINT,
    card_fingerprint    VARCHAR(64),                -- Hash for dedup across merchants
    card_token_vault    VARCHAR(256),               -- Reference to HSM-stored token
    -- Bank account fields (encrypted)
    bank_routing        VARCHAR(64) ENCRYPTED,      -- Column-level encryption
    bank_account_last4  CHAR(4),
    -- Metadata
    billing_name        VARCHAR(128),
    billing_email       VARCHAR(256),
    billing_country     CHAR(2),                    -- ISO 3166-1 alpha-2
    is_default          BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_type CHECK (type IN ('card', 'bank_account', 'wallet'))
);
```

#### merchants

```sql
CREATE TABLE merchants (
    id                  VARCHAR(26) PRIMARY KEY,
    business_name       VARCHAR(256) NOT NULL,
    country             CHAR(2) NOT NULL,
    default_currency    CHAR(3) NOT NULL,
    settlement_schedule VARCHAR(20) DEFAULT 'T+2',  -- T+1, T+2, weekly, monthly
    fee_rate_bps        INTEGER DEFAULT 290,         -- 2.90% = 290 basis points
    fee_fixed_cents     INTEGER DEFAULT 30,          -- $0.30
    payout_account_id   VARCHAR(26),                 -- Bank account for payouts
    risk_level          VARCHAR(10) DEFAULT 'normal', -- low, normal, high, restricted
    webhook_url         TEXT,
    webhook_secret      VARCHAR(64),
    api_key_hash        VARCHAR(128) NOT NULL,       -- Hashed API key
    status              VARCHAR(20) DEFAULT 'active', -- active, suspended, closed
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### idempotency_keys

```sql
CREATE TABLE idempotency_keys (
    key                 VARCHAR(64) NOT NULL,
    merchant_id         VARCHAR(26) NOT NULL,
    request_path        VARCHAR(256) NOT NULL,
    request_hash        VARCHAR(64) NOT NULL,       -- Hash of request body
    response_code       SMALLINT,
    response_body       JSONB,
    status              VARCHAR(20) NOT NULL,        -- 'processing' or 'complete'
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ NOT NULL,         -- created_at + 24h

    PRIMARY KEY (merchant_id, key)
);
```

### 6.3 Double-Entry Ledger: How Entries Balance

Every financial movement creates at least two ledger entries that sum to zero.

```
Example: Customer pays $50.00 to Merchant

Entry 1 (Debit):  PSP_CLEARING      account  +$50.00   (money coming in from card network)
Entry 2 (Credit): MERCHANT_RECEIVABLE account +$50.00   (merchant is owed this money)

When platform fee is taken ($1.75 = 2.9% + $0.30):
Entry 3 (Debit):  MERCHANT_RECEIVABLE account -$1.75    (reduce what we owe merchant)
Entry 4 (Credit): PLATFORM_REVENUE    account +$1.75    (platform earns the fee)

At settlement (T+2), payout to merchant:
Entry 5 (Debit):  MERCHANT_RECEIVABLE account -$48.25   (clear the receivable)
Entry 6 (Credit): MERCHANT_PAYABLE    account +$48.25   (payout initiated)
Entry 7 (Debit):  MERCHANT_PAYABLE    account -$48.25   (payout sent)
Entry 8 (Credit): SETTLEMENT_HOLDING  account +$48.25   (bank transfer in progress)

Invariant: SUM(debits) = SUM(credits) at all times
           Every account's balance = SUM(credits) - SUM(debits) for that account
```

---

## 7. High-Level Architecture

### 7.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              PAYMENT SYSTEM ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────────────────┘

  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ Merchant │   │ Merchant │   │  Mobile   │
  │  Server  │   │   Web    │   │   App     │
  └────┬─────┘   └────┬─────┘   └─────┬────┘
       │              │               │
       └──────────────┼───────────────┘
                      │ HTTPS / TLS 1.3
                      ▼
              ┌───────────────┐
              │  API Gateway  │──── Rate Limiting, Auth, TLS Termination
              │  (Kong/Envoy) │     Request Validation, IP Filtering
              └───────┬───────┘
                      │
         ┌────────────┼────────────────┐
         ▼            ▼                ▼
  ┌──────────┐ ┌────────────┐  ┌─────────────┐
  │ Payment  │ │  Merchant  │  │   Webhook   │
  │ Service  │ │  Service   │  │   Service   │
  │ (Core)   │ │            │  │             │
  └────┬─────┘ └────────────┘  └──────┬──────┘
       │                              │
       ├──────────────┬───────────────┤
       ▼              ▼               ▼
  ┌──────────┐ ┌────────────┐  ┌─────────────┐
  │  Risk    │ │  Ledger    │  │ Idempotency │
  │  Engine  │ │  Service   │  │   Store     │
  └────┬─────┘ └─────┬──────┘  │  (Redis)    │
       │             │         └─────────────┘
       ▼             ▼
  ┌──────────┐ ┌────────────┐
  │ Payment  │ │ PostgreSQL │
  │  Router  │ │  (Ledger)  │
  └────┬─────┘ └────────────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
  ┌──────────┐ ┌──────────┐  ┌──────────┐
  │   PSP    │ │   PSP    │  │   PSP    │
  │ Adapter  │ │ Adapter  │  │ Adapter  │
  │ (Stripe) │ │ (Adyen)  │  │ (Square) │
  └────┬─────┘ └────┬─────┘  └────┬─────┘
       │             │             │
       └─────────────┼─────────────┘
                     ▼
            ┌────────────────┐
            │  Card Networks │
            │ Visa/MC/Amex   │
            └────────┬───────┘
                     ▼
            ┌────────────────┐
            │  Issuing Banks │
            └────────────────┘
```

### 7.2 Complete Payment Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         PAYMENT PROCESSING FLOW                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

 Merchant                API         Payment      Risk       Payment    PSP        Card
 Server                Gateway      Service      Engine      Router   Adapter    Network
   │                     │            │            │           │         │          │
   │ POST /v1/payments   │            │            │           │         │          │
   │ + Idempotency-Key   │            │           │           │         │          │
   │────────────────────>│            │            │           │         │          │
   │                     │            │            │           │         │          │
   │                     │ Validate   │            │           │         │          │
   │                     │ Auth+Rate  │            │           │         │          │
   │                     │────────────>            │           │         │          │
   │                     │            │            │           │         │          │
   │                     │            │ Check      │           │         │          │
   │                     │            │ Idempotency│           │         │          │
   │                     │            │ Key (Redis)│           │         │          │
   │                     │            │──────┐     │           │         │          │
   │                     │            │      │     │           │         │          │
   │                     │            │<─────┘     │           │         │          │
   │                     │            │ (new key)  │           │         │          │
   │                     │            │            │           │         │          │
   │                     │            │ Create     │           │         │          │
   │                     │            │ Payment    │           │         │          │
   │                     │            │ Record     │           │         │          │
   │                     │            │ (status=   │           │         │          │
   │                     │            │  CREATED)  │           │         │          │
   │                     │            │            │           │         │          │
   │                     │            │ Evaluate   │           │         │          │
   │                     │            │ Risk ──────>           │         │          │
   │                     │            │            │ Score:12  │         │          │
   │                     │            │            │ APPROVE   │         │          │
   │                     │            │<───────────│           │         │          │
   │                     │            │            │           │         │          │
   │                     │            │ Route to   │           │         │          │
   │                     │            │ Best PSP───────────────>         │          │
   │                     │            │            │           │         │          │
   │                     │            │            │           │ Auth    │          │
   │                     │            │            │           │ Request │          │
   │                     │            │            │           │────────>│          │
   │                     │            │            │           │         │ Auth     │
   │                     │            │            │           │         │────────> │
   │                     │            │            │           │         │          │
   │                     │            │            │           │         │ Approved │
   │                     │            │            │           │         │<──────── │
   │                     │            │            │           │ Auth OK │          │
   │                     │            │            │           │<────────│          │
   │                     │            │            │           │         │          │
   │                     │            │ Update     │           │         │          │
   │                     │            │ status=    │           │         │          │
   │                     │            │ AUTHORIZED │           │         │          │
   │                     │            │            │           │         │          │
   │                     │            │ If auto-   │           │         │          │
   │                     │            │ capture:   │           │         │          │
   │                     │            │ Capture────────────────>         │          │
   │                     │            │            │           │────────>│          │
   │                     │            │            │           │<────────│          │
   │                     │            │            │           │         │          │
   │                     │            │ Write      │           │         │          │
   │                     │            │ Ledger     │           │         │          │
   │                     │            │ Entries    │           │         │          │
   │                     │            │            │           │         │          │
   │                     │            │ Publish    │           │         │          │
   │                     │            │ Event to   │           │         │          │
   │                     │            │ Kafka      │           │         │          │
   │                     │            │            │           │         │          │
   │  201 Created        │            │           │           │         │          │
   │  {status:succeeded} │            │            │           │         │          │
   │<────────────────────│            │            │           │         │          │
   │                     │            │            │           │         │          │
```

### 7.3 Component Breakdown

#### Payment Service (Core Orchestrator)

The central coordinator that manages the payment lifecycle. It is stateless and horizontally
scalable. Each instance connects to PostgreSQL via PgBouncer connection pooling.

**Responsibilities:**
- Accept and validate payment requests.
- Check idempotency keys (Redis lookup, then DB fallback).
- Orchestrate the authorization-capture flow.
- Write payment records with optimistic concurrency (version column).
- Publish events to Kafka for downstream consumers.

#### Risk Engine

Evaluates every payment before authorization. Produces a risk score (0-100) and a
recommendation (APPROVE, REVIEW, DECLINE).

**Signals evaluated:**
- Velocity checks: too many transactions from same card, IP, or device in short window.
- Geolocation mismatch: card's issuing country vs. customer IP country.
- BIN analysis: high-risk BIN ranges, prepaid cards.
- Amount anomalies: unusually large transaction for this merchant category.
- Device fingerprint: known fraudulent device signatures.
- ML model: trained on historical chargeback data.

#### Payment Router

Selects the optimal PSP (Payment Service Provider) based on:
- Card network and issuing country (local acquiring preferred).
- PSP success rates by card type (tracked in real time).
- PSP latency (route away from degraded providers).
- Cost optimization (interchange++ vs. blended pricing).
- Merchant-specific PSP preferences.
- PSP health status (circuit breaker state).

#### PSP Adapter Layer

Abstracts the interface to each external PSP behind a uniform internal API.

```
┌──────────────────────────────────────────────────────┐
│                 PSP Adapter Interface                 │
├──────────────────────────────────────────────────────┤
│                                                      │
│  authorize(amount, currency, token, metadata)        │
│    → AuthResult { psp_ref, status, decline_code }    │
│                                                      │
│  capture(psp_ref, amount)                            │
│    → CaptureResult { status }                        │
│                                                      │
│  void(psp_ref)                                       │
│    → VoidResult { status }                           │
│                                                      │
│  refund(psp_ref, amount)                             │
│    → RefundResult { refund_ref, status }             │
│                                                      │
│  status(psp_ref)                                     │
│    → StatusResult { current_status }                 │
│                                                      │
└──────────────────────────────────────────────────────┘
        ▲              ▲              ▲
        │              │              │
  ┌─────┴─────┐  ┌─────┴─────┐  ┌────┴──────┐
  │  Stripe   │  │   Adyen   │  │  Square   │
  │  Adapter  │  │  Adapter  │  │  Adapter  │
  └───────────┘  └───────────┘  └───────────┘
```

#### Ledger Service

Maintains the double-entry bookkeeping system. Every financial movement produces balanced
debit and credit entries. The ledger is append-only -- entries are never modified or deleted.
Corrections are made by posting reversal entries.

#### Webhook Service

Delivers payment events to merchant-configured HTTP endpoints.

**Delivery guarantees:**
- At-least-once delivery (merchants must be idempotent).
- Exponential backoff: retry at 1m, 5m, 30m, 2h, 8h, 24h (then dead-letter).
- Signed payloads (HMAC-SHA256) for authenticity verification.
- Event ordering per payment (not globally).

#### Reconciliation Service

Runs daily batch jobs that compare internal ledger entries against PSP settlement reports
and bank statements. Flags discrepancies for manual review.

---

## 8. Deep Dive: Core Components

### 8.1 Payment Processing Flow and State Machine

#### Payment States

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        PAYMENT STATE MACHINE                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

                                 ┌──────────┐
                                 │ CREATED  │
                                 └────┬─────┘
                                      │
                              Idempotency check OK,
                              Risk evaluation passed
                                      │
                                      ▼
                               ┌────────────┐
                          ┌────│ PROCESSING │────┐
                          │    └──────┬─────┘    │
                          │           │          │
                     Risk declined    │     PSP timeout /
                     or PSP error     │     network error
                          │           │          │
                          ▼           │          ▼
                    ┌──────────┐      │   ┌────────────┐
                    │  FAILED  │      │   │  REQUIRES  │
                    └──────────┘      │   │   ACTION   │ (3DS, redirect)
                                      │   └──────┬─────┘
                                      │          │
                                      │     Customer completes
                                      │     authentication
                                      │          │
                                      ▼          ▼
                               ┌──────────────┐
                          ┌────│  AUTHORIZED  │────┐
                          │    └──────┬───────┘    │
                          │           │            │
                     Void by         │       Auth expires
                     merchant        │       (7-30 days)
                          │           │            │
                          ▼           │            ▼
                    ┌──────────┐      │     ┌──────────┐
                    │ CANCELED │      │     │ EXPIRED  │
                    └──────────┘      │     └──────────┘
                                      │
                              Capture (full or partial)
                                      │
                                      ▼
                               ┌──────────────┐
                               │   CAPTURED   │
                               └──────┬───────┘
                                      │
                              Settlement batch
                              (T+1 or T+2)
                                      │
                                      ▼
                               ┌──────────────┐
                          ┌────│   SETTLED    │
                          │    └──────────────┘
                          │
                     Refund requested
                     (full or partial)
                          │
                          ▼
                   ┌───────────────┐
                   │   REFUNDED    │  (or PARTIALLY_REFUNDED)
                   └───────────────┘
```

#### Auth-Only vs. Auth+Capture Flow

```
AUTH-ONLY FLOW (e.g., hotel reservation):
  1. Merchant creates payment with capture=false
  2. Payment is AUTHORIZED (hold on customer's card)
  3. Days later, merchant calls POST /v1/payments/{id}/capture
  4. Payment moves to CAPTURED
  5. Settled in next batch

AUTH+CAPTURE FLOW (e.g., e-commerce checkout):
  1. Merchant creates payment with capture=true
  2. Authorization and capture happen atomically
  3. Payment goes directly from PROCESSING -> CAPTURED
  4. Settled in next batch
```

### 8.2 Idempotency and Exactly-Once Processing

This is the most critical design concern in a payment system. A customer must never be
charged twice for the same transaction, even if the merchant retries due to a timeout
or network error.

#### Idempotency Key Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      IDEMPOTENCY KEY PROCESSING                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

  Merchant                Payment Service                Redis          PostgreSQL
    │                          │                           │                │
    │ POST /v1/payments        │                           │                │
    │ Idempotency-Key: abc123  │                           │                │
    │─────────────────────────>│                           │                │
    │                          │                           │                │
    │                          │ GET idemp:merch_xyz:abc123 │                │
    │                          │──────────────────────────>│                │
    │                          │                           │                │
    │                          │ (key not found)           │                │
    │                          │<──────────────────────────│                │
    │                          │                           │                │
    │                          │ SET idemp:merch_xyz:abc123 │                │
    │                          │ status=processing         │                │
    │                          │ NX (set-if-not-exists)    │                │
    │                          │ EX 86400 (24h TTL)        │                │
    │                          │──────────────────────────>│                │
    │                          │                           │                │
    │                          │ (SET succeeded - we own   │                │
    │                          │  the lock)                │                │
    │                          │<──────────────────────────│                │
    │                          │                           │                │
    │                          │    ... Process payment (auth, capture) ... │
    │                          │                           │                │
    │                          │ INSERT payment record     │                │
    │                          │ INSERT idempotency record │                │
    │                          │ (in same DB transaction)  │                │
    │                          │───────────────────────────────────────────>│
    │                          │                           │                │
    │                          │ UPDATE idemp:merch_xyz:abc123              │
    │                          │ status=complete, response={...}           │
    │                          │──────────────────────────>│                │
    │                          │                           │                │
    │ 201 Created              │                           │                │
    │ {status: succeeded}      │                           │                │
    │<─────────────────────────│                           │                │
    │                          │                           │                │
    │                          │                           │                │
    │ === RETRY (same key) === │                           │                │
    │                          │                           │                │
    │ POST /v1/payments        │                           │                │
    │ Idempotency-Key: abc123  │                           │                │
    │─────────────────────────>│                           │                │
    │                          │                           │                │
    │                          │ GET idemp:merch_xyz:abc123 │                │
    │                          │──────────────────────────>│                │
    │                          │                           │                │
    │                          │ (found: complete,         │                │
    │                          │  response={...})          │                │
    │                          │<──────────────────────────│                │
    │                          │                           │                │
    │ 201 Created              │                           │                │
    │ {SAME response as before}│                           │                │
    │<─────────────────────────│                           │                │
    │                          │                           │                │
```

#### Handling Edge Cases

```
CASE 1: Retry while original is still processing
  - Redis returns status=processing
  - Return 409 Conflict with Retry-After header
  - Client retries after delay

CASE 2: Server crashes after PSP authorization but before DB write
  - Idempotency key left in "processing" state in Redis
  - Recovery worker (runs every 30s) finds stale "processing" keys (>60s old)
  - Queries PSP for transaction status using psp_reference
  - If PSP says "authorized": record the authorization, mark idempotency complete
  - If PSP says "not found": expire the idempotency key, allow retry

CASE 3: Database write succeeds but Redis update fails
  - Next retry reads Redis (still "processing") -> returns 409
  - Recovery worker eventually detects the stale key
  - Checks DB, finds completed payment, updates Redis
  - OR: Client retries after 409 TTL, DB unique constraint prevents duplicate
```

#### Outbox Pattern for Reliable Event Publishing

```
┌──────────────────────────────────────────────────────────────────┐
│              TRANSACTIONAL OUTBOX PATTERN                        │
└──────────────────────────────────────────────────────────────────┘

  Payment Service                PostgreSQL              Outbox Relay         Kafka
       │                            │                        │                 │
       │ BEGIN TRANSACTION          │                        │                 │
       │───────────────────────────>│                        │                 │
       │                            │                        │                 │
       │ INSERT INTO payments       │                        │                 │
       │ (id, amount, status...)    │                        │                 │
       │───────────────────────────>│                        │                 │
       │                            │                        │                 │
       │ INSERT INTO ledger_entries │                        │                 │
       │ (debit + credit entries)   │                        │                 │
       │───────────────────────────>│                        │                 │
       │                            │                        │                 │
       │ INSERT INTO outbox_events  │                        │                 │
       │ (event_type, payload,      │                        │                 │
       │  status=PENDING)           │                        │                 │
       │───────────────────────────>│                        │                 │
       │                            │                        │                 │
       │ COMMIT                     │                        │                 │
       │───────────────────────────>│                        │                 │
       │                            │                        │                 │
       │                            │  Poll for PENDING      │                 │
       │                            │  events (every 100ms)  │                 │
       │                            │<───────────────────────│                 │
       │                            │                        │                 │
       │                            │  Return pending events │                 │
       │                            │───────────────────────>│                 │
       │                            │                        │                 │
       │                            │                        │ Publish event   │
       │                            │                        │────────────────>│
       │                            │                        │                 │
       │                            │                        │ ACK             │
       │                            │                        │<────────────────│
       │                            │                        │                 │
       │                            │  UPDATE outbox_events  │                 │
       │                            │  SET status=PUBLISHED  │                 │
       │                            │<───────────────────────│                 │
       │                            │                        │                 │

Key insight: The payment record and the event are written in the SAME database
transaction. If the transaction commits, the event is guaranteed to be published
(eventually). If the transaction rolls back, no event is published. This avoids
the dual-write problem where the DB write succeeds but the Kafka write fails
(or vice versa).
```

### 8.3 Double-Entry Ledger

The ledger is the financial backbone of the payment system. Every monetary movement
must create balanced entries following the fundamental equation:

**Assets = Liabilities + Equity** (always balanced)

#### Ledger Entry Flow for a $50.00 Payment (2.9% + $0.30 fee)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    DOUBLE-ENTRY LEDGER FLOW                                     │
│                    Payment: $50.00 | Fee: $1.75                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

 Step 1: AUTHORIZATION (holds are off-ledger, tracked in payments table)
   - No ledger entries yet
   - Payment status: AUTHORIZED
   - Card issuer places $50 hold on customer's card

 Step 2: CAPTURE (money movement begins)
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ Entry │ Account              │ Direction │ Amount  │ Description         │
 ├───────┼──────────────────────┼───────────┼─────────┼─────────────────────┤
 │   1   │ PSP_CLEARING         │  DEBIT    │ $50.00  │ Funds from Stripe   │
 │   2   │ MERCHANT_RECEIVABLE  │  CREDIT   │ $50.00  │ Owed to merchant    │
 ├───────┼──────────────────────┼───────────┼─────────┼─────────────────────┤
 │       │                      │  Balance: │  $0.00  │ (entries sum to 0)  │
 └───────┴──────────────────────┴───────────┴─────────┴─────────────────────┘

 Step 3: FEE DEDUCTION
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ Entry │ Account              │ Direction │ Amount  │ Description         │
 ├───────┼──────────────────────┼───────────┼─────────┼─────────────────────┤
 │   3   │ MERCHANT_RECEIVABLE  │  DEBIT    │  $1.75  │ Platform fee        │
 │   4   │ PLATFORM_REVENUE     │  CREDIT   │  $1.75  │ Fee earned          │
 ├───────┼──────────────────────┼───────────┼─────────┼─────────────────────┤
 │       │                      │  Balance: │  $0.00  │ (entries sum to 0)  │
 └───────┴──────────────────────┴───────────┴─────────┴─────────────────────┘

 Step 4: SETTLEMENT (payout to merchant)
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ Entry │ Account              │ Direction │ Amount  │ Description         │
 ├───────┼──────────────────────┼───────────┼─────────┼─────────────────────┤
 │   5   │ MERCHANT_RECEIVABLE  │  DEBIT    │ $48.25  │ Clear receivable    │
 │   6   │ BANK_SETTLEMENT      │  CREDIT   │ $48.25  │ Wire to merchant    │
 ├───────┼──────────────────────┼───────────┼─────────┼─────────────────────┤
 │       │                      │  Balance: │  $0.00  │ (entries sum to 0)  │
 └───────┴──────────────────────┴───────────┴─────────┴─────────────────────┘

 Account Balances After Full Cycle:
 ┌──────────────────────────┬──────────┐
 │ Account                  │ Balance  │
 ├──────────────────────────┼──────────┤
 │ PSP_CLEARING             │ -$50.00  │  (liability - we owe PSP this on net settle)
 │ MERCHANT_RECEIVABLE      │   $0.00  │  (fully settled)
 │ PLATFORM_REVENUE         │  +$1.75  │  (our earnings)
 │ BANK_SETTLEMENT          │ +$48.25  │  (outgoing wire)
 ├──────────────────────────┼──────────┤
 │ TOTAL                    │   $0.00  │  (always balanced)
 └──────────────────────────┴──────────┘
```

#### Refund Ledger Entries

```
 REFUND: Full refund of $50.00 payment

 ┌───────────────────────────────────────────────────────────────────────────┐
 │ Entry │ Account              │ Direction │ Amount  │ Description         │
 ├───────┼──────────────────────┼───────────┼─────────┼─────────────────────┤
 │   1   │ MERCHANT_RECEIVABLE  │  DEBIT    │ $48.25  │ Charge back to      │
 │       │                      │           │         │ merchant            │
 │   2   │ REFUND_CLEARING      │  CREDIT   │ $48.25  │ Refund to customer  │
 ├───────┼──────────────────────┼───────────┼─────────┼─────────────────────┤
 │   3   │ PLATFORM_REVENUE     │  DEBIT    │  $1.75  │ Return our fee      │
 │   4   │ REFUND_CLEARING      │  CREDIT   │  $1.75  │ (or keep fee per    │
 │       │                      │           │         │  merchant agreement) │
 ├───────┼──────────────────────┼───────────┼─────────┼─────────────────────┤
 │       │                      │  Balance: │  $0.00  │ (entries sum to 0)  │
 └───────┴──────────────────────┴───────────┴─────────┴─────────────────────┘
```

### 8.4 Payment Security and PCI Compliance

#### PCI DSS Compliance Architecture

PCI DSS (Payment Card Industry Data Security Standard) Level 1 requires strict controls
over how cardholder data is stored, processed, and transmitted. The key principle is to
**minimize the scope** of PCI compliance by keeping raw card numbers (PANs) out of
the main application.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    PCI COMPLIANCE ARCHITECTURE                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │                    NON-PCI SCOPE (most of our system)               │
  │                                                                     │
  │  ┌──────────┐   ┌──────────────┐   ┌─────────────┐   ┌──────────┐ │
  │  │ Merchant │   │   Payment    │   │   Ledger    │   │ Webhook  │ │
  │  │ Service  │   │   Service    │   │   Service   │   │ Service  │ │
  │  └──────────┘   └──────┬───────┘   └─────────────┘   └──────────┘ │
  │                        │                                           │
  │              Only sees TOKENS                                      │
  │              (pm_abc123), never                                     │
  │              raw card numbers                                      │
  │                        │                                           │
  └────────────────────────┼───────────────────────────────────────────┘
                           │
              ─ ─ ─ PCI BOUNDARY ─ ─ ─
                           │
  ┌────────────────────────┼───────────────────────────────────────────┐
  │                    PCI SCOPE (isolated, hardened)                   │
  │                        │                                           │
  │                        ▼                                           │
  │                 ┌──────────────┐                                   │
  │                 │  Card Vault  │──── Isolated network segment      │
  │                 │   Service    │     No internet access             │
  │                 │              │     HSM-backed encryption          │
  │                 └──────┬───────┘     Penetration tested quarterly  │
  │                        │             Access logs reviewed daily     │
  │                        │             < 10 engineers have access     │
  │                        ▼                                           │
  │                 ┌──────────────┐                                   │
  │                 │  Encrypted   │──── AES-256 column-level encrypt  │
  │                 │  Card Store  │     Keys in HSM (never exported)  │
  │                 │  (PostgreSQL)│     Key rotation every 90 days    │
  │                 └──────────────┘                                   │
  │                                                                    │
  └────────────────────────────────────────────────────────────────────┘
```

#### Tokenization Flow

```
  Customer Browser               Tokenization API              Card Vault          HSM
       │                          (PCI scope)                     │                 │
       │                              │                           │                 │
       │ Card: 4242...4242            │                           │                 │
       │ (collected in iframe/        │                           │                 │
       │  Stripe Elements-style       │                           │                 │
       │  embedded form)              │                           │                 │
       │─────────────────────────────>│                           │                 │
       │                              │                           │                 │
       │                              │ Generate encryption key   │                 │
       │                              │──────────────────────────────────────────── >│
       │                              │                           │                 │
       │                              │ DEK (data encryption key) │                 │
       │                              │<─────────────────────────────────────────── │
       │                              │                           │                 │
       │                              │ Encrypt PAN with DEK      │                 │
       │                              │ Store encrypted PAN       │                 │
       │                              │──────────────────────────>│                 │
       │                              │                           │                 │
       │                              │ Generate fingerprint      │                 │
       │                              │ (HMAC of PAN for dedup)   │                 │
       │                              │                           │                 │
       │ Token: pm_abc123             │                           │                 │
       │ Last4: 4242                  │                           │                 │
       │ Brand: visa                  │                           │                 │
       │<─────────────────────────────│                           │                 │
       │                              │                           │                 │
       │ (Raw PAN NEVER reaches       │                           │                 │
       │  the merchant's server       │                           │                 │
       │  or our Payment Service)     │                           │                 │
       │                              │                           │                 │
```

#### 3D Secure (3DS) Authentication Flow

3DS adds an extra authentication step where the card issuer verifies the cardholder
(e.g., via SMS OTP or biometric). Required by PSD2 in Europe (Strong Customer Authentication).

```
  Customer        Merchant         Payment System       PSP          Issuing Bank
     │               │                  │                │                │
     │ Pay $50       │                  │                │                │
     │──────────────>│                  │                │                │
     │               │                  │                │                │
     │               │ Create Payment   │                │                │
     │               │─────────────────>│                │                │
     │               │                  │                │                │
     │               │                  │ Authorize      │                │
     │               │                  │───────────────>│                │
     │               │                  │                │ 3DS Required   │
     │               │                  │                │───────────────>│
     │               │                  │                │                │
     │               │                  │                │ 3DS Challenge  │
     │               │                  │ redirect_url   │ URL            │
     │               │                  │<───────────────│<───────────────│
     │               │                  │                │                │
     │               │ status:          │                │                │
     │               │ requires_action  │                │                │
     │               │ redirect_url:... │                │                │
     │               │<─────────────────│                │                │
     │               │                  │                │                │
     │ Redirect to   │                  │                │                │
     │ 3DS page      │                  │                │                │
     │<──────────────│                  │                │                │
     │                                  │                │                │
     │ Enter OTP / Biometric            │                │                │
     │─────────────────────────────────────────────────────────────────── >│
     │                                  │                │                │
     │ 3DS Result: Success              │                │                │
     │<──────────────────────────────────────────────────────────────────  │
     │                                  │                │                │
     │ Redirect to return_url           │                │                │
     │─────────────>│                  │                │                │
     │               │                  │                │                │
     │               │ Confirm Payment  │                │                │
     │               │ with 3DS result  │                │                │
     │               │─────────────────>│                │                │
     │               │                  │ Complete auth  │                │
     │               │                  │───────────────>│                │
     │               │                  │                │ Approved       │
     │               │                  │ Authorized     │<───────────────│
     │               │                  │<───────────────│                │
     │               │ status: succeeded│                │                │
     │               │<─────────────────│                │                │
     │ Payment done  │                  │                │                │
     │<──────────────│                  │                │                │
     │               │                  │                │                │
```

#### Fraud Detection Signals

```
┌─────────────────────────────────────────────────────────────────┐
│                    RISK ENGINE EVALUATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INPUT SIGNALS:                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Transaction Data    │ Card, amount, currency, merchant    │  │
│  │ Device Fingerprint  │ Browser, OS, screen, timezone       │  │
│  │ IP Geolocation      │ Country, city, ISP, proxy/VPN flag  │  │
│  │ Velocity Counters   │ Tx count per card/IP/device in      │  │
│  │                     │ last 1min, 1hr, 24hr                │  │
│  │ Historical Data     │ Chargeback rate, previous fraud     │  │
│  │ BIN Intelligence    │ Prepaid flag, issuing country, bank │  │
│  │ Address Verification│ AVS match result (street, zip)      │  │
│  │ CVC Check           │ Match / mismatch / not provided     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  DECISION FLOW:                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │ Rule Engine  │────>│   ML Model   │────>│  Decision    │    │
│  │ (hard rules) │     │  (gradient   │     │  Combiner    │    │
│  │              │     │   boosted)   │     │              │    │
│  └──────────────┘     └──────────────┘     └──────┬───────┘    │
│                                                    │            │
│  OUTPUT:                                           ▼            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Risk Score: 0-100                                       │    │
│  │ Decision:   APPROVE (score < 50)                        │    │
│  │             REVIEW  (50 <= score < 80)                  │    │
│  │             DECLINE (score >= 80)                        │    │
│  │ Signals:    [velocity_high, geo_mismatch, ...]          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Data Partitioning and Sharding

### Sharding Strategy

As the system grows beyond what a single PostgreSQL instance can handle (~10K TPS for
writes), we need a sharding strategy.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       SHARDING STRATEGY                                         │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────┐
  │                  Payment Data                              │
  │                                                            │
  │  Shard Key: merchant_id                                    │
  │  Rationale: Most queries are merchant-scoped               │
  │             (list my payments, my revenue, etc.)            │
  │                                                            │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
  │  │ Shard 0  │  │ Shard 1  │  │ Shard 2  │  │ Shard 3  │  │
  │  │merchants │  │merchants │  │merchants │  │merchants │  │
  │  │ A-F      │  │ G-L      │  │ M-R      │  │ S-Z      │  │
  │  │          │  │          │  │          │  │          │  │
  │  │ payments │  │ payments │  │ payments │  │ payments │  │
  │  │ refunds  │  │ refunds  │  │ refunds  │  │ refunds  │  │
  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
  │                                                            │
  │  Shard routing: hash(merchant_id) % num_shards            │
  │  Consistent hashing for minimal re-shuffling on scale-out  │
  └────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────┐
  │                  Ledger Data                                │
  │                                                            │
  │  Shard Key: account_id                                     │
  │  Rationale: Ledger queries are account-scoped              │
  │             (balance of account X, entries for account X)   │
  │                                                            │
  │  Special handling:                                         │
  │  - Cross-shard transactions (e.g., fee entry touches       │
  │    MERCHANT_RECEIVABLE on shard 2 and PLATFORM_REVENUE     │
  │    on shard 0) handled via saga pattern                    │
  │  - Platform accounts (PLATFORM_REVENUE, etc.) are on a     │
  │    dedicated "system shard" to avoid cross-shard writes    │
  │                                                            │
  └────────────────────────────────────────────────────────────┘
```

### Cross-Shard Transactions via Saga

```
Scenario: Payment capture creates entries across two shards

  Shard A (merchant's account)          Saga Coordinator          Shard B (platform account)
       │                                      │                          │
       │                                      │ Step 1: Debit            │
       │ INSERT ledger_entry                  │ merchant receivable      │
       │ (DEBIT, $50, merchant_recv)          │                          │
       │<─────────────────────────────────────│                          │
       │                                      │                          │
       │ Success                              │                          │
       │─────────────────────────────────────>│                          │
       │                                      │                          │
       │                                      │ Step 2: Credit           │
       │                                      │ platform revenue         │
       │                                      │─────────────────────────>│
       │                                      │                          │
       │                                      │    INSERT ledger_entry   │
       │                                      │    (CREDIT, $1.75,       │
       │                                      │     platform_revenue)    │
       │                                      │                          │
       │                                      │ Success                  │
       │                                      │<─────────────────────────│
       │                                      │                          │
       │                                      │ Saga COMPLETE            │
       │                                      │                          │

  If Step 2 fails:
       │                                      │ COMPENSATE Step 1:       │
       │ INSERT reversal entry                │ reverse the debit        │
       │ (CREDIT, $50, merchant_recv)         │                          │
       │<─────────────────────────────────────│                          │
       │                                      │                          │
```

---

## 10. Caching Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         CACHING STRATEGY                                        │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │ CACHE (Redis Cluster - 3 nodes, 32GB each)                                │
  │                                                                             │
  │ ┌───────────────────────────────────────────────────────────────────────┐   │
  │ │ LAYER 1: Idempotency Keys                                           │   │
  │ │ Key:     idemp:{merchant_id}:{idempotency_key}                      │   │
  │ │ Value:   {status, response_code, response_body}                     │   │
  │ │ TTL:     24 hours                                                   │   │
  │ │ Pattern: Write-through (written during payment processing)          │   │
  │ │ Volume:  ~1M keys/day, ~6M active at any time                      │   │
  │ └───────────────────────────────────────────────────────────────────────┘   │
  │                                                                             │
  │ ┌───────────────────────────────────────────────────────────────────────┐   │
  │ │ LAYER 2: Merchant Configuration                                     │   │
  │ │ Key:     merchant:{merchant_id}:config                              │   │
  │ │ Value:   {fee_rate, currency, psp_preference, risk_settings, ...}   │   │
  │ │ TTL:     5 minutes (invalidated on config change via pub/sub)       │   │
  │ │ Pattern: Cache-aside with event-driven invalidation                 │   │
  │ │ Volume:  ~100K merchants, ~100KB each = ~10GB                       │   │
  │ └───────────────────────────────────────────────────────────────────────┘   │
  │                                                                             │
  │ ┌───────────────────────────────────────────────────────────────────────┐   │
  │ │ LAYER 3: Exchange Rates                                             │   │
  │ │ Key:     fx:{from_currency}:{to_currency}                           │   │
  │ │ Value:   {rate, fetched_at}                                         │   │
  │ │ TTL:     60 seconds (very short - rates fluctuate)                  │   │
  │ │ Pattern: Write-through, updated by FX rate polling service          │   │
  │ │ Volume:  ~18K pairs (135 currencies squared), negligible size       │   │
  │ └───────────────────────────────────────────────────────────────────────┘   │
  │                                                                             │
  │ ┌───────────────────────────────────────────────────────────────────────┐   │
  │ │ LAYER 4: PSP Health & Routing                                       │   │
  │ │ Key:     psp:{psp_id}:health                                        │   │
  │ │ Value:   {success_rate_1m, avg_latency_1m, circuit_state}           │   │
  │ │ TTL:     10 seconds (near-real-time)                                │   │
  │ │ Pattern: Write-through, updated by health checker                   │   │
  │ └───────────────────────────────────────────────────────────────────────┘   │
  │                                                                             │
  │ ┌───────────────────────────────────────────────────────────────────────┐   │
  │ │ LAYER 5: Velocity Counters (Fraud Detection)                        │   │
  │ │ Key:     velocity:{dimension}:{value}:{window}                      │   │
  │ │          e.g., velocity:card_fp:fp_abc:1h                           │   │
  │ │ Value:   Counter (using Redis INCR)                                 │   │
  │ │ TTL:     Matches window (1min, 1hr, 24hr)                           │   │
  │ │ Pattern: Write-through on every transaction                         │   │
  │ └───────────────────────────────────────────────────────────────────────┘   │
  │                                                                             │
  └─────────────────────────────────────────────────────────────────────────────┘

  CRITICAL RULE: Payment status is NEVER cached.
  Payment state must always be read from PostgreSQL to ensure consistency.
  Serving stale payment status could cause double charges or missed refunds.
```

---

## 11. Replication and Consistency

### Consistency Requirements by Data Type

```
┌────────────────────────────────┬──────────────────────┬──────────────────────────┐
│ Data Type                      │ Consistency Model    │ Rationale                │
├────────────────────────────────┼──────────────────────┼──────────────────────────┤
│ Payment records                │ Strong (synchronous  │ Cannot risk inconsistent │
│                                │ replication)         │ payment state            │
├────────────────────────────────┼──────────────────────┼──────────────────────────┤
│ Ledger entries                 │ Strong (synchronous  │ Financial records must   │
│                                │ replication)         │ be perfectly consistent  │
├────────────────────────────────┼──────────────────────┼──────────────────────────┤
│ Idempotency keys              │ Strong (Redis with   │ Duplicate detection is   │
│                                │ WAIT + DB backup)    │ critical for correctness │
├────────────────────────────────┼──────────────────────┼──────────────────────────┤
│ Merchant configuration        │ Eventual (async      │ Config changes can       │
│                                │ replication, cache)  │ propagate in seconds     │
├────────────────────────────────┼──────────────────────┼──────────────────────────┤
│ Webhooks / notifications      │ Eventual (Kafka,     │ At-least-once delivery   │
│                                │ at-least-once)       │ is sufficient            │
├────────────────────────────────┼──────────────────────┼──────────────────────────┤
│ Analytics / reporting          │ Eventual (async      │ Minutes of delay is      │
│                                │ replication to       │ acceptable for dashboards│
│                                │ read replicas)       │                          │
├────────────────────────────────┼──────────────────────┼──────────────────────────┤
│ Audit logs                     │ Strong (synchronous  │ Regulatory requirement   │
│                                │ append-only writes)  │ for tamper-evidence      │
└────────────────────────────────┴──────────────────────┴──────────────────────────┘
```

### PostgreSQL Replication Topology

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   DATABASE REPLICATION TOPOLOGY                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

                         ┌──────────────────┐
                         │    PgBouncer     │
                         │  (Connection     │
                         │   Pool)          │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
             ┌────────────┐                ┌────────────┐
             │  Primary   │────Sync───────>│  Standby   │
             │  (DC-1)    │   Replication  │  (DC-2)    │
             │            │                │            │
             │ Writes +   │                │ Hot standby│
             │ Strong     │                │ (promote   │
             │ reads      │                │  on failure│
             └────┬───────┘                └────────────┘
                  │
                  │ Async Replication
                  │
         ┌────────┼────────┐
         ▼                 ▼
  ┌────────────┐    ┌────────────┐
  │  Read      │    │  Read      │
  │  Replica 1 │    │  Replica 2 │
  │            │    │            │
  │ Analytics  │    │ Merchant   │
  │ queries    │    │ dashboard  │
  │ Reporting  │    │ reads      │
  └────────────┘    └────────────┘

  Failover: Automatic via Patroni / pg_auto_failover
  RPO: 0 (synchronous replication to standby)
  RTO: < 30 seconds (automatic failover with health checks)
```

### Distributed Transaction: Saga Pattern

For operations that span multiple services (e.g., payment + ledger + webhook), we use
the saga pattern instead of 2PC (two-phase commit).

**Why saga over 2PC:**
- 2PC holds locks across services, creating coupling and latency.
- 2PC has a blocking failure mode (coordinator crash leaves participants in doubt).
- Saga allows each service to commit independently and compensate on failure.
- Better suited for long-running transactions (e.g., payment + settlement).

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    PAYMENT SAGA (Happy Path)                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

  Step 1: Create Payment Record
    ├── Service: Payment Service
    ├── Action:  INSERT into payments (status=CREATED)
    └── Compensate: UPDATE payments SET status=CANCELED

  Step 2: Risk Assessment
    ├── Service: Risk Engine
    ├── Action:  Evaluate and score
    └── Compensate: No-op (stateless evaluation)

  Step 3: Authorize with PSP
    ├── Service: PSP Adapter
    ├── Action:  Send authorization request to card network
    └── Compensate: Send void/reversal to PSP

  Step 4: Record Authorization
    ├── Service: Payment Service
    ├── Action:  UPDATE payments SET status=AUTHORIZED
    └── Compensate: UPDATE payments SET status=AUTH_REVERSED

  Step 5: Capture (if auto-capture)
    ├── Service: PSP Adapter
    ├── Action:  Send capture request
    └── Compensate: Send refund to PSP

  Step 6: Write Ledger Entries
    ├── Service: Ledger Service
    ├── Action:  INSERT balanced debit+credit entries
    └── Compensate: INSERT reversal entries

  Step 7: Publish Events
    ├── Service: Event Bus (Kafka)
    ├── Action:  Publish payment.succeeded event
    └── Compensate: Publish payment.reversed event

  If ANY step fails, compensating transactions run in REVERSE ORDER.
```

---

## 12. Fault Tolerance and Failure Handling

### Payment Timeout Handling

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                 TIMEOUT HANDLING DECISION TREE                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

  Payment Service sends auth request to PSP
       │
       │── PSP responds within 30s timeout? ──── YES ──── Process response normally
       │
       NO (timeout)
       │
       ▼
  DO NOT BLINDLY RETRY (could cause double charge!)
       │
       ▼
  Query PSP for transaction status
  (using our idempotency/reference key)
       │
       ├── PSP says "authorized" ──── Record the authorization, proceed
       │
       ├── PSP says "declined" ──── Record the decline, mark FAILED
       │
       ├── PSP says "not found" ──── Safe to retry the authorization
       │
       └── PSP also times out ──── Mark payment as UNKNOWN
                                    Alert operations team
                                    Reconciliation will catch it later
                                    Return status "processing" to merchant

  CRITICAL: The combination of idempotency key + status check ensures
  we NEVER send a duplicate authorization to the card network.
```

### PSP Failover

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      PSP FAILOVER WITH CIRCUIT BREAKER                          │
└─────────────────────────────────────────────────────────────────────────────────┘

  Payment Router
       │
       ▼
  ┌────────────────────────────────────────────────────────────────────┐
  │ Circuit Breaker per PSP                                           │
  │                                                                    │
  │  States:                                                           │
  │  ┌──────────┐    5 failures     ┌──────────┐    30s      ┌──────┐ │
  │  │  CLOSED  │───in 60s window──>│   OPEN   │──timeout──>│ HALF │ │
  │  │ (normal) │                   │ (reject  │            │ OPEN │ │
  │  └──────────┘                   │  all)    │            └──┬───┘ │
  │       ▲                         └──────────┘               │     │
  │       │                              ▲                     │     │
  │       │         Success              │      Failure        │     │
  │       └──────────────────────────────┼─────────────────────┘     │
  │                                      │                           │
  └──────────────────────────────────────────────────────────────────┘

  Failover Logic:
  ┌──────────────────────────────────────────────────────────────┐
  │                                                              │
  │  1. Try PRIMARY PSP (e.g., Stripe)                          │
  │     └── Circuit CLOSED? ─── YES ─── Send request            │
  │                              │                               │
  │                              NO (circuit OPEN)               │
  │                              │                               │
  │  2. Try SECONDARY PSP (e.g., Adyen)                         │
  │     └── Circuit CLOSED? ─── YES ─── Send request            │
  │                              │                               │
  │                              NO                              │
  │                              │                               │
  │  3. Try TERTIARY PSP (e.g., Square)                         │
  │     └── Circuit CLOSED? ─── YES ─── Send request            │
  │                              │                               │
  │                              NO (all circuits open)          │
  │                              │                               │
  │  4. Return SERVICE_UNAVAILABLE to merchant                   │
  │     with Retry-After header                                  │
  │                                                              │
  └──────────────────────────────────────────────────────────────┘

  PSP Selection Scoring (when multiple are available):
    Score = (success_rate * 0.5) + (1/latency_ms * 0.3) + (1/cost_bps * 0.2)
    Highest score wins.
```

### Dead Letter Queue for Webhooks

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   WEBHOOK DELIVERY WITH DLQ                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

  Kafka                  Webhook Worker              Merchant              DLQ
  (events topic)              │                      Endpoint              │
       │                      │                          │                 │
       │ payment.succeeded    │                          │                 │
       │─────────────────────>│                          │                 │
       │                      │                          │                 │
       │                      │ POST (signed payload)    │                 │
       │                      │─────────────────────────>│                 │
       │                      │                          │                 │
       │                      │ 200 OK                   │                 │
       │                      │<─────────────────────────│                 │
       │                      │                          │                 │
       │ ACK                  │                          │                 │
       │<─────────────────────│                          │                 │
       │                      │                          │                 │
       │ === FAILURE SCENARIO ===                        │                 │
       │                      │                          │                 │
       │ refund.created       │                          │                 │
       │─────────────────────>│                          │                 │
       │                      │ POST                     │                 │
       │                      │─────────────────────────>│ 500 Error       │
       │                      │                          │                 │
       │                      │ Retry 1 (after 1 min)    │                 │
       │                      │─────────────────────────>│ Timeout         │
       │                      │                          │                 │
       │                      │ Retry 2 (after 5 min)    │                 │
       │                      │─────────────────────────>│ 503             │
       │                      │                          │                 │
       │                      │ Retry 3 (after 30 min)   │                 │
       │                      │─────────────────────────>│ 503             │
       │                      │                          │                 │
       │                      │ ... retries at 2h, 8h, 24h ...            │
       │                      │                          │                 │
       │                      │ All retries exhausted    │                 │
       │                      │──────────────────────────────────────────> │
       │                      │                          │        Move to  │
       │                      │                          │        dead     │
       │                      │                          │        letter   │
       │                      │                          │        queue    │
       │                      │                          │                 │

  DLQ events are:
    - Visible in merchant dashboard for manual review.
    - Automatically retried when merchant re-enables webhook endpoint.
    - Retained for 30 days, then archived to cold storage.
    - Monitored: alert if DLQ size exceeds threshold.
```

### Reconciliation Catches Discrepancies

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    DAILY RECONCILIATION PROCESS                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

  Time: Every day at 02:00 UTC (during lowest traffic)

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Internal    │     │  PSP         │     │  Bank        │
  │  Ledger     │     │  Settlement  │     │  Statement   │
  │  (our DB)    │     │  Report      │     │  (SFTP)      │
  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Reconciliation  │
                    │  Engine          │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌────────────┐ ┌────────────┐ ┌────────────────┐
       │  Match     │ │  Mismatch  │ │  Missing       │
       │  (happy)   │ │  (amount   │ │  (in one       │
       │            │ │   differs) │ │   but not      │
       │  98.5% of  │ │            │ │   other)       │
       │  records   │ │  0.5% of   │ │                │
       │            │ │  records   │ │  1.0% of       │
       │  Auto-     │ │            │ │  records       │
       │  confirmed │ │  Alert +   │ │                │
       │            │ │  Manual    │ │  Alert +       │
       │            │ │  review    │ │  Investigation │
       └────────────┘ └────────────┘ └────────────────┘

  Common discrepancy types:
  1. OUR_ONLY:  We recorded a successful payment, PSP has no record
               → Check with PSP via API; possibly our status update was premature
  2. PSP_ONLY:  PSP settled a payment we don't have
               → Likely a crash-before-record scenario; create the record retroactively
  3. AMOUNT_DIFF: Our amount differs from PSP's settled amount
               → Usually currency conversion rounding; flag if > $0.01
  4. STATUS_DIFF: We say "captured", PSP says "refunded"
               → Webhook was missed; sync our status
```

---

## 13. Scalability

### Horizontal Scaling Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      SCALING DIMENSIONS                                         │
└─────────────────────────────────────────────────────────────────────────────────┘

  Component            Scaling Approach            Current → 10x Target
  ─────────────────────────────────────────────────────────────────────
  API Gateway          Horizontal (stateless)      4 → 40 instances
  Payment Service      Horizontal (stateless)      10 → 100 instances
  Risk Engine          Horizontal (stateless)      6 → 60 instances
  PSP Adapters         Horizontal (stateless)      8 → 80 instances

  PostgreSQL (primary) Vertical + sharding         1 → 8 shards
  PostgreSQL (reads)   Read replicas               2 → 16 replicas
  Redis Cluster        Add nodes                   3 → 12 nodes
  Kafka Cluster        Add partitions + brokers    6 → 24 brokers

  Webhook Workers      Horizontal (stateless)      10 → 100 workers
  Reconciliation       Partition by merchant range  2 → 20 workers
```

### Database Scaling Path

```
Stage 1: Single PostgreSQL (up to ~5K TPS writes)
  - 96 vCPUs, 768GB RAM, NVMe SSD
  - PgBouncer for connection pooling (10K connections → 200 DB connections)
  - 2 async read replicas for queries

Stage 2: Functional partitioning (up to ~20K TPS aggregate)
  - Separate DB clusters for: payments, ledger, card vault, analytics
  - Each cluster: primary + sync standby + 2 async replicas
  - Cross-cluster references via application-level joins

Stage 3: Horizontal sharding (up to ~100K TPS aggregate)
  - Payment DB: 8 shards by consistent hash of merchant_id
  - Ledger DB: 8 shards by consistent hash of account_id
  - Shard routing via application-layer proxy (e.g., Vitess or custom)
  - Cross-shard queries via scatter-gather (only for admin/analytics)
```

### Async Settlement Processing

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                  SETTLEMENT PIPELINE (ASYNC)                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

  Real-time path:                    Async path:
  (latency-sensitive)                (batch, throughput-optimized)

  ┌─────────────┐                   ┌─────────────────────────────────────────┐
  │ Payment API │                   │ Settlement Pipeline                     │
  │ (auth +     │                   │                                         │
  │  capture)   │                   │  1. Collect all CAPTURED payments       │
  │             │                   │     for settlement window (T+2)        │
  │ < 500ms     │                   │                                         │
  │ response    │                   │  2. Group by merchant + currency        │
  └──────┬──────┘                   │                                         │
         │                          │  3. Calculate net amount per merchant   │
         │ Event:                   │     (gross - fees - refunds - disputes) │
         │ payment.captured         │                                         │
         │                          │  4. Generate payout instructions        │
         ▼                          │                                         │
  ┌──────────────┐                  │  5. Submit to bank via ACH/wire         │
  │    Kafka     │─────────────────>│                                         │
  │              │                  │  6. Update ledger with settlement       │
  └──────────────┘                  │     entries                             │
                                    │                                         │
                                    │  Runs: Every 4 hours                    │
                                    │  Volume: ~250K payments per batch       │
                                    │  Duration: ~30 minutes per batch        │
                                    └─────────────────────────────────────────┘
```

---

## 14. Monitoring and Observability

### Key Metrics Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     PAYMENT SYSTEM METRICS                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  BUSINESS METRICS (Grafana Dashboard)                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐        │
│  │ Payment Success Rate         │ Target: > 96%    │ Alert: < 93%    │        │
│  │ Authorization Rate           │ Target: > 85%    │ Alert: < 80%    │        │
│  │ GMV (last 24h)               │ $50M             │ Alert: < $30M   │        │
│  │ Refund Rate                  │ Target: < 5%     │ Alert: > 8%     │        │
│  │ Chargeback Rate              │ Target: < 0.5%   │ Alert: > 0.75%  │        │
│  │ Fraud Detection Rate         │ Target: > 95%    │ Alert: < 90%    │        │
│  └─────────────────────────────────────────────────────────────────────┘        │
│                                                                                 │
│  SYSTEM METRICS                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐        │
│  │ API Latency (p50/p95/p99)    │ 50/200/500ms     │ Alert: p99>1s   │        │
│  │ PSP Latency (p50/p95/p99)    │ 100/500/1500ms   │ Alert: p99>3s   │        │
│  │ TPS (current)                │ 12 avg / 120 peak│ Alert: > 200    │        │
│  │ Error Rate (5xx)             │ Target: < 0.01%  │ Alert: > 0.1%   │        │
│  │ DB Connection Pool Usage     │ Target: < 70%    │ Alert: > 85%    │        │
│  │ Kafka Consumer Lag           │ Target: < 1000   │ Alert: > 10000  │        │
│  │ Redis Memory Usage           │ Target: < 70%    │ Alert: > 85%    │        │
│  └─────────────────────────────────────────────────────────────────────┘        │
│                                                                                 │
│  RECONCILIATION METRICS                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐        │
│  │ Match Rate                   │ Target: > 99%    │ Alert: < 98%    │        │
│  │ Unmatched Transactions       │ Target: < 100    │ Alert: > 500    │        │
│  │ Amount Discrepancy Total     │ Target: < $1000  │ Alert: > $5000  │        │
│  │ Reconciliation Duration      │ Target: < 1hr    │ Alert: > 3hr    │        │
│  └─────────────────────────────────────────────────────────────────────┘        │
│                                                                                 │
│  PSP HEALTH (per PSP)                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐        │
│  │ PSP          │ Success Rate │ Avg Latency │ Circuit State          │        │
│  ├──────────────┼──────────────┼─────────────┼────────────────────────┤        │
│  │ Stripe       │    97.2%     │   180ms     │ CLOSED (healthy)      │        │
│  │ Adyen        │    96.8%     │   210ms     │ CLOSED (healthy)      │        │
│  │ Square       │    95.1%     │   250ms     │ HALF_OPEN (degraded)  │        │
│  └──────────────┴──────────────┴─────────────┴────────────────────────┘        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Distributed Tracing

Every payment request gets a trace ID that follows the request across all services.

```
Trace: pay_a1b2c3d4e5
├── API Gateway (2ms)
│   └── Auth + rate limit check
├── Payment Service (15ms)
│   ├── Idempotency check (Redis) (1ms)
│   ├── Create payment record (DB) (3ms)
│   └── Risk evaluation (8ms)
├── PSP Adapter (180ms)
│   ├── Serialize request (1ms)
│   ├── HTTP to Stripe API (175ms)    ← Bulk of latency is external
│   └── Parse response (2ms)
├── Ledger Service (5ms)
│   └── Write 2 ledger entries (DB) (4ms)
├── Event Publisher (2ms)
│   └── Write to Kafka (1ms)
└── Total: 204ms

Tracing tools: OpenTelemetry → Jaeger/Tempo for visualization
```

### Alerting Strategy

```
SEVERITY LEVELS:

  P0 (Page immediately - 24/7 on-call):
    - Payment success rate drops below 90%
    - All PSP circuits open simultaneously
    - Database primary unreachable
    - Reconciliation finds > $10,000 unmatched

  P1 (Page during business hours):
    - Payment success rate below 93% for > 5 minutes
    - Single PSP circuit open for > 10 minutes
    - Kafka consumer lag > 50,000
    - Webhook DLQ size > 10,000

  P2 (Slack alert, next business day):
    - Latency p99 > 1s for > 15 minutes
    - DB connection pool > 85%
    - Fraud rate > 0.08% for rolling 24h

  P3 (Dashboard only):
    - Non-critical service restart
    - Cache hit rate drop
    - Approaching storage thresholds
```

---

## 15. Trade-offs and Design Decisions

### 15.1 Synchronous vs. Asynchronous Payment Processing

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                SYNC vs ASYNC PAYMENT PROCESSING                                 │
├────────────────────────────────┬────────────────────────────────────────────────┤
│       SYNCHRONOUS              │           ASYNCHRONOUS                         │
│       (Our choice for auth)    │           (Our choice for settlement)          │
├────────────────────────────────┼────────────────────────────────────────────────┤
│ Merchant gets immediate result │ Merchant polls or receives webhook             │
│ Simpler error handling         │ Complex state management                       │
│ Higher latency (blocks on PSP) │ Lower perceived latency for merchant           │
│ Scales to ~1000 TPS per node   │ Scales to ~10,000 TPS per node                │
│ PSP timeout = merchant timeout │ PSP timeout handled internally                │
│                                │                                                │
│ USED FOR:                      │ USED FOR:                                      │
│ - Authorization                │ - Settlement/payout processing                 │
│ - Capture                      │ - Webhook delivery                             │
│ - Refund initiation            │ - Reconciliation                               │
│                                │ - Analytics/reporting                           │
│                                │ - Retry logic                                   │
└────────────────────────────────┴────────────────────────────────────────────────┘

Decision: Authorization and capture are synchronous because merchants need immediate
confirmation to show the customer a success/failure page. Settlement and reconciliation
are asynchronous because they are batch-oriented and can tolerate minutes of delay.
```

### 15.2 Saga vs. Two-Phase Commit (2PC)

```
┌────────────────────────────┬────────────────────────────────────────────────────┐
│           SAGA             │              2PC                                   │
│       (Our choice)         │         (Not chosen)                               │
├────────────────────────────┼────────────────────────────────────────────────────┤
│ Each service commits       │ All services commit or all rollback               │
│ independently              │ atomically                                         │
│                            │                                                    │
│ Compensating transactions  │ Coordinator holds locks until all                  │
│ on failure (eventual       │ participants agree (blocking)                      │
│ consistency)               │                                                    │
│                            │                                                    │
│ No distributed locks       │ Distributed locks across services                  │
│                            │                                                    │
│ Higher availability        │ Lower availability (coordinator is SPOF)           │
│                            │                                                    │
│ More complex application   │ Simpler application logic but complex              │
│ logic (compensations)      │ infrastructure                                     │
│                            │                                                    │
│ Works across heterogeneous │ Requires all participants to support               │
│ services (DB + PSP + Kafka)│ XA/2PC protocol                                   │
└────────────────────────────┴────────────────────────────────────────────────────┘

Decision: Saga wins because:
1. External PSPs do not support 2PC.
2. 2PC would require holding DB locks for 100-500ms (duration of PSP call),
   killing throughput.
3. Saga's eventual consistency is acceptable because reconciliation catches
   any inconsistencies within 24 hours.
```

### 15.3 Single PSP vs. Multi-PSP

```
┌────────────────────────────┬────────────────────────────────────────────────────┐
│       SINGLE PSP           │         MULTI-PSP (Our choice)                     │
├────────────────────────────┼────────────────────────────────────────────────────┤
│ Simpler integration        │ Complex adapter layer                              │
│ Single contract/pricing    │ Multiple contracts to manage                       │
│ No routing logic needed    │ Intelligent routing required                       │
│ Single point of failure    │ Failover to backup PSPs                            │
│ Vendor lock-in             │ Negotiate better rates                             │
│ Limited geo coverage       │ Optimal local acquiring worldwide                  │
└────────────────────────────┴────────────────────────────────────────────────────┘

Decision: Multi-PSP because:
1. No single PSP has 99.999% uptime; failover improves our availability.
2. Local acquiring (matching PSP to card's issuing country) improves
   authorization rates by 5-15%.
3. Competitive pricing leverage across PSPs.
4. Regulatory requirements (some countries require local acquirers).
```

### 15.4 Real-Time vs. Batch Settlement

```
┌────────────────────────────┬────────────────────────────────────────────────────┐
│     REAL-TIME SETTLEMENT   │    BATCH SETTLEMENT (Our choice, industry norm)    │
├────────────────────────────┼────────────────────────────────────────────────────┤
│ Instant merchant payouts   │ T+1 or T+2 payouts                                │
│ Higher operational cost    │ Lower banking fees (bulk wire)                     │
│ Complex netting logic      │ Simple net calculation per batch                   │
│ Real-time bank integration │ SFTP/batch file to bank                            │
│ Higher fraud risk          │ Time to detect and reverse fraud                   │
│ Premium feature (Stripe    │ Standard for most merchants                        │
│ Instant Payouts)           │                                                    │
└────────────────────────────┴────────────────────────────────────────────────────┘

Decision: Batch settlement as default (T+2) because:
1. Industry standard; merchants expect it.
2. Netting across transactions reduces banking fees.
3. The 2-day window allows fraud detection and dispute handling before payout.
4. Offer "instant payout" as premium feature with additional fee (1.5%).
```

### 15.5 Additional Design Decisions

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Decision                     │ Choice              │ Key Reason                 │
├──────────────────────────────┼─────────────────────┼────────────────────────────┤
│ Primary database             │ PostgreSQL          │ ACID, mature, JSON support │
│ Message broker               │ Kafka               │ Durability, ordering, scale│
│ ID generation                │ ULID                │ Sortable, no coordination  │
│ API style                    │ REST + webhooks     │ Industry standard for      │
│                              │                     │ payment APIs               │
│ Currency representation      │ Smallest unit (int) │ Avoids floating-point      │
│                              │                     │ errors ($50.00 = 5000)     │
│ Idempotency key storage      │ Redis + PostgreSQL  │ Fast lookup + crash-safe   │
│ Secret management            │ AWS KMS + HSM       │ PCI requirement            │
│ Ledger mutability            │ Append-only         │ Audit trail, no data loss  │
└──────────────────────────────┴─────────────────────┴────────────────────────────┘
```

---

## 16. Interview Deep-Dive Questions

### Q1: How do you prevent double charging?

**Answer:** Multiple layers of defense:

1. **Idempotency key**: Every payment request includes a client-generated unique key.
   The server stores `(merchant_id, idempotency_key) -> response` in Redis (fast path)
   and PostgreSQL (durable path). Before processing, we check if this key was seen before.
   If yes, return the cached response.

2. **Database unique constraint**: `UNIQUE (merchant_id, idempotency_key)` on the
   `payments` table prevents duplicate records even if Redis is unavailable.

3. **Optimistic locking**: The `version` column on the payment record prevents concurrent
   state transitions. `UPDATE payments SET status='CAPTURED', version=version+1 WHERE
   id=? AND version=?` -- if the version doesn't match, the update affects 0 rows.

4. **PSP-level idempotency**: We forward our payment ID as the PSP's idempotency key.
   If we accidentally send the same auth request twice, the PSP returns the original result.

5. **Reconciliation**: Even if all runtime safeguards fail, daily reconciliation catches
   any duplicate charges by comparing our records with PSP settlement reports.

---

### Q2: How do you handle a payment that succeeds at the bank but your system crashes before recording it?

**Answer:** This is the classic "crash after external side effect" problem.

1. **Before the PSP call**: We write the payment record with `status=PROCESSING` and
   store the idempotency key as `processing` in Redis. This is our "intent to charge."

2. **Recovery worker**: A background job runs every 30 seconds, scanning for payments
   stuck in `PROCESSING` for more than 60 seconds.

3. **Status check**: The recovery worker queries the PSP using our payment ID / reference
   to determine the actual outcome:
   - If PSP says "authorized": update our record to `AUTHORIZED`, proceed normally.
   - If PSP says "not found": update to `FAILED`, release the idempotency key for retry.
   - If PSP is unreachable: keep in `PROCESSING`, retry the status check later.

4. **Idempotency safety**: Even during recovery, the PSP's own idempotency ensures we
   don't accidentally authorize again when checking status.

5. **Daily reconciliation**: As a final safety net, the reconciliation process compares
   every PSP-recorded transaction against our database. Any "PSP-only" transactions
   (succeeded at PSP but missing in our DB) are flagged and auto-corrected.

---

### Q3: How does reconciliation work?

**Answer:** Three-way reconciliation runs daily:

1. **Internal ledger vs. PSP settlement report**:
   - Download settlement files from each PSP (via SFTP or API).
   - Match each settlement line item to our internal payment record by PSP reference ID.
   - Flag: amount mismatches, missing records (either side), status conflicts.

2. **PSP settlement vs. bank statement**:
   - Download bank statements (MT940/CAMT.053 format via SFTP).
   - Match aggregate PSP settlement amounts to bank credit entries.
   - Verify net settlement = gross payments - refunds - chargebacks - PSP fees.

3. **Internal ledger balance check**:
   - Verify `SUM(debits) = SUM(credits)` across all ledger entries (must be zero).
   - Verify each account's computed balance matches the stored running balance.
   - Any non-zero sum indicates a bug in the ledger writing code.

Discrepancies are categorized by severity and routed to the appropriate team.
Auto-correction is applied for known patterns (e.g., rounding differences < $0.01).
Manual review is required for amounts > $1.

---

### Q4: How do you handle currency conversion?

**Answer:**

1. **Exchange rate sourcing**: We pull rates from multiple providers (e.g., European
   Central Bank, Open Exchange Rates) every 60 seconds and cache in Redis with 60-second
   TTL. We use the mid-market rate plus a configurable margin (typically 1-2%).

2. **Rate locking**: When a payment is created, we lock the exchange rate at that moment
   and store it on the payment record (`exchange_rate`, `exchange_rate_locked_at`).
   This prevents rate fluctuation between authorization and settlement.

3. **Presentation currency**: The customer sees the charge in their card's currency
   (decided by the card network via Dynamic Currency Conversion or Multi-Currency Pricing).

4. **Settlement currency**: The merchant always receives payouts in their configured
   settlement currency. Conversion happens at capture time using the locked rate.

5. **Ledger entries**: Multi-currency payments create entries in BOTH currencies:
   - Customer side: debit in customer's currency (e.g., EUR).
   - Merchant side: credit in merchant's currency (e.g., USD).
   - FX gain/loss account absorbs rounding differences.

6. **Amounts always in smallest unit**: EUR 10.50 = 1050 cents. JPY 1000 = 1000
   (JPY has no minor unit). We maintain a currency configuration table with decimal
   places per currency.

---

### Q5: How do you design for PCI compliance without handling raw card numbers?

**Answer:**

1. **Client-side tokenization**: Card numbers are collected in an isolated iframe or
   embedded component (like Stripe Elements) that communicates directly with our
   PCI-scoped Card Vault service. The merchant's server never sees the raw PAN.

2. **Network segmentation**: The Card Vault runs in an isolated VPC segment with no
   internet access (except to card networks). Only the tokenization API is exposed
   internally, and only to the Payment Service.

3. **Column-level encryption**: Raw PANs are encrypted with AES-256 using Data Encryption
   Keys (DEKs) that are themselves encrypted by Key Encryption Keys (KEKs) stored in
   an HSM (Hardware Security Module). The HSM never exports keys in plaintext.

4. **Tokenization**: After encryption, the Card Vault returns a token (e.g., `pm_abc123`)
   that represents the card. All other services reference the token, never the PAN.

5. **Scope minimization**: By keeping raw PANs confined to the Card Vault (a small,
   heavily audited service), the PCI audit scope covers only ~5% of our infrastructure
   instead of 100%.

6. **Key rotation**: Encryption keys rotate every 90 days. Old data is re-encrypted in
   background batch jobs during rotation.

---

### Q6: How do you handle partial captures and partial refunds?

**Answer:**

Partial capture: A merchant authorizes $100 but only captures $75 (e.g., one item out
of stock).
- The payment record tracks `amount` (authorized), `amount_captured`, `amount_refunded`.
- Capture request specifies the partial amount.
- Remaining authorized amount ($25) is automatically voided after capture.
- Ledger entries reflect only the captured amount.

Partial refund: A merchant refunds $30 out of a $75 captured payment.
- A new refund record is created linked to the payment.
- `amount_refunded` on the payment is incremented.
- Validation: `amount_refunded + new_refund_amount <= amount_captured`.
- Multiple partial refunds are allowed until the captured amount is fully refunded.
- Each partial refund creates its own balanced ledger entries.

---

### Q7: How does the webhook signing and verification work?

**Answer:**

1. **Signing**: Each webhook delivery is signed with the merchant's webhook secret
   using HMAC-SHA256.
   ```
   signature = HMAC-SHA256(webhook_secret, timestamp + "." + payload_json)
   ```

2. **Replay protection**: The timestamp is included in the signature. Merchants should
   reject webhooks where `abs(current_time - timestamp) > 5 minutes`.

3. **Header format**:
   ```
   Webhook-Signature: t=1712649600,v1=5d4b3...a2f1
   ```

4. **Merchant verification**: Merchant recalculates the HMAC using their stored secret
   and compares. If it matches, the webhook is authentic and untampered.

---

### Q8: How do you handle subscription/recurring payments?

**Answer:**

1. **Subscription object**: Stores plan, billing cycle (monthly, yearly), next billing
   date, payment method, retry policy.

2. **Billing scheduler**: A cron job runs hourly, queries subscriptions where
   `next_billing_date <= NOW()`, and creates payment requests.

3. **Smart retries**: If a recurring payment fails:
   - Retry 1: 24 hours later (soft decline might be temporary insufficient funds).
   - Retry 2: 3 days later (wait for paycheck deposit).
   - Retry 3: 7 days later (final attempt).
   - After 3 failures: mark subscription as `past_due`, notify merchant via webhook.

4. **Dunning**: Email notifications to customer on each failure, with a link to update
   their payment method.

5. **Proration**: When a customer upgrades/downgrades mid-cycle, calculate the prorated
   amount based on remaining days in the current period.

---

### Q9: How do you ensure exactly-once settlement (no double payouts to merchants)?

**Answer:**

1. **Settlement batch ID**: Each settlement run generates a unique batch ID. Payments
   are marked with `settlement_batch_id` when included. A payment can only appear in
   one batch (`UNIQUE INDEX` on `settlement_batch_id, payment_id`).

2. **State machine**: Payments must be in `CAPTURED` state to be included in settlement.
   After inclusion, they transition to `SETTLED`. The state transition is atomic.

3. **Batch-level idempotency**: The bank payout instruction includes the batch ID. If
   the same batch is submitted twice (e.g., due to a retry), the bank deduplicates.

4. **Settlement hold**: Payments are only eligible for settlement after a configurable
   hold period (default T+2). This window allows for fraud detection and disputes.

---

### Q10: How do you handle chargebacks/disputes?

**Answer:**

1. **Chargeback notification**: Card networks notify us via the PSP when a customer
   disputes a charge. This arrives as an asynchronous event.

2. **Automatic hold**: The disputed amount is immediately debited from the merchant's
   balance and held in a `DISPUTE_HOLDING` ledger account.

3. **Evidence submission**: The merchant is notified via webhook and can submit evidence
   (receipts, shipping info, communication logs) through our API within the response
   deadline (typically 7-21 days).

4. **Resolution**: The card network makes the final decision:
   - Won: Held funds returned to merchant, chargeback reversed.
   - Lost: Held funds returned to customer, merchant absorbs the loss.

5. **Monitoring**: Merchants exceeding chargeback thresholds (>1% of transactions) are
   flagged for review and may be restricted or suspended.

---

### Q11: How does the payment router decide which PSP to use?

**Answer:** The router uses a scoring algorithm considering:

1. **Authorization rate** (50% weight): Historical success rate for this card BIN + merchant
   category on each PSP. A PSP with 97% auth rate scores higher than one with 93%.

2. **Latency** (20% weight): Rolling p95 latency. Faster PSPs score higher.

3. **Cost** (15% weight): Interchange plus markup. Lower fees score higher.

4. **Local acquiring** (15% weight): Strong preference for PSPs that have a local acquiring
   relationship in the card's issuing country. Local acquirers see 5-15% higher auth rates.

5. **Circuit breaker override**: If a PSP's circuit is OPEN, it is excluded regardless of
   score. If HALF-OPEN, it receives a small fraction of traffic for testing.

6. **Merchant override**: Merchants can configure PSP preferences (e.g., "always use Stripe
   for USD transactions").

---

### Q12: How do you handle multi-region deployment for a payment system?

**Answer:**

1. **Active-passive per region**: One region is primary for writes (e.g., us-east-1).
   A secondary region (eu-west-1) has a warm standby database with synchronous replication.

2. **Why not active-active**: Payment processing requires strong consistency. Active-active
   with eventual consistency risks double charges. The complexity of conflict resolution
   for financial data is not worth the latency improvement.

3. **Latency mitigation**: Even with a single write region, read-heavy operations
   (payment status, merchant dashboard) can be served from regional read replicas.

4. **Regulatory compliance**: For EU/GDPR, some data must remain in EU. We handle this
   by routing EU merchant data to the EU database cluster while maintaining a global
   ledger view via async replication.

5. **Failover**: If the primary region goes down, we promote the secondary region.
   RTO: < 60 seconds. RPO: 0 (synchronous replication).

---

### Q13: How do you handle rate limiting for payment APIs?

**Answer:**

Rate limiting is essential to prevent abuse, but we must be careful not to reject
legitimate payment traffic.

1. **Per-merchant limits**: Default 100 requests/second per merchant, configurable.
   High-volume merchants (e.g., Amazon) get custom higher limits.

2. **Token bucket algorithm**: Allows short bursts above the sustained rate. A merchant
   with 100 RPS limit can burst to 200 RPS for 5 seconds.

3. **Different limits per endpoint**:
   - `POST /v1/payments`: 100/s (most critical, highest limit).
   - `GET /v1/payments/{id}`: 500/s (reads are cheaper).
   - `POST /v1/refunds`: 50/s (refunds are less frequent).

4. **429 response**: Includes `Retry-After` header and `X-RateLimit-Remaining` for
   client-side throttling.

5. **Global rate limiting**: Overall system limit (e.g., 10,000 TPS) with fair queuing
   to prevent one merchant from starving others.

---

### Q14: What happens if Kafka goes down? Are payments lost?

**Answer:** No. Kafka is used for async operations (webhooks, settlement, analytics),
not for the critical payment path.

1. **Payment processing does not depend on Kafka**: Authorization and capture happen
   synchronously via the PSP. If Kafka is down, the payment still succeeds.

2. **Outbox pattern**: Events are written to the PostgreSQL `outbox_events` table in
   the same transaction as the payment record. The outbox relay publishes to Kafka
   when it's available.

3. **If Kafka is down**: Events accumulate in the outbox table. When Kafka recovers,
   the relay publishes all pending events in order. This may cause delayed webhooks
   but no data loss.

4. **Webhook impact**: Merchants receive delayed notifications but can always poll
   `GET /v1/payments/{id}` for real-time status.

5. **Settlement impact**: Settlement batches may be delayed but will process correctly
   once Kafka recovers (events are idempotent).

---

### Q15: How would you migrate from a monolithic payment system to this microservices architecture?

**Answer:** The Strangler Fig pattern:

1. **Phase 1 - Extract Card Vault** (Week 1-4):
   - Build the PCI-scoped Card Vault as a new service.
   - Migrate raw PANs from the monolith DB to the vault.
   - Update the monolith to use tokens instead of raw PANs.
   - Immediate PCI scope reduction benefit.

2. **Phase 2 - Extract Ledger** (Week 5-8):
   - Build the Ledger Service with double-entry bookkeeping.
   - Dual-write: monolith writes to both old tables and new ledger.
   - Verify consistency between old and new for 2 weeks.
   - Cut over reads to new ledger service.

3. **Phase 3 - Extract Payment Processing** (Week 9-16):
   - Build the Payment Service, Risk Engine, and Payment Router.
   - Use feature flags to route X% of traffic to the new system.
   - Gradually increase: 1% -> 5% -> 25% -> 50% -> 100%.
   - Monitor success rates, latency, and reconciliation at each step.

4. **Phase 4 - Decommission monolith** (Week 17-20):
   - Once 100% of traffic is on the new system and stable for 2 weeks.
   - Keep monolith in read-only mode for 30 days as rollback safety net.
   - Fully decommission after 30 days.

Key principle: Never do a big-bang migration for a payment system. Gradual cutover
with dual-write verification at every stage. If anything looks wrong, immediately
route back to the monolith.

---

## Summary: Key Takeaways for Interview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    TOP INTERVIEW TALKING POINTS                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  1. EXACTLY-ONCE PROCESSING                                                    │
│     Idempotency key + DB unique constraint + PSP-level dedup + reconciliation   │
│                                                                                 │
│  2. DOUBLE-ENTRY LEDGER                                                        │
│     Every transaction creates balanced entries. SUM always = 0.                │
│     Append-only. Corrections via reversal entries, never mutations.             │
│                                                                                 │
│  3. PCI COMPLIANCE                                                             │
│     Minimize scope. Raw PANs only in Card Vault. Everything else uses tokens.  │
│                                                                                 │
│  4. FAILURE HANDLING                                                            │
│     Never retry blindly. Always check PSP status first.                        │
│     Recovery workers fix stuck payments. Reconciliation is the safety net.      │
│                                                                                 │
│  5. SAGA PATTERN                                                               │
│     No 2PC across PSP boundary. Compensating transactions for rollback.         │
│     Eventual consistency acceptable with reconciliation backstop.               │
│                                                                                 │
│  6. MULTI-PSP ROUTING                                                          │
│     Circuit breakers, success-rate-based routing, local acquiring preference.   │
│                                                                                 │
│  7. CONSISTENCY MODEL                                                          │
│     Strong consistency for payment state (PostgreSQL synchronous replication).  │
│     Eventual consistency for analytics, webhooks, dashboards.                   │
│                                                                                 │
│  8. CURRENCY HANDLING                                                          │
│     Always smallest unit (cents). Never floating point. Lock rate at capture.   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```
