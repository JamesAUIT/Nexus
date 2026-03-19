"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type Link = { id: number; name: string; url: string; category: string | null; site_id: number | null; related_entity_type: string | null; related_entity_id: string | null };

export default function LinksPage() {
  const { data: links = [], isLoading } = useQuery({
    queryKey: ["useful-links"],
    queryFn: () => apiFetch<Link[]>("/api/v1/useful-links", { token: getToken() }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Useful links</h1>
      <Card>
        <CardHeader>
          <CardTitle>Links (by category, role-filtered)</CardTitle>
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
                  <TableHead>Site</TableHead>
                  <TableHead>Related</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {links.map((l) => (
                  <TableRow key={l.id}>
                    <TableCell className="font-medium">{l.name}</TableCell>
                    <TableCell>{l.category ?? "—"}</TableCell>
                    <TableCell>{l.site_id ?? "—"}</TableCell>
                    <TableCell>{l.related_entity_type && l.related_entity_id ? `${l.related_entity_type}:${l.related_entity_id}` : "—"}</TableCell>
                    <TableCell>
                      <a href={l.url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                        Open
                      </a>
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
