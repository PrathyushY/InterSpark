import React from 'react';
import { Link } from 'react-router-dom';
export const Footer = () => {
  return <footer className="bg-white border-t border-gray-200">
      <div className="max-w-7xl mx-auto py-12 px-4 overflow-hidden sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1">
            <span className="text-blue-600 text-xl font-bold">InterSpark</span>
            <p className="mt-2 text-sm text-gray-500">
              Connecting high school students with local opportunities.
            </p>
          </div>
          <div className="col-span-1">
            <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">
              For Students
            </h3>
            <ul className="mt-4 space-y-4">
              <li>
                <Link to="/opportunities" className="text-base text-gray-500 hover:text-gray-900">
                  Find Opportunities
                </Link>
              </li>
              <li>
                <Link to="/signup" className="text-base text-gray-500 hover:text-gray-900">
                  Create Account
                </Link>
              </li>
              <li>
                <Link to="/resources" className="text-base text-gray-500 hover:text-gray-900">
                  Resources
                </Link>
              </li>
            </ul>
          </div>
          <div className="col-span-1">
            <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">
              For Organizations
            </h3>
            <ul className="mt-4 space-y-4">
              <li>
                <Link to="/post-opportunity" className="text-base text-gray-500 hover:text-gray-900">
                  Post Opportunity
                </Link>
              </li>
              <li>
                <Link to="/org-signup" className="text-base text-gray-500 hover:text-gray-900">
                  Register Organization
                </Link>
              </li>
              <li>
                <Link to="/org-resources" className="text-base text-gray-500 hover:text-gray-900">
                  Organization Resources
                </Link>
              </li>
            </ul>
          </div>
          <div className="col-span-1">
            <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">
              About
            </h3>
            <ul className="mt-4 space-y-4">
              <li>
                <Link to="/about" className="text-base text-gray-500 hover:text-gray-900">
                  About Us
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-base text-gray-500 hover:text-gray-900">
                  Contact
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="text-base text-gray-500 hover:text-gray-900">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link to="/terms" className="text-base text-gray-500 hover:text-gray-900">
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>
        </div>
        <div className="mt-8 border-t border-gray-200 pt-8">
          <p className="text-base text-gray-400 text-center">
            &copy; {new Date().getFullYear()} InterSpark. All rights reserved.
          </p>
        </div>
      </div>
    </footer>;
};