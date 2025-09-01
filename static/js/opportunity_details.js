// opportunity_details.js - extracted logic from opportunity_details.html
(function () {
  const state = window.OPPORTUNITY_STATE || { id: null, isSaved: false };

  async function toggleSave() {
    const btn = document.getElementById('save-opportunity-btn'); if (!btn) return;
    const icon = btn.querySelector('i'); const text = document.getElementById('save-text');
    if (!state.id) return;
    btn.disabled = true;
    try {
      const url = state.isSaved ? `/unsave_opportunity/${state.id}` : `/save_opportunity/${state.id}`;
      const res = await fetch(url, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        state.isSaved = !state.isSaved;
        if (state.isSaved) {
          icon.className = 'fas fa-bookmark mr-2';
          text.textContent = 'Saved';
          btn.className = btn.className.replace('border-gray-300 text-gray-700', 'bg-blue-50 border-blue-300 text-blue-700');
        } else {
          icon.className = 'far fa-bookmark mr-2';
          text.textContent = 'Save for Later';
          btn.className = btn.className.replace('bg-blue-50 border-blue-300 text-blue-700', 'border-gray-300 text-gray-700');
        }
        showAlert(data.message || 'Opportunity Saved', 'info');
      } else {
        showAlert(data.error || 'Failed to save', 'error');
      }
    } catch (e) {
      showAlert('An error occurred. Try again.', 'error');
    } finally { btn.disabled = false; }
  }

  window.OpportunityDetails = { toggleSave };
})();

