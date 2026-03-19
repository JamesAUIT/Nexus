"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import Link from "next/link";

type SearchResult = { type: string; id: number | string; title: string; subtitle: string | null; link: string };

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");

  const { data: results = [], isLoading } = useQuery({
    queryKey: ["search", submitted],
    queryFn: () => apiFetch<SearchResult[]>(`/api/v1/search?q=${encodeURIComponent(submitted)}`, { token: getToken() }),
    enabled: submitted.length > 0,
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Global search</h1>
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Search</CardTitle>
        </CardHeader>
        <CardContent>
          <form
              onSubmit={(e) => {
                e.preventDefault();
                setSubmitted(query.trim());
              }}
              className="flex gap-2"
            >
              <Input
                placeholder="VMs, hosts, IPs, racks, datastores..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="max-w-md"
              />
              <Button type="submit">Search</Button>
            </form>
        </CardContent>
      </Card>
      {submitted && (
        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <p className="text-muted-foreground">Loading...</p>
            ) : results.length === 0 ? (
              <p className="text-muted-foreground">No results.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Subtitle</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.map((r) => (
                    <TableRow key={`${r.type}-${r.id}`}>
                      <TableCell className="font-medium">{r.type.replace("_", " ")}</TableCell>
                      <TableCell>{r.title}</TableCell>
                      <TableCell className="text-muted-foreground">{r.subtitle ?? "—"}</TableCell>
                      <TableCell>
                        <Link href={r.link} className="text-primary hover:underline">
                          Open
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
