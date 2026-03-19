"use client";

import { use, useEffect } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type VM = { id: number; name: string; power_state: string | null; ip_address: string | null; owner: string | null };

export default function VMDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const vmId = Number(id);

  const { data: vm, isLoading } = useQuery({
    queryKey: ["vm", vmId],
    queryFn: async () => {
      const list = await apiFetch<VM[]>("/api/v1/vms", { token: getToken() });
      return list.find((v) => v.id === vmId) ?? null;
    },
    enabled: !Number.isNaN(vmId),
  });

  const { data: timeline } = useQuery({
    queryKey: ["change-events-timeline", "vm", id],
    queryFn: () => apiFetch<{ data: { change_type: string; field_name: string | null; old_value: string | null; new_value: string | null; changed_at: string; changed_by: string | null }[] }>(`/api/v1/change-events/timeline?entity_type=vm&entity_id=${id}`, { token: getToken() }),
    enabled: !Number.isNaN(vmId),
  });

  const copy = (text: string) => navigator.clipboard.writeText(text);

  useEffect(() => {
    if (!vm || Number.isNaN(vmId)) return;
    apiFetch(`/api/v1/recent?entity_type=vm&entity_id=${vmId}&display_name=${encodeURIComponent(vm.name)}`, { method: "POST", token: getToken() }).catch(() => {});
  }, [vm, vmId]);

  if (Number.isNaN(vmId)) return <p>Invalid VM ID</p>;
  if (isLoading || !vm) return <p className="text-muted-foreground">Loading…</p>;

  return (
    <div>
      <div className="flex items-center gap-4 mb-4">
        <Link href="/vms" className="text-primary hover:underline">← VMs</Link>
        <h1 className="text-2xl font-bold">{vm.name}</h1>
        <Button size="sm" variant="outline" onClick={() => copy(vm.name)}>Copy name</Button>
        <Button size="sm" variant="outline" onClick={() => copy(String(vm.id))}>Copy ID</Button>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-2">
            <div><dt className="text-muted-foreground text-sm">ID</dt><dd>{vm.id}</dd></div>
            <div><dt className="text-muted-foreground text-sm">Power state</dt><dd>{vm.power_state ?? "—"}</dd></div>
            <div><dt className="text-muted-foreground text-sm">IP</dt><dd>{vm.ip_address ?? "—"}</dd></div>
            <div><dt className="text-muted-foreground text-sm">Owner</dt><dd>{vm.owner ?? "—"}</dd></div>
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Change timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {(timeline?.data ?? []).map((e, i) => (
              <li key={i} className="text-sm border-l-2 pl-3 py-1">
                <span className="text-muted-foreground">{new Date(e.changed_at).toLocaleString()}</span> — {e.change_type}
                {e.field_name && ` (${e.field_name}: ${e.old_value ?? "—"} → ${e.new_value ?? "—"})`}
                {e.changed_by && ` by ${e.changed_by}`}
              </li>
            ))}
          </ul>
          {(timeline?.data ?? []).length === 0 && <p className="text-muted-foreground">No change events.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
