"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import Link from "next/link";

type Runbook = { id: number; name: string; content: string | null; category: string | null; tags: string | null; related_systems: string | null; related_links: string | null };

export default function RunbooksPage() {
  const { data: runbooks = [], isLoading } = useQuery({
    queryKey: ["runbooks"],
    queryFn: () => apiFetch<Runbook[]>("/api/v1/runbooks", { token: getToken() }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Runbooks</h1>
      <Card>
        <CardHeader>
          <CardTitle>Runbooks (markdown, categories, tags)</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Tags</TableHead>
                  <TableHead>Related systems</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runbooks.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-medium">{r.name}</TableCell>
                    <TableCell>{r.category ?? "—"}</TableCell>
                    <TableCell className="text-muted-foreground">{r.tags ?? "—"}</TableCell>
                    <TableCell>{r.related_systems ?? "—"}</TableCell>
                    <TableCell>
                      <Link href={`/runbooks/${r.id}`} className="text-primary hover:underline">View</Link>
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
