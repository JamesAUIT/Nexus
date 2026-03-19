"use client";

import Link from "next/link";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { CloudNexusLogoIcon } from "@/components/cloud-nexus-logo";

export function AppTopbar() {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center gap-4 px-6">
        <Link href="/dashboard" className="md:hidden flex items-center shrink-0" aria-label="Cloud Nexus">
          <CloudNexusLogoIcon size={28} />
        </Link>
        <div className="flex-1" />
        <nav className="flex items-center gap-2">
          <Link
            href="/settings"
            className="text-sm font-medium text-muted-foreground hover:text-foreground"
          >
            Settings
          </Link>
          <Link
            href="/login"
            className="text-sm font-medium text-muted-foreground hover:text-foreground"
          >
            Sign out
          </Link>
          <Avatar className="h-8 w-8">
            <AvatarFallback className="text-xs">CN</AvatarFallback>
          </Avatar>
        </nav>
      </div>
    </header>
  );
}
