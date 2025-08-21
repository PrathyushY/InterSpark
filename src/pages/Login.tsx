import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authenticateUser } from '../utils/dummyData';
interface LoginProps {
  onLogin: () => void;
}
export const Login = ({
  onLogin
}: LoginProps) => {
  const [userType, setUserType] = useState<'student' | 'organization'>('student');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    // Authenticate user with dummy data
    const authResult = authenticateUser(email, password);
    if (authResult) {
      // In a real app, you would store the user info in context or state management
      onLogin();
      navigate('/dashboard');
    } else {
      setError('Invalid email or password. Try using one of our demo accounts.');
    }
  };
  // Demo account info
  const demoAccounts = [{
    type: 'Student',
    email: 'alex@example.com',
    password: 'password123'
  }, {
    type: 'Student',
    email: 'taylor@example.com',
    password: 'password123'
  }, {
    type: 'Organization',
    email: 'contact@techstart.org',
    password: 'orgpassword123'
  }, {
    type: 'Organization',
    email: 'info@greenearthinitiative.org',
    password: 'orgpassword123'
  }];
  return <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Sign in to your account
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Or{' '}
          <Link to="/signup" className="font-medium text-blue-600 hover:text-blue-500">
            create a new account
          </Link>
        </p>
      </div>
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="flex justify-center space-x-4 mb-6">
            <button type="button" className={`px-4 py-2 text-sm font-medium rounded-md ${userType === 'student' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300'}`} onClick={() => setUserType('student')}>
              Student
            </button>
            <button type="button" className={`px-4 py-2 text-sm font-medium rounded-md ${userType === 'organization' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300'}`} onClick={() => setUserType('organization')}>
              Organization
            </button>
          </div>
          {error && <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              {error}
            </div>}
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <div className="mt-1">
                <input id="email" name="email" type="email" autoComplete="email" required value={email} onChange={e => setEmail(e.target.value)} className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
              </div>
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="mt-1">
                <input id="password" name="password" type="password" autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input id="remember-me" name="remember-me" type="checkbox" className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                  Remember me
                </label>
              </div>
              <div className="text-sm">
                <a href="#" className="font-medium text-blue-600 hover:text-blue-500">
                  Forgot your password?
                </a>
              </div>
            </div>
            <div>
              <button type="submit" className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                Sign in
              </button>
            </div>
          </form>
          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">
                  Demo accounts
                </span>
              </div>
            </div>
            <div className="mt-4">
              <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
                <div className="text-sm text-gray-700 mb-3">
                  Use these accounts to test the platform:
                </div>
                <div className="space-y-3 text-xs text-gray-600">
                  {demoAccounts.map((account, index) => <div key={index} className="flex flex-col sm:flex-row sm:justify-between pb-2 border-b border-gray-200 last:border-0 last:pb-0">
                      <div>
                        <span className="font-semibold">{account.type}:</span>{' '}
                        {account.email}
                      </div>
                      <div>
                        <span className="font-semibold">Password:</span>{' '}
                        {account.password}
                      </div>
                    </div>)}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>;
};