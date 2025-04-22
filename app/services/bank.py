import os
import base64
from datetime import datetime
from sqlmodel import Session, select
from fastapi import HTTPException, status

from app.models.models import User, Transaction, Deposit, Withdraw
from app.utils.security import encrypt_data, decrypt_data
from app.services.cheque import generate_cheque_number


def get_user_by_username(username: str, session: Session):
    """Get user by username"""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {username} not found"
        )
    return user


def get_user_balance(user: User) -> float:
    """Get decrypted user balance"""
    iv = base64.b64decode(user.iv)
    return float(decrypt_data(user.balance, iv))


def update_user_balance(user: User, amount: float, session: Session):
    """Update user balance by amount (can be positive or negative)"""
    iv = base64.b64decode(user.iv)
    current_balance = float(decrypt_data(user.balance, iv))
    new_balance = current_balance + amount
    
    if new_balance < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds"
        )
    
    user.balance = encrypt_data(str(new_balance), iv)
    session.add(user)
    session.commit()
    session.refresh(user)
    return new_balance


def transfer_money(sender: User, receiver_username: str, amount: float, session: Session):
    """Transfer money from sender to receiver"""
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    
    # Check if sender has enough balance
    sender_balance = get_user_balance(sender)
    if sender_balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds"
        )
    
    # Get receiver
    receiver = get_user_by_username(receiver_username, session)
    
    # Ensure sender is not receiver
    if sender.id == receiver.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer to yourself"
        )
    
    # Update balances
    update_user_balance(sender, -amount, session)
    update_user_balance(receiver, amount, session)
    
    # Create transaction record
    iv = base64.b64decode(sender.iv)
    
    transaction = Transaction(
        sender_id=sender.id,
        receiver_id=receiver.id,
        amount=encrypt_data(str(amount), iv),
        encrypted_sender=encrypt_data(sender.username, iv),
        encrypted_receiver=encrypt_data(receiver.username, iv),
        timestamp=datetime.now().isoformat()
    )
    
    session.add(transaction)
    session.commit()
    
    return {"message": "Transfer successful"}


def create_deposit(user: User, amount: float, session: Session):
    """Create a deposit request"""
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    
    # Generate cheque number
    cheque_number = generate_cheque_number("DEP")
    
    # Encrypt amount
    iv = base64.b64decode(user.iv)
    encrypted_amount = encrypt_data(str(amount), iv)
    
    # Create deposit record
    deposit = Deposit(
        user_id=user.id,
        amount=encrypted_amount,
        cheque_number=cheque_number,
        status="pending",
        created_at=datetime.now().isoformat()
    )
    
    session.add(deposit)
    session.commit()
    session.refresh(deposit)
    
    return deposit


def create_withdraw(user: User, amount: float, session: Session, method: str = None, details: dict = None):
    """Create a withdrawal request"""
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    
    # Check if user has enough balance
    user_balance = get_user_balance(user)
    if user_balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds"
        )
    
    # Generate cheque number
    cheque_number = generate_cheque_number("WDR")
    
    # Encrypt amount
    iv = base64.b64decode(user.iv)
    encrypted_amount = encrypt_data(str(amount), iv)
    
    # Store method and details as JSON if provided
    extra_data = {}
    if method:
        extra_data["method"] = method
    if details:
        extra_data["details"] = details
    
    # Create withdrawal record
    withdrawal = Withdraw(
        user_id=user.id,
        amount=encrypted_amount,
        cheque_number=cheque_number,
        status="pending",
        created_at=datetime.now().isoformat(),
        extra_data=str(extra_data) if extra_data else None
    )
    
    session.add(withdrawal)
    session.commit()
    session.refresh(withdrawal)
    
    return withdrawal


def get_user_deposits(user: User, session: Session):
    """Get all deposits for a user"""
    return session.exec(select(Deposit).where(Deposit.user_id == user.id)).all()


def get_user_withdrawals(user: User, session: Session):
    """Get all withdrawals for a user"""
    return session.exec(select(Withdraw).where(Withdraw.user_id == user.id)).all()


def get_all_pending_deposits(session: Session):
    """Get all pending deposits (for admin)"""
    return session.exec(select(Deposit).where(Deposit.status == "pending")).all()


def get_all_pending_withdrawals(session: Session):
    """Get all pending withdrawals (for admin)"""
    return session.exec(select(Withdraw).where(Withdraw.status == "pending")).all()


def update_deposit_status(deposit_id: str, status: str, session: Session):
    """Update deposit status"""
    deposit = session.exec(select(Deposit).where(Deposit.id == deposit_id)).first()
    if not deposit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deposit not found"
        )
    
    deposit.status = status
    session.add(deposit)
    session.commit()
    
    # If deposit is approved, update user balance
    if status == "approved":
        user = session.exec(select(User).where(User.id == deposit.user_id)).first()
        iv = base64.b64decode(user.iv)
        amount = float(decrypt_data(deposit.amount, iv))
        update_user_balance(user, amount, session)
    
    return deposit


def update_withdraw_status(withdraw_id: str, status: str, session: Session):
    """Update withdrawal status"""
    withdrawal = session.exec(select(Withdraw).where(Withdraw.id == withdraw_id)).first()
    if not withdrawal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Withdrawal not found"
        )
    
    withdrawal.status = status
    session.add(withdrawal)
    session.commit()
    
    # If withdrawal is approved, update user balance
    if status == "approved":
        user = session.exec(select(User).where(User.id == withdrawal.user_id)).first()
        iv = base64.b64decode(user.iv)
        amount = float(decrypt_data(withdrawal.amount, iv))
        update_user_balance(user, -amount, session)
    
    return withdrawal


def get_recent_transactions(user: User, session: Session, limit: int = 5):
    """Get recent transactions for a user (transfers, approved deposits, approved withdrawals)"""
    # Get recent sent transfers
    sent_transfers = session.exec(
        select(Transaction)
        .where(Transaction.sender_id == user.id)
        .order_by(Transaction.timestamp.desc())
    ).all()
    
    # Get recent received transfers
    received_transfers = session.exec(
        select(Transaction)
        .where(Transaction.receiver_id == user.id)
        .order_by(Transaction.timestamp.desc())
    ).all()
    
    # Get recent approved deposits
    deposits = session.exec(
        select(Deposit)
        .where(Deposit.user_id == user.id)
        .where(Deposit.status == "approved")
        .order_by(Deposit.created_at.desc())
    ).all()
    
    # Get recent approved withdrawals
    withdrawals = session.exec(
        select(Withdraw)
        .where(Withdraw.user_id == user.id)
        .where(Withdraw.status == "approved")
        .order_by(Withdraw.created_at.desc())
    ).all()
    
    # Decrypt and transform into a common format
    transactions = []
    iv = base64.b64decode(user.iv)
    
    # Process sent transfers (negative amount)
    for transfer in sent_transfers:
        amount = float(decrypt_data(transfer.amount, iv))
        receiver_username = decrypt_data(transfer.encrypted_receiver, iv)
        transactions.append({
            "type": "transfer_sent",
            "description": f"Transfer to {receiver_username}",
            "amount": -amount,  # Negative for outgoing
            "timestamp": transfer.timestamp,
            "is_positive": False
        })
    
    # Process received transfers (positive amount)
    for transfer in received_transfers:
        # We need to get the sender's iv to decrypt their encrypted data
        sender = session.exec(select(User).where(User.id == transfer.sender_id)).first()
        if sender:
            sender_iv = base64.b64decode(sender.iv)
            amount = float(decrypt_data(transfer.amount, sender_iv))
            sender_username = decrypt_data(transfer.encrypted_sender, sender_iv)
            transactions.append({
                "type": "transfer_received",
                "description": f"Transfer from {sender_username}",
                "amount": amount,  # Positive for incoming
                "timestamp": transfer.timestamp,
                "is_positive": True
            })
    
    # Process deposits (positive amount)
    for deposit in deposits:
        amount = float(decrypt_data(deposit.amount, iv))
        transactions.append({
            "type": "deposit",
            "description": "Deposit",
            "amount": amount,
            "timestamp": deposit.created_at,
            "is_positive": True
        })
    
    # Process withdrawals (negative amount)
    for withdrawal in withdrawals:
        amount = float(decrypt_data(withdrawal.amount, iv))
        transactions.append({
            "type": "withdrawal",
            "description": "Withdrawal",
            "amount": -amount,  # Negative for outgoing
            "timestamp": withdrawal.created_at,
            "is_positive": False
        })
    
    # Sort all transactions by timestamp in descending order
    transactions.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Return only the most recent ones
    return transactions[:limit] 