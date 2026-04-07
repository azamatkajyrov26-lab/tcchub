"""Staff-only content admin for the TCC HUB landing page.

Provides a custom editorial admin UI (separate from Django admin) to
create / edit / reorder / hide / delete ContentBlock instances safely.
"""
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import ContentBlock


def _is_staff(u):
    return u.is_authenticated and u.is_staff


staff_required = user_passes_test(_is_staff, login_url="/login/")


@staff_required
def content_list(request):
    blocks = ContentBlock.objects.all()
    return render(request, "landing/admin/content_list.html", {
        "blocks": blocks,
        "block_types": ContentBlock.BLOCK_TYPES,
    })


@staff_required
def content_create(request):
    if request.method == "POST":
        block_type = request.POST.get("block_type", "text")
        # Place new block at the end.
        next_order = (ContentBlock.objects.values_list("order", flat=True)
                                           .order_by("-order").first() or 0) + 10
        block = ContentBlock.objects.create(
            block_type=block_type,
            heading="Новый блок",
            order=next_order,
            is_visible=False,  # safer: created hidden
        )
        return HttpResponseRedirect(reverse("landing-admin:edit", args=[block.pk]))
    return render(request, "landing/admin/content_create.html", {
        "block_types": ContentBlock.BLOCK_TYPES,
    })


@staff_required
def content_edit(request, pk):
    block = get_object_or_404(ContentBlock, pk=pk)
    if not block.is_editable and request.method == "POST":
        # Non-editable types: only allow visibility + order via other endpoints.
        raise Http404("Этот блок не поддерживает редактирование текста.")
    if request.method == "POST":
        block.eyebrow = request.POST.get("eyebrow", "")
        block.heading = request.POST.get("heading", "")
        block.subheading = request.POST.get("subheading", "")
        block.body = request.POST.get("body", "")
        block.cta_label = request.POST.get("cta_label", "")
        block.cta_url = request.POST.get("cta_url", "")
        if "image" in request.FILES:
            block.image = request.FILES["image"]
        if request.POST.get("remove_image") == "1":
            block.image = None
        block.save()
        return HttpResponseRedirect(reverse("landing-admin:list"))
    return render(request, "landing/admin/content_edit.html", {"block": block})


@staff_required
@require_POST
def content_delete(request, pk):
    block = get_object_or_404(ContentBlock, pk=pk)
    block.delete()
    return HttpResponseRedirect(reverse("landing-admin:list"))


@staff_required
@require_POST
def content_toggle(request, pk):
    block = get_object_or_404(ContentBlock, pk=pk)
    block.is_visible = not block.is_visible
    block.save(update_fields=["is_visible", "updated_at"])
    if request.headers.get("X-Requested-With") == "fetch":
        return JsonResponse({"is_visible": block.is_visible})
    return HttpResponseRedirect(reverse("landing-admin:list"))


@staff_required
@require_POST
def content_move(request, pk, direction):
    block = get_object_or_404(ContentBlock, pk=pk)
    siblings = list(ContentBlock.objects.all())
    idx = next((i for i, b in enumerate(siblings) if b.pk == block.pk), None)
    if idx is None:
        return HttpResponseRedirect(reverse("landing-admin:list"))
    target = idx - 1 if direction == "up" else idx + 1
    if 0 <= target < len(siblings):
        other = siblings[target]
        block.order, other.order = other.order, block.order
        # Ensure distinct orders (in case of collisions).
        if block.order == other.order:
            other.order += 1
        block.save(update_fields=["order", "updated_at"])
        other.save(update_fields=["order", "updated_at"])
    return HttpResponseRedirect(reverse("landing-admin:list"))
