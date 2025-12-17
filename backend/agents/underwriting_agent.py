import os
import sys
import logging
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.loan_calculator import LoanCalculator

logger = logging.getLogger(__name__)


class UnderwritingAgent:
    MIN_CREDIT_SCORE = 700
    MAX_DTI_RATIO = 50.0
    MAX_MULTIPLIER = 2.0

    def __init__(self):
        self.agent_name = "Underwriting Agent"
        self.calculator = LoanCalculator()

    def evaluate(
        self,
        loan_amount: Optional[float],
        tenure_months: Optional[int],
        interest_rate: Optional[float],
        credit_score: Optional[int],
        pre_approved_limit: Optional[float],
        salary: Optional[float] = None
    ) -> Dict[str, Any]:
        logger.info("💰 Underwriting Agent: Evaluating loan application")
        loan_amount_str = f"Rs. {loan_amount:,.2f}" if loan_amount else "N/A"
        tenure_str = f"{tenure_months} months" if tenure_months else "N/A"
        interest_rate_str = f"{interest_rate}%" if interest_rate else "N/A"
        credit_score_str = str(credit_score) if credit_score else "N/A"
        pre_approved_str = f"Rs. {pre_approved_limit:,.2f}" if pre_approved_limit else "N/A"
        salary_str = f"Rs. {salary:,.2f}" if salary else "N/A"
        
        logger.info(f"  Loan Amount: {loan_amount_str}")
        logger.info(f"  Tenure: {tenure_str}")
        logger.info(f"  Interest Rate: {interest_rate_str}")
        logger.info(f"  Credit Score: {credit_score_str}")
        logger.info(f"  Pre-approved Limit: {pre_approved_str}")
        logger.info(f"  Salary: {salary_str}")
        
        if not loan_amount or not tenure_months or not interest_rate:
            logger.warning("❌ Missing loan details")
            return {
                "decision": "pending",
                "reason": "Missing loan details",
                "emi": None,
                "requires_salary": False
            }
        
        if not credit_score or not pre_approved_limit:
            logger.warning("❌ Missing credit information")
            return {
                "decision": "pending",
                "reason": "Missing credit information",
                "emi": None,
                "requires_salary": False
            }
        
        if credit_score < self.MIN_CREDIT_SCORE:
            logger.warning(f"❌ Credit score {credit_score} below minimum {self.MIN_CREDIT_SCORE}")
            return {
                "decision": "rejected",
                "reason": f"Credit score ({credit_score}) is below the minimum required score of {self.MIN_CREDIT_SCORE}.",
                "emi": None,
                "requires_salary": False
            }

        emi = LoanCalculator.calculate_emi(loan_amount, interest_rate, tenure_months)
        logger.info(f"  Calculated EMI: Rs. {emi:,.2f}")

        if loan_amount <= pre_approved_limit:
            logger.info(f"✅ APPROVED: Loan within pre-approved limit")
            return {
                "decision": "approved",
                "reason": f"Loan amount (Rs. {loan_amount:,.2f}) is within your pre-approved limit of Rs. {pre_approved_limit:,.2f}.",
                "emi": emi,
                "requires_salary": False
            }

        max_allowed = pre_approved_limit * self.MAX_MULTIPLIER
        logger.info(f"  Max allowed (2x limit): Rs. {max_allowed:,.2f}")

        if loan_amount > max_allowed:
            logger.warning(f"❌ REJECTED: Loan exceeds max allowed limit")
            return {
                "decision": "rejected",
                "reason": f"Loan amount (Rs. {loan_amount:,.2f}) exceeds the maximum allowed limit of Rs. {max_allowed:,.2f} (2x your pre-approved limit).",
                "emi": None,
                "requires_salary": False
            }

        if salary is None:
            required_salary = self._calculate_min_required_salary(emi)
            logger.info(f"⏳ PENDING: Salary verification required (min: Rs. {required_salary:,.2f})")
            return {
                "decision": "pending",
                "reason": f"Loan amount exceeds pre-approved limit. Salary verification required for amounts between Rs. {pre_approved_limit:,.2f} and Rs. {max_allowed:,.2f}.",
                "emi": emi,
                "requires_salary": True,
                "required_min_salary": required_salary
            }

        dti_ratio = LoanCalculator.calculate_dti_ratio(emi, salary)
        logger.info(f"  DTI Ratio: {dti_ratio:.1f}% (max: {self.MAX_DTI_RATIO}%)")

        if dti_ratio <= self.MAX_DTI_RATIO:
            logger.info(f"✅ APPROVED: DTI ratio acceptable")
            return {
                "decision": "approved",
                "reason": f"Loan approved based on salary verification. Your EMI of Rs. {emi:,.2f} is {dti_ratio:.1f}% of your monthly salary, which is within the acceptable limit of {self.MAX_DTI_RATIO}%.",
                "emi": emi,
                "requires_salary": False,
                "dti_ratio": dti_ratio
            }
        else:
            logger.warning(f"❌ REJECTED: DTI ratio too high")
            return {
                "decision": "rejected",
                "reason": f"EMI of Rs. {emi:,.2f} represents {dti_ratio:.1f}% of your monthly salary, exceeding our maximum limit of {self.MAX_DTI_RATIO}%.",
                "emi": emi,
                "requires_salary": False,
                "dti_ratio": dti_ratio,
                "suggestion": f"Consider a lower loan amount or longer tenure to reduce EMI."
            }

    def _calculate_min_required_salary(self, emi: float) -> float:
        return round(emi / (self.MAX_DTI_RATIO / 100), 2)

    def get_max_eligible_loan(
        self,
        monthly_salary: float,
        tenure_months: int,
        interest_rate: float
    ) -> float:
        max_emi = monthly_salary * (self.MAX_DTI_RATIO / 100)
        monthly_rate = interest_rate / (12 * 100)
        
        if monthly_rate <= 0:
            return max_emi * tenure_months
        
        max_principal = max_emi * (((1 + monthly_rate) ** tenure_months) - 1) / \
                       (monthly_rate * ((1 + monthly_rate) ** tenure_months))
        
        return round(max_principal, 2)

    def get_decision_summary(self, result: Dict[str, Any]) -> str:
        decision = result.get("decision", "unknown")
        reason = result.get("reason", "")
        
        if decision == "approved":
            return f"APPROVED: {reason}"
        elif decision == "rejected":
            return f"REJECTED: {reason}"
        elif decision == "pending":
            return f"PENDING: {reason}"
        else:
            return f"UNKNOWN: {reason}"
