"use client";

import Link from "next/link";

/** Static assets under `apps/web/public/logo`. */
const LOGO_SIDEBAR_ICON = "/logo/cloud-nexus-sidebar-icon.svg";
const LOGO_HEADER = "/logo/cloud-nexus-header.svg";
const LOGO_EXACT = "/logo/cloud-nexus-exact-logo.svg";

/** Square sidebar mark (512×512). */
export function CloudNexusIcon({ className = "", size = 24 }: { className?: string; size?: number }) {
  return (
    <img
      src={LOGO_SIDEBAR_ICON}
      width={size}
      height={size}
      alt=""
      className={className}
      aria-hidden
    />
  );
}

/** Sidebar: full exact logo when `showText`, else sidebar icon. */
export function CloudNexusLogo({
  showText = true,
  iconSize = 28,
  className = "",
  href = "/dashboard",
}: {
  showText?: boolean;
  iconSize?: number;
  className?: string;
  href?: string;
}) {
  const content = showText ? (
    <img
      src={LOGO_EXACT}
      alt="Cloud Nexus"
      className="h-8 w-auto max-w-[min(100%,220px)] object-contain object-left"
    />
  ) : (
    <img
      src={LOGO_SIDEBAR_ICON}
      width={iconSize}
      height={iconSize}
      alt=""
      className="shrink-0"
      aria-hidden
    />
  );
  return (
    <Link
      href={href}
      className={`flex items-center overflow-hidden ${className}`}
      aria-label="Cloud Nexus home"
    >
      {content}
    </Link>
  );
}

/**
 * Top bar: horizontal header artwork (1800×900 source).
 * `size` is the rendered height in CSS pixels; width scales with aspect ratio.
 */
export function CloudNexusLogoIcon({ className = "", size = 28 }: { className?: string; size?: number }) {
  return (
    <img
      src={LOGO_HEADER}
      alt=""
      height={size}
      className={`w-auto max-w-[min(100vw-4rem,280px)] object-contain object-left ${className}`}
      aria-hidden
    />
  );
}
