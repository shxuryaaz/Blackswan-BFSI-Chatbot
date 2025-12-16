import os
import sys
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.loan_calculator import LoanCalculator


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
        if not loan_amount or not tenure_months or not interest_rate:
            return {
                "decision": "pending",
                "reason": "Missing loan details",
                "emi": None,
                "requires_salary": False
            }
        
        if not credit_score or not pre_approved_limit:
            return {
                "decision": "pending",
                "reason": "Missing credit information",
                "emi": None,
                "requires_salary": False
            }
        
        if credit_score < self.MIN_CREDIT_SCORE:
            return {
                "decision": "rejected",
                "reason": f"Credit score ({credit_score}) is below the minimum required score of {self.MIN_CREDIT_SCORE}.",
                "emi": None,
                "requires_salary": False
            }

        emi = LoanCalculator.calculate_emi(loan_amount, interest_rate, tenure_months)

        if loan_amount <= pre_approved_limit:
            return {
                "decision": "approved",
                "reason": f"Loan amount (Rs. {loan_amount:,.2f}) is within your pre-approved limit of Rs. {pre_approved_limit:,.2f}.",
                "emi": emi,
                "requires_salary": False
            }

        max_allowed = pre_approved_limit * self.MAX_MULTIPLIER

        if loan_amount > max_allowed:
            return {
                "decision": "rejected",
                "reason": f"Loan amount (Rs. {loan_amount:,.2f}) exceeds the maximum allowed limit of Rs. {max_allowed:,.2f} (2x your pre-approved limit).",
                "emi": None,
                "requires_salary": False
            }

        if salary is None:
            return {
                "decision": "pending",
                "reason": f"Loan amount exceeds pre-approved limit. Salary verification required for amounts between Rs. {pre_approved_limit:,.2f} and Rs. {max_allowed:,.2f}.",
                "emi": emi,
                "requires_salary": True,
                "required_min_salary": self._calculate_min_required_salary(emi)
            }

        dti_ratio = LoanCalculator.calculate_dti_ratio(emi, salary)

        if dti_ratio <= self.MAX_DTI_RATIO:
            return {
                "decision": "approved",
                "reason": f"Loan approved based on salary verification. Your EMI of Rs. {emi:,.2f} is {dti_ratio:.1f}% of your monthly salary, which is within the acceptable limit of {self.MAX_DTI_RATIO}%.",
                "emi": emi,
                "requires_salary": False,
                "dti_ratio": dti_ratio
            }
        else:
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
