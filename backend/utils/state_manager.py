import uuid
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from enum import Enum


class UnderwritingStatus(str, Enum):
    PENDING = "pending"
    REQUIRES_SALARY = "requires_salary"
    APPROVED = "approved"
    REJECTED = "rejected"


class ConversationStage(str, Enum):
    GREETING = "greeting"
    COLLECTING_INFO = "collecting_info"
    KYC_VERIFICATION = "kyc_verification"
    UNDERWRITING = "underwriting"
    SALARY_COLLECTION = "salary_collection"
    DECISION = "decision"
    SANCTION_LETTER = "sanction_letter"
    COMPLETED = "completed"


@dataclass
class LoanApplicationState:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_name: Optional[str] = None
    phone_number: Optional[str] = None
    loan_amount: Optional[float] = None
    tenure_months: Optional[int] = None
    interest_rate: Optional[float] = None
    credit_score: Optional[int] = None
    salary: Optional[float] = None
    emi: Optional[float] = None
    pre_approved_limit: Optional[float] = None
    kyc_verified: bool = False
    phone_verified: bool = False
    address_verified: bool = False
    underwriting_status: UnderwritingStatus = UnderwritingStatus.PENDING
    final_decision: Optional[str] = None
    rejection_reason: Optional[str] = None
    conversation_stage: ConversationStage = ConversationStage.GREETING
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    sanction_letter_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["underwriting_status"] = self.underwriting_status.value
        data["conversation_stage"] = self.conversation_stage.value
        return data

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                if key == "underwriting_status" and isinstance(value, str):
                    value = UnderwritingStatus(value)
                elif key == "conversation_stage" and isinstance(value, str):
                    value = ConversationStage(value)
                setattr(self, key, value)

    def add_message(self, role: str, content: str) -> None:
        self.conversation_history.append({
            "role": role,
            "content": content
        })

    def get_state_summary(self) -> Dict[str, Any]:
        return {
            "customer_name": self.customer_name,
            "phone_number": self.phone_number,
            "loan_amount": self.loan_amount,
            "tenure_months": self.tenure_months,
            "interest_rate": self.interest_rate,
            "credit_score": self.credit_score,
            "salary": self.salary,
            "emi": self.emi,
            "pre_approved_limit": self.pre_approved_limit,
            "kyc_verified": self.kyc_verified,
            "underwriting_status": self.underwriting_status.value,
            "final_decision": self.final_decision,
            "conversation_stage": self.conversation_stage.value
        }


class StateManager:
    def __init__(self):
        self._sessions: Dict[str, LoanApplicationState] = {}

    def create_session(self) -> LoanApplicationState:
        state = LoanApplicationState()
        self._sessions[state.session_id] = state
        return state

    def get_session(self, session_id: str) -> Optional[LoanApplicationState]:
        return self._sessions.get(session_id)

    def update_session(self, session_id: str, **kwargs) -> Optional[LoanApplicationState]:
        state = self.get_session(session_id)
        if state:
            state.update(**kwargs)
        return state

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def get_all_sessions(self) -> Dict[str, LoanApplicationState]:
        return self._sessions
