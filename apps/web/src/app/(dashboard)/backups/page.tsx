"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type BackupStatus = { id: number; entity_type: string; entity_id: string; status: string; last_run_at: string | null; details: string | null };

export default function BackupsPage() {
  const { data: backups = [], isLoading } = useQuery({
    queryKey: ["backups"],
    queryFn: () => apiFetch<BackupStatus[]>("/api/v1/backups", { token: getToken() }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Backups</h1>
      <Card>
        <CardHeader>
          <CardTitle>Backup status</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : backups.length === 0 ? (
            <p className="text-muted-foreground">No backup status records. Data appears after connector sync.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Entity type</TableHead>
                  <TableHead>Entity ID</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last run</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {backups.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell className="font-medium">{b.entity_type}</TableCell>
                    <TableCell>{b.entity_id}</TableCell>
                    <TableCell>{b.status}</TableCell>
                    <TableCell>{b.last_run_at ?? "—"}</TableCell>
                    <TableCell className="text-muted-foreground">{b.details ?? "—"}</TableCell>
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
