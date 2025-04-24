document.addEventListener('DOMContentLoaded', () => {
  // Set up auth header for all API requests
  const token = localStorage.getItem('access_token');
  const tokenType = localStorage.getItem('token_type');
  
  const headers = {
    'Content-Type': 'application/json',
  };
  
  if (token && tokenType) {
    headers['Authorization'] = `${tokenType} ${token}`;
  }
  
  // Helper function to format currency
  window.formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };
  
  // Helper function to format date
  window.formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };
  
  // Helper function to show notifications
  window.showNotification = (message, type = 'success') => {
    const notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) return;
    
    const notification = document.createElement('div');
    notification.className = `flex items-center p-4 mb-4 rounded-lg shadow-lg animate-fadeIn`;
    
    // Set background color based on type
    if (type === 'success') {
      notification.classList.add('bg-green-100', 'text-green-800', 'border', 'border-green-200');
    } else if (type === 'error') {
      notification.classList.add('bg-red-100', 'text-red-800', 'border', 'border-red-200');
    } else if (type === 'warning') {
      notification.classList.add('bg-yellow-100', 'text-yellow-800', 'border', 'border-yellow-200');
    } else {
      notification.classList.add('bg-blue-100', 'text-blue-800', 'border', 'border-blue-200');
    }
    
    // Set icon based on type
    let icon = '';
    if (type === 'success') {
      icon = '<svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>';
    } else if (type === 'error') {
      icon = '<svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>';
    } else if (type === 'warning') {
      icon = '<svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>';
    } else {
      icon = '<svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2h.01a1 1 0 000-2H9z" clip-rule="evenodd"></path></svg>';
    }
    
    notification.innerHTML = `
      ${icon}
      <div class="flex-grow">${message}</div>
      <button type="button" class="ml-auto text-gray-500 hover:text-gray-900 focus:outline-none">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
        </svg>
      </button>
    `;
    
    // Add close button functionality
    const closeButton = notification.querySelector('button');
    closeButton.addEventListener('click', () => {
      notification.classList.add('opacity-0');
      setTimeout(() => {
        notification.remove();
      }, 300);
    });
    
    notificationContainer.appendChild(notification);
    
    // Auto-remove notification after 5 seconds
    setTimeout(() => {
      notification.classList.add('opacity-0');
      setTimeout(() => {
        notification.remove();
      }, 300);
    }, 5000);
  };
  
  // Transfer form
  const transferForm = document.getElementById('transfer-form');
  if (transferForm) {
    transferForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const formData = new FormData(transferForm);
      const receiverUsername = formData.get('receiver_username');
      const amount = parseFloat(formData.get('amount'));
      
      try {
        const response = await fetch('/api/transfer', {
          method: 'POST',
          headers,
          body: JSON.stringify({ receiver_username: receiverUsername, amount }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
          showNotification('Transfer successful!', 'success');
          transferForm.reset();
          
          // Refresh balance after short delay
          setTimeout(() => {
            window.location.reload();
          }, 2000);
        } else {
          showNotification(data.detail || 'Transfer failed', 'error');
        }
      } catch (error) {
        console.error('Transfer error:', error);
        showNotification('An error occurred during transfer', 'error');
      }
    });
  }
  
  // Deposit form
  const depositForm = document.getElementById('deposit-form');
  if (depositForm) {
    depositForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      // Disable the submit button to prevent double submissions
      const submitButton = depositForm.querySelector('button[type="submit"]');
      submitButton.disabled = true;
      submitButton.classList.add('bg-gray-400');
      submitButton.classList.remove('bg-bank-success', 'hover:bg-green-600');
      submitButton.textContent = 'Processing...';
      
      const formData = new FormData(depositForm);
      const amount = parseFloat(formData.get('amount'));
      
      try {
        const response = await fetch('/api/deposit', {
          method: 'POST',
          headers,
          body: JSON.stringify({ amount }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
          showNotification('Deposit request created successfully!', 'success');
          
          // Show download button for cheque
          const chequeNumber = data.cheque_number;
          const resultContainer = document.getElementById('deposit-result');
          
          resultContainer.innerHTML = `
            <div class="mt-4 p-4 border border-green-200 rounded-lg bg-green-50">
              <p class="text-green-700 mb-2">Deposit request created successfully!</p>
              <p class="text-gray-700 mb-2">Cheque Number: <strong>${chequeNumber}</strong></p>
              <p class="text-gray-700 mb-2">Amount: <strong>${formatCurrency(amount)}</strong></p>
              <p class="text-gray-700 mb-4">Your deposit is pending approval by an administrator.</p>
              <a href="/api/deposit/${chequeNumber}/pdf" target="_blank" class="btn btn-primary">
                Download Cheque PDF
              </a>
            </div>
          `;
          
          depositForm.reset();
          
          // Refresh the page after 3 seconds to update history
          setTimeout(() => {
            window.location.reload();
          }, 3000);
        } else {
          showNotification(data.detail || 'Deposit request failed', 'error');
          
          // Re-enable the submit button on error
          submitButton.disabled = false;
          submitButton.classList.remove('bg-gray-400');
          submitButton.classList.add('bg-bank-success', 'hover:bg-green-600');
          submitButton.textContent = 'Request Deposit';
        }
      } catch (error) {
        console.error('Deposit error:', error);
        showNotification('An error occurred during deposit request', 'error');
        
        // Re-enable the submit button on error
        submitButton.disabled = false;
        submitButton.classList.remove('bg-gray-400');
        submitButton.classList.add('bg-bank-success', 'hover:bg-green-600');
        submitButton.textContent = 'Request Deposit';
      }
    });
  }
  
  // Admin: Approve/reject deposit
  const depositButtons = document.querySelectorAll('[data-deposit-action]');
  depositButtons.forEach(button => {
    button.addEventListener('click', async function(e) {
      // Prevent double clicks
      if (this.disabled) return;
      
      // Disable the button to prevent double submissions
      this.disabled = true;
      const originalText = this.textContent.trim();
      this.textContent = 'Processing...';
      
      const depositId = this.dataset.depositId;
      const action = this.dataset.depositAction;
      
      try {
        const response = await fetch(`/api/admin/deposit/${depositId}/status`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ status: action }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
          showNotification(`Deposit ${action} successfully!`, 'success');
          
          // Refresh the page after a short delay
          setTimeout(() => {
            window.location.reload();
          }, 2000);
        } else {
          showNotification(data.detail || `Failed to ${action} deposit`, 'error');
          // Re-enable the button on error
          this.disabled = false;
          this.textContent = originalText;
        }
      } catch (error) {
        console.error('Deposit action error:', error);
        showNotification(`An error occurred while ${action}ing deposit`, 'error');
        // Re-enable the button on error
        this.disabled = false;
        this.textContent = originalText;
      }
    });
  });
  
  // Admin: Approve/reject withdrawal
  const withdrawalButtons = document.querySelectorAll('[data-withdrawal-action]');
  withdrawalButtons.forEach(button => {
    button.addEventListener('click', async function(e) {
      // Prevent double clicks
      if (this.disabled) return;
      
      // Disable the button to prevent double submissions
      this.disabled = true;
      const originalText = this.textContent.trim();
      this.textContent = 'Processing...';
      
      const withdrawalId = this.dataset.withdrawalId;
      const action = this.dataset.withdrawalAction;
      
      try {
        const response = await fetch(`/api/admin/withdraw/${withdrawalId}/status`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ status: action }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
          showNotification(`Withdrawal ${action} successfully!`, 'success');
          
          // Refresh the page after a short delay
          setTimeout(() => {
            window.location.reload();
          }, 2000);
        } else {
          showNotification(data.detail || `Failed to ${action} withdrawal`, 'error');
          // Re-enable the button on error
          this.disabled = false;
          this.textContent = originalText;
        }
      } catch (error) {
        console.error('Withdrawal action error:', error);
        showNotification(`An error occurred while ${action}ing withdrawal`, 'error');
        // Re-enable the button on error
        this.disabled = false;
        this.textContent = originalText;
      }
    });
  });
  
  // HTMX event listeners
  document.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id === 'quick-result') {
      if (evt.detail.xhr.status === 200 || evt.detail.xhr.status === 201) {
        try {
          const responseData = JSON.parse(evt.detail.xhr.responseText);
          if (responseData.message) {
            showNotification(responseData.message, 'success');
          }
        } catch (e) {
          // If not JSON, then it's HTML result, no need to show additional notification
        }
      }
    }
  });
  
  document.addEventListener('htmx:responseError', function(evt) {
    try {
      const responseData = JSON.parse(evt.detail.xhr.responseText);
      if (responseData.detail) {
        showNotification(responseData.detail, 'error');
      } else {
        showNotification('An error occurred', 'error');
      }
    } catch (e) {
      showNotification('An error occurred', 'error');
    }
  });
  
  // Global styles for animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(-10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .animate-fadeIn {
      animation: fadeIn 0.3s ease-out forwards;
    }
    .opacity-0 {
      opacity: 0;
      transition: opacity 0.3s ease-out;
    }
  `;
  document.head.appendChild(style);
}); 