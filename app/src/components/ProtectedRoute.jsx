'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function ProtectedRoute({ children }) {
  const [hasAccess, setHasAccess] = useState(null);
  const router = useRouter();

  useEffect(() => {
    const checkAccess = async () => {
      try {
        await fetch('http://localhost:5000/api/payments/check-access', {
          credentials: 'include',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token') || ''}`,
            'X-CSRF-TOKEN': localStorage.getItem('admin_csrf') || '',
          },
        });
        setHasAccess(true);
      } catch (err) {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_csrf');
        setHasAccess(false);
        router.push('/packages');
      }
    };
    checkAccess();
  }, [router]);

  if (hasAccess === null) {
    return <div>Loading...</div>;
  }

  if (!hasAccess) {
    return null;
  }

  return children;
}