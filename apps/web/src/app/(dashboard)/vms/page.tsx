"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";

type VM = { id: number; name: string; power_state: string | null; ip_address: string | null; owner: string | null };

type LinkTemplate = { id: number; name: string; url_template: string; entity_types: string | null };

export default function VMsPage() {
  const { data: vms = [], isLoading } = useQuery({
    queryKey: ["vms"],
    queryFn: () => apiFetch<VM[]>("/api/v1/vms", { token: getToken() }),
  });

  const { data: templatesResp } = useQuery({
    queryKey: ["link-templates"],
    queryFn: () => apiFetch<{ data: LinkTemplate[] }>("/api/v1/link-templates", { token: getToken() }),
  });
  const vmTemplates = (templatesResp?.data ?? []).filter((t) => (t.entity_types ?? "").split(",").map((x) => x.trim()).includes("vm"));

  const copy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const openLink = async (templateId: number, entityId: string) => {
    const r = await apiFetch<{ url: string }>(`/api/v1/link-templates/resolve?template_id=${templateId}&entity_type=vm&entity_id=${entityId}`, { token: getToken() });
    if (r?.url) window.open(r.url, "_blank");
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Virtual Machines</h1>
      <p className="text-muted-foreground text-sm mb-4">Copy to clipboard and open Grafana/Log Insight links (configurable templates).</p>
      <Card>
        <CardHeader>
          <CardTitle>Virtual Machines</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Power state</TableHead>
                  <TableHead>IP</TableHead>
                  <TableHead>Owner</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {vms.map((vm) => (
                  <TableRow key={vm.id}>
                    <TableCell className="font-medium">{vm.name}</TableCell>
                    <TableCell>{vm.power_state ?? "—"}</TableCell>
                    <TableCell>{vm.ip_address ?? "—"}</TableCell>
                    <TableCell>{vm.owner ?? "—"}</TableCell>
                    <TableCell className="flex gap-1 flex-wrap">
                      <Button size="sm" variant="ghost" onClick={() => copy(vm.name)}>Copy name</Button>
                      <Button size="sm" variant="ghost" onClick={() => copy(String(vm.id))}>Copy ID</Button>
                      {vmTemplates.map((t) => (
                        <Button key={t.id} size="sm" variant="outline" onClick={() => openLink(t.id, String(vm.id))}>{t.name}</Button>
                      ))}
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
