import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { SearchIcon, FilterIcon, MapPinIcon, CalendarIcon, ClockIcon, StarIcon } from 'lucide-react';
import { opportunities as allOpportunities } from '../utils/dummyData';
export const Opportunities = () => {
  const [opportunities, setOpportunities] = useState(allOpportunities);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const [filtersVisible, setFiltersVisible] = useState(false);
  // Feature opportunity (in a real app, this would be selected based on criteria or set by admin)
  const featuredOpportunity = allOpportunities[4]; // Using Research Assistant as featured
  // Filter opportunities based on search term and filters
  useEffect(() => {
    let filtered = allOpportunities;
    if (searchTerm) {
      filtered = filtered.filter(opp => opp.title.toLowerCase().includes(searchTerm.toLowerCase()) || opp.organization.toLowerCase().includes(searchTerm.toLowerCase()) || opp.description.toLowerCase().includes(searchTerm.toLowerCase()));
    }
    if (selectedCategory) {
      filtered = filtered.filter(opp => opp.category === selectedCategory);
    }
    if (selectedType) {
      filtered = filtered.filter(opp => opp.type === selectedType);
    }
    if (selectedLocation) {
      filtered = filtered.filter(opp => opp.location.includes(selectedLocation));
    }
    // Sort opportunities
    switch (sortBy) {
      case 'newest':
        filtered = [...filtered].sort((a, b) => b.id - a.id);
        break;
      case 'deadline':
        filtered = [...filtered].sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime());
        break;
      case 'hours':
        filtered = [...filtered].sort((a, b) => {
          const aHours = parseInt(a.hours.split('-')[0]) || 0;
          const bHours = parseInt(b.hours.split('-')[0]) || 0;
          return aHours - bHours;
        });
        break;
      default:
        break;
    }
    setOpportunities(filtered);
  }, [searchTerm, selectedCategory, selectedType, selectedLocation, sortBy]);
  // Get unique categories, types, and locations for filters
  const categories = [...new Set(allOpportunities.map(opp => opp.category))];
  const types = [...new Set(allOpportunities.map(opp => opp.type))];
  const locations = [...new Set(allOpportunities.map(opp => opp.location.split(',')[0].trim()))];
  return <div className="bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-3xl font-extrabold text-gray-900">
            Find Opportunities
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            Discover internships and volunteer positions that match your
            interests
          </p>
        </div>
        {/* Featured Opportunity */}
        <div className="mt-8">
          <div className="relative bg-white rounded-lg shadow-lg overflow-hidden border-2 border-blue-500">
            <div className="absolute top-4 right-4 bg-blue-500 text-white px-3 py-1 rounded-full flex items-center">
              <StarIcon className="h-4 w-4 mr-1" />
              <span className="text-sm font-medium">Featured</span>
            </div>
            <div className="md:flex">
              <div className="md:flex-shrink-0 md:w-64">
                <img className="h-48 w-full object-cover md:h-full" src={featuredOpportunity.image} alt={featuredOpportunity.title} />
              </div>
              <div className="p-6 flex flex-col justify-between">
                <div>
                  <div className="flex space-x-2 mb-2">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {featuredOpportunity.type}
                    </span>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {featuredOpportunity.category}
                    </span>
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-1">
                    {featuredOpportunity.title}
                  </h2>
                  <p className="text-base font-medium text-gray-500 mb-3">
                    {featuredOpportunity.organization}
                  </p>
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                    {featuredOpportunity.description}
                  </p>
                  <div className="grid grid-cols-2 gap-2 text-sm text-gray-500">
                    <div className="flex items-center">
                      <MapPinIcon className="h-4 w-4 mr-1" />
                      <span>{featuredOpportunity.location}</span>
                    </div>
                    <div className="flex items-center">
                      <CalendarIcon className="h-4 w-4 mr-1" />
                      <span>{featuredOpportunity.date}</span>
                    </div>
                    <div className="flex items-center">
                      <ClockIcon className="h-4 w-4 mr-1" />
                      <span>{featuredOpportunity.hours}</span>
                    </div>
                  </div>
                </div>
                <div className="mt-4">
                  <Link to={`/opportunity/${featuredOpportunity.id}`} className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700">
                    View Details
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="mt-8">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <SearchIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input type="text" className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:text-sm" placeholder="Search for opportunities..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
          </div>
          <div className="mt-4 flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <button type="button" onClick={() => setFiltersVisible(!filtersVisible)} className="flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none mb-3 sm:mb-0">
              <FilterIcon className="h-4 w-4 mr-1" />
              {filtersVisible ? 'Hide Filters' : 'Show Filters'}
            </button>
            <div>
              <select className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md" value={sortBy} onChange={e => setSortBy(e.target.value)}>
                <option value="newest">Sort by: Newest</option>
                <option value="deadline">Sort by: Application Deadline</option>
                <option value="hours">Sort by: Hours (Low to High)</option>
              </select>
            </div>
          </div>
          {filtersVisible && <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <label htmlFor="category-filter" className="block text-sm font-medium text-gray-700">
                  Category
                </label>
                <select id="category-filter" className="mt-1 block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md" value={selectedCategory} onChange={e => setSelectedCategory(e.target.value)}>
                  <option value="">All Categories</option>
                  {categories.map(category => <option key={category} value={category}>
                      {category}
                    </option>)}
                </select>
              </div>
              <div>
                <label htmlFor="type-filter" className="block text-sm font-medium text-gray-700">
                  Type
                </label>
                <select id="type-filter" className="mt-1 block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md" value={selectedType} onChange={e => setSelectedType(e.target.value)}>
                  <option value="">All Types</option>
                  {types.map(type => <option key={type} value={type}>
                      {type}
                    </option>)}
                </select>
              </div>
              <div>
                <label htmlFor="location-filter" className="block text-sm font-medium text-gray-700">
                  Location
                </label>
                <select id="location-filter" className="mt-1 block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md" value={selectedLocation} onChange={e => setSelectedLocation(e.target.value)}>
                  <option value="">All Locations</option>
                  {locations.map(location => <option key={location} value={location}>
                      {location}
                    </option>)}
                </select>
              </div>
            </div>}
        </div>
        <div className="mt-8">
          {opportunities.length > 0 ? <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {opportunities.map(opportunity => <div key={opportunity.id} className="flex flex-col rounded-lg shadow-lg overflow-hidden bg-white">
                  <div className="flex-shrink-0 h-48">
                    <img className="h-full w-full object-cover" src={opportunity.image} alt={opportunity.title} />
                  </div>
                  <div className="flex-1 p-6 flex flex-col justify-between">
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
                      <p className="mt-3 text-sm text-gray-500 line-clamp-3">
                        {opportunity.description.substring(0, 150)}...
                      </p>
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
            </div> : <div className="text-center py-12">
              <SearchIcon className="mx-auto h-12 w-12 text-gray-300" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">
                No opportunities found
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Try adjusting your search or filters to find more opportunities.
              </p>
            </div>}
        </div>
      </div>
    </div>;
};