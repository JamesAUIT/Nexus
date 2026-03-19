"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";

export default function IDracPage() {
  const queryClient = useQueryClient();
  const { data: hosts = [] } = useQuery({
    queryKey: ["hosts"],
    queryFn: () => apiFetch<{ id: number; name: string }[]>("/api/v1/hosts", { token: getToken() }),
  });
  const { data, isLoading } = useQuery({
    queryKey: ["idrac-inventory"],
    queryFn: () => apiFetch<{ data: { id: number; host_id: number | null; bios_version: string | null; idrac_version: string | null; compliance_status: string | null; last_scan_at: string }[] }>("/api/v1/idrac/inventory", { token: getToken() }),
  });
  const scanMutation = useMutation({
    mutationFn: (hostId: number) => apiFetch(`/api/v1/idrac/scan?host_id=${hostId}`, { method: "POST", token: getToken() }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["idrac-inventory"] }),
  });

  const rows = data?.data ?? [];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">iDRAC / Redfish</h1>
      <p className="text-muted-foreground mb-4">Firmware and hardware health: BIOS version, iDRAC version, compliance.</p>

      <Card>
        <CardHeader>
          <CardTitle>Firmware inventory</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? <p className="text-muted-foreground">Loading…</p> : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Host ID</TableHead>
                  <TableHead>BIOS version</TableHead>
                  <TableHead>iDRAC version</TableHead>
                  <TableHead>Compliance</TableHead>
                  <TableHead>Last scan</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.host_id ?? "—"}</TableCell>
                    <TableCell>{r.bios_version ?? "—"}</TableCell>
                    <TableCell>{r.idrac_version ?? "—"}</TableCell>
                    <TableCell>{r.compliance_status ?? "—"}</TableCell>
                    <TableCell>{r.last_scan_at ? new Date(r.last_scan_at).toLocaleString() : "—"}</TableCell>
                    <TableCell>
                      {r.host_id && (
                        <Button size="sm" variant="outline" onClick={() => scanMutation.mutate(r.host_id!)} disabled={scanMutation.isPending}>Scan</Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          <p className="text-sm text-muted-foreground mt-4">Scan a host: select from Hosts and run scan (Redfish scaffolding).</p>
          <div className="flex gap-2 mt-2">
            {hosts.map((h) => (
              <Button key={h.id} size="sm" variant="secondary" onClick={() => scanMutation.mutate(h.id)} disabled={scanMutation.isPending}>Scan {h.name}</Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
