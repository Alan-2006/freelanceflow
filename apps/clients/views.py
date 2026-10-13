from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from core.permissions import freelancer_required

from .forms import ClientForm
from .models import Client
from .services import ClientService


@freelancer_required
def client_list_view(request):
    freelancer = request.user.profile
    queryset = freelancer.clients.all()

    # Search query
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(name__icontains=q) |
            Q(company__icontains=q) |
            Q(email__icontains=q) |
            Q(tags__icontains=q)
        )

    # Filter by tag
    tag_filter = request.GET.get('tag', '').strip()
    if tag_filter:
        queryset = queryset.filter(tags__icontains=tag_filter)

    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'reliability':
        queryset = queryset.order_by('-reliability_score')
    elif sort_by == 'recent':
        queryset = queryset.order_by('-created_at')
    else:
        queryset = queryset.order_by('company', 'name')

    # Gather all unique tags across clients
    all_tags = set()
    for c in freelancer.clients.all():
        for t in c.tag_list:
            all_tags.add(t)

    return render(request, 'clients/list.html', {
        'clients': queryset,
        'search_query': q,
        'tag_filter': tag_filter,
        'all_tags': sorted(list(all_tags)),
        'sort_by': sort_by,
    })


@freelancer_required
def client_create_view(request):
    freelancer = request.user.profile
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.freelancer = freelancer
            client.save()
            client.get_or_create_portal_token()
            messages.success(request, f"Client '{client.display_title}' added successfully!")
            return redirect('clients:detail', pk=client.pk)
    else:
        form = ClientForm(initial={
            'currency': freelancer.currency,
            'timezone': freelancer.timezone,
        })

    return render(request, 'clients/form.html', {
        'form': form,
        'title': 'Add New Client'
    })


@freelancer_required
def client_detail_view(request, pk):
    freelancer = request.user.profile
    client = get_object_or_404(Client, pk=pk, freelancer=freelancer)

    # Financial summary
    summary = ClientService.get_client_financial_summary(client)
    ClientService.recalculate_reliability_score(client)

    # Magic link portal URL
    token = client.get_or_create_portal_token()
    portal_url = request.build_absolute_uri(f"/portal/access/{token}/")

    invoices = client.invoices.all()[:10] if hasattr(client, 'invoices') else []

    return render(request, 'clients/detail.html', {
        'client': client,
        'summary': summary,
        'portal_url': portal_url,
        'projects': client.projects.all()[:10],
        'invoices': invoices,
    })


@freelancer_required
def client_update_view(request, pk):
    freelancer = request.user.profile
    client = get_object_or_404(Client, pk=pk, freelancer=freelancer)

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f"Client '{client.display_title}' updated.")
            return redirect('clients:detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)

    return render(request, 'clients/form.html', {
        'form': form,
        'client': client,
        'title': f"Edit Client - {client.display_title}"
    })


@freelancer_required
def client_delete_view(request, pk):
    freelancer = request.user.profile
    client = get_object_or_404(Client, pk=pk, freelancer=freelancer)

    if request.method == 'POST':
        title = client.display_title
        client.delete()
        messages.success(request, f"Client '{title}' has been removed.")
        return redirect('clients:list')

    return render(request, 'clients/confirm_delete.html', {'client': client})
