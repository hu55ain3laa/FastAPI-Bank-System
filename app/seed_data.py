import os
import uuid
import base64
import random
from datetime import datetime, timedelta
from sqlmodel import Session, select

from app.models.database import engine
from app.models.models import User, Deposit, Withdraw
from app.utils.security import hash_password, encrypt_data
from app.services.cheque import generate_cheque_number


def seed_initial_data():
    """Seed initial data for testing"""
    with Session(engine) as session:
        # Check if we already have users
        existing_users = session.exec(select(User)).all()
        if existing_users:
            print("Database already has data, skipping seed")
            return True
        
        # Create admin user
        admin_iv = os.urandom(16)
        admin_user = User(
            id=str(uuid.uuid4()),
            username="admin",
            hashed_password=hash_password("admin"),
            iv=base64.b64encode(admin_iv).decode(),
            balance=encrypt_data("10000", admin_iv),
            is_admin=True
        )
        session.add(admin_user)
        
        # Create regular test users
        user_data = [
            {"username": "alice", "password": "1234", "balance": "5000"},
            {"username": "bob", "password": "1234", "balance": "3000"},
            {"username": "charlie", "password": "1234", "balance": "1500"}
        ]
        
        created_users = []
        for data in user_data:
            user_iv = os.urandom(16)
            user = User(
                id=str(uuid.uuid4()),
                username=data["username"],
                hashed_password=hash_password(data["password"]),
                iv=base64.b64encode(user_iv).decode(),
                balance=encrypt_data(data["balance"], user_iv),
                is_admin=False
            )
            session.add(user)
            created_users.append((user, user_iv))
        
        # Commit to get the user IDs
        session.commit()
        
        # Create sample deposits and withdrawals for each user
        status_options = ["pending", "approved", "rejected"]
        for user, iv in created_users:
            # Create some deposits
            for i in range(3):
                amount = random.randint(100, 1000)
                status = random.choice(status_options)
                created_date = datetime.now() - timedelta(days=random.randint(1, 30))
                
                deposit = Deposit(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    amount=encrypt_data(str(amount), iv),
                    cheque_number=generate_cheque_number("DEP"),
                    status=status,
                    created_at=created_date.isoformat()
                )
                session.add(deposit)
            
            # Create some withdrawals
            for i in range(2):
                amount = random.randint(50, 300)
                status = random.choice(status_options)
                created_date = datetime.now() - timedelta(days=random.randint(1, 30))
                
                # Add different withdrawal methods
                method = random.choice(["bank_transfer", "check", "atm"])
                extra_data = {"method": method}
                
                if method == "bank_transfer":
                    extra_data["details"] = {
                        "bank_name": f"Test Bank {i+1}",
                        "account_number": f"ACCT{random.randint(10000, 99999)}",
                        "routing_number": f"RTG{random.randint(10000, 99999)}"
                    }
                elif method == "check":
                    extra_data["details"] = {
                        "mailing_address": f"123 Test St, City {i+1}, Country"
                    }
                
                withdrawal = Withdraw(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    amount=encrypt_data(str(amount), iv),
                    cheque_number=generate_cheque_number("WDR"),
                    status=status,
                    created_at=created_date.isoformat(),
                    extra_data=str(extra_data)
                )
                session.add(withdrawal)
        
        # Commit all changes
        session.commit()
        print("Initial data seeded successfully")
        return True


if __name__ == "__main__":
    from app.models.database import create_db_and_tables
    
    # Create tables first
    create_db_and_tables()
    
    # Seed data
    seed_initial_data()