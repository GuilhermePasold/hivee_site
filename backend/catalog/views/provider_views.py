from django.shortcuts import get_object_or_404, render

from ..models import Category, Provider


def listar_prestadores(request):
    query = request.GET.get("q", "").strip()
    providers = Provider.objects.select_related("category").all()
    categories = Category.objects.all()

    if query:
        terms = query.lower().split()

        def matches(provider):
            haystack = " ".join(
                [
                    provider.name,
                    provider.headline,
                    provider.bio,
                    provider.city,
                    provider.neighborhood,
                    provider.category.name,
                    " ".join(provider.skills),
                ]
            ).lower()
            return all(term in haystack for term in terms)

        providers = [provider for provider in providers if matches(provider)]

    return render(
        request,
        "catalog/index.html",
        {
            "providers": providers,
            "categories": categories,
            "titulo_aba": "Prestadores HIVEE",
            "mostrar_busca": True,
            "query": query,
        },
    )


def detalhe_prestador(request, slug):
    provider = get_object_or_404(
        Provider.objects.select_related("category").prefetch_related("images"),
        slug=slug,
    )
    return render(
        request,
        "catalog/detalhe.html",
        {"provider": provider, "imagens_adicionais": provider.images.all()},
    )
