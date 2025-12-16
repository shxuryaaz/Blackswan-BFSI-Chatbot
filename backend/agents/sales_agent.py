import os
import sys
import json
from typing import Dict, Any, Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")


class SalesAgent:
    DEFAULT_INTEREST_RATE = 11.5
    DEFAULT_TENURE_MONTHS = 36
    
    TENURE_OPTIONS = [12, 24, 36, 48, 60]
    
    def __init__(self):
        self.agent_name = "Sales Agent"
        self.client = None
        if OPENAI_API_KEY:
            self.client = OpenAI(api_key=OPENAI_API_KEY)

    def extract_loan_requirements(
        self,
        conversation_history: List[Dict[str, str]],
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        system_prompt = """You are a professional loan sales executive at Horizon Finance Limited, an Indian NBFC.
Your job is to extract loan requirements from the customer's messages.

IMPORTANT: You must respond with ONLY valid JSON, no other text.

Extract the following information if mentioned:
- loan_amount: The loan amount in INR (number only, no currency symbols)
- tenure_months: Loan tenure in months (12, 24, 36, 48, or 60)
- customer_name: Customer's name if mentioned
- phone_number: 10-digit phone number if mentioned
- salary: Monthly salary if mentioned

Current known state:
""" + json.dumps(current_state, indent=2) + """

Rules:
1. Only extract information that is explicitly stated
2. If loan amount is in lakhs, convert to absolute number (e.g., 5 lakh = 500000)
3. If tenure is in years, convert to months (e.g., 3 years = 36 months)
4. Return null for any field not explicitly mentioned in the conversation
5. Return ONLY a JSON object, no explanations

Response format:
{
    "loan_amount": <number or null>,
    "tenure_months": <number or null>,
    "customer_name": <string or null>,
    "phone_number": <string or null>,
    "salary": <number or null>,
    "interest_rate": 11.5
}"""

        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not initialized",
                "data": {}
            }

        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in conversation_history[-10:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=messages,
                response_format={"type": "json_object"},
                max_completion_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if result.get("interest_rate") is None:
                result["interest_rate"] = self.DEFAULT_INTEREST_RATE
                
            return {
                "success": True,
                "data": result
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse response: {str(e)}",
                "data": {}
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"API error: {str(e)}",
                "data": {}
            }

    def generate_response(
        self,
        conversation_history: List[Dict[str, str]],
        current_state: Dict[str, Any],
        context: str = ""
    ) -> str:
        state_summary = self._format_state_for_prompt(current_state)
        
        system_prompt = f"""You are a professional, friendly loan sales executive at Horizon Finance Limited, an Indian NBFC.

Your role:
- Help customers understand their loan options
- Gather necessary information politely
- Be professional but warm
- Never be pushy or aggressive
- Use simple language, avoid jargon

Current customer state:
{state_summary}

Additional context: {context if context else "None"}

Guidelines:
1. If customer name is unknown, ask for it politely
2. If phone number is unknown, ask for it for KYC verification
3. If loan amount is unknown, help them determine their needs
4. Suggest reasonable tenure options (12-60 months)
5. Keep responses concise (2-3 sentences max)
6. Use Indian currency formatting (Rs., lakhs)
7. Be respectful and use appropriate honorifics

NEVER discuss credit decisions - that's handled by our underwriting team.
NEVER promise approval - always say "subject to verification"."""

        if not self.client:
            return "I apologize, but I'm having trouble processing your request. Could you please try again?"

        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in conversation_history[-10:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=messages,
                max_completion_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return "I apologize, but I'm having trouble processing your request. Could you please try again?"

    def _format_state_for_prompt(self, state: Dict[str, Any]) -> str:
        parts = []
        
        if state.get("customer_name"):
            parts.append(f"Customer Name: {state['customer_name']}")
        else:
            parts.append("Customer Name: Not provided")
            
        if state.get("phone_number"):
            parts.append(f"Phone: {state['phone_number']}")
        else:
            parts.append("Phone: Not provided")
            
        if state.get("loan_amount"):
            parts.append(f"Requested Amount: Rs. {state['loan_amount']:,.2f}")
        else:
            parts.append("Requested Amount: Not specified")
            
        if state.get("tenure_months"):
            parts.append(f"Tenure: {state['tenure_months']} months")
        else:
            parts.append("Tenure: Not specified")
            
        if state.get("salary"):
            parts.append(f"Monthly Salary: Rs. {state['salary']:,.2f}")
        else:
            parts.append("Monthly Salary: Not provided")
            
        return "\n".join(parts)

    def suggest_loan_options(
        self,
        requested_amount: float,
        credit_score: int = None
    ) -> Dict[str, Any]:
        if credit_score:
            from backend.utils.loan_calculator import LoanCalculator
            interest_rate = LoanCalculator.suggest_interest_rate(credit_score)
        else:
            interest_rate = self.DEFAULT_INTEREST_RATE

        options = []
        for tenure in self.TENURE_OPTIONS:
            from backend.utils.loan_calculator import LoanCalculator
            emi = LoanCalculator.calculate_emi(requested_amount, interest_rate, tenure)
            options.append({
                "tenure_months": tenure,
                "interest_rate": interest_rate,
                "emi": emi,
                "total_payment": emi * tenure
            })

        return {
            "loan_amount": requested_amount,
            "options": options
        }
