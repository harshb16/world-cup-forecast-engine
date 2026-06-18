export function SectionCard({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`relative overflow-hidden rounded-lg border border-white/10 bg-[#101722]/85 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.24)] ${className}`}
    >
      <div className="absolute inset-y-0 left-0 w-1 bg-[var(--turf)]" aria-hidden="true" />
      {children}
    </section>
  );
}
