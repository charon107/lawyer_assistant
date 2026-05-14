import { Sidebar, AppSidebar } from "@/components/layout";
import { AuthGuard } from "@/components/layout/auth-guard";
import { PageTransition } from "@/components/layout/page-transition";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <div className="flex h-screen">
        <AppSidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Sidebar />
          <main className="flex min-h-0 flex-1 flex-col overflow-auto p-4 sm:p-6">
            <PageTransition>{children}</PageTransition>
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}
