"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type DriftFinding = { id: number; resource_type: string; resource_id: string; drift_type: string | null; field_name: string; expected_value: string | null; actual_value: string | null; source_of_truth: string; discovered_from: string | null; created_at: string };

export default function DriftPage() {
  const queryClient = useQueryClient();
  const { data: findings = [], isLoading } = useQuery({
    queryKey: ["drift"],
    queryFn: () => apiFetch<DriftFinding[]>("/api/v1/drift", { token: getToken() }),
  });
  const runDrift = useMutation({
    mutationFn: () => apiFetch<{ findings_count: number }>("/api/v1/drift/run", { method: "POST", token: getToken() }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["drift"] }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Drift / Reconciliation</h1>
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>NetBox vs live</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm mb-4">Run drift check to compare intended state (NetBox) with live systems. Findings: undocumented assets, missing assets, IP mismatch, owner missing, tag mismatch.</p>
          <Button onClick={() => runDrift.mutate()} disabled={runDrift.isPending}>
            {runDrift.isPending ? "Running…" : "Run drift check"}
          </Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Findings</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : findings.length === 0 ? (
            <p className="text-muted-foreground">No drift findings.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Drift type</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead>Field</TableHead>
                  <TableHead>Expected</TableHead>
                  <TableHead>Actual</TableHead>
                  <TableHead>Discovered from</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {findings.map((f) => (
                  <TableRow key={f.id}>
                    <TableCell className="font-medium">{f.resource_type}</TableCell>
                    <TableCell>{f.drift_type ?? "—"}</TableCell>
                    <TableCell>{f.resource_id}</TableCell>
                    <TableCell>{f.field_name}</TableCell>
                    <TableCell className="text-muted-foreground">{f.expected_value ?? "—"}</TableCell>
                    <TableCell>{f.actual_value ?? "—"}</TableCell>
                    <TableCell>{f.discovered_from ?? "—"}</TableCell>
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
