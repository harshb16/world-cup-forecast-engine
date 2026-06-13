import { ErrorPanel } from "@/components/ui/ErrorPanel";

export function ErrorState({ message }: { message: string }) {
  return <ErrorPanel message={message} />;
}
