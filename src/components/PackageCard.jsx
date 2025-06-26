'use client';

import { useState } from 'react';
import { initiatePayment } from '../services/api';
import { useRouter } from 'next/navigation';

export default function PackageCard({ pkg, phoneNumber, onPaymentInitiated }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const router = useRouter();

  const handleBuy = async () => {
    if (!phoneNumber) {
      router.push('/login');
      return;
    }
  
    setLoading(true);
    setError(null);
    try {
      const data = await initiatePayment(phoneNumber, pkg.id);
      onPaymentInitiated(data.transaction_id);
      alert(`Payment initiated! Transaction ID: ${data.transaction_id}`);
      router.push(`/payment-status?transactionId=${data.transaction_id}`);
    } catch (err) {
      // Use detailed error message from backend if available
      const errorMessage = err?.data?.error || 
                          err?.message || 
                          'Payment initiation failed. Please try again.';
      setError(errorMessage);
      
      // CHANGED: Enhanced error logging with stringified data
      if (err?.status !== 401 && err?.status !== 404) {
        console.error('Payment Error:', {
          status: err?.status || 'N/A',
          message: err?.message || 'Unknown error',
          data: err?.data ? JSON.stringify(err.data) : 'N/A'
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border rounded-lg p-4 shadow-md hover:shadow-lg transition bg-white dark:bg-gray-800 dark:border-gray-600">
      <h3 className="text-xl font-semibold text-gray-900 dark:text-white">{pkg.name}</h3>
      <p className="text-gray-600 dark:text-gray-300">{pkg.duration_hours} hours</p>
      <p className="text-lg font-bold text-gray-900 dark:text-white">${pkg.price}</p>
      {error && <p className="text-red-500 dark:text-red-400">{error}</p>}
      <button
        onClick={handleBuy}
        disabled={loading}
        className={`mt-2 w-full py-2 rounded ${
          loading ? 'bg-gray-400 dark:bg-gray-500' : 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800'
        } text-white`}
      >
        {loading ? 'Processing...' : 'Buy Now'}
      </button>
    </div>
  );
}
