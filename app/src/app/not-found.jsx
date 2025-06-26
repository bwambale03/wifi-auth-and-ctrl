import Link from 'next/link';
import Navbar from '../components/Navbar';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      <div className="container mx-auto py-12 text-center">
        <h1 className="text-4xl font-bold mb-4">404 - Page Not Found</h1>
        <p className="text-lg text-gray-600 mb-8">
          The page you’re looking for doesn’t exist. Let’s get you back on track!
        </p>
        <Link
          href="/"
          className="inline-block bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700"
        >
          Go to Home
        </Link>
      </div>
    </div>
  );
}