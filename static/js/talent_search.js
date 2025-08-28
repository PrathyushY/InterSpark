// talent_search.js - extracted logic from talent_search.html
(function(){
  let suggestionTimeouts = {};

  function fetchSuggestions(field, term, suggestionsDiv){
    fetch(`/api/search/suggestions?field=${field}&term=${encodeURIComponent(term)}`)
      .then(r=>r.json())
      .then(data=>{
        if(data.suggestions && data.suggestions.length){
          displaySuggestions(data.suggestions, suggestionsDiv);
        } else {
          suggestionsDiv.classList.add('hidden');
        }
      })
      .catch(()=> suggestionsDiv.classList.add('hidden'));
  }

  function displaySuggestions(suggestions, suggestionsDiv){
    suggestionsDiv.innerHTML='';
    suggestions.forEach(s=>{
      const item=document.createElement('div');
      item.className='suggestion-item px-3 py-2 hover:bg-orange-50 cursor-pointer text-sm border-b border-gray-100 last:border-b-0';
      item.textContent=s;
      item.addEventListener('click',()=>{ const field = suggestionsDiv.previousElementSibling; field.value=s; suggestionsDiv.classList.add('hidden'); });
      item.addEventListener('mouseenter',()=>{ suggestionsDiv.querySelectorAll('.suggestion-item').forEach(i=>i.classList.remove('active')); item.classList.add('active');});
      suggestionsDiv.appendChild(item);
    });
    suggestionsDiv.classList.remove('hidden');
  }

  function setupSearchSuggestions(fieldId, suggestionsId){
    const field = document.getElementById(fieldId);
    const suggestionsDiv = document.getElementById(suggestionsId);
    if(!field || !suggestionsDiv) return;

    field.addEventListener('input', function(){
      const term = this.value.trim();
      if(suggestionTimeouts[fieldId]) clearTimeout(suggestionTimeouts[fieldId]);
      if(term.length < 2){ suggestionsDiv.classList.add('hidden'); return; }
      suggestionTimeouts[fieldId] = setTimeout(()=> fetchSuggestions(fieldId.replace('-', '_'), term, suggestionsDiv), 300);
    });

    document.addEventListener('click', e=>{ if(!field.contains(e.target) && !suggestionsDiv.contains(e.target)) suggestionsDiv.classList.add('hidden'); });

    field.addEventListener('keydown', e=>{
      const items = suggestionsDiv.querySelectorAll('.suggestion-item');
      const active = suggestionsDiv.querySelector('.suggestion-item.active');
      if(e.key==='ArrowDown'){
        e.preventDefault();
        if(!active && items.length){ items[0].classList.add('active'); }
        else if(active){ const next = active.nextElementSibling || items[0]; active.classList.remove('active'); next.classList.add('active'); }
      } else if(e.key==='ArrowUp'){
        e.preventDefault();
        if(active){ const prev = active.previousElementSibling || items[items.length-1]; active.classList.remove('active'); prev.classList.add('active'); }
      } else if(e.key==='Enter'){
        if(active){ e.preventDefault(); field.value = active.textContent; suggestionsDiv.classList.add('hidden'); }
      } else if(e.key==='Escape'){
        suggestionsDiv.classList.add('hidden');
      }
    });
  }

  function showAlert(message, type){
    const alert = document.createElement('div');
    const isError = type==='error';
    const isInfo = type==='info';
    alert.className = `alert p-4 rounded-lg shadow-lg fixed top-4 left-1/2 -translate-x-1/2 z-50 max-w-md ${isError ? 'bg-red-50 border border-red-200 text-red-700' : isInfo ? 'bg-blue-50 border border-blue-200 text-blue-700' : 'bg-green-50 border border-green-200 text-green-700'}`;
    alert.innerHTML = `<div class='flex justify-between items-center'><span class='text-sm font-medium'>${message}</span><button aria-label='Close' class='ml-4 text-gray-500 hover:text-gray-700'>&times;</button></div>`;
    alert.querySelector('button').onclick=()=>alert.remove();
    document.body.appendChild(alert);
    setTimeout(()=>{ if(alert.parentNode){ alert.style.transition='opacity .3s'; alert.style.opacity='0'; setTimeout(()=>alert.remove(),300);} },3000);
  }

  window.toggleSaveProfile = async function(profileId, button){
    button.disabled = true; const icon = button.querySelector('i'); const isSaved = icon.classList.contains('fas');
    try{
      const url = isSaved ? `/unsave_profile/${profileId}` : `/save_profile/${profileId}`;
      const res = await fetch(url,{method:'POST', headers:{'Content-Type':'application/json'}});
      const data = await res.json();
      if(data.success){
        if(isSaved){ icon.className='far fa-bookmark'; button.className = button.className.replace('bg-orange-50 border-orange-300 text-orange-700','border-gray-300 text-gray-700'); }
        else { icon.className='fas fa-bookmark'; button.className = button.className.replace('border-gray-300 text-gray-700','bg-orange-50 border-orange-300 text-orange-700'); }
        showAlert(data.message || (isSaved ? 'Profile removed from saved' : 'Profile saved'), 'success');
      } else showAlert(data.error || 'Failed to update profile', 'error');
    }catch(err){ showAlert('An error occurred. Please try again.', 'error'); }
    finally { button.disabled = false; }
  };

  window.clearSearch = function(){ const input = document.getElementById('search'); if(input){ input.value=''; document.getElementById('talent-search-form').submit(); } };

  document.addEventListener('DOMContentLoaded', ()=>{
    // If additional suggestion inputs are added later, call setupSearchSuggestions for each
    // Example placeholders (currently no separate inputs provided in template):
    // setupSearchSuggestions('skills','skills-suggestions');
    // setupSearchSuggestions('school','school-suggestions');
    const searchField = document.getElementById('search');
    if(searchField){ let tipShown=false; searchField.addEventListener('focus', function(){ if(!tipShown && !this.value){ showAlert('Try advanced search: "web development" OR python AND react','info'); tipShown=true; }}); }
  });
})();

