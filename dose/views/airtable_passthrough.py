#!/usr/bin/env python
"""
Custom Airtable passthrough view - NO IFRAMES
Proxies Airtable content directly through middleware passthrough
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

@login_required
def airtable_passthrough_view(request):
    """
    Redirect to the passthrough endpoint (handled by ExternalPassthroughMiddleware)
    The middleware will intercept /pt/admin/airtable/ and proxy to Airtable
    """
    # Forward to the passthrough path - middleware handles the rest
    return HttpResponseRedirect('/pt/admin/airtable/')
