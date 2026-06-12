export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-6 text-sm text-zinc-600">
      <div className="h-2 w-28 rounded-full bg-zinc-200" />
      <p className="mt-4">{label}</p>
    </div>
  );
}
