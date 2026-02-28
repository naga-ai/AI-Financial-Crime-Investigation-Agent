"""Generate realistic Wealthsimple client profiles.

Creates a diverse mix of Canadian clients across provinces, income levels,
occupations, and account types that mirror Wealthsimple's actual user base.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta

from src.data.models import (
    Account,
    AccountType,
    ClientProfile,
    KYCStatus,
    RiskProfile,
)

FIRST_NAMES = [
    "Emma", "Liam", "Olivia", "Noah", "Ava", "William", "Sophia", "James",
    "Isabella", "Oliver", "Mia", "Benjamin", "Charlotte", "Elijah", "Amelia",
    "Lucas", "Harper", "Mason", "Evelyn", "Logan", "Abigail", "Alexander",
    "Emily", "Ethan", "Elizabeth", "Jacob", "Sofia", "Michael", "Avery",
    "Daniel", "Ella", "Henry", "Madison", "Jackson", "Scarlett", "Sebastian",
    "Victoria", "Aiden", "Aria", "Matthew", "Grace", "Samuel", "Chloe",
    "David", "Penelope", "Joseph", "Riley", "Carter", "Layla", "Owen",
    "Wei", "Priya", "Mohammed", "Yuki", "Raj", "Chen", "Fatima", "Jun",
    "Aisha", "Dmitri", "Mei", "Arjun", "Sakura", "Omar", "Ananya",
    "Hiroshi", "Zara", "Vikram", "Noor", "Kenji",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Patel", "Singh", "Wang", "Li", "Zhang", "Chen",
    "Kim", "Nakamura", "Tanaka", "Sharma", "Kumar", "Ali", "Hassan",
    "Tremblay", "Roy", "Gagnon", "Côté", "Bouchard", "Gauthier", "Morin",
]

OCCUPATIONS = [
    "Software Engineer", "Teacher", "Nurse", "Accountant", "Lawyer",
    "Marketing Manager", "Data Analyst", "Graphic Designer", "Doctor",
    "Financial Advisor", "Sales Representative", "Project Manager",
    "Electrician", "Pharmacist", "Chef", "Real Estate Agent",
    "Mechanical Engineer", "Dentist", "Student", "Retired",
    "Small Business Owner", "Consultant", "Architect", "Researcher",
    "Truck Driver", "Social Worker", "Journalist", "Freelancer",
    "Restaurant Owner", "Construction Worker",
]

INCOME_RANGES = [
    "0-25k", "25k-50k", "50k-75k", "75k-100k", "100k-150k",
    "150k-200k", "200k-300k", "300k+",
]

INCOME_WEIGHTS = [0.05, 0.15, 0.25, 0.25, 0.15, 0.08, 0.05, 0.02]

PROVINCE_WEIGHTS = {
    "ON": 0.40, "BC": 0.18, "AB": 0.12, "QC": 0.15, "MB": 0.03,
    "SK": 0.02, "NS": 0.03, "NB": 0.02, "NL": 0.01, "PE": 0.005,
    "NT": 0.002, "YT": 0.002, "NU": 0.001,
}

ACCOUNT_TYPE_COMBOS: list[list[AccountType]] = [
    [AccountType.TFSA],
    [AccountType.RRSP],
    [AccountType.TFSA, AccountType.RRSP],
    [AccountType.TFSA, AccountType.PERSONAL],
    [AccountType.TFSA, AccountType.RRSP, AccountType.PERSONAL],
    [AccountType.TFSA, AccountType.CRYPTO],
    [AccountType.PERSONAL, AccountType.CRYPTO],
    [AccountType.TFSA, AccountType.RRSP, AccountType.CRYPTO],
    [AccountType.TFSA, AccountType.RRSP, AccountType.PERSONAL, AccountType.CRYPTO],
    [AccountType.CRYPTO],
    [AccountType.FHSA, AccountType.TFSA],
    [AccountType.RESP, AccountType.TFSA, AccountType.RRSP],
]

COMBO_WEIGHTS = [0.08, 0.06, 0.15, 0.10, 0.15, 0.10, 0.08, 0.12, 0.08, 0.04, 0.02, 0.02]


def _random_date(start_year: int, end_year: int) -> datetime:
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def _generate_balance(account_type: AccountType, income_range: str) -> float:
    """Generate a plausible account balance based on account type and income."""
    income_idx = INCOME_RANGES.index(income_range) if income_range in INCOME_RANGES else 3
    base_multiplier = 1 + income_idx * 0.5

    ranges = {
        AccountType.TFSA: (500, 80_000),
        AccountType.RRSP: (1_000, 200_000),
        AccountType.SPOUSAL_RRSP: (1_000, 100_000),
        AccountType.FHSA: (500, 32_000),
        AccountType.RESP: (500, 40_000),
        AccountType.PERSONAL: (100, 150_000),
        AccountType.CRYPTO: (50, 50_000),
    }
    low, high = ranges.get(account_type, (100, 50_000))
    raw = random.uniform(low, high) * base_multiplier * random.uniform(0.1, 1.0)
    return round(min(raw, high * 1.5), 2)


def generate_clients(
    n: int = 500,
    suspicious_ratio: float = 0.08,
    seed: int = 42,
) -> list[ClientProfile]:
    """Generate n realistic Wealthsimple client profiles.

    Args:
        n: Number of clients to generate.
        suspicious_ratio: Fraction of clients that will later have suspicious activity.
        seed: Random seed for reproducibility.
    """
    random.seed(seed)
    provinces = list(PROVINCE_WEIGHTS.keys())
    province_wts = list(PROVINCE_WEIGHTS.values())
    clients: list[ClientProfile] = []
    suspicious_count = int(n * suspicious_ratio)

    for i in range(n):
        client_id = f"WS-{uuid.uuid4().hex[:8].upper()}"
        province = random.choices(provinces, weights=province_wts, k=1)[0]
        income_range = random.choices(INCOME_RANGES, weights=INCOME_WEIGHTS, k=1)[0]
        dob = _random_date(1955, 2005)
        account_open = _random_date(2014, 2025)
        combo = random.choices(ACCOUNT_TYPE_COMBOS, weights=COMBO_WEIGHTS, k=1)[0]

        accounts = []
        for acct_type in combo:
            accounts.append(Account(
                account_id=f"A-{uuid.uuid4().hex[:8].upper()}",
                account_type=acct_type,
                opened_at=account_open + timedelta(days=random.randint(0, 365)),
                balance_cad=_generate_balance(acct_type, income_range),
            ))

        is_suspicious = i < suspicious_count
        if is_suspicious:
            risk = random.choices(
                [RiskProfile.LOW, RiskProfile.MEDIUM, RiskProfile.HIGH],
                weights=[0.3, 0.4, 0.3],
                k=1,
            )[0]
        else:
            risk = random.choices(
                [RiskProfile.LOW, RiskProfile.MEDIUM, RiskProfile.HIGH],
                weights=[0.7, 0.25, 0.05],
                k=1,
            )[0]

        kyc = KYCStatus.VERIFIED
        if is_suspicious and random.random() < 0.15:
            kyc = KYCStatus.FLAGGED

        client = ClientProfile(
            client_id=client_id,
            first_name=random.choice(FIRST_NAMES),
            last_name=random.choice(LAST_NAMES),
            email=f"{client_id.lower()}@email.com",
            date_of_birth=dob,
            occupation=random.choice(OCCUPATIONS),
            income_range=income_range,
            accounts=accounts,
            risk_profile=risk,
            kyc_status=kyc,
            province=province,
            country="CA",
            account_open_date=account_open,
            is_pep=is_suspicious and random.random() < 0.1,
        )
        clients.append(client)

    random.shuffle(clients)
    return clients
