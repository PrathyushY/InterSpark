import React from 'react';
import { SearchIcon, BriefcaseIcon, UserIcon, BuildingIcon } from 'lucide-react';
export const Features = () => {
  const features = [{
    name: 'Find Opportunities',
    description: 'Browse and search through hundreds of internships and volunteer positions in your local area.',
    icon: SearchIcon
  }, {
    name: 'Build Your Profile',
    description: 'Create a personalized profile to showcase your skills, interests, and availability to organizations.',
    icon: UserIcon
  }, {
    name: 'Apply Directly',
    description: 'RSVP to opportunities directly through the platform with just a few clicks.',
    icon: BriefcaseIcon
  }, {
    name: 'Connect with Organizations',
    description: 'Discover and engage with local businesses, non-profits, and community groups seeking student talent.',
    icon: BuildingIcon
  }];
  return <div className="bg-gray-50 py-12 sm:py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="lg:text-center">
          <h2 className="text-base text-blue-600 font-semibold tracking-wide uppercase">
            Features
          </h2>
          <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
            Everything you need to jumpstart your future
          </p>
          <p className="mt-4 max-w-2xl text-xl text-gray-500 lg:mx-auto">
            InterSpark provides all the tools students and organizations need to
            connect and create meaningful opportunities.
          </p>
        </div>
        <div className="mt-10">
          <dl className="space-y-10 md:space-y-0 md:grid md:grid-cols-2 md:gap-x-8 md:gap-y-10">
            {features.map(feature => <div key={feature.name} className="relative">
                <dt>
                  <div className="absolute flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white">
                    <feature.icon className="h-6 w-6" aria-hidden="true" />
                  </div>
                  <p className="ml-16 text-lg leading-6 font-medium text-gray-900">
                    {feature.name}
                  </p>
                </dt>
                <dd className="mt-2 ml-16 text-base text-gray-500">
                  {feature.description}
                </dd>
              </div>)}
          </dl>
        </div>
      </div>
    </div>;
};