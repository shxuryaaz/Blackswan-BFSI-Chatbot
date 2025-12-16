import os
import json
from typing import Dict, Any, Optional, List
from openai import OpenAI

from backend.utils.state_manager import (
    LoanApplicationState, 
    StateManager, 
    ConversationStage,
    UnderwritingStatus
)
from backend.agents.sales_agent import SalesAgent
from backend.agents.verification_agent import VerificationAgent
from backend.agents.underwriting_agent import UnderwritingAgent
from backend.agents.sanction_agent import SanctionAgent

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


class MasterAgent:
    def __init__(self, state_manager: StateManager):
        self.agent_name = "Master Agent"
        self.state_manager = state_manager
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
        self.sales_agent = SalesAgent()
        self.verification_agent = VerificationAgent()
        self.underwriting_agent = UnderwritingAgent()
        self.sanction_agent = SanctionAgent()

    def process_message(
        self, 
        session_id: str, 
        user_message: str
    ) -> Dict[str, Any]:
        state = self.state_manager.get_session(session_id)
        if not state:
            state = self.state_manager.create_session()
            session_id = state.session_id

        state.add_message("user", user_message)
        
        response = self._orchestrate(state, user_message)
        
        state.add_message("assistant", response["message"])
        
        return {
            "session_id": state.session_id,
            "message": response["message"],
            "state": state.get_state_summary(),
            "stage": state.conversation_stage.value,
            "actions": response.get("actions", []),
            "download_available": response.get("download_available", False),
            "download_path": response.get("download_path", None)
        }

    def _orchestrate(
        self, 
        state: LoanApplicationState, 
        user_message: str
    ) -> Dict[str, Any]:
        stage = state.conversation_stage

        if stage == ConversationStage.GREETING:
            return self._handle_greeting(state, user_message)
        
        elif stage == ConversationStage.COLLECTING_INFO:
            return self._handle_info_collection(state, user_message)
        
        elif stage == ConversationStage.KYC_VERIFICATION:
            return self._handle_kyc(state, user_message)
        
        elif stage == ConversationStage.UNDERWRITING:
            return self._handle_underwriting(state, user_message)
        
        elif stage == ConversationStage.SALARY_COLLECTION:
            return self._handle_salary_collection(state, user_message)
        
        elif stage == ConversationStage.DECISION:
            return self._handle_decision(state, user_message)
        
        elif stage == ConversationStage.SANCTION_LETTER:
            return self._handle_sanction_letter(state, user_message)
        
        elif stage == ConversationStage.COMPLETED:
            return self._handle_completed(state, user_message)
        
        return self._handle_info_collection(state, user_message)

    def _handle_greeting(
        self, 
        state: LoanApplicationState, 
        user_message: str
    ) -> Dict[str, Any]:
        state.conversation_stage = ConversationStage.COLLECTING_INFO
        
        greeting = self._generate_natural_response(
            state,
            context="This is the first message. Greet the customer warmly and ask how you can help with their loan needs. Ask for their name.",
            user_message=user_message
        )
        
        return {"message": greeting, "actions": ["greeting_complete"]}

    def _handle_info_collection(
        self, 
        state: LoanApplicationState, 
        user_message: str
    ) -> Dict[str, Any]:
        extraction = self.sales_agent.extract_loan_requirements(
            state.conversation_history,
            state.get_state_summary()
        )
        
        if extraction["success"]:
            data = extraction["data"]
            
            if data.get("customer_name"):
                state.customer_name = data["customer_name"]
            if data.get("phone_number"):
                state.phone_number = data["phone_number"]
            if data.get("loan_amount"):
                state.loan_amount = float(data["loan_amount"])
            if data.get("tenure_months"):
                state.tenure_months = int(data["tenure_months"])
            if data.get("interest_rate"):
                state.interest_rate = float(data["interest_rate"])
            if data.get("salary"):
                state.salary = float(data["salary"])

        missing = self._get_missing_required_fields(state)
        
        if not missing:
            state.conversation_stage = ConversationStage.KYC_VERIFICATION
            return self._handle_kyc(state, user_message)

        context = f"Missing information: {', '.join(missing)}. Ask for the next missing piece naturally."
        response = self.sales_agent.generate_response(
            state.conversation_history,
            state.get_state_summary(),
            context
        )
        
        return {"message": response, "actions": ["collecting_info"]}

    def _handle_kyc(
        self, 
        state: LoanApplicationState, 
        user_message: str
    ) -> Dict[str, Any]:
        verification_result = self.verification_agent.verify_customer(
            state.phone_number,
            state.customer_name
        )
        
        state.kyc_verified = verification_result["success"]
        state.phone_verified = verification_result["phone_verified"]
        state.address_verified = verification_result["address_verified"]
        state.credit_score = verification_result["credit_score"]
        state.pre_approved_limit = verification_result["pre_approved_limit"]
        
        if not state.interest_rate:
            from backend.utils.loan_calculator import LoanCalculator
            state.interest_rate = LoanCalculator.suggest_interest_rate(state.credit_score)

        state.conversation_stage = ConversationStage.UNDERWRITING
        
        kyc_message = self._generate_natural_response(
            state,
            context=f"KYC verification completed successfully. Credit score: {state.credit_score}. Pre-approved limit: Rs. {state.pre_approved_limit:,.2f}. Now proceeding to evaluate the loan application. Be encouraging but don't promise approval.",
            user_message="KYC complete"
        )
        
        underwriting_result = self._handle_underwriting(state, user_message)
        
        combined_message = f"{kyc_message}\n\n{underwriting_result['message']}"
        
        return {
            "message": combined_message,
            "actions": underwriting_result.get("actions", []),
            "download_available": underwriting_result.get("download_available", False),
            "download_path": underwriting_result.get("download_path", None)
        }

    def _handle_underwriting(
        self, 
        state: LoanApplicationState, 
        user_message: str
    ) -> Dict[str, Any]:
        underwriting_result = self.underwriting_agent.evaluate(
            loan_amount=state.loan_amount,
            tenure_months=state.tenure_months,
            interest_rate=state.interest_rate,
            credit_score=state.credit_score,
            pre_approved_limit=state.pre_approved_limit,
            salary=state.salary
        )
        
        decision = underwriting_result["decision"]
        
        if decision == "approved":
            state.underwriting_status = UnderwritingStatus.APPROVED
            state.final_decision = "approved"
            state.emi = underwriting_result["emi"]
            state.conversation_stage = ConversationStage.SANCTION_LETTER
            
            return self._handle_sanction_letter(state, user_message)
        
        elif decision == "rejected":
            state.underwriting_status = UnderwritingStatus.REJECTED
            state.final_decision = "rejected"
            state.rejection_reason = underwriting_result["reason"]
            state.conversation_stage = ConversationStage.COMPLETED
            
            rejection_message = self.sanction_agent.format_rejection_message(
                state.customer_name or "Valued Customer",
                underwriting_result["reason"]
            )
            
            return {
                "message": rejection_message,
                "actions": ["application_rejected"]
            }
        
        elif decision == "pending":
            state.underwriting_status = UnderwritingStatus.REQUIRES_SALARY
            state.emi = underwriting_result["emi"]
            state.conversation_stage = ConversationStage.SALARY_COLLECTION
            
            salary_request = self._generate_natural_response(
                state,
                context=f"The loan amount exceeds pre-approved limit. Need salary verification. Required minimum salary: Rs. {underwriting_result.get('required_min_salary', 0):,.2f}. Ask for monthly salary politely.",
                user_message=user_message
            )
            
            return {
                "message": salary_request,
                "actions": ["salary_required"]
            }
        
        return {"message": "Processing your application...", "actions": []}

    def _handle_salary_collection(
        self, 
        state: LoanApplicationState, 
        user_message: str
    ) -> Dict[str, Any]:
        extraction = self.sales_agent.extract_loan_requirements(
            state.conversation_history,
            state.get_state_summary()
        )
        
        if extraction["success"] and extraction["data"].get("salary"):
            state.salary = float(extraction["data"]["salary"])
            state.conversation_stage = ConversationStage.UNDERWRITING
            return self._handle_underwriting(state, user_message)
        
        try:
            cleaned = ''.join(c for c in user_message if c.isdigit() or c == '.')
            if cleaned:
                state.salary = float(cleaned)
                state.conversation_stage = ConversationStage.UNDERWRITING
                return self._handle_underwriting(state, user_message)
        except ValueError:
            pass
        
        response = self._generate_natural_response(
            state,
            context="Need to collect monthly salary. Ask again politely. Accept numeric value in INR.",
            user_message=user_message
        )
        
        return {"message": response, "actions": ["awaiting_salary"]}

    def _handle_sanction_letter(
        self, 
        state: LoanApplicationState, 
        user_message: str
    ) -> Dict[str, Any]:
        result = self.sanction_agent.generate_sanction_letter(
            customer_name=state.customer_name or "Valued Customer",
            loan_amount=state.loan_amount,
            tenure_months=state.tenure_months,
            interest_rate=state.interest_rate,
            emi=state.emi,
            session_id=state.session_id
        )
        
        if result["success"]:
            state.sanction_letter_path = result["file_path"]
            state.conversation_stage = ConversationStage.COMPLETED
            
            approval_message = self.sanction_agent.format_approval_message(
                state.customer_name or "Valued Customer",
                state.loan_amount,
                state.tenure_months,
                state.interest_rate,
                state.emi
            )
            
            return {
                "message": approval_message,
                "actions": ["application_approved", "sanction_letter_generated"],
                "download_available": True,
                "download_path": f"/api/download/{state.session_id}"
            }
        
        error_message = "We've approved your loan, but there was an issue generating the sanction letter. Our team will send it to you shortly."
        
        return {
            "message": error_message,
            "actions": ["sanction_letter_error"]
        }

    def _handle_decision(
        self, 
        state: LoanApplicationState, 
        user_message: str
    ) -> Dict[str, Any]:
        return {"message": "Your application has been processed.", "actions": []}

    def _handle_completed(
        self, 
        state: LoanApplicationState, 
        user_message: str
    ) -> Dict[str, Any]:
        response = self._generate_natural_response(
            state,
            context="The loan application process is complete. Answer any follow-up questions. If they want to start a new application, tell them to refresh the page.",
            user_message=user_message
        )
        
        download_available = state.final_decision == "approved" and state.sanction_letter_path
        
        return {
            "message": response,
            "actions": ["conversation_complete"],
            "download_available": download_available,
            "download_path": f"/api/download/{state.session_id}" if download_available else None
        }

    def _get_missing_required_fields(self, state: LoanApplicationState) -> List[str]:
        missing = []
        
        if not state.customer_name:
            missing.append("customer name")
        if not state.phone_number:
            missing.append("phone number")
        if not state.loan_amount:
            missing.append("loan amount")
        if not state.tenure_months:
            missing.append("loan tenure")
            
        return missing

    def _generate_natural_response(
        self,
        state: LoanApplicationState,
        context: str,
        user_message: str
    ) -> str:
        system_prompt = f"""You are a professional loan sales assistant at Horizon Finance Limited, an Indian NBFC.
        
Current context: {context}

Customer state:
- Name: {state.customer_name or 'Unknown'}
- Loan Amount: Rs. {state.loan_amount:,.2f if state.loan_amount else 'Not specified'}
- Tenure: {state.tenure_months or 'Not specified'} months
- Stage: {state.conversation_stage.value}

Guidelines:
1. Be professional, warm, and concise
2. Use proper Indian English
3. Keep responses to 2-3 sentences
4. Never make credit decisions - that's handled by the underwriting system
5. Use Rs. for currency, lakhs for large amounts"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_completion_tokens=200
            )
            return response.choices[0].message.content
        except Exception:
            return "Thank you for your patience. How may I assist you further?"

    def start_session(self) -> Dict[str, Any]:
        state = self.state_manager.create_session()
        
        greeting = """Welcome to Horizon Finance Limited!

I'm your personal loan assistant, and I'm here to help you with your financing needs today.

To get started, may I know your name please?"""
        
        state.add_message("assistant", greeting)
        
        return {
            "session_id": state.session_id,
            "message": greeting,
            "state": state.get_state_summary(),
            "stage": state.conversation_stage.value
        }
