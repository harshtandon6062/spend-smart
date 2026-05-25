"""
UPI Statement PDF → Categorized CSV Converter
===============================================
Parses PhonePe/UPI statement PDFs, extracts transactions,
categorizes them intelligently, and outputs analysis-ready CSV.

Supports: PhonePe, GPay, Paytm statement formats.
"""

import re
import csv
import sys
import warnings
import argparse
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber is required. Install with: pip install pdfplumber")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────

@dataclass
class Transaction:
    date: str = ""
    time: str = ""
    description: str = ""
    merchant: str = ""
    txn_type: str = ""        # DEBIT / CREDIT
    amount: float = 0.0
    txn_id: str = ""
    utr_no: str = ""
    paid_by: str = ""
    category: str = ""
    sub_category: str = ""
    is_excluded: bool = False
    exclusion_reason: str = ""
    txn_mode: str = ""        # P2P / P2M / SELF / REFUND
    confidence: str = "HIGH"


# ─────────────────────────────────────────────────────────────
# Category Engine
# ─────────────────────────────────────────────────────────────

# Priority-ordered: first match wins
CATEGORY_RULES = [
    # ── CREDITS (skip from spending) ──
    {
        "pattern": r"^(Received from|Refund from)",
        "category": "Credit",
        "sub": "Income/Refund",
        "exclude": True,
        "reason": "Credit transaction"
    },

    # ── FAMILY TRANSFERS ──
    {
        "pattern": r"Paid to\s+(Mom|Dad|Mother|Father|Sister|Brother|Son|Daughter|Bro|Sis|Family|Wife|Husband)\b",
        "category": "Family Transfer",
        "sub": "Parent/Sibling Transfer",
        "exclude": True,
        "reason": "Family transfer — not a spend"
    },

    # ── PASS-THROUGH / SELF TRANSFERS ──
    {
        "pattern": r"Paid to\s+(Self|My\s+Account|Airtel\s+No|Wallet|Paytm\s+Wallet|PhonePe\s+Wallet|Airtel\s+Payments|My\s+Bank|Savings|Post\s+Office|Paytm\s+Payments)\b",
        "category": "Self/Pass-Through Transfer",
        "sub": "Own Accounts / Wallets",
        "exclude": True,
        "reason": "Likely self/pass-through transfer"
    },

    # ── INVESTMENT / WEALTH ──
    {
        "pattern": r"\b(Zerodha|Groww|Upstox|Paytm\s+Money|NPS|PPF|Mutual\s+Fund|SIP|Securities|Brokerage|CoinDCX|WazirX|Nifty|Sensex|Indmoney|Angel\s+One)\b",
        "category": "Investment",
        "sub": "Stocks/Mutual Funds/SIP",
        "exclude": True,
        "reason": "Investment/Savings transfer"
    },

    # ── UTILITIES & RECHARGES ──
    {
        "pattern": r"\b(BESCOM|BWSSB|Electricity|Water\s+Bill|Gas\s+Bill|Indane|HP\s+Gas|Bharatgas|Airtel\s+Digital|Act\s+Fibernet|Hathway|JioFiber|Tata\s+Play|Dish\s+TV|Mobile\s+Recharge|Act\s+Corp|Broadband|Utility)\b",
        "category": "Utilities",
        "sub": "Bills & Recharges"
    },

    # ── CHARITY & DONATIONS ──
    {
        "pattern": r"\b(Charity|Donation|Donate|Temple|Church|Mosque|Trust|Care\s+Foundation|PM\s+Cares|Goonj|GiveIndia|Akshaya\s+Patra)\b",
        "category": "Charity/Donations",
        "sub": "Donations"
    },

    # ── TAXES & FINES ──
    {
        "pattern": r"\b(Challan|Fine|Tax|GST|RTO|Customs|Court|E-Challan|Income\s+Tax|Property\s+Tax|Municipal|Government|Govt|Khajane)\b",
        "category": "Taxes & Fines",
        "sub": "Government Fees & Fines"
    },

    # ── CASH / ATM ──
    {
        "pattern": r"\b(ATM|Cash\s+Withdrawal|Self\s+Withdrawal|Withdraw\s+Cash)\b",
        "category": "Cash",
        "sub": "ATM / Cash Withdrawal",
        "exclude": True,
        "reason": "Cash withdrawal"
    },

    # ── RENT & MAINTENANCE ──
    {
        "pattern": r"\b(Rent|PG\s+Hostel|Paying\s+Guest|Society|Maintenance|Security\s+Deposit|Flat\s+Rent|Room\s+Rent|House\s+Rent)\b",
        "category": "Rent/Business",
        "sub": "Housing/Maintenance",
        "exclude": True,
        "reason": "Rent/Housing Outlier"
    },

    # ── TRANSPORT: Bus / Transit ──
    {
        "pattern": r"(BMTC\s+BUS|BUS\s+KA|KA\d{2}[A-Z]{1,2}\d{3,4}|KSRTC|Chalo\s+Card|VRL|Redbus|Abhibus)",
        "category": "Transport",
        "sub": "Bus & Coach"
    },

    # ── TRANSPORT: Metro ──
    {
        "pattern": r"(Bangalore\s+Metro\s+Rail|BANGALORE\s+METRO|BMRCL|Metro\s+parking|Delhi\s+Metro|DMRC|Metro\s+Card)",
        "category": "Transport",
        "sub": "Metro"
    },

    # ── TRAVEL: Rail & Booking ──
    {
        "pattern": r"(IRCTC|UTS|Indian\s+Railways|Yatra|MakeMyTrip|Goibibo|Cleartrip|EaseMyTrip|Redbus|Bookings)",
        "category": "Travel",
        "sub": "Train/Flights"
    },

    # ── TRANSPORT: Ride Hailing / Cabs ──
    {
        "pattern": r"\b(Uber|Ola\s+Cabs|Ola|Rapido|Namma\s+Yatri|Mega\s+Cabs|Meru)\b",
        "category": "Transport",
        "sub": "Cab/Ride-Hailing"
    },

    # ── FOOD DELIVERY ──
    {
        "pattern": r"\b(Swiggy|Zomato|EatSure|Magicpin|Domino|Pizza\s+Hut|KFC)\b",
        "category": "Food",
        "sub": "Food Delivery"
    },
    {
        "pattern": r"Swiggy\s+(Ltd|Limited|Instamart)",
        "category": "Food",
        "sub": "Food Delivery / Groceries"
    },

    # ── SUBSCRIPTIONS ──
    {
        "pattern": r"(Microsoft\s+Regional|OpenAI\s+LLC|Netflix|Spotify|YouTube\s+Premium|Disney|Hotstar|Amazon\s+Prime|Google\s+Storage|Google\s+One|Apple\s+Bill|Apple\s+Services)",
        "category": "Subscriptions",
        "sub": "Digital Service"
    },
    {
        "pattern": r"Payment\s+to\s+Google\b",
        "category": "Subscriptions",
        "sub": "Google Service"
    },

    # ── TECH / CLOUD ──
    {
        "pattern": r"\b(AWS\s+India|AWS|GitHub|Heroku|Vercel|Netlify|Cloudflare|Hostinger|GoDaddy)\b",
        "category": "Tech",
        "sub": "Cloud & Dev Tools"
    },

    # ── INSURANCE ──
    {
        "pattern": r"(LICPGINEW|LIC\s+India|HDFC\s+Life|ICICI\s+Prudential|Max\s+Life|SBI\s+Life|Bajaj\s+Allianz|Insurance)",
        "category": "Insurance",
        "sub": "Insurance Premium"
    },

    # ── EDUCATION ──
    {
        "pattern": r"(University|School|College|Academy|Institu|www\.pes\.edu|PES-\d+|PES-3rd|Coursera|Udemy|EdX|Tuition)",
        "category": "Education",
        "sub": "Tuition & Fees"
    },

    # ── PERSONAL CARE ──
    {
        "pattern": r"(beauty\s+parlour|salon|barber|mens\s+beauty|grooming|spa|haircut|makeover)",
        "category": "Personal Care",
        "sub": "Grooming"
    },

    # ── MEDICAL / HEALTH ──
    {
        "pattern": r"(Apollo\s+Pharmacy|clinic|medicals|HEALTHCARE|pharmacy|hospital|dentist|doctor|practo|1mg|Medplus)",
        "category": "Health",
        "sub": "Medical"
    },

    # ── GROCERIES / PROVISIONS ──
    {
        "pattern": r"(PROVISION\s+STORE|Super\s+Market|Mataji|GREEN\s+MART|GREENMART|Reliance\s+Fresh|Big\s*Basket|Blinkit|Zepto|SML\s+AGENCY|Krishiv\s+Enterprise|Veg|Vegetable|Fruit|Organics|CHANDRAKALA\s+\d|condiments|mart\b|grocery)",
        "category": "Groceries",
        "sub": "Provisions"
    },

    # ── MILK / DAIRY ──
    {
        "pattern": r"(NANDINI\s+MILK|KAMADHENU|Milk\s+Parlour|Dairy|Milky)",
        "category": "Groceries",
        "sub": "Milk/Dairy"
    },

    # ── BAKERY ──
    {
        "pattern": r"(Honey\s+Cakes|bakery|cakes|bakehouse|sweet\s+stall|sweets)",
        "category": "Food",
        "sub": "Bakery"
    },

    # ── RESTAURANTS / EATERIES ──
    {
        "pattern": r"(HOTEL|BIRYANI|BIRIYANI|Burger\s+King|Pani\s+Puri|chats|CAFE|OOTA|Foodcourt|ROTIGHAR|JUICE\s+WORLD|WRAP|WAFFLES|biriyani|mess\b|COOL\s+POINT|canteen|restaurant|kitchen|dhaba|grill|eatery|pizza|shawarma)",
        "category": "Food",
        "sub": "Restaurant/Eatery"
    },

    # ── MEAT ──
    {
        "pattern": r"\b(MEAT|Mutton|Chicken|Fish|Fishland|Seafood|Licious|FreshToHome)\b",
        "category": "Food",
        "sub": "Meat Shop"
    },

    # ── SHOPPING ──
    {
        "pattern": r"(Amazon\s+India|Amazon\b|Flipkart|LENSKART|Rebel\s+Marketplace|BOUTIQUE|FANCY\s+STORE|Myntra|Ajio|Meesho|Nykaa|Tata\s+CLiQ|Decathlon|IKEA|ZARA|H&M|Lifestyle|Max\s+Fashion|Trends|Shopping)",
        "category": "Shopping",
        "sub": "Online/Retail"
    },

    # ── ENTERTAINMENT ──
    {
        "pattern": r"(BookMyShow|PVR|THEATRE|ROBIN\s+THEATRE|Cinema|Inox|Cinepolis|Netflix|Gaming)",
        "category": "Entertainment",
        "sub": "Movies/Events"
    },

    # ── LAUNDRY ──
    {
        "pattern": r"(DRY\s+Cleaners|laundry|dryclean)",
        "category": "Services",
        "sub": "Laundry"
    },

    # ── XEROX / PRINTING ──
    {
        "pattern": r"(XEROX|printing|SAGAR\s+XEROX|stationery|book\s+stall|xerox)",
        "category": "Education",
        "sub": "Printing/Stationery"
    },

    # ── TELECOM ──
    {
        "pattern": r"(Airtel|Jio|Vodafone|BSNL|Recharge)\b",
        "category": "Utilities",
        "sub": "Mobile Recharge"
    },

    # ── FUEL ──
    {
        "pattern": r"(SERVICE\s+STATION|petrol|fuel|HP\s+|BPCL|IOCL|Shell\s+Petrol|Petroleum)",
        "category": "Transport",
        "sub": "Fuel"
    },

    # ── PARKING ──
    {
        "pattern": r"[Pp]arking",
        "category": "Transport",
        "sub": "Parking"
    },

    # ── SERVICES ──
    {
        "pattern": r"\b(Technologies|Services|Solutions|Enterprise|Enterprises|Agency)\b",
        "category": "Services",
        "sub": "Business Services"
    },

    # ── NURSERY / FARM ──
    {
        "pattern": r"(Farm\s+And\s+Nursery|nursery|garden|plants)",
        "category": "Shopping",
        "sub": "Plants/Garden"
    },
]


def classify_txn_mode(txn: Transaction) -> str:
    """Determine if transaction is P2P, P2M, SELF, or REFUND."""
    desc = txn.description

    if "Refund from" in desc:
        return "REFUND"
    if "Received from" in desc:
        return "P2P_CREDIT"

    # Known merchant patterns
    merchant_keywords = [
        "BMTC", "METRO", "BMRCL", "IRCTC", "Swiggy", "Amazon", "Burger King",
        "Apollo", "LENSKART", "Microsoft", "OpenAI", "AWS", "LIC", "Khajane",
        "Magicpin", "EatSure", "Google", "Rebel Marketplace", "THEATRE",
        "Nandini", "Kamadhenu", "Healthcare", "clinic", "pharmacy",
        "Xerox", "Dry Cleaners", "Service Station", "Zomato", "BookMyShow",
        "Domino", "Pizza", "KFC", "Netflix", "Spotify", "Zara", "Decathlon",
        "Myntra", "Ajio", "Meesho", "Nykaa", "Uber", "Ola", "Rapido", "Namma Yatri"
    ]

    for kw in merchant_keywords:
        if kw.lower() in desc.lower():
            return "P2M"

    # If paying to a named individual (First Last pattern, no business suffix)
    merchant_name = re.sub(r"^(Paid to|Payment to)\s+", "", desc.split("DEBIT")[0].strip())
    # Business suffixes
    if re.search(r"(PVT|LTD|LLC|LLP|CORP|STORE|ENTERPRISE|PARLOUR|CAFE|MART|AGENCY|INDUSTRIES|SERVICES|TECHNOLOGIES|RESTAURANT|BAKERY|HOTEL)", merchant_name, re.I):
        return "P2M"

    # Short personal names → P2P
    words = merchant_name.split()
    if 1 <= len(words) <= 4 and not re.search(r"\d", merchant_name):
        return "P2P"

    return "UNKNOWN"


def parse_date_to_datetime(date_str: str) -> Optional[datetime]:
    """Parse YYYY-MM-DD string to datetime object."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def detect_pass_through_transfers(transactions: list[Transaction]) -> list[Transaction]:
    """
    Dynamically detect self/pass-through transfers by finding matching CREDIT-DEBIT pairs
    within a +/- 2 day window with similar or identical amounts.
    """
    n = len(transactions)
    matched_credits = set()
    matched_debits = set()

    for i in range(n):
        t1 = transactions[i]
        if t1.txn_type != "DEBIT" or t1.is_excluded:
            continue
        
        # Skip matching known merchant categories
        if t1.category in ["Subscriptions", "Insurance", "Education", "Travel", "Government", "Tech"]:
            continue
            
        dt1 = parse_date_to_datetime(t1.date)
        if not dt1:
            continue

        # Look for a corresponding CREDIT transaction within +/- 2 days
        for j in range(n):
            if i == j:
                continue
            t2 = transactions[j]
            if t2.txn_type != "CREDIT" or j in matched_credits:
                continue
                
            dt2 = parse_date_to_datetime(t2.date)
            if not dt2:
                continue
                
            days_diff = abs((dt1 - dt2).days)
            if days_diff <= 2:
                # Check if amounts match exactly or very closely (within 1% or Rs 50)
                amount_diff = abs(t1.amount - t2.amount)
                is_match = (t1.amount == t2.amount) or (amount_diff <= 50 and amount_diff / max(t1.amount, t2.amount) <= 0.02)
                
                if is_match:
                    # Found a match!
                    t1.category = "Self/Pass-Through Transfer"
                    t1.sub_category = "Dynamic Match"
                    t1.is_excluded = True
                    t1.exclusion_reason = f"Pass-through: matched CREDIT of ₹{t2.amount:.2f} on {t2.date} ({t2.merchant})"
                    t1.confidence = "HIGH"
                    
                    matched_credits.add(j)
                    matched_debits.add(i)
                    break
                    
    return transactions


def categorize_transaction(txn: Transaction) -> Transaction:
    """Apply category rules to a transaction."""
    desc = txn.description

    # First classify mode so heuristics/rules can use it
    txn.txn_mode = classify_txn_mode(txn)

    for rule in CATEGORY_RULES:
        if re.search(rule["pattern"], desc, re.IGNORECASE):
            txn.category = rule["category"]
            txn.sub_category = rule.get("sub", "")
            txn.is_excluded = rule.get("exclude", False)
            txn.exclusion_reason = rule.get("reason", "")
            txn.confidence = "HIGH"
            break

    # If no rule matched, apply heuristics
    if not txn.category:
        txn = _apply_heuristics(txn)

    # Override: large round-number P2P transfers are likely pass-through
    if (txn.txn_type == "DEBIT" and txn.txn_mode == "P2P"
            and txn.amount >= 5000 and txn.amount % 1000 == 0
            and txn.category not in ["Family Transfer", "Self/Pass-Through Transfer"]):
        txn.category = "Large P2P Transfer"
        txn.sub_category = "Possibly Pass-Through"
        txn.is_excluded = True
        txn.exclusion_reason = f"Large round P2P transfer (₹{txn.amount:,.0f})"
        txn.confidence = "MEDIUM"

    # Override: Very large debits (e.g., >= ₹15,000) to corporate entities or business services
    # are likely rent, college fees, or business expenses, and should be excluded from monthly spends.
    if (txn.txn_type == "DEBIT" and txn.amount >= 15000
            and txn.category not in ["Family Transfer", "Self/Pass-Through Transfer"]):
        txn.category = "Rent/Business"
        txn.sub_category = "Large Outlier"
        txn.is_excluded = True
        txn.exclusion_reason = f"Large transaction (₹{txn.amount:,.2f}) — likely rent or business expense"
        txn.confidence = "MEDIUM"

    return txn


def _apply_heuristics(txn: Transaction) -> Transaction:
    """Fallback categorization for unmatched transactions."""
    if txn.txn_type == "CREDIT":
        txn.category = "Credit"
        txn.sub_category = "Other Income"
        txn.is_excluded = True
        txn.exclusion_reason = "Credit transaction"
        return txn

    # For debits:
    if txn.txn_mode == "P2P":
        # Heuristic: Small P2P payments to individuals under ₹150 are typically local canteens, tea taps, chats
        if txn.amount <= 150:
            txn.category = "Food"
            txn.sub_category = "Snacks & Street Food (P2P Heuristic)"
            txn.confidence = "LOW"
        else:
            txn.category = "P2P Transfer"
            txn.sub_category = "Personal Transfer"
            txn.confidence = "LOW"
    else:
        # P2M or Unknown
        if txn.amount <= 150:
            txn.category = "Food"
            txn.sub_category = "Local Merchant (Heuristic)"
            txn.confidence = "LOW"
        elif txn.amount <= 1000:
            txn.category = "Miscellaneous"
            txn.sub_category = "Unclassified Spend"
            txn.confidence = "LOW"
        else:
            txn.category = "Miscellaneous"
            txn.sub_category = "Large Unclassified Spend"
            txn.confidence = "LOW"

    return txn


# ─────────────────────────────────────────────────────────────
# PDF Parser
# ─────────────────────────────────────────────────────────────

# Regex for the main transaction line
# e.g., "May 25, 2026 Paid to ABHIJITH NB1 75437 DEBIT ₹69"
TXN_LINE_RE = re.compile(
    r"^([A-Z][a-z]{2,3}\s+\d{1,2},\s+\d{4})\s+"     # Date: "May 25, 2026"
    r"((?:Paid to|Payment to|Received from|Refund from)\s+.*?)\s+"  # Description
    r"(DEBIT|CREDIT)\s+"                                # Type
    r"₹([\d,]+\.?\d*)\s*$"                              # Amount
)

# Time + Transaction ID line
TIME_TXN_RE = re.compile(
    r"^(\d{1,2}:\d{2}\s*[ap]m)\s+Transaction\s+ID\s+(\S+)"
)

# UTR line
UTR_RE = re.compile(r"^UTR\s+No\.\s+(\S+)")

# Paid by / Credited to line
PAIDBY_RE = re.compile(r"^(Paid by|Credited to)\s+(\S+)")

# Page footer
PAGE_RE = re.compile(r"^Page\s+\d+\s+of\s+\d+")
FOOTER_RE = re.compile(r"^(This is a|Disclaimer)")

# Header
HEADER_RE = re.compile(r"^(Date\s+Transaction|Transaction\s+Statement)")


def parse_date(date_str: str) -> str:
    """Normalize date string to YYYY-MM-DD."""
    # Handle "Sept" → "Sep"
    date_str = date_str.replace("Sept ", "Sep ")
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str


def parse_amount(amount_str: str) -> float:
    """Parse amount string like '22,420' or '24.53' to float."""
    return float(amount_str.replace(",", ""))


def extract_merchant_name(description: str) -> str:
    """Extract clean merchant/payee name from description."""
    # Remove prefix
    name = re.sub(r"^(Paid to|Payment to|Received from|Refund from)\s+", "", description)
    return name.strip()


def parse_pdf(pdf_path: str) -> list[Transaction]:
    """Parse a UPI statement PDF and return list of Transaction objects."""
    pdf = pdfplumber.open(pdf_path)
    transactions = []
    
    all_lines = []
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            for line in text.split("\n"):
                line = line.strip()
                if line and not PAGE_RE.match(line) and not FOOTER_RE.match(line) and not HEADER_RE.match(line):
                    all_lines.append(line)

    i = 0
    while i < len(all_lines):
        line = all_lines[i]
        match = TXN_LINE_RE.match(line)
        
        if match:
            txn = Transaction()
            txn.date = parse_date(match.group(1))
            txn.description = match.group(2).strip()
            txn.merchant = extract_merchant_name(txn.description)
            txn.txn_type = match.group(3)
            txn.amount = parse_amount(match.group(4))

            # Look ahead for time/txn_id, UTR, paid_by
            for j in range(1, 4):
                if i + j < len(all_lines):
                    next_line = all_lines[i + j]
                    
                    time_match = TIME_TXN_RE.match(next_line)
                    if time_match:
                        txn.time = time_match.group(1)
                        txn.txn_id = time_match.group(2)
                        continue
                    
                    utr_match = UTR_RE.match(next_line)
                    if utr_match:
                        txn.utr_no = utr_match.group(1)
                        continue
                    
                    paid_match = PAIDBY_RE.match(next_line)
                    if paid_match:
                        txn.paid_by = paid_match.group(2)
                        continue

            # Categorize
            txn = categorize_transaction(txn)
            transactions.append(txn)

        i += 1

    pdf.close()

    # Run dynamic pass-through detection
    transactions = detect_pass_through_transfers(transactions)

    return transactions


# ─────────────────────────────────────────────────────────────
# CSV Writer
# ─────────────────────────────────────────────────────────────

CSV_HEADERS = [
    "Date", "Time", "Merchant", "Amount", "Type",
    "Category", "SubCategory", "TxnMode",
    "TransactionID", "UTR", "PaidBy",
    "Excluded", "ExclusionReason", "Confidence",
    "OriginalDescription"
]


def write_csv(transactions: list[Transaction], output_path: str):
    """Write transactions to CSV."""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        for txn in transactions:
            writer.writerow([
                txn.date, txn.time, txn.merchant, f"{txn.amount:.2f}",
                txn.txn_type, txn.category, txn.sub_category, txn.txn_mode,
                txn.txn_id, txn.utr_no, txn.paid_by,
                txn.is_excluded, txn.exclusion_reason, txn.confidence,
                txn.description
            ])


def write_spend_csv(transactions: list[Transaction], output_path: str):
    """Write ONLY spendable (non-excluded DEBIT) transactions in hackathon format."""
    headers = ["Date", "Merchant", "Amount", "Category"]
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for txn in transactions:
            if txn.txn_type == "DEBIT" and not txn.is_excluded:
                writer.writerow([txn.date, txn.merchant, f"{txn.amount:.2f}", txn.category])


# ─────────────────────────────────────────────────────────────
# Summary / Analytics
# ─────────────────────────────────────────────────────────────

def print_summary(transactions: list[Transaction]):
    """Print a summary of parsed transactions."""
    total = len(transactions)
    debits = [t for t in transactions if t.txn_type == "DEBIT"]
    credits = [t for t in transactions if t.txn_type == "CREDIT"]
    excluded = [t for t in transactions if t.is_excluded]
    spendable = [t for t in debits if not t.is_excluded]

    print("\n" + "=" * 60)
    print("  UPI STATEMENT ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"  Total transactions parsed   : {total}")
    print(f"  Debits                      : {len(debits)}")
    print(f"  Credits (skipped)           : {len(credits)}")
    print(f"  Excluded (transfers/rent)   : {len(excluded)}")
    print(f"  Actual spends               : {len(spendable)}")
    print(f"  Total debit amount          : ₹{sum(t.amount for t in debits):,.2f}")
    print(f"  Total credit amount         : ₹{sum(t.amount for t in credits):,.2f}")
    print(f"  Actual spend amount         : ₹{sum(t.amount for t in spendable):,.2f}")

    # Category breakdown
    print("\n" + "-" * 60)
    print("  CATEGORY BREAKDOWN (Spendable Only)")
    print("-" * 60)
    cat_totals: dict[str, float] = {}
    cat_counts: dict[str, int] = {}
    for t in spendable:
        cat_totals[t.category] = cat_totals.get(t.category, 0) + t.amount
        cat_counts[t.category] = cat_counts.get(t.category, 0) + 1

    for cat, total_amt in sorted(cat_totals.items(), key=lambda x: -x[1]):
        pct = (total_amt / sum(t.amount for t in spendable)) * 100 if spendable else 0
        bar = "█" * int(pct / 2)
        print(f"  {cat:<25} ₹{total_amt:>10,.2f}  ({cat_counts[cat]:>3}x)  {pct:5.1f}% {bar}")

    # Low confidence items
    low_conf = [t for t in spendable if t.confidence == "LOW"]
    if low_conf:
        print(f"\n  ⚠ {len(low_conf)} transactions with LOW confidence categorization")
        for t in low_conf[:5]:
            print(f"    → {t.date} | {t.merchant:<35} | ₹{t.amount:>8,.2f} | {t.category}")
        if len(low_conf) > 5:
            print(f"    ... and {len(low_conf) - 5} more")

    print("=" * 60 + "\n")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert UPI statement PDF to categorized CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python upi_converter.py statement.pdf
  python upi_converter.py statement.pdf -o my_output.csv
  python upi_converter.py statement.pdf --spend-only
        """
    )
    parser.add_argument("pdf_path", help="Path to UPI statement PDF")
    parser.add_argument("-o", "--output", help="Output CSV path (default: auto-generated)")
    parser.add_argument("--spend-only", action="store_true",
                        help="Output only spendable transactions in hackathon format (Date,Merchant,Amount,Category)")
    parser.add_argument("--no-summary", action="store_true", help="Skip printing summary")

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)

    print(f"📄 Parsing: {pdf_path.name}")
    transactions = parse_pdf(str(pdf_path))
    print(f"✅ Extracted {len(transactions)} transactions")

    # Determine output paths
    stem = pdf_path.stem
    if args.output:
        full_csv = args.output
        spend_csv = str(Path(args.output).parent / f"{Path(args.output).stem}_spend_only.csv")
    else:
        full_csv = str(pdf_path.parent / f"{stem}_full.csv")
        spend_csv = str(pdf_path.parent / f"{stem}_spend_only.csv")

    # Write outputs
    write_csv(transactions, full_csv)
    print(f"📊 Full CSV written to: {full_csv}")

    if not args.spend_only:
        write_spend_csv(transactions, spend_csv)
        print(f"💰 Spend-only CSV written to: {spend_csv}")
    else:
        write_spend_csv(transactions, full_csv if args.output else spend_csv)

    if not args.no_summary:
        print_summary(transactions)


if __name__ == "__main__":
    main()
