import React from 'react';
export const HowItWorks = () => {
  return <div className="bg-white py-12 sm:py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="lg:text-center">
          <h2 className="text-base text-blue-600 font-semibold tracking-wide uppercase">
            How It Works
          </h2>
          <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
            Simple steps to get started
          </p>
        </div>
        <div className="mt-16">
          <div className="space-y-16">
            {/* For Students */}
            <div>
              <h3 className="text-2xl font-bold text-gray-900 mb-6 lg:text-center">
                For Students
              </h3>
              <div className="flex flex-col lg:flex-row gap-8">
                <div className="bg-gray-50 p-6 rounded-lg flex-1">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 text-blue-600 mb-4 mx-auto">
                    <span className="text-lg font-bold">1</span>
                  </div>
                  <h4 className="text-lg font-medium text-gray-900 text-center mb-2">
                    Create an account
                  </h4>
                  <p className="text-gray-500 text-center">
                    Sign up with your email and create your student profile.
                  </p>
                </div>
                <div className="bg-gray-50 p-6 rounded-lg flex-1">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 text-blue-600 mb-4 mx-auto">
                    <span className="text-lg font-bold">2</span>
                  </div>
                  <h4 className="text-lg font-medium text-gray-900 text-center mb-2">
                    Browse opportunities
                  </h4>
                  <p className="text-gray-500 text-center">
                    Search and filter through available internships and
                    volunteer positions.
                  </p>
                </div>
                <div className="bg-gray-50 p-6 rounded-lg flex-1">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 text-blue-600 mb-4 mx-auto">
                    <span className="text-lg font-bold">3</span>
                  </div>
                  <h4 className="text-lg font-medium text-gray-900 text-center mb-2">
                    RSVP to opportunities
                  </h4>
                  <p className="text-gray-500 text-center">
                    Express your interest with a simple RSVP process.
                  </p>
                </div>
              </div>
            </div>
            {/* For Organizations */}
            <div>
              <h3 className="text-2xl font-bold text-gray-900 mb-6 lg:text-center">
                For Organizations
              </h3>
              <div className="flex flex-col lg:flex-row gap-8">
                <div className="bg-gray-50 p-6 rounded-lg flex-1">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 text-blue-600 mb-4 mx-auto">
                    <span className="text-lg font-bold">1</span>
                  </div>
                  <h4 className="text-lg font-medium text-gray-900 text-center mb-2">
                    Register your organization
                  </h4>
                  <p className="text-gray-500 text-center">
                    Create an organization profile with your details and
                    mission.
                  </p>
                </div>
                <div className="bg-gray-50 p-6 rounded-lg flex-1">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 text-blue-600 mb-4 mx-auto">
                    <span className="text-lg font-bold">2</span>
                  </div>
                  <h4 className="text-lg font-medium text-gray-900 text-center mb-2">
                    Post opportunities
                  </h4>
                  <p className="text-gray-500 text-center">
                    Create listings for internships and volunteer positions
                    you're offering.
                  </p>
                </div>
                <div className="bg-gray-50 p-6 rounded-lg flex-1">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 text-blue-600 mb-4 mx-auto">
                    <span className="text-lg font-bold">3</span>
                  </div>
                  <h4 className="text-lg font-medium text-gray-900 text-center mb-2">
                    Manage RSVPs
                  </h4>
                  <p className="text-gray-500 text-center">
                    Review student RSVPs and track interest in your
                    opportunities.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>;
};