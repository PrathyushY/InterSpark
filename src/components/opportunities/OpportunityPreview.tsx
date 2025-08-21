import React from 'react';
import { Link } from 'react-router-dom';
import { MapPinIcon, CalendarIcon, ClockIcon } from 'lucide-react';
export const OpportunityPreview = () => {
  // Sample opportunity data
  const opportunities = [{
    id: 1,
    title: 'Web Development Intern',
    organization: 'TechStart Solutions',
    location: 'San Francisco, CA',
    type: 'Internship',
    category: 'Technology',
    date: 'Summer 2023',
    hours: '15-20 hrs/week',
    image: 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2072&q=80'
  }, {
    id: 2,
    title: 'Environmental Conservation Volunteer',
    organization: 'Green Earth Initiative',
    location: 'Portland, OR',
    type: 'Volunteer',
    category: 'Environment',
    date: 'Ongoing',
    hours: '5-10 hrs/week',
    image: 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2013&q=80'
  }, {
    id: 3,
    title: 'Marketing Assistant',
    organization: 'Bright Ideas Marketing',
    location: 'Chicago, IL',
    type: 'Internship',
    category: 'Marketing',
    date: 'Fall 2023',
    hours: '10-15 hrs/week',
    image: 'https://images.unsplash.com/photo-1551434678-e076c223a692?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2070&q=80'
  }];
  return <div className="bg-white py-12 sm:py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900">
            Featured Opportunities
          </h2>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            Check out these exciting positions available right now
          </p>
        </div>
        <div className="mt-12 grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {opportunities.map(opportunity => <div key={opportunity.id} className="flex flex-col rounded-lg shadow-lg overflow-hidden">
              <div className="flex-shrink-0">
                <img className="h-48 w-full object-cover" src={opportunity.image} alt={opportunity.title} />
              </div>
              <div className="flex-1 bg-white p-6 flex flex-col justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-blue-600">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {opportunity.type}
                    </span>
                    <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {opportunity.category}
                    </span>
                  </p>
                  <Link to={`/opportunity/${opportunity.id}`} className="block mt-2">
                    <p className="text-xl font-semibold text-gray-900">
                      {opportunity.title}
                    </p>
                    <p className="mt-1 text-base text-gray-500">
                      {opportunity.organization}
                    </p>
                  </Link>
                </div>
                <div className="mt-4 text-sm text-gray-500">
                  <div className="flex items-center mb-1">
                    <MapPinIcon className="h-4 w-4 mr-1" />
                    <span>{opportunity.location}</span>
                  </div>
                  <div className="flex items-center mb-1">
                    <CalendarIcon className="h-4 w-4 mr-1" />
                    <span>{opportunity.date}</span>
                  </div>
                  <div className="flex items-center">
                    <ClockIcon className="h-4 w-4 mr-1" />
                    <span>{opportunity.hours}</span>
                  </div>
                </div>
                <div className="mt-6">
                  <Link to={`/opportunity/${opportunity.id}`} className="text-base font-medium text-blue-600 hover:text-blue-500">
                    View details →
                  </Link>
                </div>
              </div>
            </div>)}
        </div>
        <div className="mt-12 text-center">
          <Link to="/opportunities" className="inline-flex items-center px-6 py-3 border border-gray-300 shadow-sm text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
            View all opportunities
          </Link>
        </div>
      </div>
    </div>;
};