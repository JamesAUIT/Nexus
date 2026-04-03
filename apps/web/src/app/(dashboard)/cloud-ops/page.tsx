"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, apiUrl } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const CLOUD_OPS_TABS = ["Snapshots", "Diagnostics", "Patch", "Load Balancer"] as const;
type CloudOpsTab = (typeof CLOUD_OPS_TABS)[number];

export default function CloudOpsPage() {
  const [tab, setTab] = useState<CloudOpsTab>("Snapshots");
  const [clusterId, setClusterId] = useState<string>("");
  const [staleBand, setStaleBand] = useState<string>("");
  const [ackFilter, setAckFilter] = useState<string>("");
  const [drawerSnapshot, setDrawerSnapshot] = useState<Record<string, unknown> | null>(null);
  const queryClient = useQueryClient();
  const base = "/api/v1/cloud-ops";

  const clustersQuery = useQuery({
    queryKey: ["proxmox-explorer", "clusters"],
    queryFn: () => apiFetch<{ id: number; name: string }[]>("/api/v1/proxmox-explorer/clusters", { token: getToken() }),
  });
  const clusters = clustersQuery.data ?? [];

  const snapshotsQuery = useQuery({
    queryKey: ["cloud-ops", "snapshots", clusterId, staleBand, ackFilter],
    queryFn: () => {
      const params = new URLSearchParams();
      if (clusterId) params.set("cluster_id", clusterId);
      if (staleBand) params.set("stale_band", staleBand);
      if (ackFilter === "yes") params.set("acknowledged", "true");
      if (ackFilter === "no") params.set("acknowledged", "false");
      return apiFetch<{ data: Record<string, unknown>[]; meta: { total: number } }>(`${base}/snapshots?${params}`, { token: getToken() });
    },
    enabled: tab === "Snapshots",
  });

  const staleBandsQuery = useQuery({
    queryKey: ["cloud-ops", "snapshots", "stale-bands", clusterId],
    queryFn: () => apiFetch<{ bands: Record<string, number> }>(`${base}/snapshots/stale-bands${clusterId ? `?cluster_id=${clusterId}` : ""}`, { token: getToken() }),
    enabled: tab === "Snapshots",
  });

  const diagnosticsQuery = useQuery({
    queryKey: ["cloud-ops", "diagnostics", clusterId],
    queryFn: () => apiFetch<{ generated_at: string; clusters: unknown[]; node_health: unknown[]; storage_health: unknown[]; ha_status: unknown[]; backup_status: unknown[] }>(`${base}/diagnostics/report${clusterId ? `?cluster_id=${clusterId}` : ""}`, { token: getToken() }),
    enabled: tab === "Diagnostics",
  });

  const patchQuery = useQuery({
    queryKey: ["cloud-ops", "patch", clusterId],
    queryFn: () => apiFetch<{ pending_updates: unknown[]; node_readiness: unknown[]; pre_checks: unknown[]; drain_plan_steps: string[]; maintenance_plan_steps: string[] }>(`${base}/patch/plan${clusterId ? `?cluster_id=${clusterId}` : ""}`, { token: getToken() }),
    enabled: tab === "Patch",
  });

  const lbEndpointsQuery = useQuery({
    queryKey: ["cloud-ops", "lb", "endpoints"],
    queryFn: () => apiFetch<{ data: unknown[] }>(`${base}/loadbalancer/endpoints`, { token: getToken() }),
    enabled: tab === "Load Balancer",
  });
  const lbConfigQuery = useQuery({
    queryKey: ["cloud-ops", "lb", "config"],
    queryFn: () => apiFetch<{ config: string; valid: boolean }>(`${base}/loadbalancer/config-preview`, { token: getToken() }),
    enabled: tab === "Load Balancer",
  });
  const lbValidationQuery = useQuery({
    queryKey: ["cloud-ops", "lb", "validation"],
    queryFn: () => apiFetch<{ valid: boolean; errors: string[]; warnings: string[] }>(`${base}/loadbalancer/validation`, { token: getToken() }),
    enabled: tab === "Load Balancer",
  });

  const ackMutation = useMutation({
    mutationFn: ({ cid, vid }: { cid: number; vid: number }) =>
      apiFetch(`${base}/snapshots/acknowledge?cluster_id=${cid}&vm_id=${vid}`, { method: "POST", token: getToken(), body: JSON.stringify({ reason: "Acknowledged from Cloud Ops" }) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cloud-ops", "snapshots"] });
      queryClient.invalidateQueries({ queryKey: ["cloud-ops", "snapshots", "stale-bands"] });
    },
  });

  const snapshots = tab === "Snapshots" ? (snapshotsQuery.data?.data ?? []) : [];
  const bands = (tab === "Snapshots" && staleBandsQuery.data?.bands) ?? {};
  const diagnostics = tab === "Diagnostics" ? diagnosticsQuery.data : null;
  const patchPlan = tab === "Patch" ? patchQuery.data : null;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Cloud Ops</h1>
      <p className="text-muted-foreground mb-4">Patch, Load Balancer, Diagnostics, and Snapshots.</p>

      <div className="flex flex-wrap gap-2 border-b pb-2 mb-4">
        {CLOUD_OPS_TABS.map((t) => (
          <Button key={t} variant={tab === t ? "default" : "outline"} size="sm" onClick={() => setTab(t)}>
            {t}
          </Button>
        ))}
      </div>

      {tab === "Snapshots" && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 gap-4 flex-wrap">
            <CardTitle>Snapshots</CardTitle>
            <div className="flex flex-wrap gap-2 items-center">
              <select className="border rounded px-2 py-1 text-sm" value={clusterId} onChange={(e) => setClusterId(e.target.value)}>
                <option value="">All clusters</option>
                {clusters.map((c) => (
                  <option key={c.id} value={String(c.id)}>{c.name}</option>
                ))}
              </select>
              <select className="border rounded px-2 py-1 text-sm" value={staleBand} onChange={(e) => setStaleBand(e.target.value)}>
                <option value="">All bands</option>
                <option value="ok">ok (&lt;7d)</option>
                <option value="7d">7d</option>
                <option value="14d">14d</option>
                <option value="30d">30d</option>
                <option value="60d">60d</option>
                <option value="90d+">90d+</option>
              </select>
              <select className="border rounded px-2 py-1 text-sm" value={ackFilter} onChange={(e) => setAckFilter(e.target.value)}>
                <option value="">All</option>
                <option value="yes">Acknowledged</option>
                <option value="no">Not acknowledged</option>
              </select>
            </div>
          </CardHeader>
          <CardContent>
            {Object.keys(bands).length > 0 && (
              <div className="flex gap-4 mb-4 text-sm">
                <span className="font-medium">Stale bands:</span>
                {Object.entries(bands).map(([b, count]) => (
                  <span key={b}>{b}: {count}</span>
                ))}
              </div>
            )}
            {snapshotsQuery.isLoading ? (
              <p className="text-muted-foreground">Loading…</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>VM</TableHead>
                    <TableHead>Snapshot</TableHead>
                    <TableHead>Node</TableHead>
                    <TableHead>Age (days)</TableHead>
                    <TableHead>Band</TableHead>
                    <TableHead>Ack</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {snapshots.map((row, i) => (
                    <TableRow key={(row.id as number) ?? i}>
                      <TableCell className="font-medium">{String(row.vm_name ?? row.vm_id)}</TableCell>
                      <TableCell>{String(row.name)}</TableCell>
                      <TableCell>{String(row.node_name)}</TableCell>
                      <TableCell>{String(row.age_days)}</TableCell>
                      <TableCell>{String(row.stale_band)}</TableCell>
                      <TableCell>{row.acknowledged ? `Yes (${row.ack_by ?? "—"})` : "No"}</TableCell>
                      <TableCell>
                        <Button size="sm" variant="ghost" onClick={() => setDrawerSnapshot(row)}>Detail</Button>
                        {!row.acknowledged && (
                          <Button size="sm" variant="outline" className="ml-1" onClick={() => ackMutation.mutate({ cid: Number(row.cluster_id), vid: Number(row.vm_id) })} disabled={ackMutation.isPending}>
                            Ack
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}

      {tab === "Diagnostics" && (
        <Card>
          <CardHeader>
            <CardTitle>Diagnostics</CardTitle>
            <div className="flex gap-2">
              <select className="border rounded px-2 py-1 text-sm" value={clusterId} onChange={(e) => setClusterId(e.target.value)}>
                <option value="">All clusters</option>
                {clusters.map((c) => (
                  <option key={c.id} value={String(c.id)}>{c.name}</option>
                ))}
              </select>
              <Button size="sm" variant="outline" onClick={() => fetch(apiUrl(`${base}/diagnostics/report?format=html${clusterId ? `&cluster_id=${clusterId}` : ""}`), { headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : {} }).then((r) => r.text()).then((html) => { const w = window.open("", "_blank"); if (w) w.document.write(html); })}>
                Export HTML
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {diagnosticsQuery.isLoading ? (
              <p className="text-muted-foreground">Loading…</p>
            ) : diagnostics ? (
              <div className="space-y-4 text-sm">
                <p>Generated: {diagnostics.generated_at}</p>
                <div><strong>Clusters:</strong> {(diagnostics.clusters as unknown[]).length}</div>
                <div><strong>Node health:</strong> {(diagnostics.node_health as unknown[]).length} entries</div>
                <div><strong>Storage health:</strong> {(diagnostics.storage_health as unknown[]).length} entries</div>
                <div><strong>HA status:</strong> {(diagnostics.ha_status as unknown[]).length} entries</div>
                <div><strong>Backup status (sample):</strong> {(diagnostics.backup_status as unknown[]).length} entries</div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}

      {tab === "Patch" && (
        <Card>
          <CardHeader>
            <CardTitle>Patch (planning only)</CardTitle>
            <p className="text-muted-foreground text-sm">No destructive execution. Pending updates, node readiness, pre-checks, drain and maintenance plan.</p>
          </CardHeader>
          <CardContent>
            {patchQuery.isLoading ? (
              <p className="text-muted-foreground">Loading…</p>
            ) : patchPlan ? (
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium mb-2">Pending updates</h3>
                  <pre className="bg-muted p-2 rounded text-sm overflow-auto">{JSON.stringify(patchPlan.pending_updates, null, 2)}</pre>
                </div>
                <div>
                  <h3 className="font-medium mb-2">Node readiness</h3>
                  <pre className="bg-muted p-2 rounded text-sm overflow-auto">{JSON.stringify(patchPlan.node_readiness, null, 2)}</pre>
                </div>
                <div>
                  <h3 className="font-medium mb-2">Pre-checks</h3>
                  <pre className="bg-muted p-2 rounded text-sm overflow-auto">{JSON.stringify(patchPlan.pre_checks, null, 2)}</pre>
                </div>
                <div>
                  <h3 className="font-medium mb-2">Drain plan steps</h3>
                  <ol className="list-decimal list-inside">{patchPlan.drain_plan_steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
                </div>
                <div>
                  <h3 className="font-medium mb-2">Maintenance plan steps</h3>
                  <ol className="list-decimal list-inside">{patchPlan.maintenance_plan_steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
                </div>
                <Button size="sm" variant="outline" onClick={() => apiFetch<{ markdown: string }>(`${base}/patch/plan/export`, { token: getToken() }).then((r) => navigator.clipboard.writeText(r.markdown))}>
                  Copy plan (markdown)
                </Button>
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}

      {tab === "Load Balancer" && (
        <Card>
          <CardHeader>
            <CardTitle>Load Balancer (HAProxy)</CardTitle>
            <p className="text-muted-foreground text-sm">Cluster endpoints, health checks, config preview, validation. Push/rollback are placeholders.</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-2">Cluster endpoints</h3>
                {lbEndpointsQuery.isLoading ? <p className="text-muted-foreground">Loading…</p> : (
                  <Table>
                    <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Host</TableHead><TableHead>Port</TableHead><TableHead>Health check</TableHead></TableRow></TableHeader>
                    <TableBody>
                      {(lbEndpointsQuery.data?.data as { name: string; host: string; port: number; health_check_url: string }[] ?? []).map((e, i) => (
                        <TableRow key={i}><TableCell>{e.name}</TableCell><TableCell>{e.host}</TableCell><TableCell>{e.port}</TableCell><TableCell>{e.health_check_url}</TableCell></TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </div>
              <div>
                <h3 className="font-medium mb-2">Config preview</h3>
                <pre className="bg-muted p-2 rounded text-sm overflow-auto max-h-64">{lbConfigQuery.data?.config ?? "Loading…"}</pre>
              </div>
              <div>
                <h3 className="font-medium mb-2">Validation</h3>
                <p>Valid: {lbValidationQuery.data?.valid ? "Yes" : "No"} | Errors: {(lbValidationQuery.data?.errors ?? []).length} | Warnings: {(lbValidationQuery.data?.warnings ?? []).length}</p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" disabled>Push (placeholder)</Button>
                <Button size="sm" variant="outline" disabled>Rollback (placeholder)</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {drawerSnapshot && (
        <div className="fixed inset-y-0 right-0 w-96 bg-background border-l shadow-lg z-50 p-4 overflow-auto">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Snapshot detail</h2>
            <Button size="sm" variant="ghost" onClick={() => setDrawerSnapshot(null)}>Close</Button>
          </div>
          <pre className="text-sm bg-muted p-2 rounded overflow-auto">{JSON.stringify(drawerSnapshot, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
