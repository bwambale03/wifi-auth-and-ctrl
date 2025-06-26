'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { generateAccessCodes, getPackages } from '../../../services/api';
import Navbar from '../../../components/Navbar';

export default function GenerateCodes() {
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [codes, setCodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const router = useRouter();

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const packageData = await getPackages();
        setPlans(packageData.packages || []);
        if (packageData.packages && packageData.packages.length > 0) {
          setSelectedPlan(packageData.packages[0].id);
        }
      } catch (err) {
        setError(err.message || 'Failed to load plans');
      }
    };
    fetchPlans();
  }, []);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setCodes([]);
    try {
      console.log('Generating codes with:', { planId: selectedPlan, quantity }); // Debug
      const response = await generateAccessCodes(selectedPlan, quantity);
      console.log('Generate codes response:', response); // Debug
      setCodes(response.codes || []);
    } catch (err) {
      console.error('Generate codes error:', err, 'Status:', err.status, 'Data:', err.data);
      if (err.status === 401) {
        setError('Session expired. Please log in again.');
        setTimeout(() => router.push('/admin/login'), 2000);
      } else {
        setError(err.message || 'Failed to generate codes');
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
        <head>
          <title>Access Codes</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .code-card {
              border: 2px dashed #333;
              padding: 15px;
              margin-bottom: 20px;
              width: 300px;
              text-align: center;
              break-inside: avoid;
              page-break-inside: avoid;
            }
            .code {
              font-size: 28px;
              font-weight: bold;
              letter-spacing: 2px;
              margin: 10px 0;
            }
            .title {
              font-size: 18px;
              font-weight: bold;
              margin-bottom: 10px;
            }
            .instructions {
              font-size: 12px;
              color: #555;
              margin-top: 10px;
            }
            @media print {
              .code-card { margin: 10px auto; }
            }
          </style>
        </head>
        <body>
          <h1 style="text-align: center; margin-bottom: 20px;">Internet Access Codes</h1>
          ${codes.map(code => `
            <div class="code-card">
              <div class="title">Internet Access Voucher</div>
              <div class="code">${code.code}</div>
              <p>Plan: ${code.plan_name}</p>
              <p>Duration: ${code.duration_hours} hours</p>
              <p>Price: $${code.price}</p>
              <p>Status: Valid (Unused)</p>
              <div class="instructions">
                <p>Instructions:</p>
                <p>1. Connect to the Wi-Fi network.</p>
                <p>2. Visit the activation page (e.g., yourdomain.com/activate-code).</p>
                <p>3. Enter this code to activate it.</p>
                <p>4. Your access duration will start when you begin using the internet.</p>
              </div>
            </div>
          `).join('')}
          <script>window.print(); window.close();</script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <Navbar />
      <div className="container mx-auto py-12">
        <h1 className="text-3xl font-bold mb-8 text-center text-gray-900 dark:text-white">
          Generate Access Codes
        </h1>
        <div className="max-w-md mx-auto bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <div className="mb-4">
            <label className="block text-gray-700 dark:text-gray-300 mb-2">
              Select Plan
            </label>
            <select
              value={selectedPlan}
              onChange={(e) => setSelectedPlan(e.target.value)}
              className="w-full p-2 border rounded dark:bg-gray-700 dark:text-white"
            >
              {plans.map((plan) => (
                <option key={plan.id} value={plan.id}>
                  {plan.name} ({plan.duration_hours} hours, ${plan.price})
                </option>
              ))}
            </select>
          </div>
          <div className="mb-4">
            <label className="block text-gray-700 dark:text-gray-300 mb-2">
              Quantity (1-100)
            </label>
            <input
              type="number"
              min="1"
              max="100"
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              className="w-full p-2 border rounded dark:bg-gray-700 dark:text-white"
            />
          </div>
          <button
            onClick={handleGenerate}
            disabled={loading || !selectedPlan || quantity < 1 || quantity > 100}
            className={`w-full py-2 rounded ${
              loading ? 'bg-gray-400 dark:bg-gray-500' : 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800'
            } text-white`}
          >
            {loading ? 'Generating...' : 'Generate Codes'}
          </button>
          {error && <p className="text-red-500 dark:text-red-400 mt-4">{error}</p>}
          {codes.length > 0 && (
            <div className="mt-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Generated Codes
              </h2>
              <button
                onClick={handlePrint}
                className="w-full py-2 rounded bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800 text-white mb-4"
              >
                Print Codes
              </button>
              <div className="space-y-4">
                {codes.map((code, index) => (
                  <div key={index} className="border p-4 rounded dark:border-gray-600">
                    <p className="text-lg font-bold text-gray-900 dark:text-white">{code.code}</p>
                    <p className="text-gray-600 dark:text-gray-300">Plan: {code.plan_name}</p>
                    <p className="text-gray-600 dark:text-gray-300">Duration: {code.duration_hours} hours</p>
                    <p className="text-gray-600 dark:text-gray-300">Price: ${code.price}</p>
                    <p className="text-gray-600 dark:text-gray-300">Status: Unused</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
