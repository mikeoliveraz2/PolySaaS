from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class UnreadDoseMessagesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # TODO: Replace with actual unread message count logic
        return Response({"unread_count": 0})

class DisplaySettingsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # TODO: Replace with actual display settings logic
        return Response({"settings": {}})
