"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type HealthDef = { id: number; name: string; slug: string; description: string | null; check_type: string };
type HealthRun = { id: number; started_at: string; finished_at: string | null; status: string; results: { id: number; definition_id: number; status: string; message: string | null }[] };

export default function HealthPage() {
  const queryClient = useQueryClient();
  const { data: definitions = [] } = useQuery({
    queryKey: ["health-definitions"],
    queryFn: () => apiFetch<HealthDef[]>("/api/v1/health-checks/definitions", { token: getToken() }),
  });
  const { data: runs = [] } = useQuery({
    queryKey: ["health-runs"],
    queryFn: () => apiFetch<HealthRun[]>("/api/v1/health-checks/runs", { token: getToken() }),
  });
  const runChecks = useMutation({
    mutationFn: () => apiFetch<{ run_id: number }>("/api/v1/health-checks/run", { method: "POST", token: getToken() }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["health-runs"] }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Health checks</h1>
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Check definitions</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm mb-4">Backup coverage, stale snapshots, missing owners, storage threshold warnings.</p>
          <Button onClick={() => runChecks.mutate()} disabled={runChecks.isPending}>
            {runChecks.isPending ? "Running…" : "Run all health checks"}
          </Button>
        </CardContent>
      </Card>
      <Card className="mb-6">
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Slug</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Description</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {definitions.map((d) => (
                <TableRow key={d.id}>
                  <TableCell className="font-medium">{d.name}</TableCell>
                  <TableCell>{d.slug}</TableCell>
                  <TableCell>{d.check_type}</TableCell>
                  <TableCell className="text-muted-foreground">{d.description ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Run history</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Run ID</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Results</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runs.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">{r.id}</TableCell>
                  <TableCell className="text-muted-foreground">{r.started_at}</TableCell>
                  <TableCell>{r.status}</TableCell>
                  <TableCell>{r.results.map((x) => `${x.status}`).join(", ")}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
