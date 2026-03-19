"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

type Runbook = { id: number; name: string; content: string | null; category: string | null; tags: string | null; related_systems: string | null; related_links: string | null };

export default function RunbookDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const { data: runbook, isLoading } = useQuery({
    queryKey: ["runbook", id],
    queryFn: () => apiFetch<Runbook>(`/api/v1/runbooks/${id}`, { token: getToken() }),
    enabled: !Number.isNaN(id),
  });

  if (isLoading || !runbook) return <p className="text-muted-foreground">Loading...</p>;
  return (
    <div>
      <div className="mb-4"><Link href="/runbooks" className="text-primary hover:underline">← Runbooks</Link></div>
      <h1 className="text-2xl font-bold mb-6">{runbook.name}</h1>
      <Card>
        <CardHeader>
          <CardTitle>Details</CardTitle>
          <p className="text-sm text-muted-foreground">Category: {runbook.category ?? "—"} | Tags: {runbook.tags ?? "—"}</p>
        </CardHeader>
        <CardContent>
          <pre className="whitespace-pre-wrap font-sans text-sm bg-muted/50 p-4 rounded-md">{runbook.content ?? "No content."}</pre>
          {runbook.related_systems && <p className="mt-4 text-sm text-muted-foreground">Related systems: {runbook.related_systems}</p>}
          {runbook.related_links && <p className="text-sm text-muted-foreground">Related links: {runbook.related_links}</p>}
        </CardContent>
      </Card>
    </div>
  );
}
