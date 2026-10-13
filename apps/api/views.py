from django.shortcuts import render


def api_docs_view(request):
    """Interactive Swagger/OpenAPI documentation page for FreelanceFlow REST API."""
    return render(request, 'api/docs.html', {})
