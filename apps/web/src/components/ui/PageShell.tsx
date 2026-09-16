import { cn } from "@/lib/utils";

export function PageShell({
  children,
  className = "",
  width = "default",
}: {
  children: React.ReactNode;
  className?: string;
  width?: "default" | "full";
}) {
  return (
    <div
      className={cn(
        "mx-auto w-full px-4 py-5 sm:px-6 lg:px-8 lg:py-7",
        width === "full" ? "max-w-none" : "max-w-[92rem]",
        className,
      )}
    >
      {children}
    </div>
  );
}
