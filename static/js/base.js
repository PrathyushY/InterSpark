// Base layout shared scripts (extracted from base.html)
(function () {
  window.toggleMobileMenu = function () {
    const menu = document.getElementById('mobile-menu');
    if (menu) menu.classList.toggle('hidden');
  };

  window.dismissAlert = function (alertId) {
    const alertElement = document.getElementById(alertId);
    if (!alertElement) return;
    alertElement.style.animation = 'slideUp 0.3s ease-out forwards';
    setTimeout(() => {
      if (alertElement && alertElement.parentNode) {
        alertElement.remove();
        const container = document.getElementById('alert-container');
        if (container && container.children.length === 0) {
          container.style.display = 'none';
        }
      }
    }, 300);
  };

  // Unified alert system that matches the base template styling
  window.showAlert = function (message, type = 'info') {
    let container = document.getElementById('alert-container');

    // Create container if it doesn't exist
    if (!container) {
      container = document.createElement('div');
      container.id = 'alert-container';
      container.className = 'fixed top-4 left-1/2 transform -translate-x-1/2 z-50 w-full max-w-md px-4 space-y-3';
      document.body.appendChild(container);
    }

    container.style.display = 'block';

    // Generate unique alert ID
    const alertId = 'alert-' + Date.now();

    // Determine styling based on type
    let bgClass, borderClass, textClass, iconClass, icon, buttonClass;
    if (type === 'error') {
      bgClass = 'bg-red-50/95';
      borderClass = 'border-red-200';
      textClass = 'text-red-700';
      iconClass = 'text-red-400';
      icon = 'fas fa-exclamation-circle';
      buttonClass = 'text-red-500 hover:bg-red-100 focus:ring-red-600 focus:ring-offset-red-50';
    } else if (type === 'success') {
      bgClass = 'bg-green-50/95';
      borderClass = 'border-green-200';
      textClass = 'text-green-700';
      iconClass = 'text-green-400';
      icon = 'fas fa-check-circle';
      buttonClass = 'text-green-500 hover:bg-green-100 focus:ring-green-600 focus:ring-offset-green-50';
    } else {
      bgClass = 'bg-blue-50/95';
      borderClass = 'border-blue-200';
      textClass = 'text-blue-700';
      iconClass = 'text-blue-400';
      icon = 'fas fa-info-circle';
      buttonClass = 'text-blue-500 hover:bg-blue-100 focus:ring-blue-600 focus:ring-offset-blue-50';
    }

    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} p-4 rounded-lg shadow-lg relative backdrop-blur-sm ${bgClass} border ${borderClass} ${textClass}`;
    alertDiv.id = alertId;
    alertDiv.style.animation = 'slideDown 0.3s ease-out';

    alertDiv.innerHTML = `
      <div class="flex justify-between items-start">
        <div class="flex">
          <div class="flex-shrink-0">
            <i class="${icon} ${iconClass}"></i>
          </div>
          <div class="ml-3">
            <p class="text-sm font-medium">${message}</p>
          </div>
        </div>
        <div class="ml-auto pl-3">
          <div class="-mx-1.5 -my-1.5">
            <button type="button" onclick="dismissAlert('${alertId}')" class="inline-flex rounded-md p-1.5 ${buttonClass} focus:outline-none focus:ring-2 focus:ring-offset-2">
              <span class="sr-only">Dismiss</span>
              <i class="fas fa-times text-sm"></i>
            </button>
          </div>
        </div>
      </div>
    `;

    // Add to container
    container.appendChild(alertDiv);

    // Auto-dismiss success messages after 5s
    if (type === 'success') {
      setTimeout(() => {
        if (document.getElementById(alertId)) {
          dismissAlert(alertId);
        }
      }, 5000);
    }
  };

  document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss success messages after 5s (staggered)
    const successAlerts = document.querySelectorAll('.alert-success');
    successAlerts.forEach((alert, idx) => {
      setTimeout(() => { if (alert && alert.id) dismissAlert(alert.id); }, 5000 + idx * 500);
    });
  });
})();
