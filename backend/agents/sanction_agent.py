import os
import sys
import logging
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)


class SanctionAgent:
    def __init__(self, output_dir: str = "generated_letters"):
        self.agent_name = "Sanction Agent"
        self.pdf_generator = PDFGenerator(output_dir=output_dir)

    def generate_sanction_letter(
        self,
        customer_name: str,
        loan_amount: Optional[float],
        tenure_months: Optional[int],
        interest_rate: Optional[float],
        emi: Optional[float],
        session_id: str
    ) -> Dict[str, Any]:
        logger.info("📄 Sanction Agent: Generating sanction letter")
        logger.info(f"  Customer: {customer_name}")
        
        if loan_amount is not None:
            loan_amount_str = f"Rs. {loan_amount:,.2f}"
        else:
            loan_amount_str = "N/A"
            
        if tenure_months is not None:
            tenure_str = f"{tenure_months} months"
        else:
            tenure_str = "N/A"
            
        if interest_rate is not None:
            interest_rate_str = f"{interest_rate}%"
        else:
            interest_rate_str = "N/A"
            
        if emi is not None:
            emi_str = f"Rs. {emi:,.2f}"
        else:
            emi_str = "N/A"
        
        logger.info(f"  Loan Amount: {loan_amount_str}")
        logger.info(f"  Tenure: {tenure_str}")
        logger.info(f"  Interest Rate: {interest_rate_str}")
        logger.info(f"  EMI: {emi_str}")
        
        if not all([customer_name, loan_amount, tenure_months, interest_rate, emi, session_id]):
            logger.error("❌ Missing required parameters for sanction letter")
            return {
                "success": False,
                "error": "Missing required parameters for sanction letter generation",
                "file_path": None
            }

        try:
            file_path = self.pdf_generator.generate_sanction_letter(
                customer_name=customer_name,
                loan_amount=loan_amount,
                tenure_months=tenure_months,
                interest_rate=interest_rate,
                emi=emi,
                session_id=session_id
            )
            
            logger.info(f"✅ Sanction letter generated: {file_path}")
            
            return {
                "success": True,
                "file_path": file_path,
                "message": f"Sanction letter generated successfully for {customer_name}",
                "details": {
                    "customer_name": customer_name,
                    "loan_amount": loan_amount,
                    "tenure_months": tenure_months,
                    "interest_rate": interest_rate,
                    "emi": emi
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate sanction letter: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to generate sanction letter: {str(e)}",
                "file_path": None
            }

    def get_letter_path(self, session_id: str) -> Optional[str]:
        return self.pdf_generator.get_download_path(session_id)

    def format_approval_message(
        self,
        customer_name: str,
        loan_amount: Optional[float],
        tenure_months: Optional[int],
        interest_rate: Optional[float],
        emi: Optional[float]
    ) -> str:
        loan_amount = loan_amount or 0
        tenure_months = tenure_months or 0
        interest_rate = interest_rate or 0
        emi = emi or 0
        total_payment = emi * tenure_months
        total_interest = total_payment - loan_amount
        
        message = f"""
Congratulations, {customer_name}!

Your Personal Loan has been APPROVED!

Loan Details:
- Loan Amount: Rs. {loan_amount:,.2f}
- Interest Rate: {interest_rate}% per annum
- Tenure: {tenure_months} months
- Monthly EMI: Rs. {emi:,.2f}
- Total Interest: Rs. {total_interest:,.2f}
- Total Payable: Rs. {total_payment:,.2f}

Your sanction letter has been generated and is ready for download.

Thank you for choosing Horizon Finance Limited!
"""
        return message.strip()

    def format_rejection_message(
        self,
        customer_name: str,
        reason: str
    ) -> str:
        message = f"""Dear {customer_name},

Thank you for your interest in Horizon Finance Limited. After careful review of your application, we are unable to approve your loan request at this time.

Reason: {reason}

We understand this may be disappointing. Here are some steps you can take:
- Review and improve your credit profile
- Consider applying for a lower loan amount that better matches your credit profile
- Contact our customer support team for personalized guidance

We appreciate your interest and hope to serve you in the future when your credit profile improves.

Best regards,
Horizon Finance Limited"""
        return message.strip()
