import { MyAssistant } from "@/components/MyAssistant";

export default function Home() {
  return (
    <main className="min-h-dvh bg-[linear-gradient(135deg,#f8fafc_0%,#eef7f6_42%,#fff7ed_100%)] p-3 md:p-4">
      <div className="mx-auto w-full max-w-7xl">
        <MyAssistant />
      </div>
    </main>
  );
}
