'use client';

import { useState, useEffect } from 'react';
import Navbar from '../../components/Navbar';
import { getPaymentHistory } from '../../services/api';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await getPaymentHistory();
        setHistory(data.history);
      } catch (err) {
        router.push('/login');
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <ProtectedRoute>
        <div className="min-h-screen bg-gray-100">
        <Navbar />
        <div className="container mx-auto py-12">
            <h1 className="text-3xl font-bold mb-8 text-center">Payment History</h1>
            {history.length === 0 ? (
            <p className="text-center text-gray-600">No payment history available.</p>
            ) : (
            <div className="space-y-4">
                {history.map((tx) => (
                <div key={tx.transaction_id} className="border rounded-lg p-4 shadow-md">
                    <p><strong>Transaction ID:</strong> {tx.transaction_id}</p>
                    <p><strong>Package ID:</strong> {tx.package_id}</p>
                    <p><strong>Amount:</strong> ${tx.amount}</p>
                    <p><strong>Status:</strong> {tx.status}</p>
                    <p><strong>Created At:</strong> {new Date(tx.created_at).toLocaleString()}</p>
                    <p><strong>Expiry:</strong> {tx.expiry ? new Date(tx.expiry).toLocaleString() : 'N/A'}</p>
                </div>
                ))}
            </div>
            )}
        </div>
        </div>
    </ProtectedRoute>
  );
}
