// Talent Search JavaScript
document.addEventListener('DOMContentLoaded', function () {
    // Handle save/unsave profile functionality
    window.toggleSaveProfile = function (profileId, button) {
        // Determine current saved state by checking the icon class
        const icon = button.querySelector('i');
        const isSaved = icon.classList.contains('fas');
        const action = isSaved ? 'unsave' : 'save';
        const url = `/${action}_profile/${profileId}`;

        // Disable button during request
        button.disabled = true;

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Toggle button appearance based on the new state
                    if (isSaved) {
                        // Was saved, now unsaved
                        button.classList.remove('bg-blue-50');
                        button.classList.add('bg-white');
                        icon.classList.remove('fas');
                        icon.classList.add('far');
                        showAlert(data.message || 'Profile removed from saved list', 'info');
                    } else {
                        // Was unsaved, now saved
                        button.classList.remove('bg-white');
                        button.classList.add('bg-blue-50');
                        icon.classList.remove('far');
                        icon.classList.add('fas');
                        showAlert(data.message || 'Profile saved successfully!', 'success');
                    }
                } else {
                    console.error('Error toggling profile save:', data.error);
                    showAlert('Error: ' + (data.error || 'Failed to save profile'), 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Network error occurred. Please try again.', 'error');
            })
            .finally(() => {
                // Re-enable button
                button.disabled = false;
            });
    };
});