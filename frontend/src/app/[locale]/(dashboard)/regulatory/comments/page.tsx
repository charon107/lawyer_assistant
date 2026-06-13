"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowLeft, MessagesSquare } from "lucide-react";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { CommentDecisionBadge } from "@/components/regulatory";
import { ROUTES } from "@/lib/constants";
import { regulatoryApi } from "@/lib/regulatory";
import type { CommentDecision, RegulatoryComment } from "@/types/regulatory";

const DECISION_ACTIONS: CommentDecision[] = ["filing", "not-filing", "filed", "waived"];

export default function RegulatoryCommentsPage() {
  const t = useTranslations("regulatory");
  const [items, setItems] = useState<RegulatoryComment[]>([]);
  const [pending, setPending] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const res = await regulatoryApi.listComments(0, 100);
      setItems(res.items);
      setPending(res.pending_within_30d);
    } catch {
      // non-critical
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function decide(c: RegulatoryComment, decision: CommentDecision) {
    const rationale = window.prompt(t("comments.rationalePrompt")) ?? undefined;
    await regulatoryApi.decideComment(c.id, { decision, rationale });
    await load();
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.REGULATORY}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("comments.back")}
        </Link>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <MessagesSquare className="text-brand h-6 w-6" />
          {t("comments.title")}
        </h1>
        <p className="text-muted-foreground mt-1">
          {t("comments.description")}
          {pending > 0 && <span className="text-amber-500"> · {t("comments.pending", { n: pending })}</span>}
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      ) : items.length === 0 ? (
        <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-10 text-center text-sm">
          {t("comments.empty")}
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {items.map((c) => (
            <li key={c.id}>
              <Card>
                <CardContent className="flex flex-col gap-3 p-4">
                  <div className="flex items-start gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="mb-1 flex flex-wrap items-center gap-2">
                        <CommentDecisionBadge value={c.decision} />
                        {c.comment_deadline && (
                          <span className="text-muted-foreground text-xs">
                            {t("comments.deadline")}: {c.comment_deadline}
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium">{c.regulation || t("unnamed")}</p>
                      <p className="text-muted-foreground text-xs">
                        {c.regulator || "—"}
                        {c.summary ? ` · ${c.summary}` : ""}
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {DECISION_ACTIONS.map((d) => (
                      <Button
                        key={d}
                        variant={c.decision === d ? "default" : "outline"}
                        size="sm"
                        onClick={() => decide(c, d)}
                      >
                        {t(`badges.decision.${d}`)}
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
