// create_opportunity.js - extracted logic from template
(function () {
  const KEY = 'opportunityDraft';
  const editing = window.OPP_EDITING === true || window.OPP_EDITING === 'true';

  // Skills functionality variables (will be set from template)
  let allowedSkills = [];
  let initialSkillsFromServer = [];

  function getRequiredFields() {
    return [
      "title", "type", "category", "location", "requirements", "compensation",
      "duration", "application_deadline", "description", "skills_needed",
      "eligibility_criteria", "age_range", "prerequisite_skills", "award_amount",
      "program_dates", "mentor_info", "research_field", "commitment_level",
      "application_materials", "selection_process"
    ];
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
      // Don't filter out skills for drafts - allow all skills to be displayed
      const bubble = document.createElement('span');
      // Add different styling for skills not in database vs existing skills
      const isInDatabase = allowedSkills.includes(skill);
      bubble.className = isInDatabase
        ? 'skill-bubble inline-flex items-center px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-sm font-medium mr-2 mb-2'
        : 'skill-bubble inline-flex items-center px-3 py-1 rounded-full bg-orange-100 text-orange-800 text-sm font-medium mr-2 mb-2';
      bubble.textContent = skill;
      // Add a small indicator for new skills
      if (!isInDatabase) {
        const newIndicator = document.createElement('span');
        newIndicator.className = 'ml-1 text-xs';
        newIndicator.textContent = '(new)';
        newIndicator.title = 'This is a new skill that will be added to the database when you publish';
        bubble.appendChild(newIndicator);
      }
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

      // If no matches and user has typed something, show "Add new skill" option
      if (matches.length === 0 && val.length >= 2) {
        // Check if the skill already exists (case-insensitive)
        const existsAlready = allowedSkills.some(s => s.toLowerCase() === val.toLowerCase());
        if (!existsAlready) {
          const newSkillItem = document.createElement('div');
          newSkillItem.className = 'px-3 py-2 cursor-pointer hover:bg-green-50 text-green-700 border-t border-gray-200';
          newSkillItem.innerHTML = `<i class="fas fa-plus mr-2"></i>Add "${val}" as a new skill`;
          newSkillItem.onclick = () => {
            addNewSkillToDatabase(val, container, input, autocompleteList);
          };
          autocompleteList.appendChild(newSkillItem);
        }
      }

      autocompleteList.style.display = (matches.length > 0 || (matches.length === 0 && val.length >= 2)) ? 'block' : 'none';
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
            // Add as new skill via backend
            addNewSkillToDatabase(skill, container, input, document.getElementById('skills-needed-autocomplete-list'));
          }
        }
        e.preventDefault();
      }
    });
  }

  function addSkillBubble(skill, container) {
    if (getCurrentSkills(container).includes(skill)) return;
    const bubble = document.createElement('span');
    // Add different styling for skills not in database vs existing skills
    const isInDatabase = allowedSkills.includes(skill);
    bubble.className = isInDatabase
      ? 'skill-bubble inline-flex items-center px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-sm font-medium mr-2 mb-2'
      : 'skill-bubble inline-flex items-center px-3 py-1 rounded-full bg-orange-100 text-orange-800 text-sm font-medium mr-2 mb-2';
    bubble.textContent = skill;
    // Add a small indicator for new skills
    if (!isInDatabase) {
      const newIndicator = document.createElement('span');
      newIndicator.className = 'ml-1 text-xs';
      newIndicator.textContent = '(new)';
      newIndicator.title = 'This is a new skill that will be added to the database when you publish';
      bubble.appendChild(newIndicator);
    }
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
      // Get the skill name from the bubble, excluding the "(new)" indicator and remove button
      const skillNodes = Array.from(bubble.childNodes);
      let skillText = '';

      // Get text from text nodes and skip the "(new)" indicator and remove button
      for (let node of skillNodes) {
        if (node.nodeType === Node.TEXT_NODE) {
          skillText += node.textContent;
        } else if (node.nodeType === Node.ELEMENT_NODE &&
          node.tagName === 'SPAN' &&
          node.textContent !== '(new)') {
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

  async function addNewSkillToDatabase(skillName, container, input, autocompleteList) {
    try {
      // Show loading state
      input.disabled = true;
      input.placeholder = "Adding skill...";

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
          allowedSkills.sort(); // Keep it sorted
        }

        // Add the skill bubble
        addSkillBubble(formattedSkill, container);

        // Clear input and hide dropdown
        input.value = '';
        autocompleteList.style.display = 'none';

        // Show success message briefly
        input.placeholder = "Skill added successfully!";
        setTimeout(() => {
          input.placeholder = "Type a skill and press Enter...";
        }, 2000);

      } else {
        // Handle errors
        if (result.error === "Skill already exists") {
          // If skill exists, use the existing one
          const existingSkill = result.existing_skill || skillName;
          if (!allowedSkills.includes(existingSkill)) {
            allowedSkills.push(existingSkill);
            allowedSkills.sort();
          }
          addSkillBubble(existingSkill, container);
          input.value = '';
          autocompleteList.style.display = 'none';
          input.placeholder = "Used existing skill";
          setTimeout(() => {
            input.placeholder = "Type a skill and press Enter...";
          }, 2000);
        } else {
          alert('Error adding skill: ' + result.error);
        }
      }
    } catch (error) {
      console.error('Error adding skill:', error);
      alert('Error adding skill. Please try again.');
    } finally {
      // Re-enable input
      input.disabled = false;
      if (input.placeholder === "Adding skill...") {
        input.placeholder = "Type a skill and press Enter...";
      }
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
    addNewSkillToDatabase,
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

