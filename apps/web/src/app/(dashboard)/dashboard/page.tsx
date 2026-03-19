"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import Link from "next/link";

type ConnectorHealth = { id: number; name: string; type: string; status: string; data_freshness_minutes: number | null; sync_status: string | null };

type Widgets = {
  connector_health: { id: number; name: string; status: string; last_ok_at: string | null }[];
  expiring_certificates: { critical: number; high: number; list: { hostname: string; port: number; severity: string; days_until_expiry: number | null }[] };
  outdated_firmware_count: number;
  stale_snapshots_count: number;
  missing_backups_count: number;
  recent_changes_count: number;
  recent_sync_failures_count: number;
};

export default function DashboardPage() {
  const { data: connectors = [] } = useQuery({
    queryKey: ["connector-health"],
    queryFn: () => apiFetch<ConnectorHealth[]>("/api/v1/connectors/health", { token: getToken() }),
  });

  const { data: widgets } = useQuery({
    queryKey: ["dashboard-widgets"],
    queryFn: () => apiFetch<Widgets>("/api/v1/dashboard/widgets", { token: getToken() }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Expiring certificates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{((widgets?.expiring_certificates?.critical ?? 0) + (widgets?.expiring_certificates?.high ?? 0))}</div>
            <p className="text-xs text-muted-foreground"><Link href="/certificates" className="text-primary hover:underline">View certificates</Link></p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Outdated firmware</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{widgets?.outdated_firmware_count ?? 0}</div>
            <p className="text-xs text-muted-foreground"><Link href="/idrac" className="text-primary hover:underline">iDRAC inventory</Link></p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Stale snapshots</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{widgets?.stale_snapshots_count ?? 0}</div>
            <p className="text-xs text-muted-foreground"><Link href="/cloud-ops" className="text-primary hover:underline">Cloud Ops</Link></p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Missing backups</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{widgets?.missing_backups_count ?? 0}</div>
            <p className="text-xs text-muted-foreground"><Link href="/backups" className="text-primary hover:underline">Backups</Link></p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Recent changes (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{widgets?.recent_changes_count ?? 0}</div>
            <p className="text-xs text-muted-foreground"><Link href="/change-events" className="text-primary hover:underline">Change events</Link></p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Sync failures (7d)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{widgets?.recent_sync_failures_count ?? 0}</div>
            <p className="text-xs text-muted-foreground"><Link href="/sync-jobs" className="text-primary hover:underline">Sync jobs</Link></p>
          </CardContent>
        </Card>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Connector health & data freshness</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Data freshness</TableHead>
                <TableHead>Last sync</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {connectors.map((c) => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium">{c.name}</TableCell>
                  <TableCell>{c.type}</TableCell>
                  <TableCell>{c.status}</TableCell>
                  <TableCell>{c.data_freshness_minutes != null ? `${c.data_freshness_minutes} min ago` : "—"}</TableCell>
                  <TableCell>{c.sync_status ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <p className="text-muted-foreground text-sm mt-4">
            <Link href="/drift" className="text-primary hover:underline">Drift</Link>, <Link href="/sync-jobs" className="text-primary hover:underline">Sync jobs</Link>, <Link href="/insights" className="text-primary hover:underline">Insights</Link>.
          </p>
        </CardContent>
      </Card>

      {widgets?.expiring_certificates?.list?.length ? (
        <Card>
          <CardHeader>
            <CardTitle>Expiring certificates (top 5)</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Hostname</TableHead>
                  <TableHead>Port</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Days</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {widgets.expiring_certificates.list.map((c, i) => (
                  <TableRow key={i}>
                    <TableCell>{c.hostname}</TableCell>
                    <TableCell>{c.port}</TableCell>
                    <TableCell>{c.severity}</TableCell>
                    <TableCell>{c.days_until_expiry ?? "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
