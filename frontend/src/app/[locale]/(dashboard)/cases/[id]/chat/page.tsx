"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { ChatContainer } from "@/components/chat";
import { useConversationStore } from "@/stores";
import { ROUTES } from "@/lib/constants";
import { Button } from "@/components/ui";
import { ArrowLeft, Briefcase } from "lucide-react";

export default function CaseChatPage() {
  const params = useParams();
  const t = useTranslations("cases");
  const caseId = params.id as string;
  const { setCurrentConversationId } = useConversationStore();

  // Reset conversation when entering case chat
  useEffect(() => {
    setCurrentConversationId(null);
  }, [setCurrentConversationId]);

  return (
    <div className="flex min-h-0 flex-1 -m-3 sm:-m-6">
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Top bar with back link */}
        <div className="flex items-center gap-2 border-b px-3 py-2 sm:px-6">
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" asChild>
            <Link href={`${ROUTES.CASES}/${caseId}`}>
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <Briefcase className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">{t("chatWithAI")}</span>
        </div>
        <div className="flex-1 min-h-0">
          <ChatContainer caseId={caseId} />
        </div>
      </div>
    </div>
  );
}
