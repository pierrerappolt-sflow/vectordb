import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="min-h-screen p-8">
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-8 text-4xl font-bold">StackAI Admin</h1>

        <div className="grid gap-4 md:grid-cols-2">
          <Link href="/libraries">
            <Card className="cursor-pointer transition-colors hover:bg-accent">
              <CardHeader>
                <CardTitle>Libraries</CardTitle>
                <CardDescription>
                  View and manage your document libraries
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Access your library collection →
                </p>
              </CardContent>
            </Card>
          </Link>
        </div>
      </div>
    </div>
  );
}
