"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function CertificatesPage() {
  const [hostname, setHostname] = useState("");
  const [port, setPort] = useState(443);
  const [severity, setSeverity] = useState("");
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["certificates", severity, page],
    queryFn: () => apiFetch<{ data: { id: number; hostname: string; port: number; severity: string; days_until_expiry: number | null; last_scan_at: string }[]; meta: { total: number } }>(`/api/v1/certificates?page=${page}&page_size=20${severity ? `&severity=${severity}` : ""}`, { token: getToken() }),
  });

  const scanMutation = useMutation({
    mutationFn: (h: { hostname: string; port: number }) => apiFetch(`/api/v1/certificates/scan?hostname=${encodeURIComponent(h.hostname)}&port=${h.port}`, { method: "POST", token: getToken() }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["certificates"] }),
  });

  const certs = data?.data ?? [];
  const total = data?.meta?.total ?? 0;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Certificate monitoring</h1>
      <p className="text-muted-foreground mb-4">TLS certificate scanning and expiry tracking.</p>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Scan host</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2 flex-wrap">
          <Input placeholder="Hostname" value={hostname} onChange={(e) => setHostname(e.target.value)} className="w-48" />
          <Input type="number" placeholder="443" value={port} onChange={(e) => setPort(Number(e.target.value) || 443)} className="w-20" />
          <Button onClick={() => hostname && scanMutation.mutate({ hostname, port })} disabled={!hostname || scanMutation.isPending}>
            {scanMutation.isPending ? "Scanning…" : "Scan"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Certificates</CardTitle>
          <select className="border rounded px-2 py-1 text-sm" value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(1); }}>
            <option value="">All severity</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="ok">OK</option>
          </select>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-muted-foreground">Loading…</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Hostname</TableHead>
                  <TableHead>Port</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Days until expiry</TableHead>
                  <TableHead>Last scan</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {certs.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium">{c.hostname}</TableCell>
                    <TableCell>{c.port}</TableCell>
                    <TableCell><span className={c.severity === "critical" ? "text-red-600" : c.severity === "high" ? "text-orange-600" : ""}>{c.severity}</span></TableCell>
                    <TableCell>{c.days_until_expiry ?? "—"}</TableCell>
                    <TableCell>{c.last_scan_at ? new Date(c.last_scan_at).toLocaleString() : "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          {total > 20 && (
            <div className="flex justify-between mt-4">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</Button>
              <Button variant="outline" size="sm" disabled={page * 20 >= total} onClick={() => setPage((p) => p + 1)}>Next</Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
