import random
from typing import Dict, Any, Optional


MOCK_CUSTOMERS = {
    "9876543210": {
        "name": "Rahul Sharma",
        "address_verified": True,
        "phone_verified": True,
        "credit_score": 750,
        "pre_approved_limit": 300000
    },
    "9876543211": {
        "name": "Priya Patel",
        "address_verified": True,
        "phone_verified": True,
        "credit_score": 680,
        "pre_approved_limit": 200000
    },
    "9876543212": {
        "name": "Amit Kumar",
        "address_verified": True,
        "phone_verified": True,
        "credit_score": 820,
        "pre_approved_limit": 500000
    },
    "9876543213": {
        "name": "Sneha Gupta",
        "address_verified": True,
        "phone_verified": True,
        "credit_score": 720,
        "pre_approved_limit": 350000
    },
    "9876543214": {
        "name": "Vikram Singh",
        "address_verified": True,
        "phone_verified": True,
        "credit_score": 650,
        "pre_approved_limit": 150000
    }
}


def get_customer(phone_number: str) -> Optional[Dict[str, Any]]:
    if phone_number in MOCK_CUSTOMERS:
        return MOCK_CUSTOMERS[phone_number].copy()
    return None


def generate_new_customer_profile(customer_name: str) -> Dict[str, Any]:
    credit_score = random.randint(650, 850)
    
    if credit_score >= 800:
        pre_approved_limit = 500000.0
    elif credit_score >= 750:
        pre_approved_limit = 400000.0
    elif credit_score >= 700:
        pre_approved_limit = 300000.0
    elif credit_score >= 650:
        pre_approved_limit = 200000.0
    else:
        pre_approved_limit = 100000.0
    
    return {
        "name": customer_name,
        "address_verified": True,
        "phone_verified": True,
        "credit_score": credit_score,
        "pre_approved_limit": pre_approved_limit
    }


def is_existing_customer(phone_number: str) -> bool:
    return phone_number in MOCK_CUSTOMERS
