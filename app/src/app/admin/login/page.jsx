'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { adminLoginStep1, adminLoginStep2, storeAuthTokens } from '../../../services/api';
import { jwtDecode } from 'jwt-decode';

export default function AdminLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [tempToken, setTempToken] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const router = useRouter();

  const handleStep1 = async (e) => {
    e.preventDefault();
    setError(null);

    if (!username.trim() || !password.trim()) {
      setError('Username and password are required');
      return;
    }

    setLoading(true);
    try {
      const data = await adminLoginStep1(username, password);
      setTempToken(data.temp_token);
      console.log('Step 1: Temp token received:', data.temp_token);
      setStep(2);
    } catch (err) {
      console.error('Step 1 error:', err);
      if (err.status === 401) {
        setError('Invalid username or password');
      } else if (err.status === 400) {
        setError('Username and password are required');
      } else {
        setError(err.message || 'Login failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleStep2 = async (e) => {
    e.preventDefault();
    setError(null);

    if (!totpCode.trim() || totpCode.length !== 6) {
      setError('Please enter a valid 6-digit code');
      return;
    }

    console.log('Submitting TOTP code:', totpCode, 'Type:', typeof totpCode);
    setLoading(true);
    try {
      const result = await adminLoginStep2(tempToken, totpCode);
      console.log('Step 2: Login response:', result);
      storeAuthTokens(result.access_token, result.csrf_token);
      const decodedToken = jwtDecode(result.access_token);
      console.log('Decoded admin_token:', decodedToken);
      router.push('/admin/dashboard');
    } catch (err) {
      console.error('TOTP verification error:', err, 'Response data:', err.data);
      if (err.status === 401) {
        setError('Invalid TOTP code');
      } else if (err.status === 400) {
        setError('TOTP code is required');
      } else if (err.status === 404) {
        setError('Session expired. Please try logging in again.');
        setStep(1);
      } else {
        setError(err.message || 'Verification failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md">
        <h1 className="text-3xl font-bold mb-6 text-center text-gray-900 dark:text-white">
          Admin Login {step === 2 && <span className="text-sm">(Step 2 of 2)</span>}
        </h1>

        {error && (
          <p className="text-red-500 mb-4 text-center">{error}</p>
        )}

        {step === 1 ? (
          <form onSubmit={handleStep1}>
            <div className="mb-4">
              <label className="block text-gray-700 dark:text-gray-300 mb-2" htmlFor="username">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600"
                required
                disabled={loading}
              />
            </div>
            <div className="mb-6">
              <label className="block text-gray-700 dark:text-gray-300 mb-2" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600"
                required
                disabled={loading}
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-2 rounded flex items-center justify-center ${
                loading ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'
              } text-white`}
            >
              {loading ? (
                <>
                  <svg
                    className="animate-spin h-5 w-5 mr-2 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v8h8a8 8 0 01-16 0z"
                    ></path>
                  </svg>
                  Verifying...
                </>
              ) : (
                'Continue'
              )}
            </button>
          </form>
        ) : (
          <form onSubmit={handleStep2}>
            <div className="mb-6">
              <label className="block text-gray-700 dark:text-gray-300 mb-2" htmlFor="totp">
                TOTP Code
              </label>
              <input
                id="totp"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={totpCode}
                onChange={(e) => {
                  const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                  setTotpCode(value);
                }}
                placeholder="Enter 6-digit code"
                className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 text-center text-xl tracking-widest"
                required
                disabled={loading}
              />
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 text-center">
                Enter the code from your authenticator app
              </p>
            </div>
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-2 rounded flex items-center justify-center ${
                loading ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'
              } text-white`}
            >
              {loading ? (
                <>
                  <svg
                    className="animate-spin h-5 w-5 mr-2 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v8h8a8 8 0 01-16 0z"
                    ></path>
                  </svg>
                  Verifying...
                </>
              ) : (
                'Login'
              )}
            </button>
            <button
              type="button"
              onClick={() => setStep(1)}
              className="mt-4 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
            >
              ← Back to username/password
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
