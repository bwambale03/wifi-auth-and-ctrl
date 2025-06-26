'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { activateAccessCode, checkCodeAccess, startSession } from '../../services/api';
import Navbar from '../../components/Navbar';

export default function ActivateCode() {
  const [code, setCode] = useState('');
  const [accessDetails, setAccessDetails] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleActivate = async () => {
    setLoading(true);
    setError(null);
    setAccessDetails(null);
    try {
      const response = await activateAccessCode(code);
      setAccessDetails(response);
      alert(`Code marked as pending. Connect to the internet to start your session.`);
    } catch (err) {
      setError(err.message || 'Failed to activate code');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckAccess = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await checkCodeAccess(code);
      setAccessDetails({
        message: response.message,
        remaining_time: response.remaining_time
      });
    } catch (err) {
      setError(err.message || 'Failed to check access');
      setAccessDetails(null);
    } finally {
      setLoading(false);
    }
  };

  // Simulate the router starting the session (for testing purposes)
  const handleStartSession = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await startSession(code);
      setAccessDetails({
        message: response.message,
        expiry: response.expiry
      });
      alert(`Session started! Expires at: ${response.expiry}`);
    } catch (err) {
      setError(err.message || 'Failed to start session');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <Navbar />
      <div className="container mx-auto py-12">
        <h1 className="text-3xl font-bold mb-8 text-center text-gray-900 dark:text-white">
          Activate Access Code
        </h1>
        <div className="max-w-md mx-auto bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <div className="mb-4">
            <label className="block text-gray-700 dark:text-gray-300 mb-2">
              Enter Access Code
            </label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="Enter your access code"
              className="w-full p-2 border rounded dark:bg-gray-700 dark:text-white"
            />
          </div>
          <div className="flex space-x-4">
            <button
              onClick={handleActivate}
              disabled={loading || !code}
              className={`w-full py-2 rounded ${
                loading ? 'bg-gray-400 dark:bg-gray-500' : 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800'
              } text-white`}
            >
              {loading ? 'Activating...' : 'Activate Code'}
            </button>
            <button
              onClick={handleCheckAccess}
              disabled={loading || !code}
              className={`w-full py-2 rounded ${
                loading ? 'bg-gray-400 dark:bg-gray-500' : 'bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800'
              } text-white`}
            >
              {loading ? 'Checking...' : 'Check Access'}
            </button>
          </div>
          {/* For testing: Simulate the router starting the session */}
          <button
            onClick={handleStartSession}
            disabled={loading || !code}
            className={`w-full py-2 rounded mt-4 ${
              loading ? 'bg-gray-400 dark:bg-gray-500' : 'bg-purple-600 hover:bg-purple-700 dark:bg-purple-700 dark:hover:bg-purple-800'
            } text-white`}
          >
            {loading ? 'Starting...' : 'Start Session (Router Simulation)'}
          </button>
          {error && <p className="text-red-500 dark:text-red-400 mt-4">{error}</p>}
          {accessDetails && (
            <div className="mt-6 p-4 border rounded dark:border-gray-600">
              <p className="text-gray-900 dark:text-white">{accessDetails.message}</p>
              {accessDetails.expiry && (
                <p className="text-gray-600 dark:text-gray-300">
                  Expires at: {accessDetails.expiry}
                </p>
              )}
              {accessDetails.remaining_time && (
                <p className="text-gray-600 dark:text-gray-300">
                  Remaining Time: {accessDetails.remaining_time.toFixed(2)} hours
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
