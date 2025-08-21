import React, { useEffect, useState } from 'react';
import { UserIcon, BuildingIcon, MapPinIcon, AtSignIcon, PhoneIcon } from 'lucide-react';
import { EditProfileForm } from '../components/profile/EditProfileForm';
import { users as dummyUsers, UserProfile } from '../utils/dummyData';
export const Profile = () => {
  const [activeTab, setActiveTab] = useState('personal');
  const [isEditing, setIsEditing] = useState(false);
  const [userData, setUserData] = useState<UserProfile>(dummyUsers[0]);
  // In a real app, we would fetch the user's profile from an API
  useEffect(() => {
    // Simulate fetching user data
    // This would be replaced with an actual API call
    const loggedInUserId = 1; // This would come from authentication context
    const user = dummyUsers.find(u => u.id === loggedInUserId);
    if (user) {
      setUserData(user);
    }
  }, []);
  const handleSaveProfile = (updatedProfile: UserProfile) => {
    setUserData(updatedProfile);
    setIsEditing(false);
    // In a real app, we would save the updated profile to the backend
  };
  return <div className="bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
              <div>
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Profile Information
                </h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  Personal details and preferences
                </p>
              </div>
              {!isEditing && <button type="button" onClick={() => setIsEditing(true)} className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                  Edit profile
                </button>}
            </div>
            <div className="border-t border-gray-200">
              {isEditing ? <div className="px-4 py-5 sm:p-6">
                  <EditProfileForm profile={userData} onSave={handleSaveProfile} onCancel={() => setIsEditing(false)} />
                </div> : <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <div className="col-span-1">
                    <div className="flex flex-col items-center">
                      <div className="h-32 w-32 rounded-full overflow-hidden">
                        <img src={userData.profileImage} alt={userData.name} className="h-full w-full object-cover" />
                      </div>
                      <div className="mt-4 text-center">
                        <h2 className="text-xl font-bold text-gray-900">
                          {userData.name}
                        </h2>
                        <p className="text-sm text-gray-500">
                          {userData.school}
                        </p>
                        <p className="text-sm text-gray-500">
                          {userData.grade}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="col-span-2 mt-6 sm:mt-0">
                    <div className="border-b border-gray-200">
                      <nav className="-mb-px flex space-x-8">
                        <button onClick={() => setActiveTab('personal')} className={`${activeTab === 'personal' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}>
                          Personal Info
                        </button>
                        <button onClick={() => setActiveTab('interests')} className={`${activeTab === 'interests' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}>
                          Interests & Availability
                        </button>
                        <button onClick={() => setActiveTab('settings')} className={`${activeTab === 'settings' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}>
                          Account Settings
                        </button>
                      </nav>
                    </div>
                    <div className="mt-6">
                      {activeTab === 'personal' && <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                          <div className="sm:col-span-2">
                            <dt className="text-sm font-medium text-gray-500">
                              Bio
                            </dt>
                            <dd className="mt-1 text-sm text-gray-900">
                              {userData.bio}
                            </dd>
                          </div>
                          <div>
                            <dt className="text-sm font-medium text-gray-500 flex items-center">
                              <AtSignIcon className="h-4 w-4 mr-1 text-gray-400" />
                              Email
                            </dt>
                            <dd className="mt-1 text-sm text-gray-900">
                              {userData.email}
                            </dd>
                          </div>
                          <div>
                            <dt className="text-sm font-medium text-gray-500 flex items-center">
                              <PhoneIcon className="h-4 w-4 mr-1 text-gray-400" />
                              Phone
                            </dt>
                            <dd className="mt-1 text-sm text-gray-900">
                              {userData.phone}
                            </dd>
                          </div>
                          <div>
                            <dt className="text-sm font-medium text-gray-500 flex items-center">
                              <MapPinIcon className="h-4 w-4 mr-1 text-gray-400" />
                              Location
                            </dt>
                            <dd className="mt-1 text-sm text-gray-900">
                              {userData.location}
                            </dd>
                          </div>
                          <div>
                            <dt className="text-sm font-medium text-gray-500 flex items-center">
                              <BuildingIcon className="h-4 w-4 mr-1 text-gray-400" />
                              School
                            </dt>
                            <dd className="mt-1 text-sm text-gray-900">
                              {userData.school}
                            </dd>
                          </div>
                        </dl>}
                      {activeTab === 'interests' && <div className="space-y-6">
                          <div>
                            <h3 className="text-sm font-medium text-gray-500">
                              Interests
                            </h3>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {userData.interests.map((interest, index) => <span key={index} className="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                                  {interest}
                                </span>)}
                            </div>
                          </div>
                          <div>
                            <h3 className="text-sm font-medium text-gray-500">
                              Availability
                            </h3>
                            <dl className="mt-2 grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
                              <div>
                                <dt className="text-xs text-gray-500">
                                  Weekdays
                                </dt>
                                <dd className="mt-1 text-sm text-gray-900">
                                  {userData.availability.weekdays}
                                </dd>
                              </div>
                              <div>
                                <dt className="text-xs text-gray-500">
                                  Weekends
                                </dt>
                                <dd className="mt-1 text-sm text-gray-900">
                                  {userData.availability.weekends}
                                </dd>
                              </div>
                              <div>
                                <dt className="text-xs text-gray-500">
                                  Summer
                                </dt>
                                <dd className="mt-1 text-sm text-gray-900">
                                  {userData.availability.summer}
                                </dd>
                              </div>
                            </dl>
                          </div>
                          <div>
                            <h3 className="text-sm font-medium text-gray-500">
                              Categories of Interest
                            </h3>
                            <div className="mt-2 space-y-2">
                              <div className="relative flex items-start">
                                <div className="flex items-center h-5">
                                  <input id="technology" name="technology" type="checkbox" className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" defaultChecked disabled />
                                </div>
                                <div className="ml-3 text-sm">
                                  <label htmlFor="technology" className="font-medium text-gray-700">
                                    Technology
                                  </label>
                                </div>
                              </div>
                              <div className="relative flex items-start">
                                <div className="flex items-center h-5">
                                  <input id="environment" name="environment" type="checkbox" className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" defaultChecked disabled />
                                </div>
                                <div className="ml-3 text-sm">
                                  <label htmlFor="environment" className="font-medium text-gray-700">
                                    Environment
                                  </label>
                                </div>
                              </div>
                              <div className="relative flex items-start">
                                <div className="flex items-center h-5">
                                  <input id="education" name="education" type="checkbox" className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" disabled />
                                </div>
                                <div className="ml-3 text-sm">
                                  <label htmlFor="education" className="font-medium text-gray-700">
                                    Education
                                  </label>
                                </div>
                              </div>
                              <div className="relative flex items-start">
                                <div className="flex items-center h-5">
                                  <input id="marketing" name="marketing" type="checkbox" className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" disabled />
                                </div>
                                <div className="ml-3 text-sm">
                                  <label htmlFor="marketing" className="font-medium text-gray-700">
                                    Marketing
                                  </label>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>}
                      {activeTab === 'settings' && <div className="space-y-6">
                          <div>
                            <h3 className="text-sm font-medium text-gray-500">
                              Email Preferences
                            </h3>
                            <div className="mt-2 space-y-4">
                              <div className="relative flex items-start">
                                <div className="flex items-center h-5">
                                  <input id="new-opportunities" name="new-opportunities" type="checkbox" className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" defaultChecked />
                                </div>
                                <div className="ml-3 text-sm">
                                  <label htmlFor="new-opportunities" className="font-medium text-gray-700">
                                    New Opportunity Alerts
                                  </label>
                                  <p className="text-gray-500">
                                    Receive emails when new opportunities
                                    matching your interests are posted.
                                  </p>
                                </div>
                              </div>
                              <div className="relative flex items-start">
                                <div className="flex items-center h-5">
                                  <input id="rsvp-updates" name="rsvp-updates" type="checkbox" className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" defaultChecked />
                                </div>
                                <div className="ml-3 text-sm">
                                  <label htmlFor="rsvp-updates" className="font-medium text-gray-700">
                                    RSVP Status Updates
                                  </label>
                                  <p className="text-gray-500">
                                    Receive emails when your RSVP status
                                    changes.
                                  </p>
                                </div>
                              </div>
                            </div>
                          </div>
                          <div>
                            <h3 className="text-sm font-medium text-gray-500">
                              Account Security
                            </h3>
                            <div className="mt-2 space-y-4">
                              <button type="button" className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                                Change Password
                              </button>
                              <button type="button" className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                                Privacy Settings
                              </button>
                            </div>
                          </div>
                        </div>}
                    </div>
                  </div>
                </div>}
            </div>
          </div>
        </div>
      </div>
    </div>;
};