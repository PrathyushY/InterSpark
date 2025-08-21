import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { MenuIcon, XIcon, UserIcon } from 'lucide-react';
interface NavbarProps {
  isLoggedIn: boolean;
  onLogout: () => void;
}
export const Navbar = ({
  isLoggedIn,
  onLogout
}: NavbarProps) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  return <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex-shrink-0 flex items-center">
              <span className="text-blue-600 text-xl font-bold">
                InterSpark
              </span>
            </Link>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <Link to="/" className="border-transparent text-gray-500 hover:border-blue-500 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                Home
              </Link>
              <Link to="/opportunities" className="border-transparent text-gray-500 hover:border-blue-500 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                Opportunities
              </Link>
              <Link to="/talent" className="border-transparent text-gray-500 hover:border-blue-500 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                Find Talent
              </Link>
              <Link to="/about" className="border-transparent text-gray-500 hover:border-blue-500 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                About
              </Link>
            </div>
          </div>
          <div className="hidden sm:ml-6 sm:flex sm:items-center">
            {isLoggedIn ? <div className="flex items-center space-x-4">
                <Link to="/dashboard" className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium">
                  Dashboard
                </Link>
                <div className="relative">
                  <Link to="/profile" className="flex items-center">
                    <span className="sr-only">Open user menu</span>
                    <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                      <UserIcon className="h-5 w-5 text-blue-600" />
                    </div>
                  </Link>
                </div>
                <button onClick={onLogout} className="border border-gray-300 text-gray-700 px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-50">
                  Log out
                </button>
              </div> : <div className="flex items-center space-x-4">
                <Link to="/login" className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium">
                  Log in
                </Link>
                <Link to="/signup" className="bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700">
                  Sign up
                </Link>
              </div>}
          </div>
          <div className="-mr-2 flex items-center sm:hidden">
            <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none">
              <span className="sr-only">Open main menu</span>
              {isMenuOpen ? <XIcon className="block h-6 w-6" /> : <MenuIcon className="block h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>
      {isMenuOpen && <div className="sm:hidden">
          <div className="pt-2 pb-3 space-y-1">
            <Link to="/" className="block px-3 py-2 text-base font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-700">
              Home
            </Link>
            <Link to="/opportunities" className="block px-3 py-2 text-base font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-700">
              Opportunities
            </Link>
            <Link to="/talent" className="block px-3 py-2 text-base font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-700">
              Find Talent
            </Link>
            <Link to="/about" className="block px-3 py-2 text-base font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-700">
              About
            </Link>
          </div>
          <div className="pt-4 pb-3 border-t border-gray-200">
            {isLoggedIn ? <div>
                <div className="flex items-center px-4">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                      <UserIcon className="h-6 w-6 text-blue-600" />
                    </div>
                  </div>
                  <div className="ml-3">
                    <div className="text-base font-medium text-gray-800">
                      Student Name
                    </div>
                    <div className="text-sm font-medium text-gray-500">
                      student@example.com
                    </div>
                  </div>
                </div>
                <div className="mt-3 space-y-1">
                  <Link to="/dashboard" className="block px-4 py-2 text-base font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-700">
                    Dashboard
                  </Link>
                  <Link to="/profile" className="block px-4 py-2 text-base font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-700">
                    Your Profile
                  </Link>
                  <button onClick={onLogout} className="block w-full text-left px-4 py-2 text-base font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-700">
                    Log out
                  </button>
                </div>
              </div> : <div className="mt-3 space-y-1">
                <Link to="/login" className="block px-4 py-2 text-base font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-700">
                  Log in
                </Link>
                <Link to="/signup" className="block px-4 py-2 text-base font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-700">
                  Sign up
                </Link>
              </div>}
          </div>
        </div>}
    </nav>;
};