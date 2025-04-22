import uuid
from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship


class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    iv: str  # Initialization vector for encryption
    balance: str  # Encrypted balance
    is_admin: bool = Field(default=False)
    
    # Relationships
    sent_transactions: List["Transaction"] = Relationship(
        back_populates="sender", sa_relationship_kwargs={"foreign_keys": "Transaction.sender_id"}
    )
    received_transactions: List["Transaction"] = Relationship(
        back_populates="receiver", sa_relationship_kwargs={"foreign_keys": "Transaction.receiver_id"}
    )
    deposits: List["Deposit"] = Relationship(back_populates="user")
    withdrawals: List["Withdraw"] = Relationship(back_populates="user")


class Transaction(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    sender_id: str = Field(foreign_key="user.id")
    receiver_id: str = Field(foreign_key="user.id")
    amount: str  # Encrypted amount
    encrypted_sender: str
    encrypted_receiver: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Relationships
    sender: User = Relationship(back_populates="sent_transactions", sa_relationship_kwargs={"foreign_keys": "Transaction.sender_id"})
    receiver: User = Relationship(back_populates="received_transactions", sa_relationship_kwargs={"foreign_keys": "Transaction.receiver_id"})


class Deposit(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    amount: str  # Encrypted amount
    cheque_number: str = Field(unique=True)
    status: str = Field(default="pending")  # pending, approved, rejected
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Relationship
    user: User = Relationship(back_populates="deposits")


class Withdraw(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    amount: str  # Encrypted amount
    cheque_number: str = Field(unique=True)
    status: str = Field(default="pending")  # pending, approved, rejected
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    extra_data: Optional[str] = Field(default=None)  # For storing method and details
    
    # Relationship
    user: User = Relationship(back_populates="withdrawals")


class Banner(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str
    subtitle: str
    background_color: str = Field(default="#0F52BA")  # Default to bank-primary
    text_color: str = Field(default="#FFFFFF")  # Default to white
    is_active: bool = Field(default=True)
    order: int = Field(default=0)  # For controlling the order of banners
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None 