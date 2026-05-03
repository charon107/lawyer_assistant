"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { UploadZone } from "@/components/review";
import { useLPAReview } from "@/hooks/use-lpa-review";
import { ReviewProgressBar } from "@/components/review/progress-bar";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api/v1";

export default function ReviewPage() {
  const router = useRouter();
  const review = useLPAReview();
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
        <h1 className="text-2xl font-bold mb-2">&#x1F50D; LPA 合同审查</h1>
        <p className="text-zinc-400">
          上传有限合伙协议（LPA），AI 将自动完成基本要素提取、费用结构审查和 GP/LP 权利义务分析。
        </p>
      </div>

      {review.status === "idle" && (
        <UploadZone onUpload={handleUpload} />
      )}

      {review.status === "uploading" && (
        <div className="flex flex-col items-center gap-4 py-12">
          <div className="animate-spin text-3xl">&#x2699;</div>
          <p className="text-zinc-400">正在上传 {fileName}...</p>
        </div>
      )}

      {review.error && (
        <div className="border border-red-500/50 bg-red-500/10 rounded-xl p-6 text-center">
          <p className="text-red-400 mb-2">上传失败</p>
          <p className="text-sm text-zinc-400">{review.error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-zinc-800 rounded-lg text-sm hover:bg-zinc-700"
          >
            重试
          </button>
        </div>
      )}
    </div>
  );
}
