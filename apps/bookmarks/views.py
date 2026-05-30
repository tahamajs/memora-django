from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
import requests
from bs4 import BeautifulSoup
from .models import BookmarkCollection, Bookmark
from .serializers import BookmarkCollectionSerializer, BookmarkSerializer

class BookmarkCollectionViewSet(viewsets.ModelViewSet):
    serializer_class = BookmarkCollectionSerializer

    def get_queryset(self):
        return BookmarkCollection.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookmarkViewSet(viewsets.ModelViewSet):
    serializer_class = BookmarkSerializer

    def get_queryset(self):
        return Bookmark.objects.filter(collection__user=self.request.user)

    def perform_create(self, serializer):
        # Auto‑fetch metadata from URL
        url = self.request.data.get('url', '')
        if url:
            metadata = self._fetch_metadata(url)
            serializer.save(**metadata)
        else:
            serializer.save()

    def _fetch_metadata(self, url):
        try:
            response = requests.get(url, timeout=5, headers={'User-Agent': 'Memora/1.0'})
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else url
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            description = desc_tag['content'] if desc_tag else ''
            favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
            favicon_url = favicon['href'] if favicon else ''
            if favicon_url and not favicon_url.startswith('http'):
                from urllib.parse import urljoin
                favicon_url = urljoin(url, favicon_url)
            return {'title': title.strip()[:500], 'description': description.strip()[:500], 'favicon_url': favicon_url}
        except Exception:
            return {'title': url[:500]}

    @action(detail=True, methods=['post'])
    def toggle_read(self, request, pk=None):
        bookmark = self.get_object()
        bookmark.is_read = not bookmark.is_read
        bookmark.save(update_fields=['is_read'])
        return Response({'is_read': bookmark.is_read})

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        bookmark = self.get_object()
        bookmark.is_favorite = not bookmark.is_favorite
        bookmark.save(update_fields=['is_favorite'])
        return Response({'is_favorite': bookmark.is_favorite})

    @action(detail=False, methods=['post'])
    def import_browser_bookmarks(self, request):
        """Import from browser bookmark export (HTML file)"""
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file'}, status=400)

        soup = BeautifulSoup(file.read(), 'html.parser')
        collection_id = request.data.get('collection_id')
        imported = 0
        for link in soup.find_all('a'):
            Bookmark.objects.create(
                collection_id=collection_id,
                url=link.get('href', ''),
                title=link.string or link.get('href', ''),
                description=link.get('description', ''),
            )
            imported += 1
        return Response({'imported': imported})
