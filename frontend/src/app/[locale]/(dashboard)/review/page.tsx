"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { UploadZone } from "@/components/review";
import { useDocumentReview } from "@/hooks/use-document-review";
import { ReviewProgressBar } from "@/components/review/progress-bar";
import { Button } from "@/components/ui";
import { FileSearch, Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api/v1";

export default function ReviewPage() {
  const router = useRouter();
  const review = useDocumentReview();
  const [fileName, setFileName] = useState("");

  const handleUpload = async (file: File) => {
    setFileName(file.name);
    const id = await review.startReview(file, API_BASE);
    if (id) {
      router.push(`/review/${id}`);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-16 px-4">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <FileSearch className="h-6 w-6 text-brand" />
          智能文件审查
        </h1>
        <p className="text-muted-foreground">
          上传法律文件（合同、协议、NDA 等），AI 将自动提取关键条款、识别风险点并生成审查报告。
        </p>
      </div>

      {review.status === "idle" && (
        <UploadZone onUpload={handleUpload} />
      )}

      {review.status === "uploading" && (
        <div className="flex flex-col items-center gap-4 py-12">
          <Loader2 className="h-8 w-8 animate-spin text-brand" />
          <p className="text-muted-foreground">正在上传 {fileName}...</p>
        </div>
      )}

      {review.error && (
        <div className="border border-destructive/30 bg-destructive/5 rounded-xl p-6 text-center">
          <p className="text-destructive font-medium mb-2">上传失败</p>
          <p className="text-sm text-muted-foreground">{review.error}</p>
          <Button
            variant="outline"
            onClick={() => window.location.reload()}
            className="mt-4"
          >
            重试
          </Button>
        </div>
      )}
    </div>
  );
}
