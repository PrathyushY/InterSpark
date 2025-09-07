// Dashboard interactions
(function () {
    // Data provided via template: window.SAVED_PROFILES / window.SAVED_OPPORTUNITIES
    const savedProfilesRaw = window.SAVED_PROFILES || [];
    const savedOpportunitiesRaw = window.SAVED_OPPORTUNITIES || [];
    const profileOrder = savedProfilesRaw.map(sp => String((sp.profiles || sp).id || sp.profile_id)).filter(Boolean);
    const opportunityOrder = savedOpportunitiesRaw.map(so => String((so.opportunities || so).id || so.opportunity_id)).filter(Boolean);

    // Maps for quick lookup / count management (keys normalized to string)
    window.savedProfilesMap = {};
    savedProfilesRaw.forEach(sp => {
        const p = sp.profiles || sp;
        const id = (p && (p.id || sp.profile_id));
        if (id != null) window.savedProfilesMap[String(id)] = p;
    });
    window.savedOpportunitiesMap = {};
    savedOpportunitiesRaw.forEach(so => {
        const o = so.opportunities || so;
        const id = (o && (o.id || so.opportunity_id));
        if (id != null) window.savedOpportunitiesMap[String(id)] = o;
    });

    function qs(id) {
        return document.getElementById(id);
    }

    // Modal controls
    window.openModal = function (id) {
        const m = qs(id);
        if (!m) return;
        m.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    };
    window.closeModal = function (id) {
        const m = qs(id);
        if (!m) return;
        m.classList.add('hidden');
        document.body.style.overflow = 'auto';
    };

    document.addEventListener('click', e => {
        if (e.target.classList.contains('bg-black') && e.target.classList.contains('bg-opacity-50')) {
            e.target.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.fixed.inset-0:not(.hidden)').forEach(m => m.classList.add('hidden'));
            document.body.style.overflow = 'auto';
        }
    });

    // Update counts + hide/show view-all buttons, replace list with empty message when needed
    window.updateSavedCounts = function () {
        const pCountEl = qs('saved-profiles-count');
        if (pCountEl) {
            const cnt = Object.keys(window.savedProfilesMap).length;
            pCountEl.textContent = cnt;
            if (cnt === 0) pCountEl.classList.add('hidden'); else pCountEl.classList.remove('hidden');
            const btn = qs('saved-profiles-view-all-btn');
            if (btn) {
                if (cnt <= 2) btn.classList.add('hidden'); else btn.classList.remove('hidden');
            }
            if (cnt === 0) {
                const list = qs('saved-profiles-list');
                if (list) {
                    const p = document.createElement('p');
                    p.className = 'text-gray-500 text-center py-8';
                    p.textContent = 'No saved profiles yet';
                    list.replaceWith(p);
                }
            }
        }
        const oCountEl = qs('saved-opps-count');
        if (oCountEl) {
            const cnt = Object.keys(window.savedOpportunitiesMap).length;
            oCountEl.textContent = cnt;
            if (cnt === 0) oCountEl.classList.add('hidden'); else oCountEl.classList.remove('hidden');
            const btn = qs('saved-opps-view-all-btn');
            if (btn) {
                if (cnt <= 2) btn.classList.add('hidden'); else btn.classList.remove('hidden');
            }
            if (cnt === 0) {
                const list = qs('saved-opportunities-list');
                if (list) {
                    const p = document.createElement('p');
                    p.className = 'text-gray-500 text-center py-8';
                    p.textContent = 'No saved opportunities yet';
                    list.replaceWith(p);
                }
            }
        }
    };

    // Delete opportunity (organization only)
    window.deleteOpportunity = async function (id, elementId) {
        if (!confirm('Delete this opportunity? This cannot be undone.')) return;
        try {
            const res = await fetch(`/delete_opportunity/${id}`, {method: 'POST'});
            const data = await res.json();
            if (data.success) {
                const el = qs(elementId);
                if (el) el.remove();
                showAlert(data.message || 'Opportunity deleted', 'success');
            } else showAlert(data.error || 'Delete failed', 'error');
        } catch (e) {
            showAlert('Error deleting opportunity', 'error');
        }
    };

    // Unsave opportunity (student side) / general
    window.unsaveOpportunity = async function (id, elementId) {
        const key = String(id);
        try {
            const res = await fetch(`/unsave_opportunity/${id}`, {method: 'POST'});
            const data = await res.json();
            if (data.success) {
                const el = qs(elementId);
                if (el) el.remove();
                const otherIds = [`saved-opp-${key}`, `modal-saved-opp-${key}`];
                otherIds.forEach(oid => {
                    if (oid !== elementId) {
                        const o = qs(oid);
                        if (o) o.remove();
                    }
                });
                delete window.savedOpportunitiesMap[key];
                updateSavedCounts();
                const modal = qs('savedOpportunitiesModal');
                if (modal && !modal.querySelector('[id^="modal-saved-opp-"]')) closeModal('savedOpportunitiesModal');
                showAlert(data.message || 'Opportunity removed from saved', 'info');
            } else showAlert(data.error || 'Remove failed', 'error');
        } catch (e) {
            showAlert('Error removing saved opportunity', 'error');
        }
    };

    // Unsave profile
    window.unsaveProfile = async function (id, elementId) {
        const key = String(id);
        try {
            const res = await fetch(`/unsave_profile/${id}`, {method: 'POST'});
            const data = await res.json();
            if (data.success) {
                const el = qs(elementId);
                if (el) el.remove();
                const otherIds = [`saved-profile-${key}`, `modal-saved-profile-${key}`];
                otherIds.forEach(oid => {
                    if (oid !== elementId) {
                        const o = qs(oid);
                        if (o) o.remove();
                    }
                });
                delete window.savedProfilesMap[key];
                updateSavedCounts();
                const modal = qs('savedProfilesModal');
                if (modal && !modal.querySelector('[id^="modal-saved-profile-"]')) closeModal('savedProfilesModal');
                showAlert(data.message || 'Profile removed from saved', 'info');
            } else showAlert(data.error || 'Remove failed', 'error');
        } catch (e) {
            showAlert('Error removing profile', 'error');
        }
    };

    function buildProfileCard(p) {
        const pid = p.id || p.profile_id;
        return `<div id="saved-profile-${pid}" class="group border border-gray-200 rounded-lg p-6 hover:bg-gray-50 transition duration-200 flex flex-col justify-between min-h-[180px] h-full">\n      <div class="flex-1 flex flex-col">\n        <a href="/profile/${pid}" class="flex-1 min-w-0 flex flex-col">\n          <h4 class="text-sm font-medium text-gray-900 truncate">${escapeHtml(p.name || p.organization_name || 'Anonymous')}</h4>\n          <p class="text-xs text-gray-500 truncate">${escapeHtml(p.email || 'No email')}</p>\n          <div class="flex items-center mt-2 space-x-2">\n            ${p.school ? `<span class=\"inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800\">${escapeHtml(p.school)}</span>` : ''}\n            ${p.grade ? `<span class=\"inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800\">${escapeHtml(p.grade)}</span>` : ''}\n            ${(!p.school && !p.grade) ? '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-transparent text-transparent select-none">info</span>' : ''}\n          </div>\n          ${p.bio ? `<p class=\"text-[11px] text-gray-400 mt-2 line-clamp-2\">${escapeHtml(p.bio)}</p>` : '<span class="mt-2 text-[11px] text-transparent select-none">Biography not available</span>'}\n        </a>\n      </div>\n      <div class="flex flex-row items-center justify-between mt-4">\n        <a href="/profile/${pid}" class="text-blue-600 hover:text-blue-800 text-xs">View</a>\n        <button title="Remove" onclick="unsaveProfile('${pid}', 'saved-profile-${pid}')" class="text-red-500 hover:text-red-700 text-xs"><i class="fas fa-times"></i></button>\n      </div>\n    </div>`;
    }

    function buildOpportunityCard(o) {
        const oid = o.id || o.opportunity_id;
        const company = (o.profiles && (o.profiles.organization_name || o.profiles.name)) || 'Company';
        return `<div id="saved-opp-${oid}" class="group border border-gray-200 rounded-lg p-6 hover:bg-gray-50 transition duration-200 flex flex-col justify-between min-h-[180px] h-full">\n      <div class="flex-1 flex flex-col">\n        <a href="/opportunity/${oid}" class="flex-1 min-w-0 flex flex-col">\n          <h4 class="text-sm font-medium text-gray-900 truncate">${escapeHtml(o.title || 'Untitled Opportunity')}</h4>\n          <p class="text-xs text-gray-500 truncate">${escapeHtml(company)}</p>\n          <div class="flex items-center mt-2 space-x-2">\n            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">${escapeHtml(o.type || 'Opportunity')}</span>\n            ${o.location ? `<span class=\"inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600\"><i class=\"fas fa-map-marker-alt mr-1\"></i>${escapeHtml(o.location)}</span>` : '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-transparent text-transparent select-none">loc</span>'}\n          </div>\n          ${o.description ? `<p class=\"text-[11px] text-gray-400 mt-2 line-clamp-2\">${escapeHtml(o.description)}</p>` : '<span class="mt-2 text-[11px] text-transparent select-none">placeholder</span>'}\n        </a>\n      </div>\n      <div class="flex flex-row items-center justify-between mt-4">\n        <a href="/opportunity/${oid}" class="text-blue-600 hover:text-blue-800 text-xs">View</a>\n        <button title="Remove" onclick="unsaveOpportunity('${oid}', 'saved-opp-${oid}')" class="text-red-500 hover:text-red-700 text-xs"><i class="fas fa-times"></i></button>\n      </div>\n    </div>`;
    }

    function escapeHtml(str) {
        return String(str).replace(/[&<>"']/g, s => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            "\"": "&quot;",
            "'": "&#39;"
        }[s]));
    }

    function replenish(type) {
        const containerId = type === 'profile' ? 'saved-profiles-list' : 'saved-opportunities-list';
        const container = qs(containerId);
        if (!container) return;
        const desired = 2;
        const prefix = type === 'profile' ? 'saved-profile-' : 'saved-opp-';
        const currentCards = Array.from(container.children).filter(c => c.id && c.id.startsWith(prefix));
        if (currentCards.length >= desired) return;
        const order = type === 'profile' ? profileOrder : opportunityOrder;
        const map = type === 'profile' ? window.savedProfilesMap : window.savedOpportunitiesMap;
        const existingIds = new Set(currentCards.map(c => c.id.substring(prefix.length))); // string ids
        for (const rawId of order) {
            const id = String(rawId);
            if (!map[id]) continue; // removed
            if (existingIds.has(id)) continue; // already present
            const raw = (type === 'profile' ? savedProfilesRaw : savedOpportunitiesRaw).find(r => {
                const obj = r.profiles || r.opportunities || r;
                const rid = (obj.id || r.profile_id || r.opportunity_id);
                return String(rid) === id;
            });
            if (!raw) continue;
            const obj = raw.profiles || raw.opportunities || raw;
            const html = type === 'profile' ? buildProfileCard(obj) : buildOpportunityCard(obj);
            container.insertAdjacentHTML('beforeend', html);
            existingIds.add(id);
            if (existingIds.size >= desired) break;
        }
    }

    // Patch after counts update
    const originalUpdate = window.updateSavedCounts;
    window.updateSavedCounts = function () {
        originalUpdate();
        replenish('profile');
        replenish('opportunity');
    };
    // Immediately attempt initial replenish (in case only 1 rendered due to initial data anomaly)
    replenish('profile');
    replenish('opportunity');

    // Initial counts sync
    updateSavedCounts();
})();
