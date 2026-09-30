import { useMutation } from "@tanstack/react-query";
import { Send, Sparkles } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import type { ChatResponse } from "@/types/api";

const EXAMPLE_QUESTIONS = [
  "What did I spend the most on this month?",
  "Explain my cash flow.",
  "What is an emergency fund?",
  "Why was a transaction flagged as unusual?",
];

export function AIChatPanel() {
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<{ question: string; response: ChatResponse }[]>([]);

  const chat = useMutation({
    mutationFn: (q: string) => api.chat(q),
    onSuccess: (response, q) => setHistory((prev) => [...prev, { question: q, response }]),
  });

  function ask(q: string) {
    if (!q.trim() || chat.isPending) return;
    chat.mutate(q);
    setQuestion("");
  }

  return (
    <div className="space-y-4 rounded-xl border border-ai-subtle bg-ai-subtle/20 p-4">
      <div className="flex items-center gap-2">
        <Sparkles className="size-4 text-ai" />
        <h4 className="text-sm font-semibold">Ask FinPilot</h4>
      </div>
      <p className="text-xs text-muted-foreground">
        Grounded in your own data, real model predictions, and a curated financial-knowledge base — not a
        general-purpose chatbot. Numbers always come from your data or the trained models, never invented.
      </p>

      {history.length === 0 && (
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => ask(q)}
              className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground hover:bg-muted"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      <div className="space-y-3">
        {history.map((turn, i) => (
          <div key={i} className="space-y-1.5">
            <p className="text-sm font-medium">{turn.question}</p>
            <div className="whitespace-pre-line rounded-lg bg-background p-3 text-sm text-foreground">
              {turn.response.answer}
            </div>
            {turn.response.sources.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {turn.response.sources.map((s) => (
                  <Badge key={s.index} variant="outline">
                    [{s.index}] {s.title}
                  </Badge>
                ))}
              </div>
            )}
            <p className="text-xs text-muted-foreground">Provider: {turn.response.provider}</p>
          </div>
        ))}
        {chat.isError && (
          <p className="text-sm text-danger">
            {chat.error instanceof ApiError ? chat.error.message : "Something went wrong."}
          </p>
        )}
      </div>

      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          ask(question);
        }}
      >
        <Input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about your spending, predictions, or a financial concept..."
        />
        <Button type="submit" isLoading={chat.isPending}>
          <Send />
        </Button>
      </form>
    </div>
  );
}
