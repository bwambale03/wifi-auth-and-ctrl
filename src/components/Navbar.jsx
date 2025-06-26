'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { getCurrentUser } from '../services/api'; // Only use for user
import { useRouter } from 'next/navigation';

export default function Navbar() {
  const [user, setUser] = useState(null);
  const [darkMode, setDarkMode] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const adminToken = localStorage.getItem('admin_token');
        if (!adminToken) {
          console.log('No admin_token found, skipping user fetch');
          setUser(null);
          return;
        }

        // Check if token is for admin
        const response = await fetch('http://localhost:5000/api/admin/me', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${adminToken}`,
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to fetch user', { cause: { status: response.status } });
        }

        const data = await response.json();
        setUser(data.admin); // Admin data
      } catch (error) {
        if (error.cause?.status === 401 || error.cause?.status === 404) {
          localStorage.removeItem('admin_token');
          localStorage.removeItem('admin_csrf');
          setUser(null);
        } else {
          console.error('User Data Fetch Error:', {
            status: error.cause?.status,
            message: error.message,
            stack: error.stack,
          });
          setUser(null);
        }
      }
    };
    fetchUser();
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const handleLogout = async () => {
    try {
      await fetch('http://localhost:5000/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Logout Error:', {
        message: error.message,
        status: error.status,
      });
    } finally {
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_csrf');
      setUser(null);
      router.push('/login');
    }
  };

  return (
    <nav className="bg-blue-600 p-4 text-white dark:bg-gray-800 dark:text-white">
      <div className="container mx-auto flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold">
          Internet Portal
        </Link>
        <div className="space-x-4 flex items-center">
          <div className="space-x-4 flex items-center">
            <div className="relative group">
              <span className="hover:underline cursor-pointer">Admin</span>
              <div className="absolute hidden group-hover:block bg-white dark:bg-gray-700 text-black dark:text-white shadow-md rounded mt-2">
                <Link 
                  href="/admin/login" 
                  className="block px-4 py-2 hover:bg-gray-200 dark:hover:bg-gray-600"
                >
                  Admin Login
                </Link>
                <Link 
                  href="/admin/generate-codes" 
                  className="block px-4 py-2 hover:bg-gray-200 dark:hover:bg-gray-600"
                >
                  Generate Codes
                </Link>
              </div>
            </div>
            <Link href="/packages" className="hover:underline">
              Packages
            </Link>
            {user ? (
              <>
                <Link href="/history" className="hover:underline">
                  Payment History
                </Link>
                <button onClick={handleLogout} className="hover:underline">
                  Logout ({user.username || user.phone_number})
                </button>
              </>
            ) : (
              <Link href="/login" className="hover:underline">
                Login
              </Link>
            )}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="hover:underline"
            >
              {darkMode ? 'Light Mode' : 'Dark Mode'}
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
