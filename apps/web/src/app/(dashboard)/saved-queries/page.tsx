"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type SavedQuery = { id: number; name: string; query_json: string | null };

export default function SavedQueriesPage() {
  const queryClient = useQueryClient();
  const [newName, setNewName] = useState("");
  const { data: queries = [], isLoading } = useQuery({
    queryKey: ["saved-queries"],
    queryFn: () => apiFetch<SavedQuery[]>("/api/v1/saved-queries", { token: getToken() }),
  });
  const create = useMutation({
    mutationFn: (name: string) =>
      apiFetch<SavedQuery>("/api/v1/saved-queries", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({ name, query_json: "{}" }),
      }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["saved-queries"] }); setNewName(""); },
  });
  const remove = useMutation({
    mutationFn: (id: number) => apiFetch(`/api/v1/saved-queries/${id}`, { method: "DELETE", token: getToken() }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["saved-queries"] }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Saved queries</h1>
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Create saved query</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input placeholder="Query name" value={newName} onChange={(e) => setNewName(e.target.value)} className="max-w-xs" />
            <Button onClick={() => newName.trim() && create.mutate(newName.trim())} disabled={create.isPending || !newName.trim()}>
              Save
            </Button>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Your saved queries (reusable filtered views)</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : queries.length === 0 ? (
            <p className="text-muted-foreground">No saved queries yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Query (JSON)</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {queries.map((q) => (
                  <TableRow key={q.id}>
                    <TableCell className="font-medium">{q.name}</TableCell>
                    <TableCell className="text-muted-foreground font-mono text-sm">{q.query_json ?? "{}"}</TableCell>
                    <TableCell>
                      <Button size="sm" variant="outline" onClick={() => remove.mutate(q.id)} disabled={remove.isPending}>Delete</Button>
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
