'use client';

import { useState } from 'react';
import Link from 'next/link';
import Navbar from '../components/Navbar';
import { activateAccessCode } from '../services/api';

export default function Home() {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleActivate = async () => {
    if (!code.trim()) {
      setError('Please enter a valid access code');
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const response = await activateAccessCode(code);
      setSuccess('Code activated successfully! Connect to the WiFi network and start your session.');
      setCode('');
    } catch (err) {
      setError(err.message || 'Failed to activate code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 dark:from-gray-800 dark:to-gray-900">
      <Navbar />
      <div className="container mx-auto px-4 py-16 text-center">
        {/* Hero Section */}
        <h1 className="text-5xl md:text-6xl font-extrabold text-white mb-6 animate-fade-in-down">
          Welcome to Gamers Galaxy PubWIFI
        </h1>
        <p className="text-lg md:text-xl text-white mb-8 max-w-2xl mx-auto animate-fade-in-up">
          Unlock lightning-fast WiFi with a single code. Activate your voucher and get connected in seconds!
        </p>

        {/* Voucher Activation Section */}
        <div className="max-w-md mx-auto bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg transform transition-all hover:scale-105">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
            Activate Your WiFi Voucher
          </h2>
          <div className="mb-4">
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="Enter your access code (e.g., ABC123)"
              className="w-full p-3 border rounded-lg dark:bg-gray-700 dark:text-white dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 text-center text-lg tracking-wider"
              disabled={loading}
            />
          </div>
          <button
            onClick={handleActivate}
            disabled={loading || !code.trim()}
            className={`w-full py-3 rounded-lg text-white font-semibold transition-all ${
              loading || !code.trim()
                ? 'bg-gray-400 dark:bg-gray-500 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 animate-pulse'
            }`}
          >
            {loading ? 'Activating...' : 'Activate Bundle'}
          </button>
          {error && (
            <p className="text-red-500 dark:text-red-400 mt-4 animate-shake">{error}</p>
          )}
          {success && (
            <div className="mt-4 p-4 bg-green-100 dark:bg-green-800 rounded-lg animate-fade-in">
              <p className="text-green-700 dark:text-green-300">{success}</p>
              <p className="text-sm text-green-600 dark:text-green-400 mt-2">
                Connect to the WiFi network and your session will start automatically.
              </p>
            </div>
          )}
        </div>

        {/* Call to Action */}
        <div className="mt-12">
          <Link
            href="/packages"
            className="inline-block bg-white text-blue-600 py-3 px-8 rounded-lg font-semibold hover:bg-gray-100 dark:bg-gray-700 dark:text-blue-300 dark:hover:bg-gray-600 transition-all animate-bounce"
          >
            Explore Packages
          </Link>
        </div>
      </div>

      {/* Optional: Add a Footer or Additional Sections */}
      <footer className="bg-gray-900 text-white py-6 text-center">
        <p>&copy; 2025 Gamers Galaxy PubWIFI. All rights reserved.</p>
      </footer>
    </div>
  );
}
