import base64
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import FileResponse, HTMLResponse
from sqlmodel import Session, select
import io
import random
from datetime import datetime

from app.models.database import get_session
from app.models.models import User, Deposit, Withdraw
from app.schemas.bank import TransferRequest, DepositRequest, WithdrawRequest, ChequeStatusUpdate
from app.utils.security import get_current_user_dependency, get_admin_user, decrypt_data
from app.services.bank import (
    transfer_money, create_deposit, create_withdraw, 
    get_user_deposits, get_user_withdrawals, get_user_balance,
    get_all_pending_deposits, get_all_pending_withdrawals,
    update_deposit_status, update_withdraw_status, get_recent_transactions
)
from app.services.cheque import generate_deposit_cheque_pdf, generate_withdraw_cheque_pdf

router = APIRouter(prefix="/api", tags=["banking"])

@router.get("/balance")
async def get_balance(current_user: User = Depends(get_current_user_dependency)):
    """Get current user's balance"""
    return {"balance": get_user_balance(current_user)}


@router.post("/transfer")
async def transfer(
    transfer_data: TransferRequest,
    current_user: User = Depends(get_current_user_dependency),
    session: Session = Depends(get_session),
    request: Request = None
):
    """Transfer money to another user"""
    result = transfer_money(
        sender=current_user,
        receiver_username=transfer_data.receiver_username,
        amount=transfer_data.amount,
        session=session
    )
    
    # Check if this is an HTMX request
    is_htmx = request and request.headers.get('HX-Request') == 'true'
    
    if is_htmx:
        # Return HTML response for HTMX
        html_content = f"""
        <div class="bg-green-50 border border-green-200 rounded-lg p-6 animate-fadeIn">
            <h3 class="text-lg font-medium text-green-800 mb-2">Transfer Successful!</h3>
            <p class="text-green-700 mb-4">You have successfully transferred ${transfer_data.amount:.2f} to {transfer_data.receiver_username}.</p>
            <p class="text-gray-600">Your funds have been transferred. The page will refresh to show your updated balance.</p>
        </div>
        <script>
            setTimeout(function() {{ window.location.reload(); }}, 2000);
        </script>
        """
        return HTMLResponse(content=html_content)
    
    # Return JSON for API clients
    return result


@router.post("/deposit", status_code=status.HTTP_201_CREATED)
async def deposit(
    deposit_data: DepositRequest,
    current_user: User = Depends(get_current_user_dependency),
    session: Session = Depends(get_session)
):
    """Create a deposit request"""
    deposit = create_deposit(
        user=current_user,
        amount=deposit_data.amount,
        session=session
    )
    
    return {
        "message": "Deposit request created successfully",
        "cheque_number": deposit.cheque_number
    }


@router.get("/deposit/{cheque_number}/pdf")
async def get_deposit_pdf(
    cheque_number: str,
    current_user: User = Depends(get_current_user_dependency),
    session: Session = Depends(get_session)
):
    """Get deposit cheque as PDF"""
    # Find deposit by cheque number
    deposit = session.exec(
        select(Deposit)
        .where(Deposit.cheque_number == cheque_number)
        .where(Deposit.user_id == current_user.id)
    ).first()
    
    if not deposit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deposit not found"
        )
    
    # Decrypt amount
    iv = base64.b64decode(current_user.iv)
    amount = float(decrypt_data(deposit.amount, iv))
    
    # Generate PDF
    pdf_bytes = generate_deposit_cheque_pdf(
        username=current_user.username,
        amount=amount,
        cheque_number=deposit.cheque_number
    )
    
    # Return PDF as response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=deposit_{deposit.cheque_number}.pdf"
        }
    )


@router.post("/withdraw", status_code=status.HTTP_201_CREATED)
async def withdraw(
    withdraw_data: WithdrawRequest,
    current_user: User = Depends(get_current_user_dependency),
    session: Session = Depends(get_session)
):
    """Create a withdrawal request"""
    withdrawal = create_withdraw(
        user=current_user,
        amount=withdraw_data.amount,
        method=withdraw_data.method,
        details=withdraw_data.details,
        session=session
    )
    
    response_data = {
        "message": "Withdrawal request created successfully",
        "cheque_number": withdrawal.cheque_number
    }
    
    # Generate ATM code if method is 'atm'
    if hasattr(withdraw_data, 'method') and withdraw_data.method == 'atm':
        # Generate a random ATM code
        atm_code = ''.join(random.choices('0123456789', k=12))
        atm_code_formatted = f"{atm_code[:4]}-{atm_code[4:8]}-{atm_code[8:12]}"
        response_data["atm_code"] = atm_code_formatted
    
    return response_data


@router.get("/withdraw/{cheque_number}/pdf")
async def get_withdraw_pdf(
    cheque_number: str,
    current_user: User = Depends(get_current_user_dependency),
    session: Session = Depends(get_session)
):
    """Get withdrawal cheque as PDF"""
    # Find withdrawal by cheque number
    withdrawal = session.exec(
        select(Withdraw)
        .where(Withdraw.cheque_number == cheque_number)
        .where(Withdraw.user_id == current_user.id)
    ).first()
    
    if not withdrawal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Withdrawal not found"
        )
    
    # Decrypt amount
    iv = base64.b64decode(current_user.iv)
    amount = float(decrypt_data(withdrawal.amount, iv))
    
    # Generate PDF
    pdf_bytes = generate_withdraw_cheque_pdf(
        username=current_user.username,
        amount=amount,
        cheque_number=withdrawal.cheque_number
    )
    
    # Return PDF as response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=withdrawal_{withdrawal.cheque_number}.pdf"
        }
    )


@router.get("/deposits")
async def get_deposits(
    current_user: User = Depends(get_current_user_dependency),
    session: Session = Depends(get_session)
):
    """Get all deposits for current user"""
    deposits = get_user_deposits(current_user, session)
    
    # Decrypt amounts
    result = []
    iv = base64.b64decode(current_user.iv)
    
    for deposit in deposits:
        amount = float(decrypt_data(deposit.amount, iv))
        result.append({
            "id": deposit.id,
            "cheque_number": deposit.cheque_number,
            "amount": amount,
            "status": deposit.status,
            "created_at": deposit.created_at
        })
    
    return result


@router.get("/withdrawals")
async def get_withdrawals(
    current_user: User = Depends(get_current_user_dependency),
    session: Session = Depends(get_session)
):
    """Get all withdrawals for current user"""
    withdrawals = get_user_withdrawals(current_user, session)
    
    # Decrypt amounts
    result = []
    iv = base64.b64decode(current_user.iv)
    
    for withdrawal in withdrawals:
        amount = float(decrypt_data(withdrawal.amount, iv))
        result.append({
            "id": withdrawal.id,
            "cheque_number": withdrawal.cheque_number,
            "amount": amount,
            "status": withdrawal.status,
            "created_at": withdrawal.created_at
        })
    
    return result


# Admin routes
@router.get("/admin/deposits/pending")
async def admin_get_pending_deposits(
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get all pending deposits (admin only)"""
    deposits = get_all_pending_deposits(session)
    
    # Gather user data and decrypt amounts
    result = []
    
    for deposit in deposits:
        # Get user
        user = session.exec(select(User).where(User.id == deposit.user_id)).first()
        if user:
            iv = base64.b64decode(user.iv)
            amount = float(decrypt_data(deposit.amount, iv))
            
            result.append({
                "id": deposit.id,
                "cheque_number": deposit.cheque_number,
                "username": user.username,
                "amount": amount,
                "created_at": deposit.created_at
            })
    
    return result


@router.get("/admin/withdrawals/pending")
async def admin_get_pending_withdrawals(
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get all pending withdrawals (admin only)"""
    withdrawals = get_all_pending_withdrawals(session)
    
    # Gather user data and decrypt amounts
    result = []
    
    for withdrawal in withdrawals:
        # Get user
        user = session.exec(select(User).where(User.id == withdrawal.user_id)).first()
        if user:
            iv = base64.b64decode(user.iv)
            amount = float(decrypt_data(withdrawal.amount, iv))
            balance = get_user_balance(user)
            
            result.append({
                "id": withdrawal.id,
                "cheque_number": withdrawal.cheque_number,
                "username": user.username,
                "amount": amount,
                "user_balance": balance,
                "created_at": withdrawal.created_at,
                "has_sufficient_funds": balance >= amount
            })
    
    return result


@router.post("/admin/deposit/{deposit_id}/status")
async def admin_update_deposit_status(
    deposit_id: str,
    status_update: ChequeStatusUpdate,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update deposit status (admin only)"""
    deposit = update_deposit_status(deposit_id, status_update.status, session)
    return {"message": f"Deposit status updated to {status_update.status}"}


@router.post("/admin/withdraw/{withdraw_id}/status")
async def admin_update_withdraw_status(
    withdraw_id: str,
    status_update: ChequeStatusUpdate,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update withdrawal status (admin only)"""
    # Check withdrawal
    withdrawal = session.exec(select(Withdraw).where(Withdraw.id == withdraw_id)).first()
    if not withdrawal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Withdrawal not found"
        )
    
    # If approving, check if user has sufficient funds
    if status_update.status == "approved":
        user = session.exec(select(User).where(User.id == withdrawal.user_id)).first()
        iv = base64.b64decode(user.iv)
        amount = float(decrypt_data(withdrawal.amount, iv))
        balance = get_user_balance(user)
        
        if balance < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has insufficient funds for this withdrawal"
            )
    
    # Update status
    withdrawal = update_withdraw_status(withdraw_id, status_update.status, session)
    return {"message": f"Withdrawal status updated to {status_update.status}"}


@router.get("/transactions/export")
async def export_transactions(
    request: Request,
    format: str = "csv",
    transaction_type: str = None,
    date_from: str = None,
    date_to: str = None,
    current_user: User = Depends(get_current_user_dependency),
    session: Session = Depends(get_session)
):
    """Export transactions in CSV or PDF format"""
    # Get user transactions - reusing the get_recent_transactions function with a large limit
    transactions = get_recent_transactions(current_user, session, limit=1000)
    
    # Filter by transaction type if specified
    if transaction_type and transaction_type != "all":
        transactions = [t for t in transactions if t["type"] == transaction_type]
    
    # Filter by date range if specified
    if date_from:
        try:
            date_from_obj = datetime.fromisoformat(date_from)
            transactions = [t for t in transactions if datetime.fromisoformat(t["timestamp"]) >= date_from_obj]
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.fromisoformat(date_to)
            transactions = [t for t in transactions if datetime.fromisoformat(t["timestamp"]) <= date_to_obj]
        except ValueError:
            pass
    
    if format.lower() == "csv":
        # Create CSV content
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Date", "Type", "Description", "Amount", "Status"])
        
        # Write transaction data
        for t in transactions:
            writer.writerow([
                t["timestamp"],
                t["type"],
                t["description"],
                f"{'+' if t['is_positive'] else ''}{t['amount']}",
                "Completed"
            ])
        
        # Create response
        response = Response(content=output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d')}.csv"
        response.headers["Content-Type"] = "text/csv"
        return response
    
    elif format.lower() == "pdf":
        # Generate PDF using ReportLab
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        import io
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Add title
        styles = getSampleStyleSheet()
        title = Paragraph(f"Transaction History - {current_user.username}", styles["Heading1"])
        story.append(title)
        
        # Add date
        date_text = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"])
        story.append(date_text)
        
        # Add transaction table
        data = [["Date", "Type", "Description", "Amount", "Status"]]
        
        for t in transactions:
            data.append([
                datetime.fromisoformat(t["timestamp"]).strftime("%Y-%m-%d %H:%M"),
                t["type"].replace("_", " ").title(),
                t["description"],
                f"{'+' if t['is_positive'] else ''}{t['amount']:.2f}",
                "Completed"
            ])
        
        table = Table(data)
        
        # Add style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        
        # Add row color alternation
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
        
        table.setStyle(style)
        story.append(table)
        
        # Build PDF
        doc.build(story)
        
        # Create response
        pdf_data = buffer.getvalue()
        buffer.close()
        
        response = Response(content=pdf_data)
        response.headers["Content-Disposition"] = f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d')}.pdf"
        response.headers["Content-Type"] = "application/pdf"
        return response
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {format}"
        ) 