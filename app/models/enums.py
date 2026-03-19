from enum import Enum, StrEnum


class EnumBase(Enum):
    @classmethod
    def get_member_values(cls):
        return [item.value for item in cls._member_map_.values()]

    @classmethod
    def get_member_names(cls):
        return [name for name in cls._member_names_]


class MethodType(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class TicketStatus(StrEnum):
    DRAFT = "draft"
    PENDING_SUBMIT = "pending_submit"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING_ASSIGN = "pending_assign"
    ASSIGNED = "assigned"
    PROCESSING = "processing"
    TRANSFERRED = "transferred"
    COMPLETED = "completed"
    CLOSED = "closed"


class AuditResult(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


class MessageType(StrEnum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    SYSTEM = "system"


class CallStatus(StrEnum):
    INITIATING = "initiating"
    RINGING = "ringing"
    CONNECTED = "connected"
    ENDED = "ended"
    FAILED = "failed"
    MISSED = "missed"


class FlowAction(StrEnum):
    CREATE = "create"
    SUBMIT = "submit"
    WITHDRAW = "withdraw"
    REVIEW_APPROVE = "review_approve"
    REVIEW_REJECT = "review_reject"
    ASSIGN = "assign"
    TRANSFER = "transfer"
    START_PROCESS = "start_process"
    COMPLETE = "complete"
    CLOSE = "close"
    RESUBMIT = "resubmit"
    ADD_REMARK = "add_remark"


class RegionLevel(StrEnum):
    PROVINCE = "province"
    CITY = "city"
    DISTRICT = "district"
    STREET = "street"
