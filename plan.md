# Hyperlocal Fresh Vendor Marketplace — Simplified Product Plan

> **Implementation status (19 July 2026):** A colourful, runnable Streamlit MVP has been scaffolded in this repository. The customer marketplace, cart, delivery-slot selection, UPI/COD demo checkout, order history, and a low-clutter vendor dashboard are complete as an interactive front-end demo. Live OTP, payment webhooks, database persistence, WhatsApp Business API notifications, GPS, and scheduled fees remain integration work before production launch.

## 1. Why This Plan Simplifies the Original PRD

The original PRD packs in a lot at once — loyalty points, multiple filters, voice pricing, multilingual everything, Aadhaar verification, Porter integration, ratings, deals engines — all on day one. That's a lot of surface area for a first version, and it slows both build time and vendor/customer adoption (vendors are often not tech-savvy; the whole pitch is "simple to use").

This plan keeps every requirement you and Laviniya specified, but organizes it into:
- **Core Loop (MVP)** — the minimum needed for a customer to buy a vegetable from a vendor and pay for it.
- **Phase 2** — things that make the app delightful but aren't needed to transact.
- **Phase 3 / Future** — admin, advanced automation, scale features.

This way nothing is dropped — it's just sequenced so the app can actually ship and be used, instead of being complex to build and confusing to use.

---

## 2. Project Overview

A mobile-first web app connecting local vegetable vendors with nearby customers — a Blinkit-style quick-commerce experience, but for hyperlocal vendors. Core pillars: **simple ordering, instant WhatsApp communication, easy digital payment, and low friction for vendors** (many of whom will be using this on a basic smartphone, possibly with low typing comfort).

---

## 3. User Roles

| Role | Description |
|---|---|
| **Customer** | Browses nearby vendors, orders vegetables, pays digitally, tracks order |
| **Vendor** | Lists/updates products & prices, receives & fulfills orders, views daily earnings |
| **Admin** | Future scope — platform oversight, vendor onboarding approval, fee reconciliation |

---

## 4. Core Loop (MVP) — Build This First

This is the smallest version of the app that lets a real transaction happen end-to-end.

### 4.1 Loading Screen
Instead of a blank spinner, show a rotating card while the app loads (2–3 sec rotation). This is cheap to build and immediately makes the app feel more polished.

Card types (content can be a static rotating array, no backend needed):
- 🥬 **Fresh Fact** — e.g. "Fresh vegetables retain more nutrients and taste."
- 👨‍🌾 **Community Impact** — e.g. "Supporting local vendors helps strengthen neighbourhood businesses."
- 🌱 **Health Tip** — e.g. "Eating seasonal vegetables supports better nutrition."
- 💚 **Sustainability Message** — e.g. "Buying locally reduces transportation and food waste."

*Simplification: keep this as a static rotating JSON array of ~10-15 cards to start. No CMS needed for v1.*

### 4.2 Customer Onboarding
- Mobile number + OTP login (no password)
- Name, Address, Gender (Gender is optional — don't block signup on it)
- Auto-detect location via GPS to determine "zone"

### 4.3 Home Screen
- Clean, Blinkit-style layout
- Zone-wise vendor listing (only show vendors who deliver to customer's area)
- Search bar (products/vendors)
- Category browsing (Leafy greens, Root veggies, Exotic, etc.)

*Simplification: Skip complex filter chips at launch — just Search + Category tabs. Add Delivery Time / Organic filters in Phase 2 once there's enough catalog depth for filters to matter.*

### 4.4 Product / Stall Listing
Each stall/product shows:
- Product name, price
- Stall photo
- Vendor rating (once reviews exist — show "New Vendor" badge until then)
- Estimated delivery time

**Demo vendor included:** **Meera's Fresh Basket** (Indiranagar, Bengaluru) is preloaded with fresh products and the WhatsApp number `+91 98765 43210`. The **“Chat with Meera on WhatsApp”** button opens WhatsApp directly with a prefilled customer message.

### 4.5 Ordering Flow
1. Customer browses → adds items to cart
2. Selects a delivery/pickup time slot (Dmart Ready style, e.g. 9–10 AM, 10–11 AM, 6–7 PM)
3. Reviews order → taps **Pay Now**

### 4.6 Payment Flow (UPI-first, per your update)
> **Note:** Vendor number is now shown as-is, **not masked** — masking was breaking the UPI payment link/flow. This is a deliberate change from the original PRD.

1. Customer taps **Pay Now**
2. UPI app opens directly (GPay / PhonePe / Paytm / BHIM — via standard UPI deep link, not a custom gateway build)
3. Customer approves payment in their UPI app
4. Payment confirms within seconds
5. Order status auto-updates to **"Paid"**
6. Vendor gets:
   - An in-app **payment confirmation**
   - An **instant WhatsApp receipt** (auto-generated, sent immediately on payment success)
7. Cash on Delivery (COD) remains available as a fallback option

*Simplification: For v1, use a standard UPI payment link/QR (via a payment aggregator like Razorpay/Cashfree UPI intent) rather than building custom bank-level payment infra. This gets you the exact flow described with far less engineering.*

### 4.7 Vendor WhatsApp Order Notification
On every order, vendor receives a WhatsApp Business message with:
- Total Items
- Total Price
- Customer Name, Address, Phone Number
- GPS Location
- **Payment receipt** (once paid)
- All of the above delivered in the **vendor's preferred language**

### 4.8 Vendor Registration & Dashboard (MVP version)
Registration:
- Name, Mobile Number, Aadhaar/ID Proof, Payment (bank/UPI) details

Dashboard (kept to 4 numbers — no clutter):
- Orders Received
- Orders Completed
- Today's Revenue
- Pending Orders (needs action)

### 4.9 Vendor Price Updates
- **Manual update** (tap to edit price) — ships in MVP
- **Voice update** (speak product + price) — Phase 2, since it needs speech-to-text integration and more QA across languages/accents

### 4.10 Platform Fee
- A flat **₹10/day** charge is deducted from each active vendor, automatically, once per day.
- Shown transparently on the vendor dashboard (e.g. "Platform fee today: ₹10 — deducted at midnight" or deducted from next payout, whichever is simpler to implement first: **recommend deducting from the vendor's next settlement/payout** rather than requiring a separate charge transaction — far simpler and avoids failed-payment edge cases).

### 4.11 Order Status & Delivery
- Vendor accepts order → chooses **Self Delivery** or **Porter Delivery**
- Status updates flow: Confirmed → Accepted → Out for Delivery → Delivered
- Customer gets WhatsApp/push updates at each stage

### 4.12 Ratings & Reviews
- After delivery, customer can rate (1–5 stars) + optional text review
- Kept simple: no photo reviews, no reply threads in v1

---

## 5. Phase 2 — Delight & Retention Features

Add once the core loop is working reliably and there's real usage data.

- **Loyalty Points** — points per order, redeemable on future orders
- **Filters** — Delivery Time, Organic Tag (needs enough catalog data to be useful)
- **Voice Price Updates** — for vendors who don't want to type
- **End-of-Day Deals / Fresh Day Deals** — vendor-created, pushed via WhatsApp
- **Multilingual App UI** (not just notifications — the full customer/vendor interface)
- **Minimum Order Amount** setting per vendor

---

## 6. Phase 3 — Platform & Scale

- Admin panel: vendor approvals, dispute resolution, fee reconciliation, analytics
- Porter delivery API integration (vs. manual "call a porter" in early phases)
- Smart/automated promotional notifications (rule-based: "haven't ordered in 7 days" etc.)
- Advanced vendor analytics (best-selling items, peak hours)

---

## 7. Functional Flow (Simplified)

**Customer:**
Loading screen → Login (OTP) → Browse zone-wise vendors → Add to cart → Pick time slot → Pay Now (UPI/COD) → Order confirmed → Track status → Rate & review

**Vendor:**
Login → Update prices (manual) → Get WhatsApp order alert → Accept → Choose Self/Porter delivery → Mark delivered → View daily dashboard (auto-adjusted for ₹10 platform fee)

---

## 8. Non-Functional Requirements

- Mobile-first, responsive web app
- Fast load time — loading screen used to mask any unavoidable delay
- Secure OTP authentication
- Secure UPI payment handling (via established payment aggregator, not custom-built)
- WhatsApp Business API integration for notifications + receipts
- GPS integration for zone detection and delivery
- Vendor UI kept minimal — large tap targets, icon-first, minimal text entry

---

## 9. Suggested Tech Approach — Streamlit-Based Deployment

Since the goal is a fast, simple-to-ship MVP (not a scaled consumer app yet), **Streamlit** is a solid choice for v1: fast to build, easy to deploy, minimal frontend boilerplate — good for validating the core loop before ever investing in a custom React frontend.

- **App framework:** Streamlit, with two entry points — a Customer app view and a Vendor app view (either as separate pages within one multipage app, or two separate Streamlit apps if you want fully separate deployments)
- **Session/state:** `st.session_state` for cart, login state, selected time slot, etc.
- **Auth:** OTP via SMS provider (MSG91/Twilio Verify) — Streamlit form triggers OTP send + verify
- **Payments:** Razorpay or Cashfree UPI intent/link — generate the payment link server-side, open it via `st.link_button` or embed the UPI QR/deep link; webhook listener (a small FastAPI/Flask endpoint alongside Streamlit) updates order status on payment success
- **Messaging:** WhatsApp Business API (Meta Cloud API or Gupshup/Twilio) triggered from backend functions on order placement and payment success
- **Database:** PostgreSQL (Supabase is a good fit — gives you Postgres + auth + storage with minimal setup, pairs well with Streamlit)
- **Storage:** Supabase Storage or S3 for stall photos
- **Deployment:** Streamlit Community Cloud for early demo/testing → migrate to a proper host (Render/Railway/AWS) once you need the webhook server and background jobs (e.g. the ₹10/day fee deduction) running reliably 24/7, since Streamlit Cloud isn't ideal for background cron-style jobs
- **Scheduled jobs:** the daily ₹10 vendor fee deduction should run as a separate scheduled script/cron job (not inside the Streamlit app process), writing directly to the database

*Note: Streamlit is great for getting the core loop working and demoable fast. If/when you outgrow it (need a native mobile-app feel, offline support, or push notifications), plan to migrate the customer-facing app to React while keeping the Streamlit vendor dashboard as-is — vendor-side tools tend to stay simple internal dashboards for a long time, which is exactly what Streamlit is best at.*

---

## 10. Project File Structure

```
veggie-market/
│
├── app/
│   ├── Home.py                     # Streamlit entry point (customer app landing)
│   ├── pages/
│   │   ├── 1_Login.py              # OTP login/signup (customer)
│   │   ├── 2_Browse.py             # Zone-wise vendor listing, search, categories
│   │   ├── 3_Stall.py              # Individual stall/product view
│   │   ├── 4_Cart.py               # Cart + time slot selection
│   │   ├── 5_Payment.py            # UPI/COD payment flow
│   │   ├── 6_Orders.py             # Order tracking & status
│   │   └── 7_Rate_Review.py        # Post-delivery rating & review
│   │
│   ├── vendor_app/
│   │   ├── Vendor_Home.py          # Vendor entry point / login
│   │   ├── pages/
│   │   │   ├── 1_Dashboard.py      # Orders received/completed, revenue, fee status
│   │   │   ├── 2_Products.py       # Manual price updates (voice = Phase 2)
│   │   │   ├── 3_Orders.py         # Incoming orders, accept/deliver flow
│   │   │   └── 4_Deals.py          # End-of-day / Fresh day deals (Phase 2)
│   │
│   └── components/
│       ├── loading_screen.py       # Rotating fact-card splash component
│       ├── otp_auth.py             # Shared OTP send/verify logic
│       ├── ui_helpers.py           # Reusable Streamlit UI snippets (cards, badges)
│       └── zone_utils.py           # GPS → zone matching logic
│
├── backend/
│   ├── main.py                     # FastAPI app (webhooks + APIs Streamlit can't do natively)
│   ├── routes/
│   │   ├── payments.py             # Razorpay/Cashfree webhook handlers
│   │   └── whatsapp.py             # WhatsApp Business API send functions
│   ├── services/
│   │   ├── payment_service.py      # UPI link/QR generation, status polling
│   │   ├── whatsapp_service.py     # Order alert + payment receipt templates
│   │   ├── otp_service.py          # SMS OTP send/verify
│   │   └── fee_service.py          # ₹10/day vendor fee logic
│   └── jobs/
│       └── daily_fee_deduction.py  # Scheduled script (cron) for vendor platform fee
│
├── db/
│   ├── models.py                   # SQLAlchemy models: Customer, Vendor, Product, Order, Review
│   ├── database.py                 # DB connection (Supabase/Postgres)
│   └── migrations/                 # Alembic migration scripts
│
├── data/
│   └── loading_facts.json          # Static rotating fact-card content (fresh facts, health tips, etc.)
│
├── assets/
│   ├── images/                     # Logo, icons, placeholder stall photos
│   └── styles/
│       └── custom.css              # Streamlit theme overrides (injected via st.markdown)
│
├── config/
│   ├── settings.py                 # Env-based config (API keys, DB URL, etc.)
│   └── .env.example                # Template for required environment variables
│
├── tests/
│   ├── test_payment_service.py
│   ├── test_whatsapp_service.py
│   ├── test_fee_service.py
│   └── test_zone_utils.py
│
├── requirements.txt
├── .streamlit/
│   └── config.toml                 # Streamlit theme/server config
├── README.md
└── .gitignore
```

**Structure notes:**
- Customer and Vendor apps are kept as **separate Streamlit multipage apps** (`app/` and `app/vendor_app/`) so each stays simple and role-focused — no conditional UI clutter for "which role is this user."
- `backend/` exists specifically for the things Streamlit can't do on its own: receiving payment webhooks and running scheduled jobs (the daily fee deduction). Everything else (UI, session state, page flow) stays in Streamlit.
- `data/loading_facts.json` keeps the splash screen content editable without touching code — easy to add new fact cards later.
- `components/` holds anything reused across multiple pages (loading screen, OTP form, zone matching) so pages stay thin.

---

## 10. What Changed From the Original PRD (Summary)

| Item | Original | Updated |
|---|---|---|
| Vendor number | Masked during payment | **Not masked** — was breaking UPI flow |
| Platform fee | Not specified | **₹10/day flat fee per vendor** |
| Loading screen | Not specified | **Rotating fact cards** (fresh facts, community, health, sustainability) |
| Payment flow | UPI/COD, general | **Explicit UPI deep-link flow** + instant WhatsApp payment receipt to vendor |
| Feature sequencing | All features at once | **Split into MVP / Phase 2 / Phase 3** to reduce complexity |
| Filters | Time + Organic, launch feature | Moved to Phase 2 |
| Voice pricing | Launch feature | Moved to Phase 2 (manual update ships first) |

---

## 11. Recommended Build Order (First 4 Sprints)

1. **Sprint 1:** Auth (OTP), vendor registration, basic product listing, loading screen
2. **Sprint 2:** Cart, time slot selection, order placement, vendor WhatsApp order alert
3. **Sprint 3:** UPI payment integration, payment status sync, WhatsApp payment receipt, ₹10/day fee logic
4. **Sprint 4:** Vendor dashboard, delivery status flow (Self/Porter), ratings & reviews

This gets a fully working, simple, transactable product live before layering on loyalty points, filters, voice input, or multilingual UI.

---

## 12. Delivery Checklist — Current Repository

### Completed in the Streamlit MVP

- [x] Colourful mobile-first customer interface with bright category and product cards
- [x] Rotating fresh-fact / community / sustainability message
- [x] Zone-focused dummy vendor listing and product catalogue
- [x] Searchable products, basket, quantity adjustment, and delivery-slot selection
- [x] UPI intent link and COD demo order flow
- [x] Customer order history
- [x] Dummy vendor account: **Meera's Fresh Basket**, `+91 98765 43210`
- [x] Direct WhatsApp chat link for the dummy vendor
- [x] Vendor dashboard with key metrics, fee transparency, order-action controls, and manual price fields
- [x] Separate customer and vendor demo login experiences
- [x] Vendor inventory management for live product price and stock updates
- [x] Product search results show vendor name, price, and item-specific WhatsApp contact action
- [x] Hackathon-level visual system: dark glassmorphism, layered gradients, 3D depth/hover treatment, and animated-feeling CTA styling
- [x] Four discoverable vendors with distinct locations, ratings, delivery times, prices, and direct WhatsApp numbers
- [x] Vendor comparison controls: select a stall to see its live catalogue and price variation
- [x] Richer vegetable discovery: free-text search, category actions, price sorting, stock state, and item-specific contact buttons
- [x] Purposeful clickable cards/actions for vendor selection, vendor contact, category filtering, product contact, cart addition, tips, and inventory publishing
- [x] High-contrast accessibility pass: readable light card surfaces, dark text, and clear form controls
- [x] Enhanced landing page with marketplace metrics, value-proposition cards, customer social proof, and clearer login entry points
- [x] Original 3D vegetable-market hero illustration integrated as the visual landing-page background
- [x] Vendor insight suite with day/week/month net-profit charts, profit/loss alerts, overall sales and cost metrics, and past monthly performance history
- [x] Vendor onboarding form for owner/stall identity, locality, PIN code, full address, mobile and WhatsApp numbers, delivery coverage, settlement UPI ID, and notification language

### Required before a production launch

- [ ] Connect OTP provider and secure session handling
- [ ] Add Postgres/Supabase persistence and role-based vendor authentication
- [ ] Integrate Razorpay/Cashfree webhook verification — do not mark UPI payments paid from the browser alone
- [ ] Configure WhatsApp Business API templates for order and receipt notifications
- [ ] Add GPS permission, zone matching, reviews, and a scheduled fee-deduction job
