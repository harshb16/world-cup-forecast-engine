export function PageShell({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`mx-auto w-full max-w-[92rem] px-4 py-5 sm:px-6 lg:px-8 lg:py-7 ${className}`}
    >
      {children}
    </div>
  );
}
