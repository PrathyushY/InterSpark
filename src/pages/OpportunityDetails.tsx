import React, { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { MapPinIcon, CalendarIcon, ClockIcon, BuildingIcon, BookmarkIcon, ShareIcon, CheckIcon, ArrowLeftIcon } from 'lucide-react';
export const OpportunityDetails = () => {
  const {
    id
  } = useParams();
  const [isRSVPed, setIsRSVPed] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  // Mock data for demonstration
  const opportunity = {
    id: parseInt(id || '1'),
    title: 'Web Development Intern',
    organization: 'TechStart Solutions',
    location: 'San Francisco, CA',
    type: 'Internship',
    category: 'Technology',
    date: 'Summer 2023 (June 15 - August 15)',
    hours: '15-20 hrs/week',
    deadline: 'May 15, 2023',
    description: "TechStart Solutions is looking for motivated high school students interested in learning web development. As an intern, you'll work alongside our development team to build and maintain websites for our clients. This is a great opportunity to gain hands-on experience in a professional environment while developing valuable skills in HTML, CSS, JavaScript, and more.",
    responsibilities: ['Assist in coding and testing new website features', 'Help maintain and update existing client websites', 'Participate in team meetings and brainstorming sessions', 'Learn modern web development frameworks and techniques', 'Document your work and contribute to project documentation'],
    requirements: ['Interest in computer science and web development', 'Basic understanding of HTML and CSS (JavaScript a plus)', 'Strong problem-solving skills and attention to detail', 'Ability to commit to 15-20 hours per week during the summer', 'Reliable transportation to our office in San Francisco'],
    benefits: ['Hands-on experience with real-world projects', 'Mentorship from experienced developers', 'Exposure to professional work environment', 'Certificate of completion', 'Potential for school credit (check with your school counselor)'],
    image: 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2072&q=80',
    orgLogo: 'https://images.unsplash.com/photo-1549921296-bc643ead1e65?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1150&q=80'
  };
  const handleRSVP = () => {
    setIsRSVPed(!isRSVPed);
    // In a real app, you would send this to your backend
  };
  const handleSave = () => {
    setIsSaved(!isSaved);
    // In a real app, you would send this to your backend
  };
  return <div className="bg-white">
      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <Link to="/dashboard" className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-500">
            <ArrowLeftIcon className="h-4 w-4 mr-1" />
            Back to opportunities
          </Link>
        </div>
        <div className="lg:grid lg:grid-cols-3 lg:gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <div className="relative h-64 sm:h-72 md:h-96 rounded-lg overflow-hidden">
              <img src={opportunity.image} alt={opportunity.title} className="w-full h-full object-cover" />
            </div>
            <div className="mt-6">
              <div className="flex flex-wrap gap-2 mb-4">
                <span className="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  {opportunity.type}
                </span>
                <span className="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                  {opportunity.category}
                </span>
              </div>
              <h1 className="text-3xl font-bold text-gray-900">
                {opportunity.title}
              </h1>
              <div className="mt-2 flex items-center">
                <BuildingIcon className="h-5 w-5 text-gray-400 mr-1" />
                <span className="text-gray-600">
                  {opportunity.organization}
                </span>
              </div>
              <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center">
                  <MapPinIcon className="h-5 w-5 text-gray-400 mr-1" />
                  <span className="text-gray-600">{opportunity.location}</span>
                </div>
                <div className="flex items-center">
                  <CalendarIcon className="h-5 w-5 text-gray-400 mr-1" />
                  <span className="text-gray-600">{opportunity.date}</span>
                </div>
                <div className="flex items-center">
                  <ClockIcon className="h-5 w-5 text-gray-400 mr-1" />
                  <span className="text-gray-600">{opportunity.hours}</span>
                </div>
              </div>
              <div className="mt-8">
                <h2 className="text-xl font-semibold text-gray-900">
                  Description
                </h2>
                <p className="mt-4 text-gray-600">{opportunity.description}</p>
              </div>
              <div className="mt-8">
                <h2 className="text-xl font-semibold text-gray-900">
                  Responsibilities
                </h2>
                <ul className="mt-4 space-y-2">
                  {opportunity.responsibilities.map((item, index) => <li key={index} className="flex items-start">
                      <CheckIcon className="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-600">{item}</span>
                    </li>)}
                </ul>
              </div>
              <div className="mt-8">
                <h2 className="text-xl font-semibold text-gray-900">
                  Requirements
                </h2>
                <ul className="mt-4 space-y-2">
                  {opportunity.requirements.map((item, index) => <li key={index} className="flex items-start">
                      <CheckIcon className="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-600">{item}</span>
                    </li>)}
                </ul>
              </div>
              <div className="mt-8">
                <h2 className="text-xl font-semibold text-gray-900">
                  Benefits
                </h2>
                <ul className="mt-4 space-y-2">
                  {opportunity.benefits.map((item, index) => <li key={index} className="flex items-start">
                      <CheckIcon className="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-600">{item}</span>
                    </li>)}
                </ul>
              </div>
            </div>
          </div>
          {/* Sidebar */}
          <div className="mt-8 lg:mt-0">
            <div className="bg-gray-50 p-6 rounded-lg shadow-sm sticky top-8">
              <div className="flex items-center mb-6">
                <div className="h-12 w-12 rounded-full overflow-hidden bg-gray-200">
                  <img src={opportunity.orgLogo} alt={opportunity.organization} className="h-full w-full object-cover" />
                </div>
                <div className="ml-3">
                  <h3 className="text-lg font-medium text-gray-900">
                    {opportunity.organization}
                  </h3>
                  <Link to="/organization/1" className="text-sm text-blue-600 hover:text-blue-500">
                    View organization
                  </Link>
                </div>
              </div>
              <div className="border-t border-gray-200 pt-4">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm text-gray-500">
                    Application deadline
                  </span>
                  <span className="text-sm font-medium text-gray-900">
                    {opportunity.deadline}
                  </span>
                </div>
                <button onClick={handleRSVP} className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${isRSVPed ? 'bg-green-600 hover:bg-green-700' : 'bg-blue-600 hover:bg-blue-700'} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}>
                  {isRSVPed ? <>
                      <CheckIcon className="h-5 w-5 mr-1" />
                      RSVP Confirmed
                    </> : 'RSVP to this opportunity'}
                </button>
                <div className="mt-4 grid grid-cols-2 gap-4">
                  <button onClick={handleSave} className={`flex items-center justify-center py-2 px-4 border ${isSaved ? 'border-blue-600 text-blue-600' : 'border-gray-300 text-gray-700'} rounded-md shadow-sm text-sm font-medium hover:bg-gray-50`}>
                    <BookmarkIcon className={`h-5 w-5 ${isSaved ? 'fill-blue-600' : ''}`} />
                    <span className="ml-2">{isSaved ? 'Saved' : 'Save'}</span>
                  </button>
                  <button className="flex items-center justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">
                    <ShareIcon className="h-5 w-5" />
                    <span className="ml-2">Share</span>
                  </button>
                </div>
                <div className="mt-6">
                  <h4 className="text-sm font-medium text-gray-900">
                    Questions about this opportunity?
                  </h4>
                  <p className="mt-1 text-sm text-gray-500">
                    Contact the organization directly through their profile
                    page.
                  </p>
                  <Link to="/contact-organization/1" className="mt-4 block text-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100">
                    Contact organization
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>;
};