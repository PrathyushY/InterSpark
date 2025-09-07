// profile.js - handles profile page interactions
(function () {
    function toggleSaveProfile() {
        const state = window.PROFILE_STATE;
        if (!state) return;
        const btn = document.getElementById('save-profile-btn');
        if (!btn) return;
        const icon = btn.querySelector('i');
        const textSpan = document.getElementById('save-profile-text');
        btn.disabled = true;
        const url = state.isSaved ? `/unsave_profile/${state.profileId}` : `/save_profile/${state.profileId}`;
        fetch(url, {method: 'POST'}).then(r => r.json()).then(data => {
            if (data.success) {
                state.isSaved = !state.isSaved;
                if (state.isSaved) {
                    icon.className = 'fas fa-bookmark mr-2';
                    textSpan.textContent = 'Saved';
                    btn.className = btn.className.replace('bg-white border-gray-300 text-gray-700', 'bg-blue-50 border-blue-300 text-blue-700');
                    showAlert('Profile saved successfully!', 'success');
                } else {
                    icon.className = 'far fa-bookmark mr-2';
                    textSpan.textContent = 'Save Profile';
                    btn.className = btn.className.replace('bg-blue-50 border-blue-300 text-blue-700', 'bg-white border-gray-300 text-gray-700');
                    showAlert('Profile removed from saved list', 'info');
                }
            } else {
                showAlert(data.error || 'Failed to update profile', 'error');
            }
        }).catch(() => showAlert('Error updating profile', 'error')).finally(() => btn.disabled = false);
    }

    window.toggleSaveProfile = toggleSaveProfile;

    function validateProfileForm(e) {
        const cfg = window.PROFILE_EDIT;
        if (!cfg) return true;
        const userType = cfg.userType;
        const fullName = document.getElementById('full_name').value.trim();
        if (!fullName || fullName === 'User') {
            e.preventDefault();
            alert(`Please enter your ${userType === 'student' ? 'full name' : 'organization name'}.`);
            return false;
        }
        if (userType === 'student') {
            const school = document.getElementById('school').value.trim();
            const grade = document.getElementById('grade').value;
            const bio = document.getElementById('bio').value.trim();
            if (!school) {
                e.preventDefault();
                alert('Please enter your school name.');
                return false;
            }
            if (!grade) {
                e.preventDefault();
                alert('Please select your grade.');
                return false;
            }
            if (!bio) {
                e.preventDefault();
                alert('Please write a bio.');
                return false;
            }
        } else if (userType === 'organization') {
            const description = document.getElementById('description')?.value.trim();
            if (!description) {
                e.preventDefault();
                alert('Please write a description of your organization.');
                return false;
            }
        }
        return true;
    }

    // Profile Picture Upload Functions
    function handleProfilePictureUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];
        if (!allowedTypes.includes(file.type)) {
            showAlert('Please select a valid image file (JPEG, PNG, WebP, or GIF)', 'error');
            return;
        }

        // Validate file size (5MB)
        const maxSize = 5 * 1024 * 1024; // 5MB in bytes
        if (file.size > maxSize) {
            showAlert('Image must be smaller than 5MB', 'error');
            return;
        }

        // Show loading state
        showImageUploadLoading(true);

        // Create FormData and upload
        const formData = new FormData();
        formData.append('profile_picture', file);

        fetch('/upload_profile_picture', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update the image display
                    updateProfileImageDisplay(data.url);
                    showAlert('Profile picture updated successfully!', 'success');
                } else {
                    showAlert(data.error || 'Failed to upload image', 'error');
                }
            })
            .catch(error => {
                console.error('Upload error:', error);
                showAlert('Error uploading image. Please try again.', 'error');
            })
            .finally(() => {
                showImageUploadLoading(false);
                // Reset the file input
                event.target.value = '';
            });
    }

    function deleteProfilePicture() {
        if (!confirm('Are you sure you want to delete your profile picture?')) {
            return;
        }

        // Show loading state
        showImageUploadLoading(true);

        fetch('/delete_profile_picture', {
            method: 'POST'
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update the image display to show placeholder
                    updateProfileImageDisplay(null);
                    showAlert('Profile picture deleted successfully!', 'success');
                } else {
                    showAlert(data.error || 'Failed to delete image', 'error');
                }
            })
            .catch(error => {
                console.error('Delete error:', error);
                showAlert('Error deleting image. Please try again.', 'error');
            })
            .finally(() => {
                showImageUploadLoading(false);
            });
    }

    function updateProfileImageDisplay(imageUrl) {
        const profileImage = document.getElementById('avatar-preview');
        const placeholder = document.getElementById('profile-image-placeholder');
        const deleteBtn = document.getElementById('delete-profile-picture-btn');

        if (imageUrl) {
            // Show image
            if (profileImage) {
                profileImage.src = imageUrl;
                profileImage.style.display = 'block';
            } else {
                // Create new image element
                const newImg = document.createElement('img');
                newImg.id = 'avatar-preview';
                newImg.src = imageUrl;
                newImg.alt = 'Profile Picture';
                newImg.className = 'h-20 w-20 rounded-full object-cover border-2 border-gray-200';

                // Replace placeholder with image
                if (placeholder) {
                    placeholder.parentNode.replaceChild(newImg, placeholder);
                }
            }

            // Hide placeholder
            if (placeholder) {
                placeholder.style.display = 'none';
            }

            // Show delete button or create it
            if (deleteBtn) {
                deleteBtn.style.display = 'flex';
            } else {
                // Create delete button
                const newDeleteBtn = document.createElement('button');
                newDeleteBtn.id = 'delete-profile-picture-btn';
                newDeleteBtn.type = 'button';
                newDeleteBtn.onclick = deleteProfilePicture;
                newDeleteBtn.className = 'absolute -top-2 -right-2 h-6 w-6 rounded-full bg-red-500 text-white flex items-center justify-center hover:bg-red-600 transition-colors text-xs';
                newDeleteBtn.title = 'Delete profile picture';
                newDeleteBtn.innerHTML = '<i class="fas fa-times"></i>';

                // Add to the profile image container
                const container = profileImage?.parentNode || placeholder?.parentNode;
                if (container) {
                    container.appendChild(newDeleteBtn);
                }
            }
        } else {
            // Show placeholder
            if (placeholder) {
                placeholder.style.display = 'flex';
            } else {
                // Create placeholder
                const newPlaceholder = document.createElement('div');
                newPlaceholder.id = 'profile-image-placeholder';
                newPlaceholder.className = 'h-20 w-20 rounded-full bg-blue-100 flex items-center justify-center border-2 border-gray-200';
                newPlaceholder.innerHTML = '<i class="fas fa-user text-blue-600 text-2xl"></i>';

                // Replace image with placeholder
                if (profileImage) {
                    profileImage.parentNode.replaceChild(newPlaceholder, profileImage);
                }
            }

            // Hide image
            if (profileImage) {
                profileImage.style.display = 'none';
            }

            // Hide delete button
            if (deleteBtn) {
                deleteBtn.style.display = 'none';
            }
        }
    }

    function showImageUploadLoading(show) {
        const container = document.querySelector('.relative'); // Profile image container
        if (!container) return;

        let loader = container.querySelector('.upload-loader');

        if (show) {
            if (!loader) {
                loader = document.createElement('div');
                loader.className = 'upload-loader absolute inset-0 rounded-full bg-black bg-opacity-50 flex items-center justify-center z-10';
                loader.innerHTML = '<i class="fas fa-spinner fa-spin text-white text-lg"></i>';
                container.appendChild(loader);
            }
            loader.style.display = 'flex';
        } else {
            if (loader) {
                loader.style.display = 'none';
            }
        }
    }

    // Export functions to global scope
    window.handleProfilePictureUpload = handleProfilePictureUpload;
    window.deleteProfilePicture = deleteProfilePicture;
    
    // Add test function
    window.testProfileUpload = function() {
        console.log('Test function called');
        console.log('handleProfilePictureUpload:', typeof window.handleProfilePictureUpload);
    };

    document.addEventListener('DOMContentLoaded', () => {
        const saveBtn = document.getElementById('save-profile-submit-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', validateProfileForm);
        }
    });
})();

