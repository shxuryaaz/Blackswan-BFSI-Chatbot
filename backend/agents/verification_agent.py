import random
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class VerificationAgent:
    MOCK_CUSTOMER_DATABASE = {
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

    def __init__(self):
        self.agent_name = "Verification Agent"

    def verify_customer(self, phone_number: Optional[str], customer_name: Optional[str] = None) -> Dict[str, Any]:
        logger.info("🔍 Verification Agent: Starting KYC verification")
        logger.info(f"  Phone: {phone_number}, Name: {customer_name}")
        
        if not phone_number:
            phone_number = "0000000000"
        
        # Demo mode: Special phone number for demo purposes
        DEMO_PHONE_NUMBER = "7982130057"
        if phone_number == DEMO_PHONE_NUMBER:
            logger.info("🎯 DEMO MODE: High credit score for demo phone number")
            credit_score = 800
            pre_approved_limit = 1000000.0  # High limit to ensure approval
            logger.info(f"  Credit Score: {credit_score}, Pre-approved Limit: Rs. {pre_approved_limit:,.2f}")
            return {
                "success": True,
                "phone_verified": True,
                "address_verified": True,
                "credit_score": credit_score,
                "pre_approved_limit": pre_approved_limit,
                "customer_name": customer_name or "Demo Customer",
                "message": "Demo customer verified successfully. High credit profile for demonstration."
            }
        
        if phone_number in self.MOCK_CUSTOMER_DATABASE:
            customer = self.MOCK_CUSTOMER_DATABASE[phone_number]
            logger.info(f"✅ Existing customer found: {customer['name']}")
            logger.info(f"  Credit Score: {customer['credit_score']}, Pre-approved Limit: Rs. {customer['pre_approved_limit']:,.2f}")
            return {
                "success": True,
                "phone_verified": customer["phone_verified"],
                "address_verified": customer["address_verified"],
                "credit_score": customer["credit_score"],
                "pre_approved_limit": customer["pre_approved_limit"],
                "customer_name": customer["name"],
                "message": "KYC verification successful. Customer found in our records."
            }
        
        credit_score = random.randint(0, 900)  # Credit score out of 900 as per requirements
        pre_approved_limit = self._calculate_pre_approved_limit(credit_score)
        
        logger.info(f"🆕 New customer profile created")
        logger.info(f"  Credit Score: {credit_score}, Pre-approved Limit: Rs. {pre_approved_limit:,.2f}")
        
        return {
            "success": True,
            "phone_verified": True,
            "address_verified": True,
            "credit_score": credit_score,
            "pre_approved_limit": pre_approved_limit,
            "customer_name": customer_name or "Valued Customer",
            "message": "New customer verified successfully. Profile created."
        }

    def _calculate_pre_approved_limit(self, credit_score: int) -> float:
        if credit_score >= 800:
            return 500000.0
        elif credit_score >= 750:
            return 400000.0
        elif credit_score >= 700:
            return 300000.0
        elif credit_score >= 650:
            return 200000.0
        else:
            return 100000.0

    def get_customer_profile(self, phone_number: str) -> Optional[Dict[str, Any]]:
        if phone_number in self.MOCK_CUSTOMER_DATABASE:
            return self.MOCK_CUSTOMER_DATABASE[phone_number].copy()
        return None

    def is_existing_customer(self, phone_number: str) -> bool:
        return phone_number in self.MOCK_CUSTOMER_DATABASE
