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
        fetch(url, { method: 'POST' }).then(r => r.json()).then(data => {
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

    document.addEventListener('DOMContentLoaded', () => {
        const saveBtn = document.getElementById('save-profile-submit-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', validateProfileForm);
        }
    });

    // Skills bubble functionality
    let currentSkills = [];
    let allowedSkills = [];

    function initializeSkills() {
        if (typeof initialSkills !== 'undefined') {
            currentSkills = Array.isArray(initialSkills) ? [...initialSkills] : [];
        }
        if (typeof skillsMaster !== 'undefined') {
            allowedSkills = Array.isArray(skillsMaster) ? [...skillsMaster] : [];
        }

        const container = document.getElementById('skills-bubble-container');
        const input = document.getElementById('skills-bubble-input');
        const hiddenInput = document.getElementById('skills-hidden-input');

        if (!container || !input || !hiddenInput) return;

        // Render initial skills
        renderSkills();
        updateHiddenInput();

        // Setup input handlers
        input.addEventListener('keydown', handleSkillInput);
        input.addEventListener('input', handleAutocomplete);

        // Hide autocomplete when clicking outside
        document.addEventListener('click', function (e) {
            if (!e.target.closest('#skills-autocomplete-list') && !e.target.closest('#skills-bubble-input')) {
                hideAutocomplete();
            }
        });
    }

    function renderSkills() {
        const container = document.getElementById('skills-bubble-container');
        if (!container) return;

        container.innerHTML = '';
        currentSkills.forEach((skill, index) => {
            const bubble = document.createElement('span');
            bubble.className = 'inline-flex items-center px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-sm font-medium';
            bubble.innerHTML = `
                ${skill}
                <button type="button" class="ml-2 text-blue-600 hover:text-blue-800" onclick="removeSkill(${index})">
                    <i class="fas fa-times text-xs"></i>
                </button>
            `;
            container.appendChild(bubble);
        });
    }

    function addSkill(skill) {
        if (!skill || currentSkills.includes(skill)) return;
        currentSkills.push(skill);
        renderSkills();
        updateHiddenInput();
    }

    async function addSkillWithCreation(skillName) {
        if (!skillName || currentSkills.includes(skillName)) return;

        // If skill is in allowed skills, just add it
        if (allowedSkills.includes(skillName)) {
            addSkill(skillName);
            return;
        }

        // Try to create new skill
        try {
            const response = await fetch('/add_skill', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ skill: skillName })
            });

            const result = await response.json();

            if (result.success) {
                // Add to local allowed skills list
                const formattedSkill = result.skill.name;
                if (!allowedSkills.includes(formattedSkill)) {
                    allowedSkills.push(formattedSkill);
                    allowedSkills.sort();
                }

                // Add the skill
                addSkill(formattedSkill);

                // Show success message
                const input = document.getElementById('skills-bubble-input');
                if (input) {
                    input.placeholder = "Skill added successfully!";
                    setTimeout(() => {
                        input.placeholder = "Type a skill and press Enter...";
                    }, 2000);
                }

            } else {
                // Handle errors
                if (result.error === "Skill already exists") {
                    // If skill exists, use the existing one
                    const existingSkill = result.existing_skill || skillName;
                    if (!allowedSkills.includes(existingSkill)) {
                        allowedSkills.push(existingSkill);
                        allowedSkills.sort();
                    }
                    addSkill(existingSkill);

                    const input = document.getElementById('skills-bubble-input');
                    if (input) {
                        input.placeholder = "Used existing skill";
                        setTimeout(() => {
                            input.placeholder = "Type a skill and press Enter...";
                        }, 2000);
                    }
                } else {
                    alert('Error adding skill: ' + result.error);
                }
            }
        } catch (error) {
            console.error('Error adding skill:', error);
            alert('Error adding skill. Please try again.');
        }
    }

    function removeSkill(index) {
        currentSkills.splice(index, 1);
        renderSkills();
        updateHiddenInput();
    }

    function updateHiddenInput() {
        const hiddenInput = document.getElementById('skills-hidden-input');
        if (hiddenInput) {
            hiddenInput.value = JSON.stringify(currentSkills);
        }
    }

    function handleSkillInput(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const skill = e.target.value.trim();
            if (skill) {
                addSkillWithCreation(skill);
                e.target.value = '';
                hideAutocomplete();
            }
        } else if (e.key === 'Escape') {
            hideAutocomplete();
        }
    }

    function handleAutocomplete(e) {
        const query = e.target.value.trim();
        const queryLower = query.toLowerCase();
        const autocompleteList = document.getElementById('skills-autocomplete-list');

        if (!query || !autocompleteList) {
            hideAutocomplete();
            return;
        }

        const matches = allowedSkills.filter(skill =>
            skill.toLowerCase().includes(queryLower) && !currentSkills.includes(skill)
        ).slice(0, 5);

        autocompleteList.innerHTML = '';

        // Add matching existing skills
        matches.forEach(skill => {
            const item = document.createElement('div');
            item.className = 'px-4 py-2 cursor-pointer hover:bg-blue-50 text-sm';
            item.textContent = skill;
            item.addEventListener('click', () => {
                addSkill(skill);
                e.target.value = '';
                hideAutocomplete();
            });
            autocompleteList.appendChild(item);
        });

        // Add "Create new skill" option if no exact match exists
        const exactMatch = allowedSkills.some(skill => skill.toLowerCase() === queryLower);
        if (!exactMatch && query.length > 0) {
            const createItem = document.createElement('div');
            createItem.className = 'px-4 py-2 cursor-pointer hover:bg-green-50 text-sm text-green-700 border-t border-gray-200 font-medium';
            createItem.innerHTML = `<i class="fas fa-plus mr-2"></i>Create "${query}"`;
            createItem.addEventListener('click', () => {
                addSkillWithCreation(query);
                e.target.value = '';
                hideAutocomplete();
            });
            autocompleteList.appendChild(createItem);
        }

        if (autocompleteList.children.length > 0) {
            autocompleteList.style.display = 'block';
        } else {
            hideAutocomplete();
        }
    }

    function hideAutocomplete() {
        const autocompleteList = document.getElementById('skills-autocomplete-list');
        if (autocompleteList) {
            autocompleteList.style.display = 'none';
        }
    }

    // Make removeSkill globally accessible
    window.removeSkill = removeSkill;

    // Initialize skills when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeSkills);
    } else {
        initializeSkills();
    }
})();

