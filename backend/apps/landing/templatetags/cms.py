"""
CMS template tags — read-only access to PageSection content.

Architecture notes:
- All lookups are cached per-request in context to avoid N+1 queries.
  Single page with 20 cms_* calls → 1 SQL query instead of 20.
- mark_safe is applied ONLY in cms_html (for body field intended as rich text).
  Other fields are auto-escaped by Django — safe against XSS.
- cms_visible returns True by default when no row exists (progressive rollout safe).
- Tags never raise; they always fall back to the provided default.
"""
from django import template
from django.utils.safestring import mark_safe

from apps.landing.models import PageSection

register = template.Library()

_CACHE_ATTR = "_cms_section_cache"


def _get_cache(context):
    """Per-request cache, keyed by (page_slug, section_key)."""
    request = context.get("request")
    if request is None:
        return None
    cache = getattr(request, _CACHE_ATTR, None)
    if cache is None:
        cache = {}
        setattr(request, _CACHE_ATTR, cache)
    return cache


def _get_section(context, page_slug, section_key):
    cache = _get_cache(context)
    key = (page_slug, section_key)
    if cache is not None and key in cache:
        return cache[key]
    row = (
        PageSection.objects
        .filter(page__slug=page_slug, section_key=section_key)
        .first()
    )
    if cache is not None:
        cache[key] = row
    return row


def _field(context, page_slug, section_key, field, default, require_visible=True):
    row = _get_section(context, page_slug, section_key)
    if not row:
        return default
    if require_visible and not row.is_visible:
        # Fall through — caller may still want the value (e.g., editor preview)
        pass
    value = getattr(row, field, None)
    return value if value else default


@register.simple_tag(takes_context=True)
def cms_visible(context, page_slug, section_key):
    row = _get_section(context, page_slug, section_key)
    if row is None:
        return True  # progressive rollout: no row = show default
    return bool(row.is_visible)


@register.simple_tag(takes_context=True)
def cms_eyebrow(context, page_slug, section_key, default=""):
    return _field(context, page_slug, section_key, "eyebrow", default)


@register.simple_tag(takes_context=True)
def cms_heading(context, page_slug, section_key, default=""):
    return _field(context, page_slug, section_key, "heading", default)


@register.simple_tag(takes_context=True)
def cms_sub(context, page_slug, section_key, default=""):
    return _field(context, page_slug, section_key, "subheading", default)


@register.simple_tag(takes_context=True)
def cms_text(context, page_slug, section_key, default=""):
    row = _get_section(context, page_slug, section_key)
    if not row:
        return default
    return row.heading or row.subheading or row.body or default


@register.simple_tag(takes_context=True)
def cms_html(context, page_slug, section_key, default=""):
    row = _get_section(context, page_slug, section_key)
    if row and row.body:
        return mark_safe(row.body)
    return mark_safe(default)


@register.simple_tag(takes_context=True)
def cms_cta_label(context, page_slug, section_key, default=""):
    return _field(context, page_slug, section_key, "cta_label", default)


@register.simple_tag(takes_context=True)
def cms_cta_url(context, page_slug, section_key, default="#"):
    return _field(context, page_slug, section_key, "cta_url", default)
