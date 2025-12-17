import os
import sys
import json
import logging
from typing import Dict, Any, Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI

logger = logging.getLogger(__name__)

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

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")


class MasterAgent:
    def __init__(self, state_manager: StateManager):
        self.agent_name = "Master Agent"
        self.state_manager = state_manager
        self.client = None
        if OPENAI_API_KEY:
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
        logger.info(f"🤖 Master Agent processing message for session: {session_id}")
        state = self.state_manager.get_session(session_id)
        if not state:
            logger.info("Creating new state for session")
            state = self.state_manager.create_session()
            session_id = state.session_id

        state.add_message("user", user_message)
        logger.info(f"Current stage: {state.conversation_stage.value}")
        
        response = self._orchestrate(state, user_message)
        
        logger.info(f"Orchestration complete. New stage: {state.conversation_stage.value}")
        logger.info(f"Response message length: {len(response.get('message', ''))}")
        
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
        logger.info("👋 Handling greeting stage")
        state.conversation_stage = ConversationStage.COLLECTING_INFO
        
        greeting = self._generate_natural_response(
            state,
            context="The customer has provided their name. Build rapport by acknowledging them warmly. Discover their needs by asking about their loan purpose and goals. Show excitement about helping them. Make them feel valued. Guide them naturally toward sharing their requirements.",
            user_message=user_message
        )
        
        logger.info(f"Greeting response generated: {greeting[:100]}...")
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
            
            logger.info(f"📝 Updating state with extracted data:")
            if data.get("customer_name"):
                state.customer_name = data["customer_name"]
                logger.info(f"  ✓ Customer name: {data['customer_name']}")
            if data.get("phone_number"):
                state.phone_number = data["phone_number"]
                logger.info(f"  ✓ Phone number: {data['phone_number']}")
            if data.get("loan_amount"):
                loan_amt = float(data["loan_amount"])
                state.loan_amount = loan_amt
                logger.info(f"  ✓ Loan amount: Rs. {loan_amt:,.2f}")
            if data.get("tenure_months"):
                tenure_val = int(data["tenure_months"])
                state.tenure_months = tenure_val
                logger.info(f"  ✓ Tenure: {tenure_val} months")
            else:
                logger.warning(f"  ✗ Tenure not extracted (value: {data.get('tenure_months')})")
            if data.get("interest_rate"):
                state.interest_rate = float(data["interest_rate"])
            if data.get("salary"):
                salary_val = float(data["salary"])
                state.salary = salary_val
                logger.info(f"  ✓ Salary: Rs. {salary_val:,.2f}")

        missing = self._get_missing_required_fields(state)
        logger.info(f"Missing required fields: {missing if missing else 'None - ready for KYC'}")
        
        # Check if user is trying to end conversation but required fields are missing
        user_lower = user_message.lower().strip()
        ending_phrases = ["that's it", "thats it", "that's all", "thats all", "nothing else", "no more", "done", "finished", "bye", "thanks"]
        is_trying_to_end = any(phrase in user_lower for phrase in ending_phrases)
        
        if not missing:
            state.conversation_stage = ConversationStage.KYC_VERIFICATION
            return self._handle_kyc(state, user_message)

        # Build sales-oriented context based on what's missing
        if "loan amount" in missing:
            if is_trying_to_end:
                context = "Customer seems done but loan amount is missing. Politely but firmly insist we need the amount to proceed. 'I'd love to help you, but I need to know the loan amount to get you pre-approved. What amount are you looking for?'"
            else:
                context = "The customer hasn't specified their loan amount yet. Ask ONLY for loan amount - don't repeat information already provided (like purpose). Be direct and focused. You MUST end your response with a DIRECT QUESTION asking for the loan amount. Examples: 'What loan amount are you looking for?' or 'How much do you need?' Keep it short and focused."
        elif "loan tenure" in missing:
            if is_trying_to_end:
                context = f"Customer seems done but tenure is missing. This is CRITICAL - we cannot proceed without tenure. Be polite but firm: 'I understand you're ready, but I need to know the loan tenure to complete your application. We recommended 36-48 months earlier - would that work for you? Or do you prefer a different tenure?' Don't let them leave without this."
            else:
                context = "The customer hasn't specified tenure yet. Ask ONLY for tenure - don't repeat information already provided (like loan amount or purpose). Be direct and focused. You MUST end your response with a DIRECT QUESTION asking for tenure. Examples: 'How many months would you like for your loan tenure?' or 'Which tenure works for you - 36 months or 48 months?' Keep it short and focused."
        elif "phone number" in missing:
            if is_trying_to_end:
                context = "Customer seems done but phone number is missing. Politely but firmly insist: 'Almost there! I just need your phone number to get you pre-approved. This will take just a moment.'"
            else:
                context = "Need phone number for KYC verification. You MUST end your response with a DIRECT QUESTION asking for phone number. Examples: 'Could you please share your phone number?' or 'What's your phone number for verification?' or 'I'll need your phone number to proceed - could you share it?' Make it clear what you need."
        elif "customer name" in missing:
            context = "Need customer name. Ask warmly and personally. Build rapport."
        else:
            if is_trying_to_end:
                context = f"Customer seems done but missing: {', '.join(missing)}. Politely but firmly insist we need this information to proceed. Don't let them leave without completing the application."
            else:
                context = f"Missing information: {', '.join(missing)}. Ask for it in a sales-oriented way - explain the value and create excitement."
        
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
        logger.info("🔐 Handling KYC verification stage")
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
        
        # Check if credit score is too low (will likely be rejected)
        # Minimum credit score for approval is typically 700
        credit_score_value = state.credit_score if state.credit_score is not None else 0
        credit_score_too_low = credit_score_value < 700
        
        logger.info(f"🔍 Credit score check: {state.credit_score} (too low: {credit_score_too_low})")
        
        # ALWAYS proceed to underwriting first to get the decision
        underwriting_result = self._handle_underwriting(state, user_message)
        
        # If credit score is too low OR application was rejected, skip KYC message
        if credit_score_too_low or underwriting_result.get("actions") == ["application_rejected"]:
            # Don't generate overly positive KYC message if rejection is likely
            # Just return the rejection message directly
            logger.info("⚠️ Skipping KYC message - credit score too low or application rejected")
            return {
                "message": underwriting_result['message'],
                "actions": underwriting_result.get("actions", []),
                "download_available": False,
                "download_path": None
            }
        
        # Credit score is good and not rejected - generate positive KYC message
        logger.info("✅ Credit score acceptable and not rejected - generating KYC message")
        kyc_message = self._generate_natural_response(
            state,
            context=f"✅ KYC verification completed successfully! Credit score: {state.credit_score} (out of 900). Pre-approved limit: Rs. {state.pre_approved_limit:,.2f}. Now proceeding to evaluate your loan application. Be professional and positive. CRITICAL: Do NOT ask for any information - all required information (loan amount, tenure, purpose) has already been collected. Just acknowledge KYC completion and proceed.",
            user_message="KYC complete"
        )
        
        # Approved or pending - combine KYC message with underwriting result
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
        logger.info("⚖️ Handling underwriting evaluation stage")
        underwriting_result = self.underwriting_agent.evaluate(
            loan_amount=state.loan_amount,
            tenure_months=state.tenure_months,
            interest_rate=state.interest_rate,
            credit_score=state.credit_score,
            pre_approved_limit=state.pre_approved_limit,
            salary=state.salary
        )
        logger.info(f"Underwriting decision: {underwriting_result.get('decision', 'unknown')}")
        
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
                context=f"🎉 Great news! Your loan amount exceeds your pre-approved limit, which means we can offer you more! To unlock this higher amount and get you approved, we need to verify your salary. Required minimum: Rs. {underwriting_result.get('required_min_salary', 0):,.2f} per month. Frame this positively - make it exciting, not a barrier. 'To unlock this higher amount, let's verify your income' - be enthusiastic!",
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
        logger.info("📋 Handling sanction letter generation stage")
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
        loan_amount_str = f"Rs. {state.loan_amount:,.2f}" if state.loan_amount else 'Not specified'
        
        system_prompt = f"""You are a top-performing loan sales executive at Horizon Finance Limited, an Indian NBFC. Your goal is to convert prospects into approved loan applications.

SALES APPROACH:
- Build rapport and show genuine interest in their goals
- Discover needs: understand WHY they need the loan, not just WHAT they need
- Highlight value: emphasize low rates (11.5%+), quick approval, flexible terms
- Create excitement: "Great news!", "Perfect!", "I can help you with that!"
- Guide naturally: "Let's get you pre-approved", "I'll make this easy for you"
- Address concerns: "I understand you might be thinking...", "Don't worry, we'll..."
- Use their name to personalize

Current context: {context}

Customer state:
- Name: {state.customer_name or 'Unknown'}
- Loan Amount: {loan_amount_str}
- Tenure: {state.tenure_months or 'Not specified'} months
- Stage: {state.conversation_stage.value}

Guidelines:
1. Be enthusiastic, warm, and persuasive (but ethical)
2. Use proper Indian English
3. Keep responses engaging (2-4 sentences)
4. Never promise specific approval - say "subject to verification" but be optimistic
5. Use Rs. for currency, lakhs for large amounts
6. Make them feel valued and excited about the opportunity
7. CRITICAL: NEVER ask for information that has already been collected. If loan amount, tenure, or purpose were already mentioned in the conversation, do NOT ask for them again.
8. CRITICAL: If the context indicates missing information, you MUST end your response with a clear, direct question asking for that information. Always end with a question mark (?) when information is needed."""

        if not self.client:
            logger.warning("⚠️ OpenAI client not initialized")
            return "Thank you for your patience. How may I assist you further?"

        try:
            logger.info("📡 Calling OpenAI API...")
            logger.debug(f"System prompt: {system_prompt[:200]}...")
            logger.debug(f"User message: {user_message}")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=200
            )
            content = response.choices[0].message.content
            logger.info(f"✅ OpenAI response received ({len(content) if content else 0} chars)")
            logger.debug(f"Response content: {content[:200]}{'...' if content and len(content) > 200 else ''}")
            return content if content else "Thank you for your patience. How may I assist you further?"
        except Exception as e:
            logger.error(f"❌ Error in _generate_natural_response: {str(e)}", exc_info=True)
            return "Thank you for your patience. How may I assist you further?"

    def start_session(self) -> Dict[str, Any]:
        state = self.state_manager.create_session()
        
        greeting = """Welcome to Horizon Finance Limited! 🎉

I'm excited to help you get the personal loan you need! Whether it's for a car, home renovation, or any other important goal, I'm here to make it happen.

We offer:
✨ Competitive interest rates starting at just 11.5%
✨ Quick approval process - get pre-approved in minutes
✨ Flexible tenure options from 12 to 60 months
✨ Transparent pricing with no hidden charges

To get started and see what you qualify for, may I know your name please?"""
        
        state.add_message("assistant", greeting)
        
        return {
            "session_id": state.session_id,
            "message": greeting,
            "state": state.get_state_summary(),
            "stage": state.conversation_stage.value
        }
