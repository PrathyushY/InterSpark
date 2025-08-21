import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { SearchIcon, FilterIcon, BookmarkIcon, ClockIcon, CheckCircleIcon } from 'lucide-react';
export const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('recommended');
  // Mock data for demonstration
  const recommendedOpportunities = [{
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
  }];
  const savedOpportunities = [{
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
  const appliedOpportunities = [{
    id: 4,
    title: 'Youth Mentor',
    organization: 'Community Youth Center',
    location: 'Boston, MA',
    type: 'Volunteer',
    category: 'Education',
    date: 'Fall 2023',
    hours: '5 hrs/week',
    status: 'Pending',
    image: 'https://images.unsplash.com/photo-1529390079861-591de354faf5?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2070&q=80'
  }, {
    id: 5,
    title: 'Research Assistant',
    organization: 'City Science Museum',
    location: 'Seattle, WA',
    type: 'Internship',
    category: 'Science',
    date: 'Summer 2023',
    hours: '20 hrs/week',
    status: 'Confirmed',
    image: 'https://images.unsplash.com/photo-1532094349884-543bc11b234d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2070&q=80'
  }];
  return <div className="bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Welcome, Alex</h1>
            <p className="mt-1 text-sm text-gray-500">
              Find and manage your opportunities
            </p>
          </div>
          <div className="mt-4 md:mt-0">
            <Link to="/profile" className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
              Edit Profile
            </Link>
          </div>
        </div>
        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <SearchIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input type="text" className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:text-sm" placeholder="Search for opportunities..." />
          </div>
          <div className="mt-4 flex items-center justify-between">
            <div className="flex space-x-3">
              <button type="button" className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none">
                <FilterIcon className="h-4 w-4 mr-1" />
                Filter
              </button>
              <select className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md">
                <option>All Categories</option>
                <option>Technology</option>
                <option>Environment</option>
                <option>Education</option>
                <option>Marketing</option>
                <option>Science</option>
              </select>
            </div>
            <div>
              <select className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md">
                <option>Sort by: Newest</option>
                <option>Sort by: Location</option>
                <option>Sort by: Hours</option>
              </select>
            </div>
          </div>
        </div>
        <div className="mt-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button onClick={() => setActiveTab('recommended')} className={`${activeTab === 'recommended' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}>
                Recommended
              </button>
              <button onClick={() => setActiveTab('saved')} className={`${activeTab === 'saved' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}>
                <BookmarkIcon className="h-4 w-4 mr-1" />
                Saved
              </button>
              <button onClick={() => setActiveTab('applied')} className={`${activeTab === 'applied' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}>
                <ClockIcon className="h-4 w-4 mr-1" />
                Applied
              </button>
            </nav>
          </div>
          <div className="mt-6">
            {activeTab === 'recommended' && <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {recommendedOpportunities.map(opportunity => <div key={opportunity.id} className="bg-white rounded-lg shadow overflow-hidden">
                    <div className="h-40 overflow-hidden">
                      <img className="w-full h-full object-cover" src={opportunity.image} alt={opportunity.title} />
                    </div>
                    <div className="p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex space-x-2 mb-2">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {opportunity.type}
                            </span>
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                              {opportunity.category}
                            </span>
                          </div>
                          <h3 className="text-lg font-medium text-gray-900">
                            {opportunity.title}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {opportunity.organization}
                          </p>
                        </div>
                        <button className="text-gray-400 hover:text-blue-500">
                          <BookmarkIcon className="h-5 w-5" />
                        </button>
                      </div>
                      <div className="mt-4 text-sm text-gray-500">
                        <div className="flex items-center mb-1">
                          <span>{opportunity.location}</span>
                        </div>
                        <div className="flex items-center mb-1">
                          <span>{opportunity.date}</span>
                        </div>
                        <div className="flex items-center">
                          <span>{opportunity.hours}</span>
                        </div>
                      </div>
                      <div className="mt-4">
                        <Link to={`/opportunity/${opportunity.id}`} className="text-sm font-medium text-blue-600 hover:text-blue-500">
                          View details →
                        </Link>
                      </div>
                    </div>
                  </div>)}
              </div>}
            {activeTab === 'saved' && <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {savedOpportunities.length > 0 ? savedOpportunities.map(opportunity => <div key={opportunity.id} className="bg-white rounded-lg shadow overflow-hidden">
                      <div className="h-40 overflow-hidden">
                        <img className="w-full h-full object-cover" src={opportunity.image} alt={opportunity.title} />
                      </div>
                      <div className="p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="flex space-x-2 mb-2">
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                {opportunity.type}
                              </span>
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                {opportunity.category}
                              </span>
                            </div>
                            <h3 className="text-lg font-medium text-gray-900">
                              {opportunity.title}
                            </h3>
                            <p className="text-sm text-gray-500">
                              {opportunity.organization}
                            </p>
                          </div>
                          <button className="text-blue-500 hover:text-gray-400">
                            <BookmarkIcon className="h-5 w-5" />
                          </button>
                        </div>
                        <div className="mt-4 text-sm text-gray-500">
                          <div className="flex items-center mb-1">
                            <span>{opportunity.location}</span>
                          </div>
                          <div className="flex items-center mb-1">
                            <span>{opportunity.date}</span>
                          </div>
                          <div className="flex items-center">
                            <span>{opportunity.hours}</span>
                          </div>
                        </div>
                        <div className="mt-4">
                          <Link to={`/opportunity/${opportunity.id}`} className="text-sm font-medium text-blue-600 hover:text-blue-500">
                            View details →
                          </Link>
                        </div>
                      </div>
                    </div>) : <div className="col-span-3 text-center py-12">
                    <BookmarkIcon className="mx-auto h-12 w-12 text-gray-300" />
                    <h3 className="mt-2 text-lg font-medium text-gray-900">
                      No saved opportunities
                    </h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Bookmark opportunities to save them for later.
                    </p>
                  </div>}
              </div>}
            {activeTab === 'applied' && <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {appliedOpportunities.map(opportunity => <div key={opportunity.id} className="bg-white rounded-lg shadow overflow-hidden">
                    <div className="h-40 overflow-hidden relative">
                      <img className="w-full h-full object-cover" src={opportunity.image} alt={opportunity.title} />
                      <div className="absolute top-2 right-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${opportunity.status === 'Confirmed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                          {opportunity.status}
                        </span>
                      </div>
                    </div>
                    <div className="p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex space-x-2 mb-2">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {opportunity.type}
                            </span>
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                              {opportunity.category}
                            </span>
                          </div>
                          <h3 className="text-lg font-medium text-gray-900">
                            {opportunity.title}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {opportunity.organization}
                          </p>
                        </div>
                      </div>
                      <div className="mt-4 text-sm text-gray-500">
                        <div className="flex items-center mb-1">
                          <span>{opportunity.location}</span>
                        </div>
                        <div className="flex items-center mb-1">
                          <span>{opportunity.date}</span>
                        </div>
                        <div className="flex items-center">
                          <span>{opportunity.hours}</span>
                        </div>
                      </div>
                      <div className="mt-4">
                        <Link to={`/opportunity/${opportunity.id}`} className="text-sm font-medium text-blue-600 hover:text-blue-500">
                          View details →
                        </Link>
                      </div>
                    </div>
                  </div>)}
              </div>}
          </div>
        </div>
      </div>
    </div>;
};