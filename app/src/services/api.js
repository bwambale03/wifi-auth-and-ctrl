import { jwtDecode } from 'jwt-decode';

// Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000/api';
const IS_DEVELOPMENT = process.env.NODE_ENV === 'development';
const LOG_REQUESTS = IS_DEVELOPMENT && true;
const LOG_ERRORS = IS_DEVELOPMENT && true;

class ApiError extends Error {
  constructor(message, status, data = {}, config = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status || 'N/A';
    this.data = data;
    this.config = {
      endpoint: config.endpoint || 'unknown',
      method: config.method || 'N/A',
      ...config
    };
  }

  toDebugString() {
    return `[${this.status}] ${this.config.method} ${this.config.endpoint} - ${this.message}`;
  }

  toSerializable() {
    return {
      message: this.message,
      status: this.status,
      data: this.data,
      config: this.config
    };
  }
}

const apiRequest = async (endpoint, method = 'GET', body = null, requiresAuth = false, customHeaders = {}) => {
  const headers = {
    'Content-Type': 'application/json',
    ...customHeaders,
  };

  if (requiresAuth) {
    const adminToken = localStorage.getItem('admin_token');
    if (!adminToken) {
      const error = new ApiError('Authentication token missing', 401, {}, { endpoint, method });
      if (LOG_ERRORS) {
        console.error(error.toDebugString());
      }
      throw error;
    }
    headers['Authorization'] = `Bearer ${adminToken}`;
    if (LOG_REQUESTS) {
      console.debug(`[API] Auth attached to ${method} ${endpoint}`);
    }
  }

  const config = {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
    credentials: 'include',
  };

  try {
    if (LOG_REQUESTS) {
      console.debug(`[API] ${method} ${endpoint}`, {
        headers: {
          ...headers,
          Authorization: headers.Authorization ? 'Bearer [REDACTED]' : undefined
        },
        body: body ? '[REDACTED]' : null
      });
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    let data = {};

    if (response.status !== 204) {
      try {
        data = await response.json();
      } catch (e) {
        data = { error: await response.text() || 'Empty response body' };
      }
    }

    if (!response.ok) {
      const error = new ApiError(
        data.error || `Request failed with status ${response.status}`,
        response.status,
        data,
        { endpoint, method }
      );

      if (![400, 401, 403, 404].includes(response.status) && LOG_ERRORS) {
        console.error(error.toDebugString(), error.toSerializable());
      }
      throw error;
    }

    return response.status === 204 ? {} : data;
  } catch (error) {
    const isExpectedError = error instanceof ApiError && [400, 401, 403, 404].includes(error.status);
    if (!isExpectedError && LOG_ERRORS) {
      const errorData = error instanceof ApiError
        ? error.toSerializable()
        : {
            message: error.message || 'Unknown error',
            ...(IS_DEVELOPMENT && { stack: error.stack })
          };
      console.error(`[API] ${method} ${endpoint} failed:`, errorData);
    }
    throw error;
  }
};

// Authentication APIs
export const register = (phoneNumber, email, password, isAdmin=false) =>
  apiRequest('/auth/register', 'POST', { phone_number: phoneNumber, email, password, is_admin: isAdmin });

export const login = (phoneNumber, password) =>
  apiRequest('/auth/login', 'POST', { phone_number: phoneNumber, password });

export const logout = () =>
  apiRequest('/auth/logout', 'POST');

export const getCurrentUser = () =>
  apiRequest('/auth/me', 'GET', null, true);

export const checkUser = (phoneNumber) =>
  apiRequest('/auth/check-user', 'POST', { phone_number: phoneNumber });

// Admin APIs
export const getCurrentAdmin = () =>
  apiRequest('/admin/me', 'GET', null, true);

export const adminLoginStep1 = (username, password) =>
  apiRequest('/admin/login', 'POST', { username, password });

export const adminLoginStep2 = (tempToken, totpCode) => {
  let csrfToken;
  try {
    csrfToken = jwtDecode(tempToken).csrf;
  } catch (e) {
    const error = new ApiError('Invalid session token', 401);
    if (LOG_ERRORS) console.error(error.toDebugString());
    throw error;
  }

  return apiRequest(
    '/admin/verify-totp',
    'POST',
    { totp_code: String(totpCode) },
    false,
    {
      Authorization: `Bearer ${tempToken}`,
      'X-CSRF-TOKEN': csrfToken
    }
  );
};

// Package APIs
export const getPackages = () =>
  apiRequest('/payments/packages', 'GET', null, false);

export const getPaymentHistory = () =>
  apiRequest('/payments/history', 'GET', null, true);

export const initiatePayment = (phoneNumber, packageId) =>
  apiRequest('/payments/initiate', 'POST', { phone_number: phoneNumber, package_id: packageId });

export const verifyPayment = (transactionId) =>
  apiRequest(`/payments/verify/${transactionId}`, 'POST');

export const generateAccessCodes = (planId, quantity) =>
  apiRequest('/payments/generate-codes', 'POST', { plan_id: planId, quantity }, true);

export const activateAccessCode = (code) =>
  apiRequest('/payments/activate-code', 'POST', { code });

export const checkCodeAccess = (code) =>
  apiRequest(`/payments/check-code-access?code=${code}`, 'GET');

export const startSession = (code) =>
  apiRequest('/payments/start-session', 'POST', { code });

// Admin management APIs
export const getExclusions = () =>
  apiRequest('/admin/exclusions', 'GET', null, true);

export const addExclusion = (exclusion) =>
  apiRequest('/admin/exclusions', 'POST', exclusion, true);

export const deleteExclusion = (exclusionId) =>
  apiRequest(`/admin/exclusions/${exclusionId}`, 'DELETE', null, true);

export const getAllTransactions = () =>
  apiRequest('/admin/transactions', 'GET', null, true);

export const getAllUsers = () =>
  apiRequest('/admin/users', 'GET', null, true);

// Token utilities
export const storeAuthTokens = (accessToken, csrfToken) => {
  localStorage.setItem('admin_token', accessToken);
};

export const clearAuthTokens = () => {
  localStorage.removeItem('admin_token');
};
