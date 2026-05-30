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
from django.utils.html import escape
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


# ── i18n for DB-driven SiteItem content ──
# Translations live in SiteItem.data['i18n'] = {'kz': {...}, 'en': {...}}.
# The Russian value rendered server-side stays the source of truth; this tag
# emits sibling `data-i18n-en`/`data-i18n-kz` attributes that i18n.js swaps in
# on language change (falling back to the rendered RU when a value is missing).

def _i18n_value(item, lang, field, idx=None):
    data = getattr(item, "data", None) or {}
    block = (data.get("i18n") or {}).get(lang) or {}
    val = block.get(field)
    if idx is not None:
        if isinstance(val, (list, tuple)) and 0 <= idx < len(val):
            val = val[idx]
        else:
            return None
    if val is None or val == "":
        return None
    return str(val)


@register.simple_tag
def i18n_attr(item, field, idx=None):
    """Render ` data-i18n-en="..." data-i18n-kz="..."` for a SiteItem field.

    `idx` selects an element when the field is a list (e.g. data.bullets).
    Returns an empty string when no translations exist (JS then keeps RU).
    """
    parts = []
    for lang in ("en", "kz"):
        v = _i18n_value(item, lang, field, idx)
        if v:
            parts.append('data-i18n-%s="%s"' % (lang, escape(v)))
    if not parts:
        return ""
    return mark_safe(" " + " ".join(parts))


@register.simple_tag
def i18n_blk(obj, field, idx=None):
    """Like i18n_attr but for plain dicts carrying obj['i18n'] = {'en':..,'kz':..}.

    Used for hardcoded ARTICLES content blocks localized in the view
    (apps/web/views.py::_localize_article). `idx` selects a list element.
    """
    i18n = (obj.get("i18n") if isinstance(obj, dict) else None) or {}
    parts = []
    for lang in ("en", "kz"):
        v = (i18n.get(lang) or {}).get(field)
        if idx is not None:
            v = v[idx] if isinstance(v, (list, tuple)) and 0 <= idx < len(v) else None
        if v:
            parts.append('data-i18n-%s="%s"' % (lang, escape(str(v))))
    if not parts:
        return ""
    return mark_safe(" " + " ".join(parts))
