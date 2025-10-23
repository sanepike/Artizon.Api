from enum import Enum

class UserTypeEnum(str, Enum):
    CUSTOMER = "customer"
    VENDOR = "vendor"

    def __str__(self) -> str:
        return self.value
    
class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    def __str__(self) -> str:
        return self.value