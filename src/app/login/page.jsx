'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '../../components/Navbar';
import PhoneInput from '../../components/PhoneInput';
import { register, login, checkUser } from '../../services/api';

const IS_DEVELOPMENT = process.env.NODE_ENV === 'development';

export default function Login() {
  const [isRegistering, setIsRegistering] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (!phoneNumber.trim()) {
        throw new Error('Phone number is required');
      }
      if (!password.trim()) {
        throw new Error('Password is required');
      }
      if (password !== confirmPassword) {
        throw new Error('Passwords do not match');
      }
      if (password.length < 8) {
        throw new Error('Password must be at least 8 characters');
      }
      if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        throw new Error('Invalid email format');
      }
      if (IS_DEVELOPMENT) {
        console.log('Registering with:', { phoneNumber, email, password: '[REDACTED]' });
      }
      await register(phoneNumber, email, password, false);
      alert('Registration successful! Please log in.');
      setIsRegistering(false);
    } catch (err) {
      // Log unexpected errors for debugging in development
      if (IS_DEVELOPMENT && ![400, 409, 500, 'Phone number is required', 'Password is required', 'Passwords do not match', 'Password must be at least 8 characters', 'Invalid email format'].includes(err.status || err.message)) {
        console.error('Registration error:', {
          name: err.name || 'Unknown',
          message: err.message || 'Unknown error',
          status: err.status || 'N/A',
          data: err.data || {},
          endpoint: err.config?.endpoint || 'unknown',
          stack: IS_DEVELOPMENT ? err.stack : undefined
        });
      }
  
      let errorMessage;
      switch (true) {
        case err.message === 'Phone number is required':
          errorMessage = 'Please enter a phone number.';
          break;
        case err.message === 'Password is required':
          errorMessage = 'Please enter a password.';
          break;
        case err.message === 'Passwords do not match':
          errorMessage = 'The passwords you entered do not match.';
          break;
        case err.message === 'Password must be at least 8 characters':
          errorMessage = 'Your password must be at least 8 characters long.';
          break;
        case err.message === 'Invalid email format':
          errorMessage = 'Please enter a valid email address.';
          break;
        case err.status === 400 && err.data?.error?.includes('Invalid phone number format'):
          errorMessage = 'Please enter a valid phone number (e.g., +1234567890).';
          break;
        case err.status === 400 && err.data?.error?.includes('Invalid email format'):
          errorMessage = 'Please enter a valid email address.';
          break;
        case err.status === 400 && err.data?.error?.includes('Password must be at least 8 characters'):
          errorMessage = 'Your password must be at least 8 characters long.';
          break;
        case err.status === 400:
          errorMessage = 'Please check your phone number, email, or password and try again.';
          break;
        case err.status === 409:
          errorMessage = 'This phone number or email is already registered. Please log in.';
          break;
        case err.status === 500:
          errorMessage = 'Registration failed due to a server issue. Please try again later.';
          break;
        case err.message?.includes('Failed to fetch'):
          errorMessage = 'Unable to connect to the server. Please check your internet connection.';
          break;
        case err.status === 429:
          errorMessage = 'Too many registration attempts. Please try again in a minute.';
          break;
        default:
          errorMessage = 'An error occurred during registration. Please try again.';
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (!phoneNumber.trim()) {
        throw new Error('Phone number is required');
      }
      if (!password.trim()) {
        throw new Error('Password is required');
      }
      // Check if user exists
      const userCheck = await checkUser(phoneNumber);
      if (!userCheck.exists) {
        setError('Phone number not registered. Please register first.');
        setIsRegistering(true);
        return;
      }

      // Attempt login
      const result = await login(phoneNumber, password);
      if (!result?.access_token) {
        throw new Error('No access token received');
      }
      localStorage.setItem('access_token', result.access_token);
      router.push('/');
    } catch (err) {
      if (IS_DEVELOPMENT && ![400, 401, 403, 404, 'Phone number is required', 'Password is required', 'No access token received'].includes(err.status || err.message)) {
        console.error('Login error:', {
          message: err.message || 'Unknown error',
          status: err.status || 'N/A',
          data: err.data || {},
        });
      }

      let errorMessage;
      switch (true) {
        case err.message === 'Phone number is required':
          errorMessage = 'Please enter a phone number.';
          break;
        case err.message === 'Password is required':
          errorMessage = 'Please enter a password.';
          break;
        case err.message === 'No access token received':
          errorMessage = 'Login failed due to a server issue. Please try again.';
          break;
        case err.status === 400:
          errorMessage = 'Please check your phone number or email and password.';
          break;
        case err.status === 401:
          errorMessage = 'Incorrect phone number or password. Please try again.';
          break;
        case err.status === 403:
          errorMessage = 'Access denied. Please contact support.';
          break;
        case err.status === 404:
          errorMessage = 'User not found. Please register first.';
          break;
        case err.message?.includes('Failed to fetch'):
          errorMessage = 'Unable to connect to the server. Please check your internet connection.';
          break;
        default:
          errorMessage = 'Something went wrong during login. Please try again.';
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <Navbar />
      <div className="container mx-auto py-12 max-w-md">
        <h1 className="text-3xl font-bold mb-8 text-center text-gray-900 dark:text-white">
          {isRegistering ? 'Register' : 'Login'}
        </h1>
        {error && <p className="text-red-500 dark:text-red-400 mb-4 text-center">{error}</p>}

        <form onSubmit={isRegistering ? handleRegister : handleLogin} className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <PhoneInput value={phoneNumber} onChange={setPhoneNumber} />

          {isRegistering && (
            <div className="mb-4">
              <label className="block text-gray-700 dark:text-gray-300 mb-2">Email (optional)</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>
          )}

          <div className="mb-4">
            <label className="block text-gray-700 dark:text-gray-300 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>

          {isRegistering && (
            <div className="mb-4">
              <label className="block text-gray-700 dark:text-gray-300 mb-2">Confirm Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm your password"
                className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-2 rounded ${
              loading ? 'bg-gray-400 dark:bg-gray-500' : 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800'
            } text-white`}
          >
            {loading ? 'Processing...' : isRegistering ? 'Register' : 'Login'}
          </button>

          <p className="mt-4 text-center text-gray-700 dark:text-gray-300">
            {isRegistering ? 'Already have an account?' : 'Don’t have an account?'}{' '}
            <button
              type="button"
              onClick={() => {
                setIsRegistering(!isRegistering);
                setError(null);
              }}
              className="text-blue-600 hover:underline dark:text-blue-400 dark:hover:underline"
            >
              {isRegistering ? 'Login' : 'Register'}
            </button>
          </p>
        </form>
      </div>
    </div>
  );
}
