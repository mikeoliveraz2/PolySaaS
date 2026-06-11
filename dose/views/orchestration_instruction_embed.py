"""Minimal Instruction add/change for orchestration modal iframe (no admin chrome)."""

# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Orchestration Bar + Instruction Embed — commit 8cd810c0
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator

from urllib.parse import quote

from dose.admin import InstructionAdmin, _allow_sameorigin_iframe
from dose.models import Instruction


class EmbedInstructionAdmin(InstructionAdmin):
    """Same as InstructionAdmin but renders form-only template for modal iframe."""

    change_form_template = 'admin/dose/instruction/embed_form.html'
    show_save_and_add = False
    show_save_and_continue = False

    def _orch_theme_context(self, request):
        from dose.views.orchestration import _resolve_active_bootswatch_theme
        theme, mode = _resolve_active_bootswatch_theme(request)
        theme = request.GET.get('orch_theme') or request.POST.get('_orch_theme') or theme
        mode = request.GET.get('orch_mode') or request.POST.get('_orch_mode') or mode
        dark_themes = {'darkly', 'cyborg', 'slate', 'solar', 'superhero'}
        return {
            'orch_active_theme': theme,
            'orch_display_mode': mode,
            'orch_is_dark': mode == 'dark' or theme in dark_themes,
        }

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context.update(self._orch_theme_context(request))
        return super().render_change_form(
            request, context, add=add, change=change, form_url=form_url, obj=obj
        )

    def _theme_query(self, request):
        theme = request.POST.get('_orch_theme') or request.GET.get('orch_theme')
        mode = request.POST.get('_orch_mode') or request.GET.get('orch_mode')
        if not theme and not mode:
            return ''
        qs = ''
        if theme:
            qs += '&orch_theme=' + quote(theme, safe='')
        if mode:
            qs += '&orch_mode=' + quote(mode, safe='')
        return qs

    @method_decorator(_allow_sameorigin_iframe)
    def add_view(self, request, form_url='', extra_context=None):
        q = request.GET.copy()
        q['_popup'] = '1'
        request.GET = q
        return super().add_view(request, form_url, extra_context)

    @method_decorator(_allow_sameorigin_iframe)
    def change_view(self, request, object_id, form_url='', extra_context=None):
        q = request.GET.copy()
        q['_popup'] = '1'
        request.GET = q
        return super().change_view(request, object_id, form_url, extra_context)

    def response_add(self, request, obj, post_url_continue=None):
        url = reverse('dose:orchestration_instruction_embed_change', args=[obj.pk])
        return HttpResponseRedirect(url + '?_popup=1&saved=1' + self._theme_query(request))

    def response_change(self, request, obj):
        return HttpResponseRedirect(request.path + '?_popup=1&saved=1' + self._theme_query(request))


def _embed_admin():
    return EmbedInstructionAdmin(Instruction, admin.site)


@login_required
@staff_member_required
def orchestration_instruction_embed_add(request):
    return _embed_admin().add_view(request)


@login_required
@staff_member_required
def orchestration_instruction_embed_change(request, object_id):
    return _embed_admin().change_view(request, str(object_id))
