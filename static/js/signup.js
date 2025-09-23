class Signup {
    static selectUserType(type) {
        const slider = document.getElementById('slider-indicator');
        const studentBtn = document.getElementById('student-btn');
        const organizationBtn = document.getElementById('organization-btn');
        const userTypeInput = document.getElementById('user_type');

        userTypeInput.value = type;

        if (type === 'student') {
            slider.style.transform = 'translateX(0)';
            studentBtn.classList.remove('text-gray-700');
            studentBtn.classList.add('text-white');
            organizationBtn.classList.remove('text-white');
            organizationBtn.classList.add('text-gray-700');
        } else {
            slider.style.transform = 'translateX(100%)';
            organizationBtn.classList.remove('text-gray-700');
            organizationBtn.classList.add('text-white');
            studentBtn.classList.remove('text-white');
            studentBtn.classList.add('text-gray-700');
        }

        this.toggleFormFields();
    }

    static toggleFormFields() {
        const userType = document.getElementById('user_type').value;
        const studentFields = document.getElementById('student-fields');
        const organizationFields = document.getElementById('organization-fields');
        const nameLabel = document.getElementById('name-label');

        if (userType === 'student') {
            studentFields.classList.remove('hidden');
            organizationFields.classList.add('hidden');
            nameLabel.textContent = 'Full Name';

            // Make student fields required
            document.getElementById('school').required = true;
            document.getElementById('grade').required = true;

            // Make organization fields not required
            document.getElementById('description').required = false;
        } else {
            studentFields.classList.add('hidden');
            organizationFields.classList.remove('hidden');
            nameLabel.textContent = 'Organization Name';

            // Make organization fields required
            document.getElementById('description').required = true;

            // Make student fields not required
            document.getElementById('school').required = false;
            document.getElementById('grade').required = false;
        }
    }
}

// Initialize form on page load
document.addEventListener('DOMContentLoaded', function () {
    Signup.toggleFormFields();
});