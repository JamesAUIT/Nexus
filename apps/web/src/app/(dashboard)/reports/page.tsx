"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type ReportDef = { id: number; name: string; slug: string; description: string | null };
type ReportRun = { id: number; report_definition_id: number; started_at: string; finished_at: string | null; status: string; result_path: string | null };

export default function ReportsPage() {
  const queryClient = useQueryClient();
  const { data: definitions = [] } = useQuery({
    queryKey: ["report-definitions"],
    queryFn: () => apiFetch<ReportDef[]>("/api/v1/reports/definitions", { token: getToken() }),
  });
  const { data: runs = [] } = useQuery({
    queryKey: ["report-runs"],
    queryFn: () => apiFetch<ReportRun[]>("/api/v1/reports/runs", { token: getToken() }),
  });
  const runReport = useMutation({
    mutationFn: (id: number) => apiFetch<{ run_id: number }>(`/api/v1/reports/definitions/${id}/run`, { method: "POST", token: getToken() }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["report-runs"] }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Reports</h1>
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Report definitions</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Slug</TableHead>
                <TableHead>Description</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {definitions.map((d) => (
                <TableRow key={d.id}>
                  <TableCell className="font-medium">{d.name}</TableCell>
                  <TableCell>{d.slug}</TableCell>
                  <TableCell className="text-muted-foreground">{d.description ?? "—"}</TableCell>
                  <TableCell>
                    <Button size="sm" variant="outline" onClick={() => runReport.mutate(d.id)} disabled={runReport.isPending}>
                      Run (CSV placeholder)
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Execution history</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Run ID</TableHead>
                <TableHead>Report ID</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runs.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">{r.id}</TableCell>
                  <TableCell>{r.report_definition_id}</TableCell>
                  <TableCell className="text-muted-foreground">{r.started_at}</TableCell>
                  <TableCell>{r.status}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
