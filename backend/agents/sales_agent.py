import os
import sys
import json
import logging
from typing import Dict, Any, Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI

logger = logging.getLogger(__name__)

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
- tenure_months: Loan tenure in months (any number, e.g., 12, 13, 24, 36, 48, 60, etc.)
- customer_name: Customer's name if mentioned
- phone_number: 10-digit phone number if mentioned
- salary: Monthly salary if mentioned

Current known state:
""" + json.dumps(current_state, indent=2) + """

Rules:
1. Extract information that is explicitly stated OR implied/agreed upon
2. If loan amount is in lakhs, convert to absolute number (e.g., 5 lakh = 500000)
3. If tenure is in years, convert to months (e.g., 3 years = 36 months)
4. If tenure is mentioned as "X months", extract X as the number
5. If agent suggested a tenure range (e.g., "36 to 48 months") and customer didn't object, extract the lower value (36) as default
6. If customer agrees to a suggested tenure (e.g., "yes", "sounds good", "that works"), extract the suggested value
7. Accept any tenure value (not just 12, 24, 36, 48, 60)
8. Return null ONLY if information is truly not available in the conversation
9. Return ONLY a JSON object, no explanations

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
                model="gpt-4o-mini",
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if result.get("interest_rate") is None:
                result["interest_rate"] = self.DEFAULT_INTEREST_RATE
            
            logger.info("📊 Extracted loan requirements:")
            logger.info(f"  - Customer Name: {result.get('customer_name', 'Not found')}")
            logger.info(f"  - Phone Number: {result.get('phone_number', 'Not found')}")
            logger.info(f"  - Loan Amount: {result.get('loan_amount', 'Not found')}")
            logger.info(f"  - Tenure: {result.get('tenure_months', 'Not found')} months")
            logger.info(f"  - Salary: {result.get('salary', 'Not found')}")
            logger.info(f"  - Interest Rate: {result.get('interest_rate', 'Not found')}%")
                
            return {
                "success": True,
                "data": result
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {str(e)}")
            logger.error(f"Response content: {response.choices[0].message.content if 'response' in locals() else 'N/A'}")
            return {
                "success": False,
                "error": f"Failed to parse response: {str(e)}",
                "data": {}
            }
        except Exception as e:
            logger.error(f"❌ API error in extract_loan_requirements: {str(e)}", exc_info=True)
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
        
        system_prompt = f"""You are a top-performing loan sales executive at Horizon Finance Limited, an Indian NBFC. Your goal is to convert prospects into approved loan applications through consultative selling.

SALES OBJECTIVES:
1. Build rapport and understand customer needs deeply
2. Highlight value propositions (low rates starting at 11.5%, quick approval, flexible tenure 12-60 months, transparent pricing)
3. Overcome objections naturally and address concerns
4. Create appropriate urgency when relevant
5. Guide customers confidently through the process

SALES TECHNIQUES:
- Use customer's name frequently to personalize
- Reference their specific needs/purpose (car, home renovation, etc.)
- Show empathy: "I understand how important this is for you"
- Present options, not just ask questions: "Based on your needs, I'd recommend..."
- Highlight value: "With your profile, you qualify for competitive rates"
- Create urgency when appropriate: "This pre-approval is valid for 30 days"
- Address concerns proactively: "I know you might be thinking about..."

Current customer state:
{state_summary}

Additional context: {context if context else "None"}

GUIDELINES:
1. If customer name is unknown, ask warmly: "May I know your name? I'd love to help you personally."
2. If phone number is unknown, you MUST end with a direct question: "I'll need your phone number to verify your details and get you pre-approved quickly. Could you please share your phone number?"
3. If loan amount is unknown, you MUST end with a direct question: "What loan amount are you looking for?" or "How much do you need?" - Don't repeat purpose if already mentioned.
4. If tenure is unknown, you MUST end with a direct question: "How many months would you like for your loan tenure?" or "Which tenure works for you - 36 months or 48 months?" - Don't repeat loan amount or purpose if already mentioned.
5. CRITICAL RULE: When any information is missing, your response MUST end with a clear, direct question asking for that specific information. Don't repeat information already provided. Be focused - ask ONLY for what's missing.
6. Keep responses short (1-2 sentences) and always end with a question when information is needed
7. Use Indian currency formatting (Rs., lakhs)
8. Be persuasive but ethical - never lie or mislead

IMPORTANT:
- Build excitement about the loan opportunity
- Make them feel valued and understood
- Guide them naturally toward application
- Never promise specific approval - say "subject to verification" but be optimistic
- If they hesitate, address concerns and highlight benefits
- CRITICAL: When information is missing, you MUST end your response with a DIRECT, CLEAR QUESTION asking for that specific information. Don't just discuss - ASK!"""

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
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=300
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
