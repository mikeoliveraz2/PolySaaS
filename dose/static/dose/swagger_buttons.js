// Inject custom buttons into Swagger UI
window.addEventListener('DOMContentLoaded', function() {
    var swaggerHeader = document.querySelector('.swagger-ui .topbar');
    if (swaggerHeader) {
        var btnContainer = document.createElement('div');
        btnContainer.style.display = 'flex';
        btnContainer.style.gap = '1rem';
        btnContainer.style.marginLeft = '2rem';

        var dashboardBtn = document.createElement('a');
        dashboardBtn.href = '/dose/dashboard/';
        dashboardBtn.className = 'btn btn-primary';
        dashboardBtn.textContent = 'Back to Dashboard';
        dashboardBtn.style.padding = '8px 16px';
        dashboardBtn.style.background = '#2c3e50';
        dashboardBtn.style.color = '#fff';
        dashboardBtn.style.borderRadius = '4px';
        dashboardBtn.style.textDecoration = 'none';

        var adminBtn = document.createElement('a');
        adminBtn.href = '/admin/';
        adminBtn.className = 'btn btn-secondary';
        adminBtn.textContent = 'Admin Interface';
        adminBtn.style.padding = '8px 16px';
        adminBtn.style.background = '#3498db';
        adminBtn.style.color = '#fff';
        adminBtn.style.borderRadius = '4px';
        adminBtn.style.textDecoration = 'none';

        btnContainer.appendChild(dashboardBtn);
        btnContainer.appendChild(adminBtn);
        swaggerHeader.appendChild(btnContainer);
    }
});
