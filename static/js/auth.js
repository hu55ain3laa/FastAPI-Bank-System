document.addEventListener('DOMContentLoaded', () => {
  // Login form submission
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      // Get form data
      const formData = new FormData(loginForm);
      const username = formData.get('username');
      const password = formData.get('password');
      const rememberMe = formData.get('remember_me') === 'on';
      
      // Clear previous error messages
      const errorMessage = document.getElementById('login-error');
      if (errorMessage) {
        errorMessage.textContent = '';
        errorMessage.classList.add('hidden');
      }
      
      try {
        // Submit login request
        const response = await fetch('/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username, password, remember_me: rememberMe }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
          // Store token in localStorage
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('token_type', data.token_type);
          
          // Set cookie for HTMX and other non-JS requests
          document.cookie = `access_token=Bearer ${data.access_token}; path=/; max-age=${rememberMe ? 604800 : 86400}; SameSite=Lax`;
          
          // Redirect to dashboard
          window.location.href = '/dashboard';
        } else {
          // Show error message
          if (errorMessage) {
            errorMessage.textContent = data.detail || 'Login failed';
            errorMessage.classList.remove('hidden');
          }
        }
      } catch (error) {
        console.error('Login error:', error);
        if (errorMessage) {
          errorMessage.textContent = 'An error occurred during login';
          errorMessage.classList.remove('hidden');
        }
      }
    });
  }
  
  // Registration form submission
  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      // Get form data
      const formData = new FormData(registerForm);
      const username = formData.get('username');
      const password = formData.get('password');
      const passwordConfirm = formData.get('password_confirm');
      
      // Clear previous error messages
      const errorMessage = document.getElementById('register-error');
      if (errorMessage) {
        errorMessage.textContent = '';
        errorMessage.classList.add('hidden');
      }
      
      // Validate passwords match
      if (password !== passwordConfirm) {
        if (errorMessage) {
          errorMessage.textContent = 'Passwords do not match';
          errorMessage.classList.remove('hidden');
        }
        return;
      }
      
      try {
        // Submit registration request
        const response = await fetch('/auth/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username, password }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
          // Show success message and redirect to login page after a short delay
          const successMessage = document.getElementById('register-success');
          if (successMessage) {
            successMessage.textContent = 'Registration successful! Redirecting to login...';
            successMessage.classList.remove('hidden');
          }
          
          setTimeout(() => {
            window.location.href = '/login';
          }, 2000);
        } else {
          // Show error message
          if (errorMessage) {
            errorMessage.textContent = data.detail || 'Registration failed';
            errorMessage.classList.remove('hidden');
          }
        }
      } catch (error) {
        console.error('Registration error:', error);
        if (errorMessage) {
          errorMessage.textContent = 'An error occurred during registration';
          errorMessage.classList.remove('hidden');
        }
      }
    });
  }
  
  // Logout functionality
  const logoutButton = document.getElementById('logout-button');
  if (logoutButton) {
    logoutButton.addEventListener('click', async (e) => {
      e.preventDefault();
      
      try {
        // Submit logout request
        const response = await fetch('/auth/logout', {
          method: 'POST',
        });
        
        // Clear localStorage and cookies
        localStorage.removeItem('access_token');
        localStorage.removeItem('token_type');
        document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
        
        // Redirect to login page
        window.location.href = '/login';
      } catch (error) {
        console.error('Logout error:', error);
      }
    });
  }
  
  // Add Authorization header to all fetch requests
  const originalFetch = window.fetch;
  window.fetch = function(url, options = {}) {
    // Only add auth header to our API endpoints
    if (url.toString().startsWith('/api/')) {
      const token = localStorage.getItem('access_token');
      const tokenType = localStorage.getItem('token_type');
      
      if (token && tokenType) {
        options.headers = options.headers || {};
        if (!options.headers['Authorization']) {
          options.headers['Authorization'] = `${tokenType} ${token}`;
        }
      }
    }
    
    return originalFetch(url, options);
  };
  
  // Add Authorization header to all HTMX requests
  document.addEventListener('htmx:configRequest', function(evt) {
    // Only add auth header to our API endpoints
    if (evt.detail.path.startsWith('/api/')) {
      const token = localStorage.getItem('access_token');
      const tokenType = localStorage.getItem('token_type');
      
      if (token && tokenType) {
        evt.detail.headers['Authorization'] = `${tokenType} ${token}`;
      }
    }
  });
}); 