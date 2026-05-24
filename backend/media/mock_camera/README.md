# Mock Camera Images

This folder contains mock images used as a fake camera feed during development.

## Setup

### SKU Camera (packaged products)
Put `.jpg`, `.jpeg`, or `.png` images of packaged supermarket products into:
```
media/mock_camera/sku/
```

### Weighted Camera (fruits/vegetables/scale)
Put `.jpg`, `.jpeg`, or `.png` images of the scale display or weighted items into:
```
media/mock_camera/weighted/
```

The backend will cycle through these images in alphabetical order, advancing
every `frame_interval_ms` milliseconds (default: 1000 ms), simulating a live
camera feed.

## Configuring the source

From the cashier UI, go to **Settings → Camera Settings** and set:
- Source Type: `Mock Folder`
- Folder Path: `media/mock_camera/sku/` (or `weighted/`)

## Switching to a real camera later

From the same settings page, change Source Type to:
- `USB` — enter the device index (0 for the first USB camera)
- `Network` — enter the RTSP/HTTP stream URL

No frontend changes are needed. The backend handles the source switch transparently.

## Notes

- Do **not** commit large image datasets. Add images locally only.
- The `.gitkeep` files keep the folders tracked in git while empty.
