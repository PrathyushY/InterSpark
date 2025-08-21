import React, { useEffect, useState } from 'react';
import { SearchIcon, FilterIcon, MapPinIcon, UserIcon, BriefcaseIcon } from 'lucide-react';
import { users as allUsers } from '../utils/dummyData';
export const TalentSearch = () => {
  const [users, setUsers] = useState(allUsers);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedInterest, setSelectedInterest] = useState('');
  const [selectedGrade, setSelectedGrade] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [filtersVisible, setFiltersVisible] = useState(false);
  // Get all unique interests, grades, and locations for filters
  const allInterests = [...new Set(allUsers.flatMap(user => user.interests))];
  const grades = [...new Set(allUsers.map(user => user.grade))];
  const locations = [...new Set(allUsers.map(user => user.location.split(',')[0].trim()))];
  // Filter users based on search term and filters
  useEffect(() => {
    let filtered = allUsers;
    if (searchTerm) {
      filtered = filtered.filter(user => user.name.toLowerCase().includes(searchTerm.toLowerCase()) || user.bio.toLowerCase().includes(searchTerm.toLowerCase()) || user.interests.some(interest => interest.toLowerCase().includes(searchTerm.toLowerCase())));
    }
    if (selectedInterest) {
      filtered = filtered.filter(user => user.interests.includes(selectedInterest));
    }
    if (selectedGrade) {
      filtered = filtered.filter(user => user.grade === selectedGrade);
    }
    if (selectedLocation) {
      filtered = filtered.filter(user => user.location.includes(selectedLocation));
    }
    setUsers(filtered);
  }, [searchTerm, selectedInterest, selectedGrade, selectedLocation]);
  return <div className="bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-3xl font-extrabold text-gray-900">Find Talent</h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            Connect with other students to collaborate on projects and
            initiatives
          </p>
        </div>
        <div className="mt-8">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <SearchIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input type="text" className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:text-sm" placeholder="Search by name, interests, or bio..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
          </div>
          <div className="mt-4 flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <button type="button" onClick={() => setFiltersVisible(!filtersVisible)} className="flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none mb-3 sm:mb-0">
              <FilterIcon className="h-4 w-4 mr-1" />
              {filtersVisible ? 'Hide Filters' : 'Show Filters'}
            </button>
          </div>
          {filtersVisible && <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <label htmlFor="interest-filter" className="block text-sm font-medium text-gray-700">
                  Interest
                </label>
                <select id="interest-filter" className="mt-1 block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md" value={selectedInterest} onChange={e => setSelectedInterest(e.target.value)}>
                  <option value="">All Interests</option>
                  {allInterests.map(interest => <option key={interest} value={interest}>
                      {interest}
                    </option>)}
                </select>
              </div>
              <div>
                <label htmlFor="grade-filter" className="block text-sm font-medium text-gray-700">
                  Grade
                </label>
                <select id="grade-filter" className="mt-1 block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md" value={selectedGrade} onChange={e => setSelectedGrade(e.target.value)}>
                  <option value="">All Grades</option>
                  {grades.map(grade => <option key={grade} value={grade}>
                      {grade}
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
          {users.length > 0 ? <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {users.map(user => <div key={user.id} className="bg-white rounded-lg shadow overflow-hidden flex flex-col">
                  <div className="p-6 flex items-center">
                    <div className="h-16 w-16 rounded-full overflow-hidden mr-4">
                      <img className="h-full w-full object-cover" src={user.profileImage} alt={user.name} />
                    </div>
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">
                        {user.name}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {user.grade} • {user.location}
                      </p>
                    </div>
                  </div>
                  <div className="px-6 pb-4 flex-1">
                    <div className="mb-4">
                      <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                        Interests
                      </h4>
                      <div className="flex flex-wrap gap-1">
                        {user.interests.map((interest, index) => <span key={index} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {interest}
                          </span>)}
                      </div>
                    </div>
                    <div className="mb-4">
                      <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                        Bio
                      </h4>
                      <p className="text-sm text-gray-600 line-clamp-3">
                        {user.bio}
                      </p>
                    </div>
                    <div>
                      <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                        Availability
                      </h4>
                      <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-xs text-gray-600">
                        <div>Weekdays: {user.availability.weekdays}</div>
                        <div>Weekends: {user.availability.weekends}</div>
                      </div>
                    </div>
                  </div>
                  <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
                    <button className="w-full flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none">
                      <UserIcon className="h-4 w-4 mr-1" />
                      Connect
                    </button>
                  </div>
                </div>)}
            </div> : <div className="text-center py-12">
              <UserIcon className="mx-auto h-12 w-12 text-gray-300" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">
                No users found
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Try adjusting your search or filters to find more people.
              </p>
            </div>}
        </div>
      </div>
    </div>;
};