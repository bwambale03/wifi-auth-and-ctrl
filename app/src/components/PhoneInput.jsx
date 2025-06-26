'use client';

import { useState } from 'react';

export default function PhoneInput({ value, onChange, placeholder = 'Enter phone number' }) {
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const phone = e.target.value;
    onChange(phone);

    // Validate phone number format (+ followed by 10-15 digits)
    if (phone && !/^\+\d{10,15}$/.test(phone)) {
      setError('Phone number must start with + and contain 10-15 digits');
    } else {
      setError(null);
    }
  };

  return (
    <div className="mb-4">
      <input
        type="text"
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
      />
      {error && <p className="text-red-500 dark:text-red-400 text-sm mt-1">{error}</p>}
    </div>
  );
}
