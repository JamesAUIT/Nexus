"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function ScriptsPage() {
  const [selectedScriptId, setSelectedScriptId] = useState<number | null>(null);

  const { data: definitions } = useQuery({
    queryKey: ["script-definitions"],
    queryFn: () => apiFetch<{ data: { id: number; name: string; slug: string; description: string | null; script_type: string; approved_only: boolean; timeout_seconds: number | null }[] }>("/api/v1/scripts/definitions", { token: getToken() }),
  });

  const { data: executions } = useQuery({
    queryKey: ["script-executions", selectedScriptId],
    queryFn: () => apiFetch<{ data: { id: number; script_definition_id: number; started_at: string; finished_at: string | null; status: string; stdout: string | null; stderr: string | null }[] }>(`/api/v1/scripts/executions?page=1&page_size=20${selectedScriptId ? `&script_definition_id=${selectedScriptId}` : ""}`, { token: getToken() }),
  });

  const defs = definitions?.data ?? [];
  const execs = executions?.data ?? [];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Scripts</h1>
      <p className="text-muted-foreground mb-4">Approved script definitions and execution history. No arbitrary execution from UI.</p>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Script definitions (PowerShell-ready)</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Slug</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Approved only</TableHead>
                <TableHead>Timeout</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {defs.map((d) => (
                <TableRow key={d.id}>
                  <TableCell className="font-medium">{d.name}</TableCell>
                  <TableCell>{d.slug}</TableCell>
                  <TableCell>{d.script_type}</TableCell>
                  <TableCell>{d.approved_only ? "Yes" : "No"}</TableCell>
                  <TableCell>{d.timeout_seconds ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Execution history</CardTitle>
          <select className="border rounded px-2 py-1 text-sm" value={selectedScriptId ?? ""} onChange={(e) => setSelectedScriptId(e.target.value ? Number(e.target.value) : null)}>
            <option value="">All scripts</option>
            {defs.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Script ID</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Finished</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {execs.map((e) => (
                <TableRow key={e.id}>
                  <TableCell>{e.id}</TableCell>
                  <TableCell>{e.script_definition_id}</TableCell>
                  <TableCell>{e.started_at ? new Date(e.started_at).toLocaleString() : "—"}</TableCell>
                  <TableCell>{e.finished_at ? new Date(e.finished_at).toLocaleString() : "—"}</TableCell>
                  <TableCell>{e.status}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
