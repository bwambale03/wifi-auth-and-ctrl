'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import Navbar from '../../components/Navbar';
import { verifyPayment } from '../../services/api';
import { useRouter } from 'next/navigation';

export default function PaymentStatus() {
  const searchParams = useSearchParams();
  const transactionId = searchParams.get('transactionId');
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeLeft, setTimeLeft] = useState(null);
  const router = useRouter();

  useEffect(() => {
    if (!transactionId) {
      setError('Transaction ID not found');
      setLoading(false);
      return;
    }

    const verify = async () => {
      try {
        const data = await verifyPayment(transactionId);
        setStatus(data);
        if (data.expiry) {
          const expiryTime = new Date(data.expiry);
          const updateTimeLeft = () => {
            const now = new Date();
            const timeRemaining = expiryTime - now;
            if (timeRemaining <= 0) {
              setTimeLeft('Expired');
              router.push('/packages'); // Redirect to packages page on expiry
            } else {
              const hours = Math.floor(timeRemaining / (1000 * 60 * 60));
              const minutes = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));
              const seconds = Math.floor((timeRemaining % (1000 * 60)) / 1000);
              setTimeLeft(`${hours}h ${minutes}m ${seconds}s`);
            }
          };
          updateTimeLeft();
          const timer = setInterval(updateTimeLeft, 1000);
          return () => clearInterval(timer);
        }
      } catch (err) {
        setError(err.message || 'Failed to verify payment');
      } finally {
        setLoading(false);
      }
    };

    verify();

    const interval = setInterval(async () => {
      try {
        const data = await verifyPayment(transactionId);
        setStatus(data);
        if (data.status === 'SUCCESSFUL' || data.status === 'FAILED') {
          clearInterval(interval);
        }
      } catch (err) {
        setError(err.message || 'Failed to verify payment');
        clearInterval(interval);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [transactionId, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <p>Verifying payment...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Navbar />
        <div className="container mx-auto py-12 text-center">
          <p className="text-red-500">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-center mb-6 text-gray-900 dark:text-white">
          Payment Status
        </h1>
        <div className="max-w-md mx-auto bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          {status && (
            <div className="text-center">
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                Transaction ID: {status.transaction_id}
              </p>
              <p className={`text-lg mt-2 ${status.status === 'SUCCESSFUL' ? 'text-green-500 dark:text-green-400' : status.status === 'FAILED' ? 'text-red-500 dark:text-red-400' : 'text-yellow-500 dark:text-yellow-400'}`}>
                Status: {status.status}
              </p>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                Amount: {status.amount} EUR
              </p>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                Phone: {status.phone_number}
              </p>
              {status.expiry && (
                <p className="text-gray-600 dark:text-gray-300 mt-2">
                  Access Until: {new Date(status.expiry).toLocaleString()}
                </p>
              )}
              {status.status === 'SUCCESSFUL' && timeLeft && (
                <p className={`text-lg mt-2 ${timeLeft === 'Expired' ? 'text-red-500 dark:text-red-400' : 'text-blue-500 dark:text-blue-400'}`}>
                  Time Left: {timeLeft}
                </p>
              )}
              {status.status === 'SUCCESSFUL' && timeLeft === 'Expired' && (
                <p className="text-red-500 dark:text-red-400 mt-4">
                  Your package has expired. Please purchase a new package to continue.
                </p>
              )}
              {status.status === 'SUCCESSFUL' && (
                <p className="text-green-500 dark:text-green-400 mt-4">
                  Payment successful! You now have access to Wi-Fi.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
