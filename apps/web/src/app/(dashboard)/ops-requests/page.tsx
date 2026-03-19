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

type Template = { id: number; name: string; slug: string; request_type: string; form_schema: string | null };

export default function OpsRequestsPage() {
  const [templateId, setTemplateId] = useState<number | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [recipient, setRecipient] = useState("");
  const [preview, setPreview] = useState<{ subject: string; body_html: string } | null>(null);
  const [draftId, setDraftId] = useState<number | null>(null);
  const queryClient = useQueryClient();

  const { data: templatesResp } = useQuery({
    queryKey: ["ops-request-templates"],
    queryFn: () => apiFetch<{ data: Template[] }>("/api/v1/ops-requests/templates", { token: getToken() }),
  });
  const templates = templatesResp?.data ?? [];

  const { data: listResp } = useQuery({
    queryKey: ["ops-requests"],
    queryFn: () => apiFetch<{ data: { id: number; request_type: string; status: string; subject: string; created_at: string }[] }>("/api/v1/ops-requests", { token: getToken() }),
  });
  const requests = listResp?.data ?? [];

  const previewMutation = useMutation({
    mutationFn: () => apiFetch<{ subject: string; body_html: string }>("/api/v1/ops-requests/preview", { method: "POST", token: getToken(), body: JSON.stringify({ template_id: templateId, request_type: templates.find((t) => t.id === templateId)?.request_type ?? "datacenter_entry", form_data: formData, recipient }) }),
    onSuccess: (data) => setPreview(data),
  });

  const createDraftMutation = useMutation({
    mutationFn: () => apiFetch<{ id: number; status: string }>("/api/v1/ops-requests", { method: "POST", token: getToken(), body: JSON.stringify({ template_id: templateId, request_type: templates.find((t) => t.id === templateId)?.request_type ?? "datacenter_entry", form_data: formData, recipient: recipient || undefined }) }),
    onSuccess: (data) => { setDraftId(data.id); queryClient.invalidateQueries({ queryKey: ["ops-requests"] }); },
  });

  const sendMutation = useMutation({
    mutationFn: (id: number) => apiFetch<{ status: string }>(`/api/v1/ops-requests/${id}/send`, { method: "POST", token: getToken() }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ops-requests"] }),
  });

  const selectedTemplate = templateId ? templates.find((t) => t.id === templateId) : null;
  const formSchema: Record<string, string> = selectedTemplate?.form_schema ? (() => { try { return JSON.parse(selectedTemplate.form_schema); } catch { return {}; } })() : {};

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Operations Requests</h1>
      <p className="text-muted-foreground mb-4">Datacenter entry and asset install/removal. Structured forms, preview, draft and send (placeholder email).</p>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>New request</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Template</Label>
            <select className="border rounded px-2 py-1 w-full mt-1" value={templateId ?? ""} onChange={(e) => { setTemplateId(e.target.value ? Number(e.target.value) : null); setFormData({}); setPreview(null); }}>
              <option value="">Select…</option>
              {templates.map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </div>
          {Object.keys(formSchema).map((key) => (
            <div key={key}>
              <Label>{key}</Label>
              <Input value={formData[key] ?? ""} onChange={(e) => setFormData((prev) => ({ ...prev, [key]: e.target.value }))} className="mt-1" />
            </div>
          ))}
          <div>
            <Label>Recipient (placeholder)</Label>
            <Input value={recipient} onChange={(e) => setRecipient(e.target.value)} placeholder="ops@example.com" />
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => previewMutation.mutate()} disabled={!templateId || previewMutation.isPending}>Preview</Button>
            <Button variant="outline" onClick={() => createDraftMutation.mutate()} disabled={!templateId || createDraftMutation.isPending}>Save draft</Button>
          </div>
          {preview && (
            <Card>
              <CardHeader><CardTitle>Preview</CardTitle></CardHeader>
              <CardContent>
                <p className="font-medium">{preview.subject}</p>
                <div className="mt-2 prose prose-sm max-w-none" dangerouslySetInnerHTML={{ __html: preview.body_html }} />
              </CardContent>
            </Card>
          )}
          {draftId && (
            <Button onClick={() => sendMutation.mutate(draftId)} disabled={sendMutation.isPending}>Send (placeholder)</Button>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Request history</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Subject</TableHead>
                <TableHead>Created</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {requests.map((r) => (
                <TableRow key={r.id}>
                  <TableCell>{r.id}</TableCell>
                  <TableCell>{r.request_type}</TableCell>
                  <TableCell>{r.status}</TableCell>
                  <TableCell className="max-w-xs truncate">{r.subject}</TableCell>
                  <TableCell>{new Date(r.created_at).toLocaleString()}</TableCell>
                  <TableCell>
                    {r.status === "draft" && (
                      <Button size="sm" variant="outline" onClick={() => sendMutation.mutate(r.id)} disabled={sendMutation.isPending}>Send</Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
