








You said
Light and dark. And can you summarize all the above in one page so I can save it in my project
Copilot said
Overview
Persistent per-user Jazzmin theme with separate light and dark theme choices, a top-menu link, and dynamic application via a context processor. Includes: user profile model, signal, admin theme selector view and template with light/dark mapping, URL, Jazzmin settings entry, and context processor to inject JAZZMIN_UI_TWEAKS.

Models and Signal
models.py

python


Copy
from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    light_theme = models.CharField(max_length=50, default="flatly")
    dark_theme = models.CharField(max_length=50, default="darkly")
    use_system_pref = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} profile"
signals.py

python


Copy
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        UserProfile.objects.get_or_create(user=instance)
Register signals in your app config:

python


Copy
# apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = "yourapp"
    def ready(self):
        import yourapp.signals
Admin Theme Selector View and Template
admin_views.py

python


Copy
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

THEMES = ["flatly","cerulean","cosmo","cyborg","darkly","journal","litera","lumen","lux","minty","pulse","sandstone","simplex","sketchy","slate","solar","spacelab","superhero","united","yeti"]

@login_required
def select_theme(request):
    profile = request.user.userprofile
    if request.method == "POST":
        profile.light_theme = request.POST.get("light_theme")
        profile.dark_theme = request.POST.get("dark_theme")
        profile.use_system_pref = request.POST.get("use_system_pref") == "on"
        profile.save()
        return redirect("/admin/")
    return render(request, "admin/select_theme.html", {
        "themes": THEMES,
        "light_theme": profile.light_theme,
        "dark_theme": profile.dark_theme,
        "use_system_pref": profile.use_system_pref,
    })
templates/admin/select_theme.html

html


Copy
{% extends "admin/base_site.html" %}
{% block content %}
  <h2>Admin Theme Settings</h2>
  <form method="post">{% csrf_token %}
    <label for="light_theme">Light theme</label>
    <select name="light_theme" id="light_theme">
      {% for t in themes %}
        <option value="{{ t }}" {% if t == light_theme %}selected{% endif %}>{{ t }}</option>
      {% endfor %}
    </select>

    <br><br>
    <label for="dark_theme">Dark theme</label>
    <select name="dark_theme" id="dark_theme">
      {% for t in themes %}
        <option value="{{ t }}" {% if t == dark_theme %}selected{% endif %}>{{ t }}</option>
      {% endfor %}
    </select>

    <br><br>
    <label>
      <input type="checkbox" name="use_system_pref" {% if use_system_pref %}checked{% endif %}>
      Use system dark mode preference
    </label>

    <br><br>
    <button type="submit">Save</button>
  </form>
{% endblock %}
URL and Top Menu Entry
urls.py

python


Copy
from django.urls import path
from . import admin_views

urlpatterns = [
    path("admin/select-theme/", admin_views.select_theme, name="select_theme"),
]
settings.py — add to JAZZMIN_SETTINGS

python


Copy
JAZZMIN_SETTINGS = {
    "topmenu_links": [
        {"name": "Select Theme", "url": "select_theme", "permissions": ["auth.view_user"]},
    ],
}
Context Processor (dynamic Jazzmin tweaks)
context_processors.py

python


Copy
def jazzmin_ui_tweaks(request):
    if not request.user.is_authenticated:
        return {}
    profile = getattr(request.user, "userprofile", None)
    if not profile:
        return {}
    # If user chose to follow system preference, pass both and let frontend handle switching
    return {
        "JAZZMIN_UI_TWEAKS": {
            "theme": profile.light_theme,
            "dark_mode_theme": profile.dark_theme,
        },
        "JAZZMIN_USE_SYSTEM_PREF": profile.use_system_pref,
    }
Add to TEMPLATES in settings.py

python


Copy
TEMPLATES = [
    {
        "OPTIONS": {
            "context_processors": [
                # existing processors...
                "yourapp.context_processors.jazzmin_ui_tweaks",
            ],
        },
    },
]
Migrations, Tests, and Optional Live Preview
Run migrations:

python manage.py  makemigrations

python manage.py  migrate

Quick test steps:

Create or use a staff user and open admin.

Click Top Menu → Select Theme.

Choose distinct light and dark themes, toggle system pref, save.

Verify admin UI changes on reload and when switching system theme if supported by browser.

Optional live preview: implement JS on select_theme template that stores preview choice in session via AJAX and reloads admin CSS without saving. The context processor should check session key before profile.

Notes for Integration
Mapping: Use separate light_theme and dark_theme fields for explicit mapping.

System preference: Set use_system_pref to true to let the browser/system determine dark vs light; handle with small JS that toggles a CSS class and optionally reloads the admin stylesheet.

Permissions: Restrict access to the selector view using staff-only decorator or permissions as desired.

Extensibility: Replace the simple form with a Django ModelForm for validation and admin integration if needed.

Save this file into your project as ADMIN_THEME_README.md and apply the code snippets into1
 the matching modules.

1
github.com
Continue the conversation

