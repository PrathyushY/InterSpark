// Base layout shared scripts (extracted from base.html)
(function(){
  window.toggleMobileMenu = function() {
    const menu = document.getElementById('mobile-menu');
    if (menu) menu.classList.toggle('hidden');
  };

  window.dismissAlert = function(alertId){
    const alertElement = document.getElementById(alertId);
    if (!alertElement) return;
    alertElement.style.animation = 'slideUp 0.3s ease-out forwards';
    setTimeout(()=>{
      if (alertElement && alertElement.parentNode){
        alertElement.remove();
        const container = document.getElementById('alert-container');
        if (container && container.children.length === 0){
          container.style.display = 'none';
        }
      }
    },300);
  };

  document.addEventListener('DOMContentLoaded',()=>{
    // Auto-dismiss success messages after 5s (staggered)
    const successAlerts = document.querySelectorAll('.alert-success');
    successAlerts.forEach((alert, idx)=>{
      setTimeout(()=>{ if (alert && alert.id) dismissAlert(alert.id); }, 5000 + idx*500);
    });
  });
})();
