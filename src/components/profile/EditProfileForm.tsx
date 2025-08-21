import React, { useState } from 'react';
import { UserProfile } from '../../utils/dummyData';
interface EditProfileFormProps {
  profile: UserProfile;
  onSave: (updatedProfile: UserProfile) => void;
  onCancel: () => void;
}
export const EditProfileForm = ({
  profile,
  onSave,
  onCancel
}: EditProfileFormProps) => {
  const [formData, setFormData] = useState({
    name: profile.name,
    email: profile.email,
    phone: profile.phone,
    location: profile.location,
    school: profile.school,
    grade: profile.grade,
    bio: profile.bio,
    interests: [...profile.interests],
    availability: {
      weekdays: profile.availability.weekdays,
      weekends: profile.availability.weekends,
      summer: profile.availability.summer
    }
  });
  const [newInterest, setNewInterest] = useState('');
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const {
      name,
      value
    } = e.target;
    if (name.includes('.')) {
      // Handle nested fields (availability)
      const [parent, child] = name.split('.');
      setFormData({
        ...formData,
        [parent]: {
          ...((formData as any)[parent] as object),
          [child]: value
        }
      });
    } else {
      setFormData({
        ...formData,
        [name]: value
      });
    }
  };
  const handleAddInterest = () => {
    if (newInterest && !formData.interests.includes(newInterest)) {
      setFormData({
        ...formData,
        interests: [...formData.interests, newInterest]
      });
      setNewInterest('');
    }
  };
  const handleRemoveInterest = (interest: string) => {
    setFormData({
      ...formData,
      interests: formData.interests.filter(item => item !== interest)
    });
  };
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      ...profile,
      ...formData
    });
  };
  return <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 gap-y-6 sm:grid-cols-2 sm:gap-x-4">
        <div className="sm:col-span-2">
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Full name
          </label>
          <div className="mt-1">
            <input type="text" name="name" id="name" value={formData.name} onChange={handleChange} className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md" />
          </div>
        </div>
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Email address
          </label>
          <div className="mt-1">
            <input type="email" name="email" id="email" value={formData.email} onChange={handleChange} className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md" />
          </div>
        </div>
        <div>
          <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
            Phone
          </label>
          <div className="mt-1">
            <input type="tel" name="phone" id="phone" value={formData.phone} onChange={handleChange} className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md" />
          </div>
        </div>
        <div>
          <label htmlFor="location" className="block text-sm font-medium text-gray-700">
            Location
          </label>
          <div className="mt-1">
            <input type="text" name="location" id="location" value={formData.location} onChange={handleChange} className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md" />
          </div>
        </div>
        <div>
          <label htmlFor="school" className="block text-sm font-medium text-gray-700">
            School
          </label>
          <div className="mt-1">
            <input type="text" name="school" id="school" value={formData.school} onChange={handleChange} className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md" />
          </div>
        </div>
        <div>
          <label htmlFor="grade" className="block text-sm font-medium text-gray-700">
            Grade
          </label>
          <div className="mt-1">
            <select id="grade" name="grade" value={formData.grade} onChange={handleChange} className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md">
              <option value="9th Grade">9th Grade</option>
              <option value="10th Grade">10th Grade</option>
              <option value="11th Grade">11th Grade</option>
              <option value="12th Grade">12th Grade</option>
            </select>
          </div>
        </div>
        <div className="sm:col-span-2">
          <label htmlFor="bio" className="block text-sm font-medium text-gray-700">
            Bio
          </label>
          <div className="mt-1">
            <textarea id="bio" name="bio" rows={4} value={formData.bio} onChange={handleChange} className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md" />
          </div>
          <p className="mt-2 text-sm text-gray-500">
            Brief description about yourself, your interests, and goals.
          </p>
        </div>
        <div className="sm:col-span-2">
          <label htmlFor="interests" className="block text-sm font-medium text-gray-700">
            Interests
          </label>
          <div className="mt-1 flex flex-wrap gap-2">
            {formData.interests.map(interest => <div key={interest} className="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                {interest}
                <button type="button" onClick={() => handleRemoveInterest(interest)} className="ml-1 h-4 w-4 rounded-full flex items-center justify-center text-blue-400 hover:bg-blue-200 hover:text-blue-600 focus:outline-none">
                  <span className="sr-only">Remove {interest}</span>
                  <span aria-hidden="true">&times;</span>
                </button>
              </div>)}
          </div>
          <div className="mt-2 flex">
            <input type="text" value={newInterest} onChange={e => setNewInterest(e.target.value)} placeholder="Add a new interest" className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md" />
            <button type="button" onClick={handleAddInterest} className="ml-2 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
              Add
            </button>
          </div>
        </div>
        <div>
          <label htmlFor="availability.weekdays" className="block text-sm font-medium text-gray-700">
            Weekday Availability
          </label>
          <div className="mt-1">
            <input type="text" name="availability.weekdays" id="availability.weekdays" value={formData.availability.weekdays} onChange={handleChange} className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md" />
          </div>
        </div>
        <div>
          <label htmlFor="availability.weekends" className="block text-sm font-medium text-gray-700">
            Weekend Availability
          </label>
          <div className="mt-1">
            <input type="text" name="availability.weekends" id="availability.weekends" value={formData.availability.weekends} onChange={handleChange} className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md" />
          </div>
        </div>
        <div className="sm:col-span-2">
          <label htmlFor="availability.summer" className="block text-sm font-medium text-gray-700">
            Summer Availability
          </label>
          <div className="mt-1">
            <input type="text" name="availability.summer" id="availability.summer" value={formData.availability.summer} onChange={handleChange} className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md" />
          </div>
        </div>
      </div>
      <div className="flex justify-end space-x-3">
        <button type="button" onClick={onCancel} className="py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
          Cancel
        </button>
        <button type="submit" className="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
          Save Changes
        </button>
      </div>
    </form>;
};