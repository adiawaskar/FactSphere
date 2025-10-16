// In frontend/src/components/chat/DetailedAnalysis.tsx

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Badge } from "@/components/ui/badge";
import { BookCopy } from "lucide-react";

// This matches the type from the AskAI page
interface ApiAnalysisResult {
  source_url: string;
  final_score: number;
  judgment: string;
  detailed_analysis: Array<{
    category_name: string;
    score: number;
    justification: string;
  }>;
}

// Helper to determine badge color based on judgment
const getJudgmentVariant = (judgment: string): "default" | "secondary" | "destructive" | "outline" => {
  if (judgment.includes("Left")) return "secondary";
  if (judgment.includes("Right")) return "destructive";
  return "default";
};

export function DetailedAnalysis({ analyses }: { analyses: ApiAnalysisResult[] }) {
  if (!analyses || analyses.length === 0) {
    return null;
  }

  return (
    <div className="mt-4">
        <h4 className="text-xs sm:text-sm font-semibold flex items-center gap-2 mb-2">
            <BookCopy className="h-3 w-3 sm:h-4 sm:w-4 text-primary" />
            <span>Detailed Article Analysis</span>
        </h4>
        <Accordion type="single" collapsible className="w-full">
            {analyses.map((analysis, index) => (
                <AccordionItem value={`item-${index}`} key={index} className="border border-border/50 rounded-lg px-4 mb-2 bg-background/50">
                    <AccordionTrigger className="text-xs sm:text-sm text-left hover:no-underline">
                        <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                            <Badge variant={getJudgmentVariant(analysis.judgment)}>{analysis.judgment}</Badge>
                            <span className="truncate text-muted-foreground">{new URL(analysis.source_url).hostname}</span>
                        </div>
                    </AccordionTrigger>
                    <AccordionContent>
                        <table className="w-full text-xs">
                            <thead className="border-b border-border/50">
                                <tr className="text-left">
                                    <th className="py-2 pr-2 font-semibold">Category</th>
                                    <th className="py-2 px-2 font-semibold text-center">Score</th>
                                    <th className="py-2 pl-2 font-semibold">Justification</th>
                                </tr>
                            </thead>
                            <tbody>
                                {analysis.detailed_analysis.map((detail, detailIndex) => (
                                    <tr key={detailIndex} className="border-b border-border/20 last:border-b-0">
                                        <td className="py-2 pr-2 text-muted-foreground">{detail.category_name}</td>
                                        <td className={`py-2 px-2 font-bold text-center ${detail.score < 0 ? 'text-blue-400' : detail.score > 0 ? 'text-red-400' : ''}`}>
                                            {detail.score > 0 ? `+${detail.score}` : detail.score}
                                        </td>
                                        <td className="py-2 pl-2 italic text-muted-foreground">{detail.justification}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </AccordionContent>
                </AccordionItem>
            ))}
        </Accordion>
    </div>
  )
}