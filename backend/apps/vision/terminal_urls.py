"""URL patterns for terminal-scoped camera and detection endpoints.

Mounted at /api/terminals/ in config/urls.py.

Endpoints:
  GET    /api/terminals/{terminal_id}/cameras/
  GET    /api/terminals/{terminal_id}/cameras/{camera_role}/settings/
  PATCH  /api/terminals/{terminal_id}/cameras/{camera_role}/settings/
  POST   /api/terminals/{terminal_id}/cameras/{camera_role}/test/
  GET    /api/terminals/{terminal_id}/cameras/{camera_role}/preview/
  POST   /api/terminals/{terminal_id}/vision/detect-sku-frame/
  POST   /api/terminals/{terminal_id}/vision/detect-weighted-frame/

camera_role in the URL is case-insensitive: 'sku' and 'weighted' are both accepted.
"""

from django.urls import path

from apps.vision.views import (
	CameraListAPIView,
	CameraPreviewAPIView,
	CameraSettingsAPIView,
	CameraTestAPIView,
	DetectSKUFrameAPIView,
	DetectWeightedFrameAPIView,
)

urlpatterns = [
	# Camera config list for a terminal
	path(
		"<str:terminal_id>/cameras/",
		CameraListAPIView.as_view(),
		name="terminal-camera-list",
	),
	# Per-role camera settings
	path(
		"<str:terminal_id>/cameras/<str:camera_role>/settings/",
		CameraSettingsAPIView.as_view(),
		name="terminal-camera-settings",
	),
	# Camera test (POST)
	path(
		"<str:terminal_id>/cameras/<str:camera_role>/test/",
		CameraTestAPIView.as_view(),
		name="terminal-camera-test",
	),
	# Camera preview (GET → returns JPEG)
	path(
		"<str:terminal_id>/cameras/<str:camera_role>/preview/",
		CameraPreviewAPIView.as_view(),
		name="terminal-camera-preview",
	),
	# Detection endpoints
	path(
		"<str:terminal_id>/vision/detect-sku-frame/",
		DetectSKUFrameAPIView.as_view(),
		name="terminal-detect-sku-frame",
	),
	path(
		"<str:terminal_id>/vision/detect-weighted-frame/",
		DetectWeightedFrameAPIView.as_view(),
		name="terminal-detect-weighted-frame",
	),
]
