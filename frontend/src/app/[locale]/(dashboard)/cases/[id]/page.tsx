"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useCaseDetail } from "@/hooks/use-cases";
import { ROUTES } from "@/lib/constants";
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Skeleton,
  Badge,
} from "@/components/ui";
import {
  ArrowLeft,
  Upload,
  FileText,
  Trash2,
  MessageSquare,
  File,
  Loader2,
} from "lucide-react";
import { useRef, useState } from "react";
import type { LPADocument } from "@/types";

export default function CaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations("cases");
  const caseId = params.id as string;
  const { caseDetail, isLoading, error, fetchCase, uploadDocument, deleteDocument, refreshDocuments } =
    useCaseDetail(caseId);

  useEffect(() => {
    fetchCase();
  }, [fetchCase]);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6 p-3 sm:p-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error || !caseDetail) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
        <p className="text-lg font-medium">{error || "Case not found"}</p>
        <Button variant="outline" className="mt-4" onClick={() => router.push(ROUTES.CASES)}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          {t("backToCases")}
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-3 sm:p-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0" asChild>
              <Link href={ROUTES.CASES}>
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <h1 className="text-2xl font-bold tracking-tight truncate">{caseDetail.name}</h1>
            <Badge variant={caseDetail.status === "active" ? "default" : "secondary"}>
              {t(caseDetail.status as "active" | "closed")}
            </Badge>
            {caseDetail.document_type && caseDetail.document_type !== "lpa" && (
              <Badge variant="outline">
                {t(`documentType${caseDetail.document_type.charAt(0).toUpperCase()}${caseDetail.document_type.slice(1)}`, { defaultValue: caseDetail.document_type })}
              </Badge>
            )}
          </div>
          {caseDetail.description && (
            <p className="text-muted-foreground text-sm ml-10">{caseDetail.description}</p>
          )}
        </div>
        <Button asChild>
          <Link href={`${ROUTES.CASES}/${caseId}/chat`}>
            <MessageSquare className="mr-2 h-4 w-4" />
            {t("startChat")}
          </Link>
        </Button>
      </div>

      {/* Documents */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              {t("documents")} ({caseDetail.document_count})
            </CardTitle>
            <UploadButton onUpload={uploadDocument} onRefresh={refreshDocuments} />
          </div>
        </CardHeader>
        <CardContent>
          {caseDetail.documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <FileText className="h-10 w-10 mb-3 opacity-50" />
              <p className="font-medium">{t("noDocuments")}</p>
              <p className="text-sm">{t("dragDrop")}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {caseDetail.documents.map((doc) => (
                <DocumentItem key={doc.id} doc={doc} onDelete={deleteDocument} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function UploadButton({
  onUpload,
  onRefresh,
}: {
  onUpload: (file: File) => Promise<import("@/types").LPADocument | null>;
  onRefresh: () => Promise<void>;
}) {
  const t = useTranslations("cases");
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const result = await onUpload(file);
    setUploading(false);
    if (inputRef.current) inputRef.current.value = "";
    if (result) {
      await onRefresh();
    }
  };

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept=".pdf,.docx,.doc,.txt"
        onChange={handleFileChange}
      />
      <Button
        variant="outline"
        size="sm"
        disabled={uploading}
        onClick={() => inputRef.current?.click()}
      >
        {uploading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            {t("uploading")}
          </>
        ) : (
          <>
            <Upload className="mr-2 h-4 w-4" />
            {t("uploadDocument")}
          </>
        )}
      </Button>
    </>
  );
}

function DocumentItem({
  doc,
  onDelete,
}: {
  doc: LPADocument;
  onDelete: (docId: string) => Promise<boolean>;
}) {
  const t = useTranslations("cases");
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!window.confirm(t("deleteDocumentConfirm"))) return;
    setDeleting(true);
    await onDelete(doc.id);
    setDeleting(false);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case "pdf":
        return <FileText className="h-5 w-5 text-red-500" />;
      case "docx":
      case "doc":
        return <FileText className="h-5 w-5 text-blue-500" />;
      default:
        return <File className="h-5 w-5 text-muted-foreground" />;
    }
  };

  return (
    <div className="flex items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-muted/50">
      {getFileIcon(doc.file_type)}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{doc.filename}</p>
        <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
          <span>{formatSize(doc.size)}</span>
          {doc.summary && (
            <>
              <span>·</span>
              <span className="truncate">{doc.summary}</span>
            </>
          )}
        </div>
      </div>
      <Button
        variant="ghost"
        size="sm"
        className="h-8 w-8 p-0 shrink-0"
        disabled={deleting}
        onClick={handleDelete}
      >
        <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
      </Button>
    </div>
  );
}
