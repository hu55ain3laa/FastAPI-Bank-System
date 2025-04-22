from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
import base64
from datetime import datetime

from app.models.database import get_session
from app.models.models import User
from app.utils.security import get_current_user, get_current_user_dependency, decrypt_data
from app.services.bank import (
    get_user_deposits, get_user_withdrawals, get_user_balance,
    get_all_pending_deposits, get_all_pending_withdrawals,
    update_deposit_status, update_withdraw_status, get_recent_transactions
)
from app.services.banner import get_active_banners

router = APIRouter(tags=["pages"])

# Templates
templates = Jinja2Templates(directory="templates")

# Helper function to get current user or redirect to login
async def get_user_or_redirect(request: Request, session: Session = Depends(get_session)):
    try:
        return await get_current_user(request=request, session=session)
    except HTTPException:
        return None


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, current_user: User = Depends(get_user_or_redirect)):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, current_user: User = Depends(get_user_or_redirect)):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, current_user: User = Depends(get_user_or_redirect)):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    session: Session = Depends(get_session)
):
    # Debug: print request cookies and headers
    print("Cookies:", request.cookies)
    print("Headers:", request.headers.get("authorization"))
    
    try:
        # Try to get the user
        current_user = await get_current_user(request=request, session=session)
        
        # Get user balance
        balance = get_user_balance(current_user)
        
        # Get recent transactions (5 most recent)
        recent_transactions = get_recent_transactions(current_user, session, limit=5)
        
        # Add a human-readable relative date for each transaction
        for transaction in recent_transactions:
            timestamp = datetime.fromisoformat(transaction["timestamp"])
            now = datetime.now()
            delta = now - timestamp
            
            if delta.days == 0:
                if delta.seconds < 3600:
                    transaction["relative_time"] = f"{delta.seconds // 60} minutes ago"
                else:
                    transaction["relative_time"] = f"{delta.seconds // 3600} hours ago"
            elif delta.days == 1:
                transaction["relative_time"] = "Yesterday"
            else:
                transaction["relative_time"] = f"{delta.days} days ago"
        
        # Get active banners
        banners = get_active_banners(session)
        
        return templates.TemplateResponse(
            "dashboard/index.html", 
            {
                "request": request, 
                "user": current_user,
                "balance": balance,
                "recent_transactions": recent_transactions,
                "banners": banners
            }
        )
    except HTTPException as e:
        # Log the exception
        print(f"Authentication error: {e.detail}")
        # Redirect to login
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/transfer", response_class=HTMLResponse)
async def transfer_page(
    request: Request, 
    session: Session = Depends(get_session)
):
    try:
        current_user = await get_current_user(request=request, session=session)
        # Get user balance
        balance = get_user_balance(current_user)
        
        return templates.TemplateResponse(
            "dashboard/transfer.html", 
            {
                "request": request, 
                "user": current_user,
                "balance": balance
            }
        )
    except HTTPException:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/deposit", response_class=HTMLResponse)
async def deposit_page(
    request: Request, 
    session: Session = Depends(get_session)
):
    try:
        current_user = await get_current_user(request=request, session=session)
        # Get user deposits
        deposits = get_user_deposits(current_user, session)
        
        # Get user balance
        balance = get_user_balance(current_user)
        
        # Decrypt deposits amount
        deposit_list = []
        iv = base64.b64decode(current_user.iv)
        
        for deposit in deposits:
            amount = float(decrypt_data(deposit.amount, iv))
            deposit_list.append({
                "id": deposit.id,
                "cheque_number": deposit.cheque_number,
                "amount": amount,
                "status": deposit.status,
                "created_at": deposit.created_at
            })
        
        return templates.TemplateResponse(
            "deposit/index.html", 
            {
                "request": request, 
                "user": current_user,
                "deposits": deposit_list,
                "balance": balance
            }
        )
    except HTTPException:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/withdraw", response_class=HTMLResponse)
async def withdraw_page(
    request: Request, 
    session: Session = Depends(get_session)
):
    try:
        current_user = await get_current_user(request=request, session=session)
        # Get user withdrawals
        withdrawals = get_user_withdrawals(current_user, session)
        
        # Get user balance
        balance = get_user_balance(current_user)
        
        # Decrypt withdrawals amount
        withdrawal_list = []
        iv = base64.b64decode(current_user.iv)
        
        for withdrawal in withdrawals:
            amount = float(decrypt_data(withdrawal.amount, iv))
            withdrawal_list.append({
                "id": withdrawal.id,
                "cheque_number": withdrawal.cheque_number,
                "amount": amount,
                "status": withdrawal.status,
                "created_at": withdrawal.created_at
            })
        
        return templates.TemplateResponse(
            "withdraw/index.html", 
            {
                "request": request, 
                "user": current_user,
                "withdrawals": withdrawal_list,
                "balance": balance
            }
        )
    except HTTPException:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(
    request: Request, 
    session: Session = Depends(get_session)
):
    try:
        current_user = await get_current_user(request=request, session=session)
        # Check if user is admin
        if not current_user.is_admin:
            return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        
        # Get user balance
        balance = get_user_balance(current_user)
        
        # Get pending deposits
        pending_deposits = get_all_pending_deposits(session)
        
        # Get pending withdrawals
        pending_withdrawals = get_all_pending_withdrawals(session)
        
        # Process deposits
        deposit_list = []
        for deposit in pending_deposits:
            user = session.exec(select(User).where(User.id == deposit.user_id)).first()
            if user:
                iv = base64.b64decode(user.iv)
                amount = float(decrypt_data(deposit.amount, iv))
                deposit_list.append({
                    "id": deposit.id,
                    "cheque_number": deposit.cheque_number,
                    "username": user.username,
                    "amount": amount,
                    "created_at": deposit.created_at
                })
        
        # Process withdrawals
        withdrawal_list = []
        for withdrawal in pending_withdrawals:
            user = session.exec(select(User).where(User.id == withdrawal.user_id)).first()
            if user:
                iv = base64.b64decode(user.iv)
                amount = float(decrypt_data(withdrawal.amount, iv))
                balance = get_user_balance(user)
                withdrawal_list.append({
                    "id": withdrawal.id,
                    "cheque_number": withdrawal.cheque_number,
                    "username": user.username,
                    "amount": amount,
                    "user_balance": balance,
                    "created_at": withdrawal.created_at,
                    "has_sufficient_funds": balance >= amount
                })
        
        return templates.TemplateResponse(
            "dashboard/admin.html", 
            {
                "request": request, 
                "user": current_user,
                "deposits": deposit_list,
                "withdrawals": withdrawal_list,
                "balance": balance
            }
        )
    except HTTPException:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/transactions", response_class=HTMLResponse)
async def transactions_page(
    request: Request,
    page: int = 1,
    limit: int = 20,
    transaction_type: str = None,
    session: Session = Depends(get_session)
):
    try:
        current_user = await get_current_user(request=request, session=session)
        
        # Get user balance
        balance = get_user_balance(current_user)
        
        # Get all user transactions (not just limited to recent ones)
        all_transactions = get_recent_transactions(current_user, session, limit=1000)  # Using a large limit to get all
        
        # Filter by transaction type if specified
        if transaction_type and transaction_type != "all":
            filtered_transactions = [t for t in all_transactions if t["type"] == transaction_type]
        else:
            filtered_transactions = all_transactions
        
        # Simple pagination
        total_items = len(filtered_transactions)
        total_pages = (total_items + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = min(start_idx + limit, total_items)
        paginated_transactions = filtered_transactions[start_idx:end_idx]
        
        # Calculate resulting balance for each transaction
        running_balance = balance
        for idx in range(len(paginated_transactions)-1, -1, -1):
            # Subtract the transaction amount from running balance
            # For deposits and incoming transfers (positive), we subtract
            # For withdrawals and outgoing transfers (negative), we add (because we're going backward)
            running_balance -= paginated_transactions[idx]["amount"]
            paginated_transactions[idx]["resulting_balance"] = running_balance + paginated_transactions[idx]["amount"]
        
        # Calculate summary
        deposits_sum = sum(t["amount"] for t in all_transactions if t["type"] == "deposit")
        withdrawals_sum = sum(t["amount"] for t in all_transactions if t["type"] == "withdrawal")
        transfers_in_sum = sum(t["amount"] for t in all_transactions if t["type"] == "transfer_received")
        transfers_out_sum = sum(t["amount"] for t in all_transactions if t["type"] == "transfer_sent")
        
        summary = {
            "deposits": deposits_sum,
            "withdrawals": withdrawals_sum,
            "transfers_in": transfers_in_sum,
            "transfers_out": transfers_out_sum
        }
        
        # Pagination info
        pagination = {
            "page": page,
            "pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "prev_num": page - 1,
            "next_num": page + 1
        }
        
        # Add proper datetime objects from ISO strings
        for transaction in paginated_transactions:
            transaction["timestamp"] = datetime.fromisoformat(transaction["timestamp"])
            transaction["status"] = "completed"  # All fetched transactions are completed
        
        # Calculate the end item number for display
        end_item = min(page * limit, total_items)
        start_item = (page - 1) * limit + 1 if total_items > 0 else 0
        
        return templates.TemplateResponse(
            "dashboard/transactions.html", 
            {
                "request": request, 
                "user": current_user,
                "balance": balance,
                "transactions": paginated_transactions,
                "pagination": pagination,
                "summary": summary,
                "min": min,  # Add min function to template context
                "total_items": total_items,
                "start_item": start_item,
                "end_item": end_item
            }
        )
    except HTTPException:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER) 