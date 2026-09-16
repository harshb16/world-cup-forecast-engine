import { GroupsDashboard } from "@/components/groups/GroupsDashboard";
import { PageHeader } from "@/components/PageHeader";

export default function GroupsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Groups"
        title="Group races"
        description="See who is favored, who is fighting for second, and which groups are most likely to get messy."
      />
      <GroupsDashboard />
    </>
  );
}
