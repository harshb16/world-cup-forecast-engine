import { AlertTriangle } from "lucide-react";

export function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-rose-300/20 bg-rose-300/10 p-4 text-rose-100">
      <div className="flex gap-3">
        <AlertTriangle
          size={18}
          aria-hidden="true"
          className="mt-0.5 shrink-0"
        />
        <div>
          <p className="font-semibold">Unable to load this view</p>
          <p className="mt-1 text-sm leading-6 text-rose-100/80">{message}</p>
        </div>
      </div>
    </div>
  );
}
