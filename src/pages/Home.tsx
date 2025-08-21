import React from 'react';
import { Link } from 'react-router-dom';
import { Hero } from '../components/landing/Hero';
import { Features } from '../components/landing/Features';
import { HowItWorks } from '../components/landing/HowItWorks';
import { OpportunityPreview } from '../components/opportunities/OpportunityPreview';
export const Home = () => {
  return <div className="w-full">
      <Hero />
      <Features />
      <HowItWorks />
      <OpportunityPreview />
      <div className="bg-blue-50 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            Ready to get started?
          </h2>
          <p className="mt-4 text-lg text-gray-500 max-w-2xl mx-auto">
            Join InterSpark today and discover opportunities that will shape
            your future.
          </p>
          <div className="mt-8 flex justify-center">
            <Link to="/signup" className="inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
              Create an account
            </Link>
            <Link to="/opportunities" className="ml-4 inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-blue-600 bg-white hover:bg-gray-50">
              Browse opportunities
            </Link>
          </div>
        </div>
      </div>
    </div>;
};