"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, apiUrl } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const TABS = ["Nodes", "Virtual Machines", "Storage", "Snapshots", "Backups", "Networks", "Containers", "Disks", "Tasks", "Replication", "HA", "Findings"] as const;
type TabId = (typeof TABS)[number];

const TAB_TO_ENDPOINT: Record<TabId, string> = {
  Nodes: "nodes",
  "Virtual Machines": "vms",
  Storage: "storage",
  Snapshots: "snapshots",
  Backups: "backups",
  Networks: "networks",
  Containers: "containers",
  Disks: "disks",
  Tasks: "tasks",
  Replication: "replication",
  HA: "ha",
  Findings: "findings",
};

function downloadExport(path: string, format: "csv" | "xlsx", filename: string) {
  const token = getToken();
  const url = `${apiUrl(path)}?format=${format}`;
  fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
    .then((r) => r.blob())
    .then((blob) => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
    })
    .catch(console.error);
}

export default function ProxmoxExplorerPage() {
  const [tab, setTab] = useState<TabId>("Nodes");
  const [clusterId, setClusterId] = useState<string>("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [nodeId, setNodeId] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState("");
  const [findingType, setFindingType] = useState("");
  const queryClient = useQueryClient();
  const pageSize = 50;

  const basePath = "/api/v1/proxmox-explorer";
  const clustersQuery = useQuery({
    queryKey: ["proxmox-explorer", "clusters"],
    queryFn: () => apiFetch<{ id: number; name: string }[]>(`${basePath}/clusters`, { token: getToken() }),
  });
  const clusters = clustersQuery.data ?? [];

  const endpoint = TAB_TO_ENDPOINT[tab];
  const isPaginated = !["Replication", "HA"].includes(tab);
  const queryParams = new URLSearchParams();
  if (clusterId) queryParams.set("cluster_id", clusterId);
  if (search) queryParams.set("search", search);
  if (isPaginated) {
    queryParams.set("page", String(page));
    queryParams.set("page_size", String(pageSize));
  }
  if (tab === "Virtual Machines" && nodeId) queryParams.set("node_id", nodeId);
  if ((tab === "Backups" || tab === "Tasks") && statusFilter) queryParams.set("status", statusFilter);
  if (tab === "Findings" && findingType) queryParams.set("finding_type", findingType);

  const listQuery = useQuery({
    queryKey: ["proxmox-explorer", endpoint, clusterId, search, page, nodeId, statusFilter, findingType],
    queryFn: () => apiFetch<{ data: Record<string, unknown>[]; meta?: { page: number; page_size: number; total: number } }>(`${basePath}/${endpoint}?${queryParams}`, { token: getToken() }),
    enabled: !!endpoint,
  });

  const runFindingsMutation = useMutation({
    mutationFn: () => apiFetch<{ findings_written: number }>(`${basePath}/findings/run` + (clusterId ? `?cluster_id=${clusterId}` : ""), { method: "POST", token: getToken() }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["proxmox-explorer", "findings"] }),
  });

  const result = listQuery.data;
  const data = result?.data ?? [];
  const meta = result?.meta;
  const total = meta?.total ?? 0;
  const totalPages = meta ? Math.max(1, Math.ceil(meta.total / pageSize)) : 1;

  const exportPath = `${basePath}/${endpoint}/export`;
  const exportFilename = `proxmox-${endpoint}.`;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Proxmox Explorer</h1>
      <p className="text-muted-foreground mb-4">RVTools-style explorer: nodes, VMs, storage, snapshots, backups, networks, containers, disks, tasks, replication, HA, and findings.</p>

      <div className="flex flex-wrap gap-2 border-b pb-2 mb-4">
        {TABS.map((t) => (
          <Button key={t} variant={tab === t ? "default" : "outline"} size="sm" onClick={() => setTab(t)}>
            {t}
          </Button>
        ))}
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 gap-4 flex-wrap">
          <CardTitle>{tab}</CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            <Label className="sr-only">Cluster</Label>
            <select
              className="border rounded px-2 py-1 text-sm"
              value={clusterId}
              onChange={(e) => { setClusterId(e.target.value); setPage(1); }}
            >
              <option value="">All clusters</option>
              {clusters.map((c) => (
                <option key={c.id} value={String(c.id)}>{c.name}</option>
              ))}
            </select>
            {(tab === "Nodes" || tab === "Virtual Machines" || tab === "Storage") && (
              <>
                <Label className="sr-only">Search</Label>
                <Input
                  className="w-40"
                  placeholder="Search"
                  value={search}
                  onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                />
              </>
            )}
            {tab === "Virtual Machines" && (
              <>
                <Label className="sr-only">Node</Label>
                <Input
                  className="w-28"
                  placeholder="Node ID"
                  value={nodeId}
                  onChange={(e) => { setNodeId(e.target.value); setPage(1); }}
                />
              </>
            )}
            {(tab === "Backups" || tab === "Tasks") && (
              <Input className="w-28" placeholder="Status" value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} />
            )}
            {tab === "Findings" && (
              <Input className="w-36" placeholder="Finding type" value={findingType} onChange={(e) => { setFindingType(e.target.value); setPage(1); }} />
            )}
            {tab === "Findings" && (
              <Button size="sm" variant="secondary" onClick={() => runFindingsMutation.mutate()} disabled={runFindingsMutation.isPending}>
                {runFindingsMutation.isPending ? "Running…" : "Run findings"}
              </Button>
            )}
            <Button size="sm" variant="outline" onClick={() => downloadExport(exportPath, "csv", exportFilename + "csv")}>
              Export CSV
            </Button>
            <Button size="sm" variant="outline" onClick={() => downloadExport(exportPath, "xlsx", exportFilename + "xlsx")}>
              Export XLSX
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {listQuery.isLoading ? (
            <p className="text-muted-foreground">Loading…</p>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    {data.length > 0 && Object.keys(data[0]).filter((k) => k !== "data").map((k) => (
                      <TableHead key={k}>{k.replace(/_/g, " ")}</TableHead>
                    ))}
                    {data.length === 0 && <TableHead>No columns</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.map((row, i) => (
                    <TableRow key={(row as { id?: number }).id ?? i}>
                      {Object.entries(row).filter(([k]) => k !== "data").map(([k, v]) => (
                        <TableCell key={k}>{v != null ? String(v) : "—"}</TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {isPaginated && totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-muted-foreground">
                    Page {page} of {totalPages} ({total} total)
                  </p>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
                      Previous
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
