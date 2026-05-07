"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useCases } from "@/hooks/use-cases";
import { ROUTES } from "@/lib/constants";
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Textarea,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Skeleton,
} from "@/components/ui";
import { Plus, Briefcase, FileText, Trash2, ArrowRight } from "lucide-react";
import type { LPACase } from "@/types";

export default function CasesPage() {
  const t = useTranslations("cases");
  const { cases, total, isLoading, fetchCases, createCase, deleteCase } = useCases();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setCreating(true);
    const result = await createCase(name.trim(), description.trim() || undefined);
    setCreating(false);
    if (result) {
      setOpen(false);
      setName("");
      setDescription("");
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm(t("deleteConfirm"))) return;
    await deleteCase(id);
  };

  return (
    <div className="flex flex-col gap-6 p-3 sm:p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-muted-foreground text-sm">
            {total > 0 ? t("caseCount", { count: total }) : t("noCases")}
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              {t("createCase")}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("createCase")}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 pt-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">{t("caseName")}</label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder={t("caseName")}
                  onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">{t("caseDescription")}</label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder={t("caseDescription")}
                  rows={3}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setOpen(false)}>
                  {t("cancel", { defaultValue: "取消" })}
                </Button>
                <Button onClick={handleCreate} disabled={!name.trim() || creating}>
                  {creating ? t("loading", { defaultValue: "创建中..." }) : t("createCase")}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-2/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : cases.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
          <Briefcase className="h-12 w-12 mb-4 opacity-50" />
          <p className="text-lg font-medium">{t("noCases")}</p>
          <p className="text-sm">{t("createFirst")}</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cases.map((c) => (
            <CaseCard key={c.id} caseData={c} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
}

function CaseCard({
  caseData,
  onDelete,
}: {
  caseData: LPACase;
  onDelete: (e: React.MouseEvent, id: string) => void;
}) {
  const t = useTranslations("cases");
  const router = useRouter();

  return (
    <Card
      className="group cursor-pointer transition-shadow hover:shadow-md"
      onClick={() => router.push(`${ROUTES.CASES}/${caseData.id}`)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <Briefcase className="h-5 w-5 text-muted-foreground shrink-0" />
            <CardTitle className="truncate text-base">{caseData.name}</CardTitle>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
            onClick={(e) => onDelete(e, caseData.id)}
          >
            <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
          </Button>
        </div>
        {caseData.description && (
          <p className="text-sm text-muted-foreground line-clamp-2">{caseData.description}</p>
        )}
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <FileText className="h-4 w-4" />
            <span>{t("documentCount", { count: caseData.document_count })}</span>
          </div>
          <ArrowRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      </CardContent>
    </Card>
  );
}
