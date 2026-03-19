"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function ConnectivityPage() {
  const [target, setTarget] = useState("");
  const [checkType, setCheckType] = useState<"ping" | "tcp" | "dns">("ping");
  const queryClient = useQueryClient();

  const runMutation = useMutation({
    mutationFn: () => apiFetch<{ success: boolean; result: { detail: string }; checked_at: string }>(`/api/v1/connectivity/check?target=${encodeURIComponent(target)}&check_type=${checkType}`, { method: "POST", token: getToken() }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["connectivity-recent"] }),
  });

  const { data: recentResp } = useQuery({
    queryKey: ["connectivity-recent"],
    queryFn: () => apiFetch<{ data: { target: string; check_type: string; success: boolean; result: { detail?: string }; checked_at: string }[] }>("/api/v1/connectivity/recent?limit=20", { token: getToken() }),
  });

  const list = recentResp?.data ?? [];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Connectivity testing</h1>
      <p className="text-muted-foreground mb-4">Ping, TCP port check, DNS lookup. Results are cached.</p>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Run check</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2 flex-wrap items-center">
          <Input placeholder={checkType === "tcp" ? "host:port" : "Hostname or IP"} value={target} onChange={(e) => setTarget(e.target.value)} className="w-56" />
          <select className="border rounded px-2 py-1" value={checkType} onChange={(e) => setCheckType(e.target.value as "ping" | "tcp" | "dns")}>
            <option value="ping">Ping</option>
            <option value="tcp">TCP port</option>
            <option value="dns">DNS lookup</option>
          </select>
          <Button onClick={() => target && runMutation.mutate()} disabled={!target || runMutation.isPending}>
            {runMutation.isPending ? "Checking…" : "Check"}
          </Button>
          {runMutation.data && (
            <span className={runMutation.data.success ? "text-green-600" : "text-red-600"}>
              {runMutation.data.success ? "OK" : "Failed"} {runMutation.data.result?.detail}
            </span>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent results</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Target</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Result</TableHead>
                <TableHead>Checked at</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {list.map((r: { target: string; check_type: string; success: boolean; result?: { detail?: string }; checked_at: string }, i: number) => (
                <TableRow key={i}>
                  <TableCell>{r.target}</TableCell>
                  <TableCell>{r.check_type}</TableCell>
                  <TableCell><span className={r.success ? "text-green-600" : "text-red-600"}>{r.success ? "OK" : "Fail"}</span> {r.result?.detail}</TableCell>
                  <TableCell>{r.checked_at ? new Date(r.checked_at).toLocaleString() : "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
