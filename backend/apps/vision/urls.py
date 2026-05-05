from django.urls import path

from apps.vision.views import DetectionRunDetailAPIView, VisionDetectAPIView

urlpatterns = [
	path("detect/", VisionDetectAPIView.as_view(), name="vision-detect"),
	path("runs/<int:run_id>/", DetectionRunDetailAPIView.as_view(), name="vision-run-detail"),
]
