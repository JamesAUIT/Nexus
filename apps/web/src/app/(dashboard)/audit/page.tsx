"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type AuditLog = { id: number; user_id: number | null; action: string; resource_type: string; resource_id: string | null; details: string | null; ip: string | null; created_at: string };

export default function AuditPage() {
  const { data: logs = [], isLoading } = useQuery({
    queryKey: ["audit"],
    queryFn: () => apiFetch<AuditLog[]>("/api/v1/audit?limit=100", { token: getToken() }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Audit log</h1>
      <Card>
        <CardHeader>
          <CardTitle>Events</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : logs.length === 0 ? (
            <p className="text-muted-foreground">No audit events yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead>User ID</TableHead>
                  <TableHead>IP</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((l) => (
                  <TableRow key={l.id}>
                    <TableCell className="text-muted-foreground text-sm">{l.created_at}</TableCell>
                    <TableCell className="font-medium">{l.action}</TableCell>
                    <TableCell>{l.resource_type}{l.resource_id ? ` ${l.resource_id}` : ""}</TableCell>
                    <TableCell>{l.user_id ?? "—"}</TableCell>
                    <TableCell>{l.ip ?? "—"}</TableCell>
                    <TableCell>{l.details ?? "—"}</TableCell>
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
