"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { CloudNexusLogo } from "@/components/cloud-nexus-logo";

const nav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/search", label: "Search" },
  { href: "/sites", label: "Sites" },
  { href: "/racks", label: "Racks" },
  { href: "/hosts", label: "Hosts" },
  { href: "/vms", label: "Virtual Machines" },
  { href: "/containers", label: "Containers" },
  { href: "/storage", label: "Storage" },
  { href: "/backups", label: "Backups" },
  { href: "/network", label: "Network" },
  { href: "/drift", label: "Drift / Reconciliation" },
  { href: "/sync-jobs", label: "Sync Jobs" },
  { href: "/audit", label: "Audit Log" },
  { href: "/settings", label: "Settings" },
  { href: "/links", label: "Useful Links" },
  { href: "/reports", label: "Reports" },
  { href: "/runbooks", label: "Runbooks" },
  { href: "/script-library", label: "Script Library" },
  { href: "/health", label: "Health Checks" },
  { href: "/saved-queries", label: "Saved Queries" },
  { href: "/proxmox-explorer", label: "Proxmox Explorer" },
  { href: "/cloud-ops", label: "Cloud Ops" },
  { href: "/certificates", label: "Certificates" },
  { href: "/idrac", label: "iDRAC / Redfish" },
  { href: "/change-events", label: "Change events" },
  { href: "/connectivity", label: "Connectivity" },
  { href: "/insights", label: "Insights" },
  { href: "/scripts", label: "Scripts" },
  { href: "/ops-requests", label: "Operations Requests" },
];

export function AppSidebar() {
  const pathname = usePathname();
  return (
    <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col overflow-hidden border-r bg-muted/30">
      <div className="flex shrink-0 items-center border-b p-4 min-w-0">
        <CloudNexusLogo href="/dashboard" iconSize={28} />
      </div>
      <nav className="min-h-0 flex-1 space-y-0.5 overflow-y-auto overscroll-contain p-2">
        {nav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "block px-3 py-2 rounded-md text-sm font-medium transition-colors",
              pathname === item.href
                ? "bg-primary text-primary-foreground"
                : "hover:bg-accent hover:text-accent-foreground"
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
