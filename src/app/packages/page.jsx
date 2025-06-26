// 'use client';

// import { useState, useEffect } from 'react';
// import Navbar from '../../components/Navbar';
// import { useRouter } from 'next/navigation';
// import PackageCard from '../../components/PackageCard';
// import PhoneInput from '../../components/PhoneInput';
// import { getPackages, getCurrentUser, getPaymentHistory } from '../../services/api';

// export default function Packages() {
//   const [packages, setPackages] = useState([]);
//   const [phoneNumber, setPhoneNumber] = useState('');
//   const [user, setUser] = useState(null);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);
//   const  router = useRouter();
//   const [paymentHistory, setPaymentHistory] = useState([]);

//   // CHANGED: Separate package loading from auth checks
// useEffect(() => {
//   const fetchPackages = async () => {
//     try {
//       const packageData = await getPackages();
//       setPackages(packageData.packages || []);
//     } catch (err) {
//       setError(err.message || 'Failed to load packages');
//     }
//   };

//   const fetchUserData = async () => {
//     try {
//       const [userData, historyData] = await Promise.all([
//         getCurrentUser(),
//         getPaymentHistory()
//       ]);
//       setUser(userData);
//       setPaymentHistory(historyData.transactions || []);
//     } catch (err) {
//       // Silent handling for unauthorized users
//       if (err.status !== 401) {
//         setError(err.message || 'Failed to load user data');
//       }
//     } finally {
//       setLoading(false);
//     }
//   };

//   fetchPackages();
//   fetchUserData();
// }, [router]);


//   const handlePaymentInitiated = (transactionId) => {
//     console.log('Payment initiated:', transactionId);
//   };

//   if (loading) {
//     return (
//       <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
//         <p className="text-gray-900 dark:text-white">Loading...</p>
//       </div>
//     );
//   }

//   if (error) {
//     return (
//       <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
//         <p className="text-red-500 dark:text-red-400">{error}</p>
//       </div>
//     );
//   }

//   return (
//     <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
//       <Navbar />
//       <div className="container mx-auto py-12">
//         <h1 className="text-3xl font-bold mb-8 text-center text-gray-900 dark:text-white">
//           Choose a Package
//         </h1>
//         {!user && (
//           <div className="max-w-md mx-auto mb-8 bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
//             <PhoneInput
//               value={phoneNumber}
//               onChange={setPhoneNumber}
//               placeholder="Enter your phone number to proceed"
//             />
//           </div>
//         )}
//         <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
//           {packages.map((pkg) => (
//             <PackageCard
//               key={pkg.id}
//               pkg={pkg}
//               phoneNumber={phoneNumber}
//               onPaymentInitiated={handlePaymentInitiated}
//             />
//           ))}
//         </div>
//       </div>
//     </div>
//   );
// }
'use client';

import { useState, useEffect } from 'react';
import Navbar from '../../components/Navbar';
import { useRouter } from 'next/navigation';
import PackageCard from '../../components/PackageCard';
import PhoneInput from '../../components/PhoneInput';
import { getPackages, getCurrentUser, getPaymentHistory } from '../../services/api';

export default function Packages() {
  const [packages, setPackages] = useState([]);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const router = useRouter();
  const [paymentHistory, setPaymentHistory] = useState([]);

  useEffect(() => {
    const fetchPackages = async () => {
      try {
        const packageData = await getPackages();
        setPackages(packageData.packages || []);
      } catch (err) {
        setError(err.message || 'Failed to load packages');
      }
    };

    const fetchUserData = async () => {
      try {
        const userData = await getCurrentUser();
        setUser(userData);
        // Only fetch payment history if user is authenticated
        const historyData = await getPaymentHistory();
        setPaymentHistory(historyData.transactions || []);
      } catch (err) {
        // Silent handling for unauthorized/not found users
        if (err.status === 401 || err.status === 404) {
          setUser(null);
          setPaymentHistory([]); // Clear payment history if user is not logged in
        } else {
          setError(err.message || 'Failed to load user data');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPackages();
    fetchUserData();
  }, [router]);

  const handlePaymentInitiated = (transactionId) => {
    console.log('Payment initiated:', transactionId);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
        <p className="text-gray-900 dark:text-white">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
        <p className="text-red-500 dark:text-red-400">{error}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <Navbar />
      <div className="container mx-auto py-12">
        <h1 className="text-3xl font-bold mb-8 text-center text-gray-900 dark:text-white">
          Choose a Package
        </h1>
        {!user && (
          <div className="max-w-md mx-auto mb-8 bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
            <PhoneInput
              value={phoneNumber}
              onChange={setPhoneNumber}
              placeholder="Enter your phone number to proceed"
            />
          </div>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {packages.map((pkg) => (
            <PackageCard
              key={pkg.id}
              pkg={pkg}
              phoneNumber={phoneNumber}
              onPaymentInitiated={handlePaymentInitiated}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
