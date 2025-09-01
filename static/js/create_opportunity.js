// create_opportunity.js - extracted logic from template
(function () {
    const KEY = 'opportunityDraft';
    const editing = window.OPP_EDITING === true || window.OPP_EDITING === 'true';

    function getRequiredFields() {
        return ["title", "type", "category", "location", "requirements", "compensation", "duration", "application_deadline", "description"];
    }

    function saveFormLocally() {
        if (editing) return; // only for new drafts
        const data = {};
        getRequiredFields().forEach(f => {
            const el = document.getElementById(f);
            if (el) data[f] = el.value;
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
                const el = document.getElementById(f);
                if (el && data[f] !== undefined) el.value = data[f];
            });
        } catch (e) {
            console.warn('Restore draft failed', e);
        }
    }

    function clearFormLocally() {
        if (!editing) localStorage.removeItem(KEY);
    }

    function highlightRequiredFields(missing) {
        missing.forEach(f => {
            const el = document.getElementById(f);
            if (el) el.classList.add('required-highlight');
        });
    }

    function clearRequiredHighlights() {
        document.querySelectorAll('.required-highlight').forEach(el => el.classList.remove('required-highlight'));
    }

    function publishOpportunity() {
        clearRequiredHighlights();
        const missing = [];
        getRequiredFields().forEach(f => {
            const el = document.getElementById(f);
            if (el && !el.value) missing.push(f);
        });
        if (missing.length) {
            saveFormLocally();
            highlightRequiredFields(missing);
            alert('Missing required fields: ' + missing.join(', ') + '\nDraft saved locally. Complete all fields to publish.');
            return;
        }
        document.getElementById('status-field').value = 'active';
        let publishField = document.getElementById('publish-field');
        if (!publishField) {
            publishField = document.createElement('input');
            publishField.type = 'hidden';
            publishField.name = 'publish';
            publishField.id = 'publish-field';
            document.getElementById('opportunity-form').appendChild(publishField);
        }
        publishField.value = '1';
        clearFormLocally();
        document.getElementById('opportunity-form').submit();
    }

    function saveAsDraft() {
        document.getElementById('status-field').value = 'draft';
        clearFormLocally();
        document.getElementById('opportunity-form').submit();
    }

    function confirmCancel() {
        if (confirm('Are you sure you want to cancel? Any unsaved changes will be lost.')) {
            clearFormLocally();
            if (document.referrer && document.referrer !== window.location.href) window.location = document.referrer; else window.location = '/dashboard';
        }
    }

    function previewOpportunity() {
        const data = {};
        getRequiredFields().forEach(f => {
            const el = document.getElementById(f);
            data[f] = el ? el.value : '';
        });
        showPreviewModal(data);
    }

    function showPreviewModal(data) {
        const gradient = 'from-orange-500 to-blue-600';
        const badge = data.type === 'Internship' ? 'bg-orange-100 text-orange-800' : 'bg-blue-100 text-blue-800';
        const modalHTML = `\n    <div id="preview-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">\n      <div class=\"relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white\">\n        <div class=\"mt-3\">\n          <div class=\"flex justify-between items-center mb-4\">\n            <h3 class=\"text-lg font-medium text-gray-900\">Opportunity Preview</h3>\n            <button onclick=\"CO.closePreviewModal()\" class=\"text-gray-400 hover:text-gray-600\"><i class=\"fas fa-times text-xl\"></i></button>\n          </div>\n          <div class=\"bg-white rounded-lg shadow-md overflow-hidden\">\n            <div class=\"h-32 bg-gradient-to-br ${gradient} flex items-center justify-center\">\n              <i class=\"fas fa-briefcase text-white text-4xl\"></i>\n            </div>\n            <div class=\"p-6\">\n              <div class=\"flex items-center justify-between mb-4\">\n                <div class=\"flex items-center space-x-3\">\n                  <span class=\"inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${badge}\">${data.type || 'Type not specified'}</span>\n                  <span class=\"text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full\">${data.category || 'Category not specified'}</span>\n                </div>\n              </div>\n              <h1 class=\"text-2xl font-bold text-gray-900 mb-4\">${data.title || 'Opportunity Title'}</h1>\n              <div class=\"grid grid-cols-1 md:grid-cols-2 gap-6 mb-6\">\n                <div class=\"space-y-3\">\n                  <div class=\"flex items-center\"><i class=\"fas fa-map-marker-alt text-gray-400 w-5 mr-3\"></i><span class=\"text-gray-700\">${data.location || 'Location not specified'}</span></div>\n                  <div class=\"flex items-center\"><i class=\"fas fa-clock text-gray-400 w-5 mr-3\"></i><span class=\"text-gray-700\">${data.duration || 'Duration not specified'}</span></div>\n                  <div class=\"flex items-center\"><i class=\"fas fa-dollar-sign text-gray-400 w-5 mr-3\"></i><span class=\"text-gray-700\">${data.compensation || 'Compensation not specified'}</span></div>\n                </div>\n                <div class=\"space-y-3\">\n                  <div class=\"flex items-center\"><i class=\"fas fa-calendar text-gray-400 w-5 mr-3\"></i><span class=\"text-gray-700\">Deadline: ${data.application_deadline ? new Date(data.application_deadline).toLocaleDateString() : 'No deadline specified'}</span></div>\n                </div>\n              </div>\n              ${data.description ? `<div class=\"mb-6\"><h3 class=\"text-lg font-semibold text-gray-900 mb-3\">About This Opportunity</h3><p class=\"text-gray-700 leading-relaxed\">${data.description.replace(/\n/g, '<br>')}</p></div>` : ''}\n              ${data.requirements ? `<div class=\"mb-6\"><h3 class=\"text-lg font-semibold text-gray-900 mb-3\">Requirements</h3><ul class=\"space-y-2 text-gray-700\">${data.requirements.split('\n').filter(r => r.trim()).map(r => `<li class=\\"flex items-start\\"><i class=\\"fas fa-circle text-gray-400 mr-3 mt-2 flex-shrink-0\\" style=\\"font-size:6px;\\"></i><span>${r.trim()}</span></li>`).join('')}</ul></div>` : ''}\n            </div>\n          </div>\n          <div class=\"flex justify-end mt-6 space-x-3\">\n            <button onclick=\"CO.closePreviewModal()\" class=\"bg-gray-300 hover:bg-gray-400 text-gray-800 font-medium py-2 px-4 rounded\">Close Preview</button>\n          </div>\n        </div>\n      </div>\n    </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    function closePreviewModal() {
        const m = document.getElementById('preview-modal');
        if (m) m.remove();
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
        clearRequiredHighlights
    };

    document.addEventListener('DOMContentLoaded', () => {
        restoreFormLocally();
        // Auto-save typing
        getRequiredFields().forEach(f => {
            const el = document.getElementById(f);
            if (el) {
                el.addEventListener('input', () => {
                    saveFormLocally();
                    el.classList.remove('required-highlight');
                });
            }
        });
        window.addEventListener('beforeunload', saveFormLocally);
    });
})();

