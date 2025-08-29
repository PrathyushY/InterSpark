// Talent Search JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Handle save/unsave profile functionality
    window.toggleSaveProfile = function(profileId, button) {
        const isSaved = button.classList.contains('bg-blue-50');
        const action = isSaved ? 'unsave' : 'save';
        const url = `/${action}_profile/${profileId}`;

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Toggle button appearance
                const icon = button.querySelector('i');
                if (isSaved) {
                    button.classList.remove('bg-blue-50', 'border-blue-300', 'text-blue-700');
                    button.classList.add('bg-white', 'border-blue-300', 'text-blue-700');
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                } else {
                    button.classList.remove('bg-white');
                    button.classList.add('bg-blue-50', 'border-blue-300', 'text-blue-700');
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                }
            } else {
                console.error('Error toggling profile save:', data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    };
});

