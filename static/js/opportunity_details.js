// opportunity_details.js - extracted logic from opportunity_details.html
(function(){
  const state = window.OPPORTUNITY_STATE || { id: null, isSaved: false };

  function showAlert(message, type){
    const isError = type==='error';
    const alert = document.createElement('div');
    alert.className = `alert p-4 rounded-lg shadow-lg fixed top-4 left-1/2 -translate-x-1/2 z-50 max-w-md ${isError?'bg-red-50 border border-red-200 text-red-700':'bg-green-50 border border-green-200 text-green-700'}`;
    alert.innerHTML = `<div class='flex justify-between items-center'><div class='flex items-center'><i class='fas fa-${isError?'exclamation-circle text-red-400':'check-circle text-green-400'} mr-3'></i><span class='text-sm font-medium'>${message}</span></div><button aria-label='Close' class='ml-4 text-gray-500 hover:text-gray-700'>&times;</button></div>`;
    alert.querySelector('button').onclick=()=>alert.remove();
    document.body.appendChild(alert);
    setTimeout(()=>{ if(alert.parentNode){ alert.style.transition='opacity .3s'; alert.style.opacity='0'; setTimeout(()=>alert.remove(),300);} },3000);
  }

  async function toggleSave(){
    const btn = document.getElementById('save-opportunity-btn'); if(!btn) return;
    const icon = btn.querySelector('i'); const text = document.getElementById('save-text');
    if(!state.id) return;
    btn.disabled = true;
    try {
      const url = state.isSaved ? `/unsave_opportunity/${state.id}` : `/save_opportunity/${state.id}`;
      const res = await fetch(url,{method:'POST'});
      const data = await res.json();
      if(data.success){
        state.isSaved = !state.isSaved;
        if(state.isSaved){
          icon.className = 'fas fa-bookmark mr-2';
          text.textContent = 'Saved';
          btn.className = btn.className.replace('border-gray-300 text-gray-700','bg-orange-50 border-orange-300 text-orange-700');
        } else {
          icon.className = 'far fa-bookmark mr-2';
          text.textContent = 'Save for Later';
          btn.className = btn.className.replace('bg-orange-50 border-orange-300 text-orange-700','border-gray-300 text-gray-700');
        }
        showAlert(data.message || 'Updated','success');
      } else {
        showAlert(data.error || 'Failed to update','error');
      }
    } catch(e){
      showAlert('An error occurred. Try again.','error');
    } finally { btn.disabled = false; }
  }

  window.OpportunityDetails = { toggleSave };
})();

