// profile.js - handles profile page interactions
(function(){
  function showAlert(message, type){
    const alert = document.createElement('div');
    const isError = type==='error';
    alert.className = `alert p-4 rounded-lg shadow-lg fixed top-4 left-1/2 -translate-x-1/2 z-50 max-w-md ${isError?'bg-red-50 border border-red-200 text-red-700':'bg-green-50 border border-green-200 text-green-700'}`;
    alert.innerHTML = `<div class="flex justify-between items-center"><span class="text-sm font-medium">${message}</span><button aria-label="Close" class="ml-4 text-gray-500 hover:text-gray-700">&times;</button></div>`;
    alert.querySelector('button').onclick=()=>alert.remove();
    document.body.appendChild(alert);
    setTimeout(()=>{ if(alert.parentNode){ alert.style.transition='opacity .3s'; alert.style.opacity='0'; setTimeout(()=>alert.remove(),300);} },3000);
  }
  // Public for other scripts
  window.ProfileAlerts = { showAlert };

  function toggleSaveProfile(){
    const state = window.PROFILE_STATE; if(!state) return;
    const btn = document.getElementById('save-profile-btn'); if(!btn) return;
    const icon = btn.querySelector('i'); const textSpan = document.getElementById('save-profile-text');
    btn.disabled = true;
    const url = state.isSaved ? `/unsave_profile/${state.profileId}` : `/save_profile/${state.profileId}`;
    fetch(url,{method:'POST'}).then(r=>r.json()).then(data=>{
      if(data.success){
        state.isSaved = !state.isSaved;
        if(state.isSaved){
          icon.className='fas fa-bookmark mr-2';
          textSpan.textContent='Saved';
          btn.className = btn.className.replace('border-gray-300 text-gray-700','bg-orange-50 border-orange-300 text-orange-700');
        } else {
          icon.className='far fa-bookmark mr-2';
            textSpan.textContent='Save Profile';
            btn.className = btn.className.replace('bg-orange-50 border-orange-300 text-orange-700','border-gray-300 text-gray-700');
        }
        showAlert(data.message || 'Updated', 'success');
      } else { showAlert(data.error || 'Failed', 'error'); }
    }).catch(()=>showAlert('Error updating.','error')).finally(()=>btn.disabled=false);
  }
  window.toggleSaveProfile = toggleSaveProfile;

  function validateProfileForm(e){
    const cfg = window.PROFILE_EDIT; if(!cfg) return true;
    const userType = cfg.userType;
    const fullName = document.getElementById('full_name').value.trim();
    if(!fullName || fullName==='User'){ e.preventDefault(); alert(`Please enter your ${userType==='student'?'full name':'organization name'}.`); return false; }
    if(userType==='student'){
      const school = document.getElementById('school').value.trim();
      const grade = document.getElementById('grade').value;
      const bio = document.getElementById('bio').value.trim();
      if(!school){ e.preventDefault(); alert('Please enter your school name.'); return false; }
      if(!grade){ e.preventDefault(); alert('Please select your grade.'); return false; }
      if(!bio){ e.preventDefault(); alert('Please write a bio.'); return false; }
    } else if(userType==='organization'){
      const description = document.getElementById('description')?.value.trim();
      if(!description){ e.preventDefault(); alert('Please write a description of your organization.'); return false; }
    }
    return true;
  }
  document.addEventListener('DOMContentLoaded',()=>{
    const saveBtn = document.getElementById('save-profile-submit-btn');
    if(saveBtn){ saveBtn.addEventListener('click', validateProfileForm); }
  });
})();

