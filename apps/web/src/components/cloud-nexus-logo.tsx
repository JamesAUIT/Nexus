"use client";

import Link from "next/link";
import Image from "next/image";

const LOGO_ICON_TRANSPARENT = "/logo/cloud-nexus-logo-icon-transparent.svg";
const LOGO_PRIMARY = "/logo/cloud-nexus-logo-primary.svg";
const LOGO_DARK = "/logo/cloud-nexus-logo-dark.svg";

/** Cloud Nexus logo mark (C + infinity + cloud) from official pack. Use in sidebar, header. */
export function CloudNexusIcon({
  className = "",
  size = 24,
}: {
  className?: string;
  size?: number;
}) {
  return (
    <img
      src={LOGO_ICON_TRANSPARENT}
      width={size}
      height={size}
      alt=""
      className={className}
      aria-hidden
    />
  );
}

/** Full logo: horizontal logo with "Cloud Nexus" wordmark from official pack. */
export function CloudNexusLogo({
  showText = true,
  iconSize = 28,
  className = "",
  href = "/dashboard",
  variant = "default",
}: {
  showText?: boolean;
  iconSize?: number;
  className?: string;
  href?: string;
  variant?: "default" | "dark";
}) {
  const logoSrc = variant === "dark" ? LOGO_DARK : LOGO_PRIMARY;
  const content = showText ? (
    <Image
      src={logoSrc}
      alt="Cloud Nexus"
      width={140}
      height={32}
      className="h-8 w-auto object-contain"
    />
  ) : (
    <img
      src={LOGO_ICON_TRANSPARENT}
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

/** Icon-only for collapsed sidebar or header. */
export function CloudNexusLogoIcon({ className = "", size = 24 }: { className?: string; size?: number }) {
  return (
    <img
      src={LOGO_ICON_TRANSPARENT}
      width={size}
      height={size}
      alt=""
      className={className}
      aria-hidden
    />
  );
}
