import streamlit as st
import pandas as pd
import json
from urllib.parse import quote, unquote
from pathlib import Path
from components.data import FACTS, PRODUCTS, VENDOR, VENDORS, LOCATIONS, VENDOR_TRANSLATIONS
from components.ui_helpers import inject_styles, inr
from components.voice_assistant import render_voice_assistant
import base64

st.set_page_config(page_title="FreshKart Local", page_icon="🥕", layout="wide")
inject_styles()

BASE_DIR = Path(__file__).resolve().parent
VENDOR_USERS_FILE = BASE_DIR / "vendor_users.json"
VENDOR_COOKIE_NAME = "freshkart_vendor_user"

def normalize_mobile(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) == 12 and digits.startswith("91"):
        return digits[2:]
    return digits

def load_vendor_accounts():
    try:
        with VENDOR_USERS_FILE.open("r", encoding="utf-8") as f:
            accounts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [account for account in accounts if account.get("profile")]

def get_cookie_vendor_account():
    context = getattr(st, "context", None)
    if not context:
        return None
    try:
        raw_cookie = context.cookies.get(VENDOR_COOKIE_NAME)
    except Exception:
        return None
    if not raw_cookie or not isinstance(raw_cookie, str):
        return None
    try:
        return json.loads(unquote(raw_cookie))
    except json.JSONDecodeError:
        return None

def set_vendor_cookie(account):
    payload = json.dumps(account, separators=(",", ":"))
    encoded_payload = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    cookie_name = json.dumps(VENDOR_COOKIE_NAME)
    st.iframe(
        f"""
        <script>
        const encodedPayload = "{encoded_payload}";
        const bytes = Uint8Array.from(atob(encodedPayload), c => c.charCodeAt(0));
        const payload = new TextDecoder().decode(bytes);
        const expires = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toUTCString();
        document.cookie = {cookie_name} + "=" + encodeURIComponent(payload) + "; expires=" + expires + "; path=/; SameSite=Lax";
        </script>
        """,
        height=1,
    )

def profile_to_vendor_listing(profile):
    loc_id = next((loc["id"] for loc in LOCATIONS if loc["name"] == profile.get("locality")), "bandra")
    return {
        "id": profile["id"],
        "name": profile["stall"],
        "owner": profile["owner"],
        "phone": profile["whatsapp"],
        "area": profile["locality"],
        "home_zone": loc_id,
        "zones": [loc_id],
        "zone_deltas": {loc_id: 0},
        "zone_time": {loc_id: "15 min"},
        "rating": 5.0,
        "delivery": "15 min",
        "tagline": "Freshly onboarded local stall",
        "accent": "#10b981",
        "delta": 0,
        "photo": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=800",
    }

def open_vendor_account(account):
    profile = dict(account["profile"])
    st.session_state.role = "vendor"
    st.session_state.vendor_profile = profile
    if "custom_vendors_profiles" not in st.session_state:
        st.session_state.custom_vendors_profiles = {}
    st.session_state.custom_vendors_profiles[normalize_mobile(profile.get("mobile"))] = profile
    if not any(v["id"] == profile["id"] for v in st.session_state.vendors):
        st.session_state.vendors = st.session_state.vendors + [profile_to_vendor_listing(profile)]
    if profile.get("language") in ["English", "Hindi", "Marathi"]:
        st.session_state.cockpit_lang = profile["language"]

# Define image search helper
def get_vegetable_image(name):
    import urllib.request
    import urllib.parse
    import re
    import html
    query = f"fresh {name} vegetable"
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.bing.com/images/search?q={encoded_query}"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    try:
        response = urllib.request.urlopen(req, timeout=5)
        response_html = response.read().decode('utf-8', errors='ignore')
        unescaped_html = html.unescape(response_html)
        murls = re.findall(r'"murl"\s*:\s*"(https?://[^"]+)"', unescaped_html)
        if murls:
            for m in murls:
                if m.startswith("http") and not any(x in m for x in ["facebook", "twitter", "login", "instagram"]):
                    return m
    except Exception as e:
        pass
    return "https://images.unsplash.com/photo-1610348725531-843dff163e2c?w=400&auto=format&fit=crop&q=60"

# Check for Speech to Text updates in query parameters
if "update_prod" in st.query_params and "update_price" in st.query_params:
    prod_name = st.query_params["update_prod"]
    try:
        new_price = int(st.query_params["update_price"])
        if "inventory" in st.session_state and prod_name in st.session_state.inventory:
            st.session_state.inventory[prod_name]["price"] = new_price
            st.toast(f"🎙️ Voice Updated: {prod_name} -> ₹{new_price}!")
    except Exception as e:
        pass
    # Clear query parameters
    st.query_params.clear()
    st.rerun()

for key, default in {"cart": {}, "orders": [], "role": None, "selected_vendor": "meera", "active_category": "All", "vendor_profile": None, "selected_location": "bandra"}.items():
    if key not in st.session_state: st.session_state[key] = default

if "products" not in st.session_state:
    st.session_state.products = list(PRODUCTS)
else:
    for p in st.session_state.products:
        default_p = next((x for x in PRODUCTS if x["name"] == p["name"]), None)
        if default_p and p.get("image") != default_p.get("image") and not p.get("image", "").startswith("data:image"):
            p["image"] = default_p["image"]

if "vendors" not in st.session_state:
    st.session_state.vendors = list(VENDORS)

if "inventory" not in st.session_state:
    st.session_state.inventory = {p["name"]: {"price": p["price"], "stock": p["stock"]} for p in st.session_state.products}

if "vendor_photos" not in st.session_state:
    st.session_state.vendor_photos = {}

def vendor_price(product, vendor):
    base = st.session_state.inventory.get(product["name"], {"price": product["price"]})["price"] if vendor["id"] == "meera" else product["price"]
    zone = st.session_state.get("selected_location", vendor.get("home_zone", ""))
    zone_delta = vendor.get("zone_deltas", {}).get(zone, 5)
    return max(1, base + vendor["delta"] + zone_delta)

def vendor_delivery_time(vendor):
    zone = st.session_state.get("selected_location", vendor.get("home_zone", ""))
    return vendor.get("zone_time", {}).get(zone, vendor["delivery"])

def available_vendors():
    zone = st.session_state.get("selected_location", "bandra")
    return [v for v in st.session_state.vendors if zone in v.get("zones", [])]

def selected_vendor():
    avail = available_vendors()
    if not avail: return st.session_state.vendors[0]
    match = next((v for v in avail if v["id"] == st.session_state.selected_vendor), None)
    return match if match else avail[0]
def normalize_whatsapp(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) == 10:
        return "91" + digits
    elif len(digits) == 12 and digits.startswith("91"):
        return digits
    return digits or "919876543210"

def whatsapp_url(vendor, product=None, price=None):
    phone = normalize_whatsapp(vendor.get("phone") or vendor.get("whatsapp"))
    text = f"Hi {vendor['owner']}, I found {vendor['name']} on FreshKart Local."
    if product: text += f" Is {product['name']} available today at {inr(price)}?"
    return f"https://wa.me/{phone}?text={quote(text)}"

def vendor_order_whatsapp_url(vendor, order_id, items_for_vendor, slot, payment):
    phone = normalize_whatsapp(vendor.get("phone") or vendor.get("whatsapp"))
    owner_name = vendor.get("owner", "Vendor")
    stall_name = vendor.get("name") or vendor.get("stall") or "Local Stall"
    
    lines = [
        f"🛒 *FreshKart Local - New Order Alert (#{order_id})*",
        f"📍 *Stall:* {stall_name} (Owner: {owner_name})",
        f"⏰ *Slot:* {slot} | 💳 *Payment:* {payment}",
        "",
        "🥬 *Vegetable Order List & Quantities:*",
    ]
    
    subtotal_total = 0
    for item in items_for_vendor:
        p_name = item['product']['name']
        p_unit = item['product'].get('unit', 'unit')
        qty = item['qty']
        price = item['price']
        subtotal = qty * price
        subtotal_total += subtotal
        lines.append(f"  • {p_name}: {qty} x {p_unit} ({inr(price)} each) = {inr(subtotal)}")
    
    lines.append("")
    lines.append(f"💰 *Vendor Subtotal:* {inr(subtotal_total)}")
    lines.append("Please prepare these fresh vegetables for fulfilment. Thank you!")
    
    msg_text = "\n".join(lines)
    return f"https://wa.me/{phone}?text={quote(msg_text)}", msg_text
def add_item(product):
    key = f"{selected_vendor()['id']}::{product['name']}"
    st.session_state.cart[key] = st.session_state.cart.get(key, 0) + 1
def cart_total():
    return sum(v["price"] * v["qty"] for v in cart_items())
def cart_items():
    output=[]
    for key, qty in st.session_state.cart.items():
        vendor_id, name = key.split("::", 1); p=next(x for x in st.session_state.products if x["name"] == name); v=next(x for x in st.session_state.vendors if x["id"] == vendor_id)
        output.append({"key":key,"qty":qty,"product":p,"vendor":v,"price":vendor_price(p,v)})
    return output

st.sidebar.markdown("## 🥕 FreshKart")
st.sidebar.caption("Hyperlocal. Hyperfresh.")
if st.session_state.role and st.sidebar.button("↪ Log out", use_container_width=True): st.session_state.role=None; st.rerun()

if not st.session_state.role:
    st.markdown("""<div class="hero"><span class="pill">✦ INDIA'S LOCAL-FOOD NETWORK</span><h1>The freshest way to shop your neighbourhood.</h1><p>Compare real-time vegetable prices, discover nearby stalls, and chat with a vendor in one tap.</p></div>""", unsafe_allow_html=True)
    for col, (number, label) in zip(st.columns(3), [("4", "live local stalls"), ("50+", "fresh items daily"), ("25 min", "average delivery")]):
        col.markdown(f'<div class="landing-stat"><b>{number}</b><span class="muted">{label}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">A better way to fill your basket</div>', unsafe_allow_html=True)
    for col, (icon, title, text) in zip(st.columns(3), [("🔎", "Compare, don’t guess", "See real vendor prices before you commit."), ("💬", "One-tap vendor chat", "Ask about freshness or availability on WhatsApp."), ("🌱", "Neighbourhood impact", "Your purchase supports local food businesses.")]):
        col.markdown(f'<div class="feature-card"><div class="icon">{icon}</div><h3>{title}</h3><p>{text}</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="social-proof"><b>“I found fresher vegetables at a better price, two streets away.”</b><br><span>— Ananya, FreshKart Local customer</span></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">Fresh in your neighbourhood today 🥬</div>', unsafe_allow_html=True)
    gallery_cols = st.columns(6)
    for col, p in zip(gallery_cols, st.session_state.products[:6]):
        with col:
            img_url = p.get("image", "https://images.unsplash.com/photo-1610348725531-843dff163e2c?w=400&auto=format&fit=crop&q=60")
            st.markdown(f"""
            <div class="product-card" style="padding: 10px; margin-bottom: 20px; text-align: center; min-height: 165px;">
                <img src="{img_url}" style="width: 100%; height: 95px; object-fit: cover; border-radius: 8px; margin-bottom: 6px;">
                <b style="font-size: 0.85rem; display: block; height: 35px; overflow: hidden;">{p['emoji']} {p['name']}</b>
                <span class="muted" style="font-size: 0.75rem;">{p['unit']}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Choose your entry point</div>', unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        st.markdown('<div class="login-card"><div style="font-size:42px">🛍️</div><h2>Shop fresh</h2><p class="muted">Browse 4 local vendors and build a beautiful basket.</p></div>',unsafe_allow_html=True)
        with st.form("customer_login"):
            name=st.text_input("Your name",placeholder="e.g. Ananya"); phone=st.text_input("Mobile number",placeholder="10-digit number")
            _loc_labels=[f"{l['emoji']} {l['name']}" for l in LOCATIONS]
            loc_choice=st.selectbox("📍 Your delivery location",_loc_labels,help="Vendors and prices update based on your zone.")
            if st.form_submit_button("Enter marketplace →",type="primary",use_container_width=True):
                if name and len(phone)>=10:
                    st.session_state.role="customer"; st.session_state.customer_name=name
                    st.session_state.selected_location=LOCATIONS[_loc_labels.index(loc_choice)]["id"]; st.rerun()
                st.error("Please enter your name and a valid mobile number.")
    with b:
        st.markdown('<div class="login-card"><div style="font-size:42px">🏪</div><h2>Run your stall</h2><p class="muted">Manage stock, prices, orders, and your daily pulse.</p></div>',unsafe_allow_html=True)
        vendor_mode = st.radio(
            "Vendor access",
            ["Already have an account", "New user signin"],
            horizontal=True,
            label_visibility="collapsed",
        )
        saved_cookie_account = get_cookie_vendor_account()
        vendor_accounts = load_vendor_accounts()
        if saved_cookie_account and saved_cookie_account.get("profile"):
            saved_mobile = normalize_mobile(saved_cookie_account.get("mobile"))
            if not any(normalize_mobile(account.get("mobile")) == saved_mobile for account in vendor_accounts):
                vendor_accounts.append(saved_cookie_account)

        if vendor_mode == "Already have an account":
            with st.form("vendor_existing_login"):
                account_labels = [
                    f"{account['profile']['stall']} · {account['mobile']}"
                    for account in vendor_accounts
                ]
                selected_label = st.selectbox("Choose account", account_labels)
                password = st.text_input("Password", type="password", placeholder="Enter password")
                if st.form_submit_button("Open vendor cockpit →", type="primary", use_container_width=True):
                    selected_account = vendor_accounts[account_labels.index(selected_label)] if account_labels else None
                    if selected_account and password == selected_account.get("password"):
                        open_vendor_account(selected_account)
                        st.rerun()
                    st.error("Please choose a valid account and enter the correct password.")
            st.caption("Demo passwords: fresh123, organic123, amma123. Accounts are loaded from app/vendor_users.json.")
        else:
            with st.form("vendor_new_user"):
                owner_name = st.text_input("Owner name", placeholder="e.g. Meera Sharma")
                stall_name = st.text_input("Stall / shop name", placeholder="e.g. Meera's Fresh Basket")
                phone = st.text_input("Vendor mobile", placeholder="10-digit number", key="new_vendor_phone")
                password = st.text_input("Create password", type="password", placeholder="Minimum 4 characters")
                if st.form_submit_button("Create account →", type="primary", use_container_width=True):
                    clean_phone = normalize_mobile(phone)
                    if not owner_name or not stall_name or len(clean_phone) != 10 or len(password) < 4:
                        st.error("Please enter owner name, stall name, a 10-digit mobile number, and a password.")
                    else:
                        profile = {
                            "id": f"cookie_vendor_{clean_phone}",
                            "owner": owner_name,
                            "stall": stall_name,
                            "mobile": clean_phone,
                            "whatsapp": f"91{clean_phone}",
                            "email": "",
                            "locality": "Bandra (West)",
                            "pincode": "400050",
                            "address": "Bandra West, Mumbai",
                            "radius": "2 km",
                            "language": "English",
                            "upi": f"{clean_phone}@upi",
                            "delivery_mode": "Self delivery",
                        }
                        new_account = {"mobile": clean_phone, "password": password, "profile": profile}
                        set_vendor_cookie(new_account)
                        open_vendor_account(new_account)
                        st.session_state.new_vendor_cookie_saved = True
                        st.success("Account created and saved in your browser cookie.")
            if st.session_state.get("new_vendor_cookie_saved"):
                if st.button("Open vendor cockpit →", type="primary", use_container_width=True):
                    st.session_state.new_vendor_cookie_saved = False
                    st.rerun()
    st.stop()

if st.session_state.role == "vendor":
    # Setup dynamic localization dictionary
    if "cockpit_lang" not in st.session_state:
        st.session_state.cockpit_lang = st.session_state.vendor_profile.get("language", "English") if st.session_state.vendor_profile else "English"
    
    st.sidebar.markdown("---")
    curr_lang = st.session_state.cockpit_lang
    if curr_lang not in ["English", "Hindi", "Marathi"]:
        curr_lang = "English"
        st.session_state.cockpit_lang = "English"
        
    st.session_state.cockpit_lang = st.sidebar.selectbox(
        "🌐 Dashboard Language / भाषा",
        ["English", "Hindi", "Marathi"],
        index=["English", "Hindi", "Marathi"].index(curr_lang)
    )
    
    lang = st.session_state.cockpit_lang
    tr = VENDOR_TRANSLATIONS.get(lang, VENDOR_TRANSLATIONS["English"])
    
    # Sync cockpit language choice back to vendor profile
    if st.session_state.vendor_profile and st.session_state.vendor_profile.get("language") != lang:
        st.session_state.vendor_profile["language"] = lang

    if not st.session_state.vendor_profile:
        st.markdown(f"""<div class="hero"><span class="pill">{tr['onboarding_hero_tag']}</span><h1>{tr['onboarding_title']}</h1><p>{tr['onboarding_subtitle']}</p></div>""", unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">{tr["onboarding_section_title"]}</div>', unsafe_allow_html=True)
        with st.form("vendor_profile_form"):
            left, right = st.columns(2)
            with left:
                owner_name = st.text_input(tr["owner_name_label"], placeholder=tr["owner_name_placeholder"])
                stall_name = st.text_input(tr["stall_name_label"], placeholder=tr["stall_name_placeholder"])
                mobile = st.text_input(tr["mobile_label"], placeholder=tr["mobile_placeholder"])
                whatsapp = st.text_input(tr["whatsapp_label"], placeholder=tr["whatsapp_placeholder"])
                email = st.text_input(tr["email_label"], placeholder=tr["email_placeholder"])
            with right:
                locality = st.selectbox(tr["locality_label"], [l["name"] for l in LOCATIONS])
                pincode = st.text_input(tr["pincode_label"], placeholder=tr["pincode_placeholder"], max_chars=6)
                address = st.text_area(tr["address_label"], placeholder=tr["address_placeholder"])
                delivery_radius = st.selectbox(tr["radius_label"], ["1 km", "2 km", "3 km", "5 km"])
                language = st.selectbox(tr["whatsapp_lang_label"], ["English", "Hindi", "Marathi", "Kannada", "Tamil", "Telugu"])
            st.markdown(f"#### {tr['settlement_title']}")
            settlement_left, settlement_right = st.columns(2)
            upi_id = settlement_left.text_input(tr["upi_label"], placeholder=tr["upi_placeholder"])
            
            # Localize delivery option values
            delivery_opts_map = {
                tr["delivery_mode_self"]: "Self delivery",
                tr["delivery_mode_partner"]: "Porter / delivery partner",
                tr["delivery_mode_both"]: "Both"
            }
            delivery_choice = settlement_right.selectbox(tr["delivery_mode_label"], list(delivery_opts_map.keys()), key="delivery_mode_widget")
            delivery_mode = delivery_opts_map[delivery_choice]
            
            agreed = st.checkbox(tr["agreed_label"])
            if st.form_submit_button(tr["submit_onboarding"], type="primary", use_container_width=True):
                required = [owner_name, stall_name, mobile, whatsapp, locality, pincode, address, upi_id]
                if not all(required) or len(pincode) != 6 or not agreed:
                    st.error(tr["onboarding_error"])
                else:
                    new_v_id = f"custom_vendor_{len(st.session_state.vendors) + 1}"
                    loc_id = next((l["id"] for l in LOCATIONS if l["name"] == locality), "bandra")
                    
                    st.session_state.vendor_profile = {
                        "id": new_v_id, 
                        "owner": owner_name, 
                        "stall": stall_name, 
                        "mobile": mobile, 
                        "whatsapp": whatsapp, 
                        "email": email, 
                        "locality": locality, 
                        "pincode": pincode, 
                        "address": address, 
                        "radius": delivery_radius, 
                        "language": language, 
                        "upi": upi_id, 
                        "delivery_mode": delivery_mode
                    }
                    
                    new_v = {
                        "id": new_v_id,
                        "name": stall_name,
                        "owner": owner_name,
                        "phone": whatsapp,
                        "area": locality,
                        "home_zone": loc_id,
                        "zones": [loc_id],
                        "zone_deltas": {loc_id: 0},
                        "zone_time": {loc_id: "15 min"},
                        "rating": 5.0,
                        "delivery": "15 min",
                        "tagline": "Freshly onboarded local stall",
                        "accent": "#10b981",
                        "delta": 0,
                        "photo": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=800"
                    }
                    
                    st.session_state.vendors = st.session_state.vendors + [new_v]
                    
                    if "custom_vendors_profiles" not in st.session_state:
                        st.session_state.custom_vendors_profiles = {}
                    phone_key = st.session_state.get("temp_vendor_phone", mobile)
                    st.session_state.custom_vendors_profiles[phone_key] = st.session_state.vendor_profile
                    
                    if language in ["English", "Hindi", "Marathi"]:
                        st.session_state.cockpit_lang = language
                    st.success("Stall profile saved. Welcome to your vendor cockpit!")
                    st.rerun()
        st.stop()
        
    profile = st.session_state.vendor_profile
    st.title(f"{profile['owner']}’s {tr['title']} ✦")
    st.caption(f"{profile['stall']} · {profile['locality']} – {profile['pincode']} · {tr['subtitle']}")
    
    with st.expander(tr["edit_profile"]):
        with st.form("edit_profile_form"):
            left, right = st.columns(2)
            with left:
                new_owner = st.text_input(tr["owner_name_label"], value=profile.get("owner", ""))
                new_stall = st.text_input(tr["stall_name_label"], value=profile.get("stall", ""))
                st.text_input(tr["mobile_label"], value=profile.get("mobile", ""), disabled=True)
                new_whatsapp = st.text_input(tr["whatsapp_label"], value=profile.get("whatsapp", ""))
                new_email = st.text_input(tr["email_label"], value=profile.get("email", ""))
            with right:
                loc_names = [l["name"] for l in LOCATIONS]
                loc_cur = profile.get("locality", "Bandra")
                loc_idx = loc_names.index(loc_cur) if loc_cur in loc_names else 0
                new_locality = st.selectbox(tr["locality_label"], loc_names, index=loc_idx)
                
                new_pincode = st.text_input(tr["pincode_label"], value=profile.get("pincode", ""), max_chars=6)
                new_address = st.text_area(tr["address_label"], value=profile.get("address", ""))
                
                radius_vals = ["1 km", "2 km", "3 km", "5 km"]
                radius_idx = radius_vals.index(profile.get("radius", "2 km")) if profile.get("radius", "2 km") in radius_vals else 1
                new_radius = st.selectbox(tr["radius_label"], radius_vals, index=radius_idx)
                
                lang_opts = ["English", "Hindi", "Marathi", "Kannada", "Tamil", "Telugu"]
                lang_cur = profile.get("language", "English")
                lang_idx = lang_opts.index(lang_cur) if lang_cur in lang_opts else 0
                new_lang = st.selectbox(tr["whatsapp_lang_label"], lang_opts, index=lang_idx)
                
            st.markdown(f"#### {tr['settlement_title']}")
            settlement_left, settlement_right = st.columns(2)
            new_upi = settlement_left.text_input(tr["upi_label"], value=profile.get("upi", ""))
            
            delivery_opts_map = {
                tr["delivery_mode_self"]: "Self delivery",
                tr["delivery_mode_partner"]: "Porter / delivery partner",
                tr["delivery_mode_both"]: "Both"
            }
            curr_mode = profile.get("delivery_mode", "Self delivery")
            delivery_mode_keys = list(delivery_opts_map.keys())
            delivery_mode_vals = list(delivery_opts_map.values())
            mode_idx = delivery_mode_vals.index(curr_mode) if curr_mode in delivery_mode_vals else 0
            new_delivery_choice = settlement_right.selectbox(tr["delivery_mode_label"], delivery_mode_keys, index=mode_idx)
            new_delivery_mode = delivery_opts_map[new_delivery_choice]
            
            if st.form_submit_button(tr["save_profile_button"] if "save_profile_button" in tr else "Save Profile Changes 💾"):
                if not new_owner or not new_stall or not new_whatsapp or not new_locality or len(new_pincode) != 6 or not new_address or not new_upi:
                    st.error(tr["onboarding_error"])
                else:
                    profile["owner"] = new_owner
                    profile["stall"] = new_stall
                    profile["whatsapp"] = new_whatsapp
                    profile["email"] = new_email
                    profile["locality"] = new_locality
                    profile["pincode"] = new_pincode
                    profile["address"] = new_address
                    profile["radius"] = new_radius
                    profile["language"] = new_lang
                    profile["upi"] = new_upi
                    profile["delivery_mode"] = new_delivery_mode
                    
                    # Sync back to the st.session_state.vendors list
                    v_id = profile.get("id", "meera")
                    loc_id = next((l["id"] for l in LOCATIONS if l["name"] == new_locality), "bandra")
                    for v in st.session_state.vendors:
                        if v["id"] == v_id:
                            v["owner"] = new_owner
                            v["name"] = new_stall
                            v["phone"] = new_whatsapp
                            v["area"] = new_locality
                            v["home_zone"] = loc_id
                            v["zones"] = [loc_id]
                            v["zone_deltas"] = {loc_id: 0}
                            v["zone_time"] = {loc_id: "15 min"}
                            
                    # Update cockpit UI language immediately if changed to English, Hindi, or Marathi
                    if new_lang in ["English", "Hindi", "Marathi"]:
                        st.session_state.cockpit_lang = new_lang
                        
                    # Also save to custom profiles list
                    if "custom_vendors_profiles" not in st.session_state:
                        st.session_state.custom_vendors_profiles = {}
                    phone_key = profile.get("mobile", new_whatsapp)
                    st.session_state.custom_vendors_profiles[phone_key] = profile
                    
                    st.success("Stall profile updated successfully!")
                    st.rerun()

    # Vendor Photo Management Section
    with st.expander(tr["upload_photos"]):
        st.write(tr["upload_photos_desc"])
        uploaded_file = st.file_uploader(tr["upload_photos"], type=["png", "jpg", "jpeg"])
        
        vid = profile.get("id", "meera")
        if uploaded_file is not None:
            bytes_data = uploaded_file.read()
            b64_data = base64.b64encode(bytes_data).decode("utf-8")
            data_url = f"data:{uploaded_file.type};base64,{b64_data}"
            
            if vid not in st.session_state.vendor_photos:
                st.session_state.vendor_photos[vid] = []
            if data_url not in st.session_state.vendor_photos[vid]:
                st.session_state.vendor_photos[vid].append(data_url)
                st.success(tr["uploaded_success"])
        
        # Display current photos
        all_cur_photos = st.session_state.vendor_photos.get(vid, [])
        if all_cur_photos:
            st.markdown(f"#### {tr['curr_photos']}")
            img_cols = st.columns(4)
            for idx, img_url in enumerate(all_cur_photos):
                with img_cols[idx % 4]:
                    st.image(img_url, use_container_width=True)
                    if st.button("🗑️ Delete", key=f"del_photo_{idx}"):
                        st.session_state.vendor_photos[vid].remove(img_url)
                        st.success("Stall photo deleted successfully!")
                        st.rerun()
    stats=[("📩",tr["new_orders"],"12"),("⚡",tr["fulfillment"],"94%"),("💸",tr["revenue"],"₹2,840"),("🥬",tr["low_stock"],tr["low_stock_val"])]
    for col,(icon,label,value) in zip(st.columns(4),stats): col.markdown(f'<div class="stat-card">{icon} <span class="muted">{label}</span><div class="stat-value">{value}</div></div>',unsafe_allow_html=True)
    overview, past = st.tabs([tr["insights_tab"], tr["history_tab"]])
    with overview:
        st.markdown(f"### {tr['net_profit_tracker']}")
        period = st.radio(tr["view_perf_by"], [tr["Day"], tr["Week"], tr["Month"]], horizontal=True)
        # Map localized keys back to standard keys for dataframe retrieval
        std_period = "Day"
        if period == tr["Week"]: std_period = "Week"
        elif period == tr["Month"]: std_period = "Month"
        
        profit_data = {
            "Day": pd.DataFrame({"Period": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "Net profit": [420, 610, -95, 780, 640, 920, 540]}),
            "Week": pd.DataFrame({"Period": ["Week 1", "Week 2", "Week 3", "Week 4"], "Net profit": [2850, 3440, 2310, 4210]}),
            "Month": pd.DataFrame({"Period": ["Feb", "Mar", "Apr", "May", "Jun", "Jul"], "Net profit": [9680, 11240, 10410, 12680, 13850, 15420]}),
        }
        frame = profit_data[std_period].set_index("Period")
        net_profit = int(frame["Net profit"].sum())
        profit_col, sales_col, costs_col = st.columns(3)
        profit_col.metric(f"{period}{tr['net_profit_label']}", inr(net_profit), f"+12.4% vs last {std_period.lower()}")
        sales_col.metric(tr["sales_collected"], inr(int(net_profit * 2.58)), "42 orders")
        costs_col.metric(tr["costs_fee"], inr(int(net_profit * 1.58)), tr["p_fee_included"])
        st.caption(tr["profit_caption"])
        st.line_chart(frame, color="#159c65", height=300)
        if (frame["Net profit"] < 0).any():
            loss_period = frame[frame["Net profit"] < 0].index[0]
            loss_val = inr(abs(int(frame.loc[loss_period, 'Net profit'])))
            st.warning(f"{loss_period} {tr['loss_warning'].format(loss=loss_val)}")
        else:
            profit_val = inr(int(frame['Net profit'].max()))
            st.success(tr["profit_success"].format(period=period.lower(), profit=profit_val))
    with past:
        st.markdown(f"### {tr['history_title']}")
        history = pd.DataFrame({
            "Month": ["February", "March", "April", "May", "June", "July"],
            "Sales": [25480, 29400, 28100, 33150, 36120, 39840],
            "Costs": [15800, 18160, 17690, 20470, 22270, 24420],
            "Net profit": [9680, 11240, 10410, 12680, 13850, 15420],
        })
        st.bar_chart(history.set_index("Month")[["Sales", "Costs"]], color=["#36c983", "#ff8f66"], height=300)
        st.dataframe(history.style.format({"Sales": "₹{:,.0f}", "Costs": "₹{:,.0f}", "Net profit": "₹{:,.0f}"}), use_container_width=True, hide_index=True)
        st.info(tr["history_info"])
    x,y=st.columns([2,1]); x.markdown(f'<div class="glass-card"><b>{tr["incoming_order"]}</b><br><span class="muted">{tr["incoming_desc"]}</span></div>',unsafe_allow_html=True)
    with y:
        st.button(tr["accept_order"],type="primary",use_container_width=True); st.button(tr["assign_delivery"],use_container_width=True)
        
    st.markdown('<div class="section-title">Live inventory</div>',unsafe_allow_html=True)
    st.caption(tr["inventory_caption"])

    # Render JavaScript Voice Assistant
    st.markdown(f"#### {tr['voice_section']}")
    render_voice_assistant(st.session_state.products, lang=lang)
    
    # Headers for inventory table
    hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([4, 2, 2, 3, 1])
    hcol1.markdown("<b>Vegetable / भाजी</b>", unsafe_allow_html=True)
    hcol2.markdown("<b>Price / किंमत</b>", unsafe_allow_html=True)
    hcol3.markdown("<b>Stock / स्टॉक</b>", unsafe_allow_html=True)
    hcol4.markdown("<b>Image Override / फोटो बदला</b>", unsafe_allow_html=True)
    hcol5.markdown("<b>Action</b>", unsafe_allow_html=True)
    
    for p in st.session_state.products:
        c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 3, 1])
        live = st.session_state.inventory.get(p["name"], {"price": p["price"], "stock": p["stock"]})
        img_url = p.get("image", "https://images.unsplash.com/photo-1610348725531-843dff163e2c?w=400&auto=format&fit=crop&q=60")
        
        # Render image + name in first column
        c1.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <img src="{img_url}" style="width: 44px; height: 44px; object-fit: cover; border-radius: 8px;">
            <div>
                {p['emoji']} <b>{p['name']}</b><br>
                <span class="muted" style="font-size:0.75rem;">{p['unit']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        price = c2.number_input("Price ₹", value=live["price"], min_value=1, key="price"+p["name"], label_visibility="collapsed")
        stock = c3.number_input("Units", value=live["stock"], min_value=0, key="stock"+p["name"], label_visibility="collapsed")
        st.session_state.inventory[p["name"]] = {"price": price, "stock": stock}
        
        # Replace image uploader
        new_img = c4.file_uploader(tr["replace_img_lbl"], type=["jpg", "png", "jpeg"], key="img"+p["name"], label_visibility="collapsed")
        if new_img:
            bytes_data = new_img.read()
            b64_data = base64.b64encode(bytes_data).decode("utf-8")
            p["image"] = f"data:{new_img.type};base64,{b64_data}"
            st.toast(f"✅ {p['name']}: {tr['replace_img_success']}")
            st.rerun()
            
        # Delete button
        if c5.button("🗑️", key="del"+p["name"], help=f"Delete {p['name']}", use_container_width=True):
            st.session_state.products = [x for x in st.session_state.products if x["name"] != p["name"]]
            if p["name"] in st.session_state.inventory:
                del st.session_state.inventory[p["name"]]
            st.toast(f"🗑️ Deleted {p['name']} successfully.")
            st.rerun()
            
    if st.button(tr["save_inventory"], type="primary", use_container_width=True):
        st.success(tr["inventory_saved"])
        
    st.markdown("---")
    if st.session_state.get("last_added_veg"):
        st.success(tr["add_veg_success"].format(name=st.session_state.last_added_veg))
        st.session_state.last_added_veg = None
        
    with st.expander(tr["add_veg_expander"], expanded=False):
        with st.form("add_vegetable_form", clear_on_submit=True):
            v_name = st.text_input(tr["add_veg_name"], placeholder=tr["add_veg_name_placeholder"])
            v_cat = st.selectbox(tr["add_veg_category"], ["Daily essentials", "Leafy greens", "Root veggies", "Exotic"])
            v_price = st.number_input(tr["add_veg_price"], min_value=1, value=30)
            v_unit = st.text_input(tr["add_veg_unit"], value="1 kg", placeholder=tr["add_veg_unit_placeholder"])
            v_stock = st.number_input(tr["add_veg_stock"], min_value=0, value=20)
            v_emoji = st.text_input(tr["add_veg_emoji"], placeholder="e.g. 🌶️")
            v_file = st.file_uploader(tr["add_veg_photo"], type=["jpg", "png", "jpeg"], help=tr["add_veg_photo_desc"])
            
            if st.form_submit_button(tr["add_veg_button"]):
                if not v_name.strip():
                    st.error(tr["add_veg_error"])
                else:
                    emoji_val = v_emoji.strip() if v_emoji.strip() else "🥦"
                    if v_file:
                        bytes_data = v_file.read()
                        b64_data = base64.b64encode(bytes_data).decode("utf-8")
                        image_url = f"data:{v_file.type};base64,{b64_data}"
                    else:
                        with st.spinner("Searching internet for vegetable image..."):
                            image_url = get_vegetable_image(v_name.strip())
                    new_prod = {
                        "name": v_name.strip(),
                        "emoji": emoji_val,
                        "price": v_price,
                        "unit": v_unit.strip(),
                        "category": v_cat,
                        "stock": v_stock,
                        "image": image_url
                    }
                    st.session_state.products = st.session_state.products + [new_prod]
                    st.session_state.inventory[v_name.strip()] = {"price": v_price, "stock": v_stock}
                    st.session_state.last_added_veg = v_name.strip()
                    st.rerun()
                    
    st.stop()

nav=st.sidebar.radio("Navigate",["Discover", "My cart", "My orders"],label_visibility="collapsed")
_sloc_labels=[f"{l['emoji']} {l['name']}" for l in LOCATIONS]; _sloc_ids=[l["id"] for l in LOCATIONS]
_sloc_cur=_sloc_ids.index(st.session_state.get("selected_location","bandra"))
_sloc_chosen=st.sidebar.selectbox("📍 Delivery zone",_sloc_labels,index=_sloc_cur,key="sidebar_loc")
_sloc_new=_sloc_ids[_sloc_labels.index(_sloc_chosen)]
if _sloc_new!=st.session_state.selected_location:
    st.session_state.selected_location=_sloc_new
    _avail=[v["id"] for v in available_vendors()]
    if _avail and st.session_state.selected_vendor not in _avail: st.session_state.selected_vendor=_avail[0]
    st.rerun()
if st.session_state.cart: st.sidebar.success(f"🧺 {sum(st.session_state.cart.values())} items · {inr(cart_total())}")

if nav == "Discover":
    _cur_loc=next((l for l in LOCATIONS if l["id"]==st.session_state.get("selected_location","bandra")),LOCATIONS[0])
    _zone_vendors=available_vendors()
    _stall_count=len(_zone_vendors)
    st.markdown(f"""<div class="hero"><span class="pill">⚡ {_stall_count} LIVE STALL{'S' if _stall_count!=1 else ''} · {_cur_loc['emoji']} {_cur_loc['name'].upper()}</span><h1>Good food is closer than you think.</h1><p>Browsing <b>{_stall_count} vendor{'s' if _stall_count!=1 else ''}</b> delivering to <b>{_cur_loc['name']}</b>. Prices already include your zone's delivery adjustment.</p></div>""",unsafe_allow_html=True)
    if not _zone_vendors:
        st.warning(f"😔 No vendors deliver to **{_cur_loc['name']}** yet. Pick a different zone from the sidebar to see available stalls.")
        st.stop()
    if st.session_state.selected_vendor not in [v["id"] for v in _zone_vendors]: st.session_state.selected_vendor=_zone_vendors[0]["id"]
    fact=FACTS[st.session_state.get("fact_index",0)%len(FACTS)]
    f1,f2=st.columns([5,1]); f1.markdown(f'<div class="glass-card">{fact[0]} <b>{fact[1]}</b><br><span class="muted">{fact[2]}</span></div>',unsafe_allow_html=True)
    if f2.button("New insight ✦",use_container_width=True): st.session_state.fact_index=st.session_state.get("fact_index",0)+1;st.rerun()
    st.markdown(f'<div class="section-title">Vendors delivering to {_cur_loc["emoji"]} {_cur_loc["name"]}</div>',unsafe_allow_html=True)
    st.caption(f"Prices reflect {_cur_loc['name']} delivery zone. Change zone in the sidebar to compare prices across Maharashtra.")
    for row in range(0,len(_zone_vendors),4):
        for col,v in zip(st.columns(4),_zone_vendors[row:row+4]):
            with col:
                active=" ✓ Selected" if v["id"]==st.session_state.selected_vendor else ""
                dtime=vendor_delivery_time(v)
                zdelta=v.get("zone_deltas",{}).get(st.session_state.get("selected_location",""),0)
                zpill=f"+₹{zdelta}/item" if zdelta>0 else "🏠 Home zone"
                zpill_bg="#c9ffdd" if zdelta==0 else "#fff3cd"
                zpill_color="#0d4b38" if zdelta==0 else "#7a4f00"
                st.markdown(f'<div class="vendor-card"><span class="mini-pill" style="background:{v["accent"]};color:white">{dtime}</span> <span class="mini-pill" style="background:{zpill_bg};color:{zpill_color}">{zpill}</span><div class="vendor-name" style="margin-top:12px">{v["name"]}</div><div class="muted">{v["area"]} · {v["tagline"]}</div><div class="rating">★ {v["rating"]}</div></div>',unsafe_allow_html=True)
                if st.button("View prices"+active,key="vendor_"+v["id"],use_container_width=True): st.session_state.selected_vendor=v["id"];st.rerun()
                st.button("View Stall & Photos 📸", key="profile_"+v["id"], use_container_width=True)
                st.link_button("WhatsApp",whatsapp_url(v),use_container_width=True)
                
    # Vendor Profile Modal/Card if clicked
    view_id = st.session_state.get("view_profile_id")
    # Also open if a profile button was clicked
    for v in _zone_vendors:
        if st.session_state.get(f"profile_{v['id']}"):
            st.session_state.view_profile_id = v["id"]
            st.rerun()
            
    if view_id:
        v_details = next((vendor for vendor in st.session_state.vendors if vendor["id"] == view_id), None)
        if v_details:
            st.markdown("---")
            p_col1, p_col2 = st.columns([1, 2])
            with p_col1:
                st.markdown(f"""
                <div class="glass-card" style="border-left: 5px solid {v_details['accent']}">
                    <h2>{v_details['name']}</h2>
                    <p><b>🧑‍🌾 Owner:</b> {v_details['owner']}</p>
                    <p><b>📍 Area:</b> {v_details['area']}</p>
                    <p><b>⭐ Rating:</b> {v_details['rating']} / 5.0</p>
                    <p><b>🚚 Delivery Time:</b> {vendor_delivery_time(v_details)}</p>
                    <p><b>💬 Tagline:</b> <i>"{v_details['tagline']}"</i></p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Close Profile View ❌", use_container_width=True):
                    st.session_state.view_profile_id = None
                    st.rerun()
            with p_col2:
                st.markdown("### Stall Photo Gallery 📸")
                gallery_cols = st.columns(3)
                all_photos = [v_details["photo"]] + st.session_state.vendor_photos.get(view_id, [])
                for idx, photo_url in enumerate(all_photos):
                    col_target = gallery_cols[idx % 3]
                    col_target.image(photo_url, use_container_width=True, caption=f"Stall View {idx + 1}" if idx > 0 else "Stall Main View")
            st.markdown("---")
            
    v=selected_vendor()

    st.markdown(f'<div class="section-title">Search {v["name"]}’s harvest</div>',unsafe_allow_html=True)
    qcol,sortcol=st.columns([3,1]); query=qcol.text_input("Search vegetables",placeholder="Try tomato, gourd, leafy, exotic…",label_visibility="collapsed"); sort=sortcol.selectbox("Sort",["Recommended","Price: low to high","Price: high to low"],label_visibility="collapsed")
    cats=[("All","✦"),("Leafy greens","🥬"),("Root veggies","🥕"),("Daily essentials","🧺"),("Exotic","🥦")]
    for col,(category,icon) in zip(st.columns(5),cats):
        if col.button(f"{icon} {category}",key="cat"+category,use_container_width=True): st.session_state.active_category=category;st.rerun()
    matches=[p for p in st.session_state.products if (not query or query.lower() in (p["name"]+p["category"]).lower()) and (st.session_state.active_category=="All" or p["category"]==st.session_state.active_category)]
    if sort.startswith("Price"): matches.sort(key=lambda p:vendor_price(p,v),reverse=sort.endswith("low"))
    if not matches: st.warning("No vegetables match that search. Try 'gourd', 'leafy', or 'exotic'.")
    for row in range(0,len(matches),4):
        for col,p in zip(st.columns(4),matches[row:row+4]):
            with col:
                price=vendor_price(p,v); stock=st.session_state.inventory.get(p["name"], {"price": p["price"], "stock": p["stock"]})["stock"] if v["id"]=="meera" else p["stock"]
                img_url = p.get("image", "https://images.unsplash.com/photo-1610348725531-843dff163e2c?w=400&auto=format&fit=crop&q=60")
                st.markdown(f"""
                <div class="product-card" style="padding: 10px; min-height: 250px; margin-bottom: 12px;">
                    <img src="{img_url}" style="width: 100%; height: 110px; object-fit: cover; border-radius: 12px; margin-bottom: 8px;">
                    <b>{p['emoji']} {p['name']}</b>
                    <div class="muted">{p['unit']} · {v['name']}</div>
                    <div class="price">{inr(price)}</div>
                    <span class="muted">{"Only a few left" if stock<10 else "In stock today"}</span>
                </div>
                """, unsafe_allow_html=True)
                st.link_button("Ask on WhatsApp",whatsapp_url(v,p,price),use_container_width=True)
                if st.button("Add to basket",key="add"+v["id"]+p["name"],use_container_width=True): add_item(p);st.toast(f"Added from {v['name']} ✨")

elif nav == "My cart":
    st.title("Your vibrant basket 🧺")
    items=cart_items()
    if not items: st.info("Your basket is waiting. Explore local stalls to start adding goodness.")
    for item in items:
        a,b,c=st.columns([4,2,1])
        img_url = item['product'].get("image", "https://images.unsplash.com/photo-1610348725531-843dff163e2c?w=100&auto=format&fit=crop&q=60")
        a.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px;">
            <img src="{img_url}" style="width: 38px; height: 38px; object-fit: cover; border-radius: 6px;">
            <div>
                {item['product']['emoji']} <b>{item['product']['name']}</b><br>
                <span class="muted" style="font-size:0.75rem;">{item['vendor']['name']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        b.write(f"{item['qty']} × {inr(item['price'])}")
        if c.button("−1",key="remove"+item["key"]): st.session_state.cart[item["key"]]-=1; st.session_state.cart={k:v for k,v in st.session_state.cart.items() if v};st.rerun()
    if items:
        st.markdown(f'<div class="order-box"><b>Total</b><span style="float:right;font-size:1.35rem;font-weight:800">{inr(cart_total())}</span><br><span class="muted">Your order is grouped by vendor for fresh fulfilment.</span></div>',unsafe_allow_html=True)
        slot=st.selectbox("Delivery slot",["9–10 AM","10–11 AM","6–7 PM","7–8 PM"]); payment=st.radio("Payment",["UPI","Cash on delivery"],horizontal=True)
        if st.button("Place demo order",type="primary",use_container_width=True):
            order_id = f"FK{1001+len(st.session_state.orders)}"
            vendor_groups = {}
            for it in items:
                v_id = it["vendor"]["id"]
                if v_id not in vendor_groups:
                    vendor_groups[v_id] = {"vendor": it["vendor"], "items": []}
                vendor_groups[v_id]["items"].append(it)
            
            vendor_breakdown = []
            auto_script_links = []
            for v_id, group in vendor_groups.items():
                v = group["vendor"]
                v_items = group["items"]
                wa_url, wa_msg = vendor_order_whatsapp_url(v, order_id, v_items, slot, payment)
                vendor_breakdown.append({
                    "vendor_id": v_id,
                    "vendor_name": v["name"],
                    "vendor_owner": v["owner"],
                    "vendor_phone": normalize_whatsapp(v.get("phone") or v.get("whatsapp")),
                    "items": [{"name": i["product"]["name"], "unit": i["product"].get("unit", ""), "qty": i["qty"], "price": i["price"]} for i in v_items],
                    "subtotal": sum(i["qty"] * i["price"] for i in v_items),
                    "whatsapp_url": wa_url,
                    "whatsapp_msg": wa_msg
                })
                auto_script_links.append(wa_url)
            
            new_order = {
                "id": order_id,
                "total": cart_total(),
                "slot": slot,
                "payment": payment,
                "status": "Confirmed",
                "vendor_breakdown": vendor_breakdown
            }
            st.session_state.orders.append(new_order)
            st.session_state.last_order_placed = new_order
            st.session_state.cart = {}
            st.rerun()

    if "last_order_placed" in st.session_state and st.session_state.last_order_placed:
        last = st.session_state.last_order_placed
        st.success(f"🎉 Order {last['id']} created successfully! Vegetable lists and quantities generated for vendors.")
        st.markdown("### 📲 Dispatch Vegetable List & Quantity to Vendors via WhatsApp")
        for vb in last.get("vendor_breakdown", []):
            with st.container():
                st.markdown(f"**🏪 {vb['vendor_name']}** ({vb['vendor_owner']}) — *WhatsApp:* `{vb['vendor_phone']}`")
                for itm in vb["items"]:
                    st.markdown(f"  - {itm['name']}: **{itm['qty']} × {itm['unit']}** @ {inr(itm['price'])} = **{inr(itm['qty']*itm['price'])}**")
                st.link_button(f"📲 Send Vegetable List to {vb['vendor_name']} ({vb['vendor_phone']})", vb["whatsapp_url"], use_container_width=True)
                st.markdown("---")
        if st.button("Close Order Dispatch Summary"):
            del st.session_state["last_order_placed"]
            st.rerun()

else:
    st.title("Your orders 📦")
    if not st.session_state.orders: st.info("No orders yet — your neighbourhood harvest is waiting.")
    for order in reversed(st.session_state.orders):
        st.markdown(f'<div class="order-box"><b>{order["id"]}</b><span style="float:right">{order["status"]}</span><br><span class="muted">{order["slot"]} · {order["payment"]}</span><br><b>{inr(order["total"])}</b></div>',unsafe_allow_html=True)
        if "vendor_breakdown" in order and order["vendor_breakdown"]:
            with st.expander(f"🥬 Vegetable List & Quantity Breakdown ({len(order['vendor_breakdown'])} Vendor{'s' if len(order['vendor_breakdown'])>1 else ''})"):
                for vb in order["vendor_breakdown"]:
                    st.markdown(f"**🏪 {vb['vendor_name']}** ({vb['vendor_owner']}) — 📱 `{vb['vendor_phone']}`")
                    for itm in vb["items"]:
                        st.write(f"  • {itm['name']}: {itm['qty']} × {itm['unit']} ({inr(itm['price'])}) = {inr(itm['qty']*itm['price'])}")
                    st.link_button(f"📲 Send Vegetable List on WhatsApp ({vb['vendor_phone']})", vb["whatsapp_url"], use_container_width=True)
                    st.markdown("---")
