import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card"
import { ExternalLink } from "lucide-react"

export default function SourcesPopover() {
  const sources = Array.isArray(props.sources) ? props.sources.slice(0, 10) : []
  if (!sources.length) return null

  const first = sources[0]
  const remaining = sources.slice(1)

  return (
    <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
      <span className="font-medium text-foreground">Fonte:</span>
      <a
        href={first.url}
        target="_blank"
        rel="noreferrer"
        className="inline-flex max-w-[28rem] items-center gap-1 truncate text-sky-400 hover:underline"
      >
        {first.title || first.url}
        <ExternalLink className="h-3.5 w-3.5 shrink-0" />
      </a>

      {remaining.length > 0 && (
        <HoverCard openDelay={120} closeDelay={180}>
          <HoverCardTrigger asChild>
            <button className="rounded-full border border-border bg-muted px-2.5 py-1 font-semibold text-sky-400 hover:bg-accent">
              +{remaining.length}
            </button>
          </HoverCardTrigger>
          <HoverCardContent className="w-96 p-3" align="start">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Outras fontes consultadas
            </p>
            <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
              {remaining.map((source, index) => (
                <a
                  key={`${source.url}-${index}`}
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-start gap-2 rounded-md p-2 text-sm text-sky-400 hover:bg-accent hover:underline"
                >
                  <span className="min-w-0 break-words">{source.title || source.url}</span>
                  <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                </a>
              ))}
            </div>
          </HoverCardContent>
        </HoverCard>
      )}
    </div>
  )
}
