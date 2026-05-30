from django.http import JsonResponse

def postman_collection(request):
    # Build a collection from the URL patterns
    from django.urls import get_resolver
    resolver = get_resolver()
    items = []
    for pattern in resolver.url_patterns:
        # simplified: extract view names, methods, paths
        items.append({
            "name": str(pattern.pattern),
            "request": {"method": "GET", "url": "{{base_url}}/" + str(pattern.pattern)}
        })
    return JsonResponse({
        "info": {"name": "Memora API", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
        "item": items
    })
