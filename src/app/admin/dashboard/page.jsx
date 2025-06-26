'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Navbar from '../../../components/Navbar';
import { getExclusions, addExclusion, deleteExclusion, getAllTransactions, getAllUsers } from '../../../services/api';

export default function AdminDashboard() {
  const [exclusions, setExclusions] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [users, setUsers] = useState([]);
  const [newExclusion, setNewExclusion] = useState({
    type: 'PHONE',
    value: '',
    reason: '',
    exclude_from_payment: false,
    exclude_from_connection: false,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const router = useRouter();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const exclusionsData = await getExclusions();
        setExclusions(exclusionsData.exclusions);
        const transactionsData = await getAllTransactions();
        setTransactions(transactionsData.transactions);
        const usersData = await getAllUsers();
        setUsers(usersData.users);
      } catch (err) {
        if (err.message === 'Unauthorized') {
          router.push('/admin/login');
        } else {
          setError(err.message || 'Failed to load data');
        }
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [router]);

  const handleAddExclusion = async (e) => {
    e.preventDefault();
    try {
      const addedExclusion = await addExclusion(newExclusion);
      setExclusions([...exclusions, addedExclusion]);
      setNewExclusion({
        type: 'PHONE',
        value: '',
        reason: '',
        exclude_from_payment: false,
        exclude_from_connection: false,
      });
    } catch (err) {
      if (err.message === 'Unauthorized') {
        router.push('/admin/login');
      } else {
        setError(err.message || 'Failed to add exclusion');
      }
    }
  };

  const handleDeleteExclusion = async (exclusionId) => {
    try {
      await deleteExclusion(exclusionId);
      setExclusions(exclusions.filter((e) => e.id !== exclusionId));
    } catch (err) {
      if (err.message === 'Unauthorized') {
        router.push('/admin/login');
      } else {
        setError(err.message || 'Failed to delete exclusion');
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
        <p className="text-gray-900 dark:text-white">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6 text-center text-gray-900 dark:text-white">
          Admin Dashboard
        </h1>
        {error && <p className="text-red-500 dark:text-red-400 text-center mb-4">{error}</p>}

        {/* Navigation Links */}
        <div className="mb-8 flex justify-center space-x-4">
          <Link
            href="/admin/generate_codes"
            className="bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 transition-all"
          >
            Generate Access Codes
          </Link>
        </div>

        {/* Exclusions Management */}
        <div className="mb-12">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
            Manage Exclusions
          </h2>
          <form
            onSubmit={handleAddExclusion}
            className="mb-6 bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-gray-700 dark:text-gray-300 mb-2">Type</label>
                <select
                  value={newExclusion.type}
                  onChange={(e) => setNewExclusion({ ...newExclusion, type: e.target.value })}
                  className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="PHONE">Phone Number</option>
                  <option value="MAC">MAC Address</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-700 dark:text-gray-300 mb-2">Value</label>
                <input
                  type="text"
                  value={newExclusion.value}
                  onChange={(e) => setNewExclusion({ ...newExclusion, value: e.target.value })}
                  placeholder="Enter phone number or MAC address"
                  className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-gray-700 dark:text-gray-300 mb-2">Reason</label>
                <input
                  type="text"
                  value={newExclusion.reason}
                  onChange={(e) => setNewExclusion({ ...newExclusion, reason: e.target.value })}
                  placeholder="Reason for exclusion"
                  className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
              <div className="flex items-center space-x-4">
                <label className="flex items-center text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={newExclusion.exclude_from_payment}
                    onChange={(e) =>
                      setNewExclusion({ ...newExclusion, exclude_from_payment: e.target.checked })
                    }
                    className="mr-2"
                  />
                  Exclude from Payment
                </label>
                <label className="flex items-center text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={newExclusion.exclude_from_connection}
                    onChange={(e) =>
                      setNewExclusion({
                        ...newExclusion,
                        exclude_from_connection: e.target.checked,
                      })
                    }
                    className="mr-2"
                  />
                  Exclude from Connection
                </label>
              </div>
            </div>
            <button
              type="submit"
              className="mt-4 w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800"
            >
              Add Exclusion
            </button>
          </form>
          <div className="space-y-4">
            {exclusions.map((exclusion) => (
              <div
                key={exclusion.id}
                className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md flex justify-between items-center"
              >
                <div>
                  <p className="text-gray-900 dark:text-white">
                    <strong>Type:</strong> {exclusion.type}
                  </p>
                  <p className="text-gray-900 dark:text-white">
                    <strong>Value:</strong> {exclusion.value}
                  </p>
                  <p className="text-gray-600 dark:text-gray-300">
                    <strong>Reason:</strong> {exclusion.reason || 'N/A'}
                  </p>
                  <p className="text-gray-600 dark:text-gray-300">
                    <strong>Exclude from Payment:</strong> {exclusion.exclude_from_payment ? 'Yes' : 'No'}
                  </p>
                  <p className="text-gray-600 dark:text-gray-300">
                    <strong>Exclude from Connection:</strong> {exclusion.exclude_from_connection ? 'Yes' : 'No'}
                  </p>
                </div>
                <button
                  onClick={() => handleDeleteExclusion(exclusion.id)}
                  className="bg-red-600 text-white py-1 px-3 rounded hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Transactions Overview */}
        <div className="mb-12">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
            Transactions
          </h2>
          <div className="space-y-4">
            {transactions.map((tx) => (
              <div
                key={tx.id}
                className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md"
              >
                <p className="text-gray-900 dark:text-white">
                  <strong>Transaction ID:</strong> {tx.transaction_id}
                </p>
                <p className="text-gray-600 dark:text-gray-300">
                  <strong>Phone:</strong> {tx.phone_number}
                </p>
                <p className="text-gray-600 dark:text-gray-300">
                  <strong>Package ID:</strong> {tx.package_id}
                </p>
                <p className="text-gray-600 dark:text-gray-300">
                  <strong>Amount:</strong> {tx.amount} EUR
                </p>
                <p className="text-gray-600 dark:text-gray-300">
                  <strong>Status:</strong> {tx.status}
                </p>
                <p className="text-gray-600 dark:text-gray-300">
                  <strong>Expiry:</strong> {tx.expiry || 'N/A'}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Users Overview */}
        <div>
          <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
            Users
          </h2>
          <div className="space-y-4">
            {users.map((user) => (
              <div
                key={user.id}
                className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md"
              >
                <p className="text-gray-900 dark:text-white">
                  <strong>Phone Number:</strong> {user.phone_number}
                </p>
                <p className="text-gray-600 dark:text-gray-300">
                  <strong>Email:</strong> {user.email || 'N/A'}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
