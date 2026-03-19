"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";

export default function ChangeEventsPage() {
  const [entityType, setEntityType] = useState("");
  const [entityId, setEntityId] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["change-events", entityType, entityId, page],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      if (entityType) params.set("entity_type", entityType);
      if (entityId) params.set("entity_id", entityId);
      return apiFetch<{ data: { id: number; entity_type: string; entity_id: string; change_type: string; field_name: string | null; old_value: string | null; new_value: string | null; changed_at: string; changed_by: string | null }[]; meta: { total: number } }>(`/api/v1/change-events?${params}`, { token: getToken() });
    },
  });

  const rows = data?.data ?? [];
  const total = data?.meta?.total ?? 0;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Change events</h1>
      <p className="text-muted-foreground mb-4">Change history and timeline.</p>

      <Card>
        <CardHeader className="flex flex-row items-center gap-4 flex-wrap">
          <CardTitle>History</CardTitle>
          <Input placeholder="Entity type" value={entityType} onChange={(e) => setEntityType(e.target.value)} className="w-32" />
          <Input placeholder="Entity ID" value={entityId} onChange={(e) => setEntityId(e.target.value)} className="w-32" />
        </CardHeader>
        <CardContent>
          {isLoading ? <p className="text-muted-foreground">Loading…</p> : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Entity</TableHead>
                  <TableHead>Change type</TableHead>
                  <TableHead>Field</TableHead>
                  <TableHead>Old → New</TableHead>
                  <TableHead>Changed at</TableHead>
                  <TableHead>By</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.entity_type}/{r.entity_id}</TableCell>
                    <TableCell>{r.change_type}</TableCell>
                    <TableCell>{r.field_name ?? "—"}</TableCell>
                    <TableCell className="max-w-xs truncate">{r.old_value ?? "—"} → {r.new_value ?? "—"}</TableCell>
                    <TableCell>{new Date(r.changed_at).toLocaleString()}</TableCell>
                    <TableCell>{r.changed_by ?? "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          {total > 20 && (
            <div className="flex justify-between mt-4">
              <button type="button" className="text-sm text-primary" onClick={() => setPage((p) => Math.max(1, p - 1))}>Previous</button>
              <button type="button" className="text-sm text-primary" onClick={() => setPage((p) => p + 1)}>Next</button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
