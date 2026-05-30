from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from apps.notes.models import Note

class RecommendationService:
    def get_related_notes(self, note_id: int, limit: int = 5) -> list:
        try:
            target_note = Note.objects.get(id=note_id)
        except Note.DoesNotExist:
            return []

        notes = Note.objects.exclude(id=note_id)[:200]
        documents = [target_note.content] + [n.content for n in notes]
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf = vectorizer.fit_transform(documents)
        similarities = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()
        related_indices = similarities.argsort()[-limit:][::-1]
        return [{"id": notes[i].id, "title": notes[i].title, "score": similarities[i]} for i in related_indices]
