"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function InsightsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["insights"],
    queryFn: () => apiFetch<{ data: { rule: string; entity_type: string; entity_id: string; title: string; detail: string; severity: string }[] }>("/api/v1/insights?limit=50", { token: getToken() }),
  });

  const rows = data?.data ?? [];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Insights</h1>
      <p className="text-muted-foreground mb-4">Rule-based recommendations: oversized VMs, stale snapshots, missing backups, storage, firmware, certificates.</p>

      <Card>
        <CardHeader>
          <CardTitle>Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? <p className="text-muted-foreground">Loading…</p> : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Rule</TableHead>
                  <TableHead>Entity</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Detail</TableHead>
                  <TableHead>Severity</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((r, i) => (
                  <TableRow key={i}>
                    <TableCell>{r.rule}</TableCell>
                    <TableCell>{r.entity_type}/{r.entity_id}</TableCell>
                    <TableCell>{r.title}</TableCell>
                    <TableCell>{r.detail}</TableCell>
                    <TableCell><span className={r.severity === "high" ? "text-orange-600" : r.severity === "critical" ? "text-red-600" : ""}>{r.severity}</span></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
