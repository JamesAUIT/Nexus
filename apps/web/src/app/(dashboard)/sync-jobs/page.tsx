"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type SyncJob = { id: number; connector_id: number; schedule_cron: string | null; last_run_at: string | null; last_status: string | null };
type SyncRun = { id: number; sync_job_id: number; started_at: string; finished_at: string | null; status: string; error_message: string | null };

export default function SyncJobsPage() {
  const queryClient = useQueryClient();
  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ["sync-jobs"],
    queryFn: () => apiFetch<SyncJob[]>("/api/v1/sync-jobs", { token: getToken() }),
  });

  const trigger = useMutation({
    mutationFn: (id: number) => apiFetch<{ status: string }>(`/api/v1/sync-jobs/${id}/trigger`, { method: "POST", token: getToken() }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sync-jobs"] }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Sync jobs</h1>
      <Card>
        <CardHeader>
          <CardTitle>Sync jobs</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Connector ID</TableHead>
                  <TableHead>Schedule</TableHead>
                  <TableHead>Last run</TableHead>
                  <TableHead>Last status</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.map((j) => (
                  <TableRow key={j.id}>
                    <TableCell className="font-medium">{j.id}</TableCell>
                    <TableCell>{j.connector_id}</TableCell>
                    <TableCell>{j.schedule_cron ?? "—"}</TableCell>
                    <TableCell>{j.last_run_at ?? "—"}</TableCell>
                    <TableCell>{j.last_status ?? "—"}</TableCell>
                    <TableCell>
                      <Button size="sm" variant="outline" onClick={() => trigger.mutate(j.id)} disabled={trigger.isPending}>
                        Trigger
                      </Button>
                    </TableCell>
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
