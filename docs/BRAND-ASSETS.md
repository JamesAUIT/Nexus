# Cloud Nexus — Brand assets and logo

## Logo

- **Base icon**: The "C" icon is the base of Cloud Nexus branding (cloud + letter C).
- **Full logo**: C icon + "Cloud Nexus" wordmark.
- **Variants**: Light (for dark backgrounds), dark (for light backgrounds), default (uses current text color).

## Usage

- **Sidebar**: Full logo with icon + text; responsive, truncates on narrow width.
- **Header (mobile)**: Icon-only logo linking to dashboard.
- **Favicon**: `apps/web/public/favicon.svg` — C icon in cloud blue (#0ea5e9).

## Assets

| Asset        | Path                          | Notes                    |
|-------------|--------------------------------|--------------------------|
| Favicon     | `apps/web/public/favicon.svg` | 32×32, cloud blue fill   |
| Logo component | `apps/web/src/components/cloud-nexus-logo.tsx` | Icon, full logo, icon-only |

## Components

- `CloudNexusIcon` — SVG C icon; size and variant (default | light | dark).
- `CloudNexusLogo` — Icon + optional "Cloud Nexus" text; for sidebar/header.
- `CloudNexusLogoIcon` — Icon only; for collapsed sidebar, mobile header, favicon context.

Scaling and padding are handled via `size`, `className`, and layout (flex, truncate) so the logo works in sidebar, header, and mobile contexts.
