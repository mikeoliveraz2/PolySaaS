// Inject custom buttons into Swagger UI

function injectSwaggerButtons() {
    var swaggerHeader = document.querySelector('.swagger-ui .topbar');
    if (swaggerHeader && !document.getElementById('dose-swagger-btns')) {
        var btnContainer = document.createElement('div');
        btnContainer.id = 'dose-swagger-btns';
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
}

// Try to inject buttons every 500ms until found
var interval = setInterval(function() {
    injectSwaggerButtons();
    if (document.getElementById('dose-swagger-btns')) {
        clearInterval(interval);
    }
}, 500);
