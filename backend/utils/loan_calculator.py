from typing import Dict, Any


class LoanCalculator:
    @staticmethod
    def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
        if principal <= 0 or annual_rate <= 0 or tenure_months <= 0:
            return 0.0
        
        monthly_rate = annual_rate / (12 * 100)
        
        emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure_months) / \
              (((1 + monthly_rate) ** tenure_months) - 1)
        
        return round(emi, 2)

    @staticmethod
    def calculate_total_interest(principal: float, emi: float, tenure_months: int) -> float:
        if emi <= 0 or tenure_months <= 0:
            return 0.0
        
        total_payment = emi * tenure_months
        total_interest = total_payment - principal
        return round(total_interest, 2)

    @staticmethod
    def calculate_total_payment(emi: float, tenure_months: int) -> float:
        return round(emi * tenure_months, 2)

    @staticmethod
    def calculate_dti_ratio(emi: float, monthly_salary: float) -> float:
        if monthly_salary <= 0:
            return 100.0
        
        return round((emi / monthly_salary) * 100, 2)

    @staticmethod
    def is_emi_affordable(emi: float, monthly_salary: float, max_dti_percent: float = 50.0) -> bool:
        dti = LoanCalculator.calculate_dti_ratio(emi, monthly_salary)
        return dti <= max_dti_percent

    @staticmethod
    def get_loan_summary(
        principal: float,
        annual_rate: float,
        tenure_months: int,
        monthly_salary: float = None
    ) -> Dict[str, Any]:
        emi = LoanCalculator.calculate_emi(principal, annual_rate, tenure_months)
        total_interest = LoanCalculator.calculate_total_interest(principal, emi, tenure_months)
        total_payment = LoanCalculator.calculate_total_payment(emi, tenure_months)
        
        summary = {
            "principal": principal,
            "annual_rate": annual_rate,
            "tenure_months": tenure_months,
            "emi": emi,
            "total_interest": total_interest,
            "total_payment": total_payment
        }
        
        if monthly_salary:
            dti = LoanCalculator.calculate_dti_ratio(emi, monthly_salary)
            summary["dti_ratio"] = dti
            summary["is_affordable"] = dti <= 50.0
        
        return summary

    @staticmethod
    def suggest_interest_rate(credit_score: int) -> float:
        if credit_score >= 800:
            return 10.5
        elif credit_score >= 750:
            return 11.0
        elif credit_score >= 700:
            return 12.0
        elif credit_score >= 650:
            return 14.0
        else:
            return 16.0

    @staticmethod
    def format_currency(amount: float) -> str:
        if amount >= 10000000:
            return f"Rs. {amount/10000000:.2f} Cr"
        elif amount >= 100000:
            return f"Rs. {amount/100000:.2f} L"
        else:
            return f"Rs. {amount:,.2f}"
