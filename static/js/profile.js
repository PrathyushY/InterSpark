// profile.js - handles profile page interactions
(function () {
  function toggleSaveProfile() {
    const state = window.PROFILE_STATE; if (!state) return;
    const btn = document.getElementById('save-profile-btn'); if (!btn) return;
    const icon = btn.querySelector('i'); const textSpan = document.getElementById('save-profile-text');
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
    const cfg = window.PROFILE_EDIT; if (!cfg) return true;
    const userType = cfg.userType;
    const fullName = document.getElementById('full_name').value.trim();
    if (!fullName || fullName === 'User') { e.preventDefault(); alert(`Please enter your ${userType === 'student' ? 'full name' : 'organization name'}.`); return false; }
    if (userType === 'student') {
      const school = document.getElementById('school').value.trim();
      const grade = document.getElementById('grade').value;
      const bio = document.getElementById('bio').value.trim();
      if (!school) { e.preventDefault(); alert('Please enter your school name.'); return false; }
      if (!grade) { e.preventDefault(); alert('Please select your grade.'); return false; }
      if (!bio) { e.preventDefault(); alert('Please write a bio.'); return false; }
    } else if (userType === 'organization') {
      const description = document.getElementById('description')?.value.trim();
      if (!description) { e.preventDefault(); alert('Please write a description of your organization.'); return false; }
    }
    return true;
  }
  document.addEventListener('DOMContentLoaded', () => {
    const saveBtn = document.getElementById('save-profile-submit-btn');
    if (saveBtn) { saveBtn.addEventListener('click', validateProfileForm); }
  });
})();

