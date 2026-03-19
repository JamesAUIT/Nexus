"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type ScriptDef = {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  script_type: string;
  approved_only: boolean;
  timeout_seconds: number | null;
  parameters_schema: string | null;
  required_permission: string | null;
  can_execute: boolean;
};

type ParamSchema = { name: string; type: string; label: string }[];

export default function ScriptLibraryPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [params, setParams] = useState<Record<string, string>>({});
  const queryClient = useQueryClient();

  const { data: definitions } = useQuery({
    queryKey: ["script-definitions"],
    queryFn: () => apiFetch<{ data: ScriptDef[] }>("/api/v1/scripts/definitions", { token: getToken() }),
  });

  const { data: definition } = useQuery({
    queryKey: ["script-definition", selectedId],
    queryFn: () => apiFetch<ScriptDef>(`/api/v1/scripts/definitions/${selectedId}`, { token: getToken() }),
    enabled: selectedId != null,
  });

  const executeMutation = useMutation({
    mutationFn: (id: number) => apiFetch<{ execution_id: number; status: string }>(`/api/v1/scripts/definitions/${id}/execute`, { method: "POST", token: getToken(), body: JSON.stringify({ parameters: params }) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["script-executions"] }),
  });

  const { data: executions } = useQuery({
    queryKey: ["script-executions", selectedId],
    queryFn: () => apiFetch<{ data: { id: number; script_definition_id: number; started_at: string; status: string; stdout: string | null }[] }>(`/api/v1/scripts/executions?page=1&page_size=10${selectedId ? `&script_definition_id=${selectedId}` : ""}`, { token: getToken() }),
  });

  const defs = definitions?.data ?? [];
  const paramSchema: ParamSchema = definition?.parameters_schema ? (() => { try { return JSON.parse(definition.parameters_schema); } catch { return []; } })() : [];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Script Library</h1>
      <p className="text-muted-foreground mb-4">Predefined scripts with parameter forms. RBAC-gated execution and audit integration.</p>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Scripts</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Can run</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {defs.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell className="font-medium">{d.name}</TableCell>
                    <TableCell>{d.script_type}</TableCell>
                    <TableCell>{d.can_execute ? "Yes" : "No"}</TableCell>
                    <TableCell>
                      <Button size="sm" variant="outline" onClick={() => { setSelectedId(d.id); setParams({}); }}>Open</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{definition?.name ?? "Select a script"}</CardTitle>
          </CardHeader>
          <CardContent>
            {definition && (
              <>
                {definition.description && <p className="text-muted-foreground text-sm mb-4">{definition.description}</p>}
                {paramSchema.length > 0 && (
                  <div className="space-y-2 mb-4">
                    {paramSchema.map((p) => (
                      <div key={p.name}>
                        <Label>{p.label || p.name}</Label>
                        <Input value={params[p.name] ?? ""} onChange={(e) => setParams((prev) => ({ ...prev, [p.name]: e.target.value }))} className="mt-1" />
                      </div>
                    ))}
                  </div>
                )}
                {definition.can_execute ? (
                  <Button onClick={() => executeMutation.mutate(definition.id)} disabled={executeMutation.isPending}>
                    {executeMutation.isPending ? "Running…" : "Run script"}
                  </Button>
                ) : (
                  <p className="text-muted-foreground text-sm">You do not have permission to run this script.</p>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Execution history</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Script</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(executions?.data ?? []).map((e) => (
                <TableRow key={e.id}>
                  <TableCell>{e.id}</TableCell>
                  <TableCell>{e.script_definition_id}</TableCell>
                  <TableCell>{e.started_at ? new Date(e.started_at).toLocaleString() : "—"}</TableCell>
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
