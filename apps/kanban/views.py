from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Board, Column, Card
from .serializers import BoardSerializer, ColumnSerializer, CardSerializer

class BoardViewSet(viewsets.ModelViewSet):
    serializer_class = BoardSerializer

    def get_queryset(self):
        return Board.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        board = serializer.save(user=self.request.user)
        # Create default columns
        for name in ['To Do', 'In Progress', 'Done']:
            Column.objects.create(board=board, name=name, order=len(board.columns.all()))

class ColumnViewSet(viewsets.ModelViewSet):
    serializer_class = ColumnSerializer

    def get_queryset(self):
        return Column.objects.filter(board__user=self.request.user)

    @action(detail=True, methods=['post'])
    def reorder_cards(self, request, pk=None):
        column = self.get_object()
        card_ids = request.data.get('card_ids', [])
        for idx, card_id in enumerate(card_ids):
            Card.objects.filter(id=card_id, column=column).update(order=idx)
        return Response({'status': 'reordered'})

class CardViewSet(viewsets.ModelViewSet):
    serializer_class = CardSerializer

    def get_queryset(self):
        return Card.objects.filter(column__board__user=self.request.user)

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        card = self.get_object()
        new_column_id = request.data.get('column_id')
        new_order = request.data.get('order')
        if new_column_id:
            card.column_id = new_column_id
        if new_order is not None:
            card.order = new_order
        card.save()
        return Response(CardSerializer(card).data)
