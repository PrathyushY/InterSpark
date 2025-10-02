// create_opportunity.js - extracted logic from template
(function () {
  const KEY = 'opportunityDraft';
  const editing = window.OPP_EDITING === true || window.OPP_EDITING === 'true';

  // Skills functionality variables (will be set from template)
  let allowedSkills = [];
  let initialSkillsFromServer = [];

  function getRequiredFields() {
    // Core fields required for all opportunity types
    const coreFields = [
      "title", "type", "category", "location", "requirements", "compensation",
      "duration", "application_deadline", "description", "skills_needed"
    ];

    // Get the current opportunity type
    const typeField = document.getElementById('type');
    const opportunityType = typeField ? typeField.value : '';

    // Add type-specific required fields based on opportunity type
    const typeSpecificFields = [];

    switch (opportunityType) {
      case 'Scholarship':
      case 'Competition':
        typeSpecificFields.push('eligibility_criteria');
        if (opportunityType === 'Scholarship') {
          typeSpecificFields.push('award_amount');
        }
        break;
      case 'Summer Camp':
      case 'Workshop':
        typeSpecificFields.push('age_range');
        break;
      case 'Research Opportunity':
        typeSpecificFields.push('research_field');
        break;
      case 'Mentorship':
        typeSpecificFields.push('mentor_info');
        break;
    }

    // Always include these helpful fields but don't make them strictly required
    // typeSpecificFields.push('application_materials', 'selection_process');

    return [...coreFields, ...typeSpecificFields];
  }

  function saveFormLocally() {
    if (editing) return; // only for new drafts
    const data = {};
    getRequiredFields().forEach(f => {
      if (f === "skills_needed") {
        const el = document.getElementById('skills-needed-hidden-input');
        if (el) data[f] = el.value;
      } else {
        const el = document.getElementById(f);
        if (el) data[f] = el.value;
      }
    });
    localStorage.setItem(KEY, JSON.stringify(data));
  }
  function restoreFormLocally() {
    if (editing) return;
    try {
      const raw = localStorage.getItem(KEY);
      if (!raw) return;
      const data = JSON.parse(raw);
      getRequiredFields().forEach(f => {
        if (f === "skills_needed") {
          const el = document.getElementById('skills-needed-hidden-input');
          if (el && data[f] !== undefined) {
            el.value = data[f];
            // Schedule skills rendering after DOM is ready
            setTimeout(() => {
              const container = document.getElementById('skills-needed-bubble-container');
              if (container && window.renderSkillBubbles) {
                try {
                  const skills = JSON.parse(data[f]);
                  window.renderSkillBubbles(skills, container);
                } catch (e) {
                  console.warn('Failed to restore skills:', e);
                }
              }
            }, 100);
          }
        } else {
          const el = document.getElementById(f);
          if (el && data[f] !== undefined) el.value = data[f];
        }
      });
    } catch (e) { console.warn('Restore draft failed', e); }
  }
  function clearFormLocally() { if (!editing) localStorage.removeItem(KEY); }

  function highlightRequiredFields(missing) {
    missing.forEach(f => {
      let el;
      if (f === "skills_needed") {
        el = document.getElementById('skills-needed-bubble-input'); // Highlight the visible input, not the hidden one
      } else {
        el = document.getElementById(f);
      }
      if (el) el.classList.add('required-highlight');
    });
  }
  function clearRequiredHighlights() { document.querySelectorAll('.required-highlight').forEach(el => el.classList.remove('required-highlight')); }

  function publishOpportunity() {
    clearRequiredHighlights();
    const missing = [];
    getRequiredFields().forEach(f => {
      let el;
      if (f === "skills_needed") {
        el = document.getElementById('skills-needed-hidden-input');
      } else {
        el = document.getElementById(f);
      }
      if (el && !el.value) missing.push(f);
    });
    if (missing.length) { saveFormLocally(); highlightRequiredFields(missing); alert('Missing required fields: ' + missing.join(', ') + '\nDraft saved locally. Complete all fields to publish.'); return; }
    document.getElementById('status-field').value = 'active';
    let publishField = document.getElementById('publish-field');
    if (!publishField) { publishField = document.createElement('input'); publishField.type = 'hidden'; publishField.name = 'publish'; publishField.id = 'publish-field'; document.getElementById('opportunity-form').appendChild(publishField); }
    publishField.value = '1'; clearFormLocally(); document.getElementById('opportunity-form').submit();
  }
  function saveAsDraft() { document.getElementById('status-field').value = 'draft'; clearFormLocally(); document.getElementById('opportunity-form').submit(); }

  function confirmCancel() { if (confirm('Are you sure you want to cancel? Any unsaved changes will be lost.')) { clearFormLocally(); if (document.referrer && document.referrer !== window.location.href) window.location = document.referrer; else window.location = '/dashboard'; } }

  function previewOpportunity() {
    // Create a form with all the current data and submit to preview endpoint
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/preview_opportunity';
    form.target = '_blank';
    form.style.display = 'none';

    // Get all form fields from the current form
    const currentForm = document.getElementById('opportunity-form');
    const formData = new FormData(currentForm);

    // Add all form data to the new form
    for (let [key, value] of formData.entries()) {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = key;
      input.value = value;
      form.appendChild(input);
    }

    // Add additional dynamic fields
    const additionalFields = [
      'award_amount', 'eligibility_criteria', 'age_range', 'program_dates',
      'research_field', 'prerequisite_skills', 'mentor_info', 'commitment_level',
      'application_materials', 'selection_process'
    ];

    additionalFields.forEach(fieldName => {
      const field = document.getElementById(fieldName);
      if (field && field.value) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = fieldName;
        input.value = field.value;
        form.appendChild(input);
      }
    });

    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
  }

  function showPreviewModal(data) {
    const gradient = 'from-orange-500 to-blue-600';
    let badge = 'bg-blue-100 text-blue-800'; // default
    if (data.type === 'Internship') badge = 'bg-blue-100 text-blue-800';
    else if (data.type === 'Job') badge = 'bg-purple-100 text-purple-800';
    else if (data.type === 'Summer Camp') badge = 'bg-yellow-100 text-yellow-800';
    else if (data.type === 'Research Opportunity') badge = 'bg-indigo-100 text-indigo-800';
    else if (data.type === 'Summer Program') badge = 'bg-orange-100 text-orange-800';
    else if (data.type === 'Scholarship') badge = 'bg-pink-100 text-pink-800';
    else if (data.type === 'Competition') badge = 'bg-red-100 text-red-800';
    else if (data.type === 'Workshop') badge = 'bg-teal-100 text-teal-800';
    else if (data.type === 'Mentorship') badge = 'bg-cyan-100 text-cyan-800';
    else if (data.type === 'Volunteer') badge = 'bg-green-100 text-green-800';
    else if (data.type === 'Full-time') badge = 'bg-gray-100 text-gray-800';
    else if (data.type === 'Part-time') badge = 'bg-slate-100 text-slate-800';
    const modalHTML = `\n    <div id="preview-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">\n      <div class=\"relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white\">\n        <div class=\"mt-3\">\n          <div class=\"flex justify-between items-center mb-4\">\n            <h3 class=\"text-lg font-medium text-gray-900\">Opportunity Preview</h3>\n            <button onclick=\"CO.closePreviewModal()\" class=\"text-gray-400 hover:text-gray-600\"><i class=\"fas fa-times text-xl\"></i></button>\n          </div>\n          <div class=\"bg-white rounded-lg shadow-md overflow-hidden\">\n            <div class=\"h-32 bg-gradient-to-br ${gradient} flex items-center justify-center\">\n              <i class=\"fas fa-briefcase text-white text-4xl\"></i>\n            </div>\n            <div class=\"p-6\">\n              <div class=\"flex items-center justify-between mb-4\">\n                <div class=\"flex items-center space-x-3\">\n                  <span class=\"inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${badge}\">${data.type || 'Type not specified'}</span>\n                  <span class=\"text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full\">${data.category || 'Category not specified'}</span>\n                </div>\n              </div>\n              <h1 class=\"text-2xl font-bold text-gray-900 mb-4\">${data.title || 'Opportunity Title'}</h1>\n              <div class=\"grid grid-cols-1 md:grid-cols-2 gap-6 mb-6\">\n                <div class=\"space-y-3\">\n                  <div class=\"flex items-center\"><i class=\"fas fa-map-marker-alt text-gray-400 w-5 mr-3\"></i><span class=\"text-gray-700\">${data.location || 'Location not specified'}</span></div>\n                  <div class=\"flex items-center\"><i class=\"fas fa-clock text-gray-400 w-5 mr-3\"></i><span class=\"text-gray-700\">${data.duration || 'Duration not specified'}</span></div>\n                  <div class=\"flex items-center\"><i class=\"fas fa-dollar-sign text-gray-400 w-5 mr-3\"></i><span class=\"text-gray-700\">${data.compensation || 'Compensation not specified'}</span></div>\n                </div>\n                <div class=\"space-y-3\">\n                  <div class=\"flex items-center\"><i class=\"fas fa-calendar text-gray-400 w-5 mr-3\"></i><span class=\"text-gray-700\">Deadline: ${data.application_deadline ? new Date(data.application_deadline).toLocaleDateString() : 'No deadline specified'}</span></div>\n                </div>\n              </div>\n              ${data.description ? `<div class=\"mb-6\"><h3 class=\"text-lg font-semibold text-gray-900 mb-3\">About This Opportunity</h3><p class=\"text-gray-700 leading-relaxed\">${data.description.replace(/\n/g, '<br>')}</p></div>` : ''}\n              ${data.requirements ? `<div class=\"mb-6\"><h3 class=\"text-lg font-semibold text-gray-900 mb-3\">Requirements</h3><ul class=\"space-y-2 text-gray-700\">${data.requirements.split('\n').filter(r => r.trim()).map(r => `<li class=\\"flex items-start\\"><i class=\\"fas fa-circle text-gray-400 mr-3 mt-2 flex-shrink-0\\" style=\\"font-size:6px;\\"></i><span>${r.trim()}</span></li>`).join('')}</ul></div>` : ''}\n            </div>\n          </div>\n          <div class=\"flex justify-end mt-6 space-x-3\">\n            <button onclick=\"CO.closePreviewModal()\" class=\"bg-gray-300 hover:bg-gray-400 text-gray-800 font-medium py-2 px-4 rounded\">Close Preview</button>\n          </div>\n        </div>\n      </div>\n    </div>`;
    document.body.insertAdjacentHTML('beforeend', modalHTML);
  }
  function closePreviewModal() { const m = document.getElementById('preview-modal'); if (m) m.remove(); }

  // Skills functionality
  function initializeSkills(skillsMaster, initialSkills) {
    allowedSkills = skillsMaster || [];
    initialSkillsFromServer = initialSkills || [];

    // Initialize the UI after setting the data
    initializeSkillsUI();
  }

  function renderSkillBubbles(skills, container) {
    if (!container) {
      return;
    }

    if (!Array.isArray(skills)) {
      return;
    }

    // Make sure allowedSkills is available
    if (typeof allowedSkills === 'undefined') {
      return;
    }

    container.innerHTML = '';
    skills.forEach((skill) => {
      // Only display skills that exist in the database
      const isInDatabase = allowedSkills.includes(skill);
      if (!isInDatabase) {
        return; // Skip skills not in database
      }

      const bubble = document.createElement('span');
      bubble.className = 'skill-bubble inline-flex items-center px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-sm font-medium mr-2 mb-2';
      bubble.textContent = skill;
      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'ml-2 text-blue-500 hover:text-red-600 focus:outline-none';
      removeBtn.innerHTML = '<i class="fas fa-times"></i>';
      removeBtn.onclick = () => {
        container.removeChild(bubble);
        updateHiddenInput(container);
      };
      bubble.appendChild(removeBtn);
      container.appendChild(bubble);
    });
  }

  function setupAutocomplete(input, container) {
    input.addEventListener('input', function () {
      const val = input.value.trim().toLowerCase();
      let matches = allowedSkills.filter(s => s.toLowerCase().includes(val) && !getCurrentSkills(container).includes(s));
      matches = matches.slice(0, 5);
      const autocompleteList = document.getElementById('skills-needed-autocomplete-list');
      autocompleteList.innerHTML = '';

      // Show existing skill matches
      matches.forEach(skill => {
        const item = document.createElement('div');
        item.className = 'px-3 py-2 cursor-pointer hover:bg-blue-50';
        item.textContent = skill;
        item.onclick = () => {
          addSkillBubble(skill, container);
          input.value = '';
          autocompleteList.style.display = 'none';
        };
        autocompleteList.appendChild(item);
      });

      // Skills can only be selected from existing options - no new skill creation allowed

      // If no matches but user has typed something, show "not found" message
      if (matches.length === 0 && val.length > 0) {
        const notFoundItem = document.createElement('div');
        notFoundItem.className = 'px-3 py-2 text-sm text-gray-500 italic';
        notFoundItem.textContent = `"${val}" - Skill not found. Please select from existing skills.`;
        autocompleteList.appendChild(notFoundItem);
      }

      autocompleteList.style.display = autocompleteList.children.length > 0 ? 'block' : 'none';
      const inputRect = input.getBoundingClientRect();
      autocompleteList.style.position = 'absolute';
      autocompleteList.style.maxHeight = '180px';
      autocompleteList.style.overflowY = 'auto';
      autocompleteList.style.zIndex = '50';
      autocompleteList.style.top = (input.offsetTop + input.offsetHeight) + 'px';
      autocompleteList.style.left = input.offsetLeft + 'px';
      autocompleteList.style.width = '350px';
      autocompleteList.style.maxWidth = '350px';
      autocompleteList.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
    });

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ',') {
        const skill = input.value.trim();
        if (skill) {
          // Check if skill exists in allowed list (case insensitive)
          const existingSkill = allowedSkills.find(s => s.toLowerCase() === skill.toLowerCase());
          if (existingSkill) {
            // Use the properly cased version from the list
            if (!getCurrentSkills(container).includes(existingSkill)) {
              addSkillBubble(existingSkill, container);
            }
            input.value = '';
            document.getElementById('skills-needed-autocomplete-list').style.display = 'none';
          } else {
            // Show error for non-existent skills
            input.placeholder = "Skill not found. Please select from existing skills.";
            input.value = '';
            setTimeout(() => {
              input.placeholder = "Start typing to see available skills...";
            }, 3000);
          }
        }
        e.preventDefault();
      }
    });
  }

  function addSkillBubble(skill, container) {
    if (getCurrentSkills(container).includes(skill)) return;

    // Only allow skills that exist in database
    const isInDatabase = allowedSkills.includes(skill);
    if (!isInDatabase) {
      return; // Don't add skills not in database
    }

    const bubble = document.createElement('span');
    bubble.className = 'skill-bubble inline-flex items-center px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-sm font-medium mr-2 mb-2';
    bubble.textContent = skill;
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'ml-2 text-blue-500 hover:text-red-600 focus:outline-none';
    removeBtn.innerHTML = '<i class="fas fa-times"></i>';
    removeBtn.onclick = () => {
      container.removeChild(bubble);
      updateHiddenInput(container);
    };
    bubble.appendChild(removeBtn);
    container.appendChild(bubble);
    updateHiddenInput(container);
  }

  function getCurrentSkills(container) {
    return Array.from(container.children).map(bubble => {
      // Get the skill name from the bubble, excluding the remove button
      const skillNodes = Array.from(bubble.childNodes);
      let skillText = '';

      // Get text from text nodes and skip the remove button
      for (let node of skillNodes) {
        if (node.nodeType === Node.TEXT_NODE) {
          skillText += node.textContent;
        }
      }

      return skillText.trim().replace(/\s*\u00d7\s*$/, ''); // Remove any trailing × character
    });
  }

  function updateHiddenInput(container) {
    const skills = getCurrentSkills(container);
    document.getElementById('skills-needed-hidden-input').value = JSON.stringify(skills);
    // Trigger auto-save when skills are updated
    if (window.CO && window.CO.saveFormLocally) {
      window.CO.saveFormLocally();
    }
  }

  function initializeSkillsUI() {
    const skillsContainer = document.getElementById('skills-needed-bubble-container');
    const skillsInput = document.getElementById('skills-needed-bubble-input');
    const hiddenInput = document.getElementById('skills-needed-hidden-input');

    // Use the skills passed from server during initialization
    let initialSkills = [];
    if (Array.isArray(initialSkillsFromServer)) {
      initialSkills = initialSkillsFromServer;
    }

    if (skillsContainer) {
      renderSkillBubbles(initialSkills, skillsContainer);
    }

    if (skillsInput && skillsContainer) {
      setupAutocomplete(skillsInput, skillsContainer);
    }

    if (skillsContainer) {
      updateHiddenInput(skillsContainer);
    }
  }

  // Expose
  window.CO = {
    getRequiredFields,
    saveFormLocally,
    restoreFormLocally,
    clearFormLocally,
    publishOpportunity,
    saveAsDraft,
    confirmCancel,
    previewOpportunity,
    showPreviewModal,
    closePreviewModal,
    highlightRequiredFields,
    clearRequiredHighlights,
    // Skills functions
    initializeSkills,
    renderSkillBubbles,
    setupAutocomplete,
    addSkillBubble,
    getCurrentSkills,
    updateHiddenInput,
    initializeSkillsUI
  };

  document.addEventListener('DOMContentLoaded', () => {
    restoreFormLocally();

    // Don't initialize skills UI here - it will be done when initializeSkills is called from template

    // Auto-save typing
    getRequiredFields().forEach(f => {
      if (f === "skills_needed") {
        const el = document.getElementById('skills-needed-hidden-input');
        if (el) {
          // Listen for input events on the hidden field
          el.addEventListener('input', () => { saveFormLocally(); });
          // Also set up periodic check for changes (fallback)
          let lastValue = el.value;
          setInterval(() => {
            if (el.value !== lastValue) {
              lastValue = el.value;
              saveFormLocally();
            }
          }, 1000);
        }
      } else {
        const el = document.getElementById(f);
        if (el) {
          el.addEventListener('input', () => {
            saveFormLocally();
            el.classList.remove('required-highlight');
          });
        }
      }
    });
    window.addEventListener('beforeunload', saveFormLocally);
  });
})();

