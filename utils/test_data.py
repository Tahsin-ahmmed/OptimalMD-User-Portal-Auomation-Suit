import os
import random
import string

from dotenv import load_dotenv
from faker import Faker

load_dotenv()

fake = Faker("en_US")

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
PRIME = "OptimalMD Prime"
PRIME_INDIVIDUAL = "OptimalMD Prime (Individual)"

GENDERS = ["Male", "Female"]

# Real addresses so street, city, state and ZIP always match.
# NJ, RI and WA are left out: the Impact plan is not available there.
US_ADDRESSES = [
    {"street": "233 S Wacker Dr", "city": "Chicago", "state": "Illinois", "zip": "60606"},
    {"street": "350 5th Ave", "city": "New York", "state": "New York", "zip": "10118"},
    {"street": "1 Dr Carlton B Goodlett Pl", "city": "San Francisco", "state": "California", "zip": "94102"},
    {"street": "100 Congress Ave", "city": "Austin", "state": "Texas", "zip": "78701"},
    {"street": "600 Brickell Ave", "city": "Miami", "state": "Florida", "zip": "33131"},
    {"street": "1 Federal St", "city": "Boston", "state": "Massachusetts", "zip": "02110"},
    {"street": "1700 Lincoln St", "city": "Denver", "state": "Colorado", "zip": "80203"},
    {"street": "191 Peachtree St NE", "city": "Atlanta", "state": "Georgia", "zip": "30303"},
]

US_AREA_CODES = ["212", "305", "312", "415", "512", "617", "702", "713", "813", "917"]

# Referral code (coupon) created by the admin on staging; replace it when the admin issues a new one.
REFERRAL_CODE = "OMD-7M2EJXOM"

# Stripe test cards: https://docs.stripe.com/testing
VALID_CARD = {"number": "4242424242424242", "expiry": "12/34", "cvc": "123"}


def _letters_only(generator) -> str:
    # The form rejects anything except A-Z (no apostrophes, hyphens or spaces).
    while True:
        value = generator()
        if value.isalpha():
            return value


def us_phone() -> str:
    return f"{random.choice(US_AREA_CODES)}{random.randint(200, 999)}{random.randint(0, 9999):04d}"


def adult_dob(min_age: int = 21, max_age: int = 65) -> str:
    dob = fake.date_of_birth(minimum_age=min_age, maximum_age=max_age)
    return dob.strftime("%m/%d/%Y")


def unique_email(first_name: str) -> str:
    # Gmail delivers "name+anything@gmail.com" to "name@gmail.com", so every
    # registration gets its own address that still lands in the QA inbox,
    # e.g. qa.optimalmd+emily472@gmail.com.
    local, domain = GMAIL_ADDRESS.split("@")
    return f"{local}+{first_name.lower()}{random.randint(100, 999)}@{domain}"


def new_member() -> dict:
    first_name = _letters_only(fake.first_name)
    return {
        "first_name": first_name,
        "last_name": _letters_only(fake.last_name),
        "email": unique_email(first_name),
        "phone": us_phone(),
        "dob": adult_dob(),
    }


# Relation choices in the "Select a relation" popup, with a sensible age for each.
DEPENDENT_AGES = {"Spouse": (25, 60), "Child": (5, 15), "Parent": (60, 80), "Other": (25, 60)}


def new_dependent(relation: str) -> dict:
    first_name = _letters_only(fake.first_name)
    min_age, max_age = DEPENDENT_AGES[relation]
    return {
        "relation": relation,
        "first_name": first_name,
        "last_name": _letters_only(fake.last_name),
        "gender": random.choice(GENDERS),
        "dob": adult_dob(min_age, max_age),
        # Dependents aged 18+ must have an email and phone (it gives them their own login).
        "email": unique_email(first_name),
        "phone": us_phone(),
        "adult": min_age >= 18,
    }


def new_password() -> str:
    """Meets every reset-page rule: 6+ chars, upper, lower, number, special (e.g. "Kqwbtz47!")."""
    lower = "".join(random.choices(string.ascii_lowercase, k=5))
    return f"{random.choice(string.ascii_uppercase)}{lower}{random.randint(10, 99)}!"


def new_profile_details() -> dict:
    return {"gender": random.choice(GENDERS), "address": random.choice(US_ADDRESSES)}
