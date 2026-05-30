from rest_framework import serializers
from .models import Board, Column, Card

class CardSerializer(serializers.ModelSerializer):
    note_title = serializers.SerializerMethodField()
    note_content = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Card
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def get_note_title(self, obj): return obj.note.title
    def get_note_content(self, obj): return obj.note.excerpt
    def get_tags(self, obj): return list(obj.note.tags.values_list('name', flat=True))

class ColumnSerializer(serializers.ModelSerializer):
    cards = CardSerializer(many=True, read_only=True)
    card_count = serializers.SerializerMethodField()

    class Meta:
        model = Column
        fields = '__all__'

    def get_card_count(self, obj): return obj.cards.count()

class BoardSerializer(serializers.ModelSerializer):
    columns = ColumnSerializer(many=True, read_only=True)
    column_count = serializers.SerializerMethodField()
    card_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']

    def get_column_count(self, obj): return obj.columns.count()
    def get_card_count(self, obj): return sum(col.cards.count() for col in obj.columns.all())
