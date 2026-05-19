type StepEvent = {
  event_time?: string;
  event_type?: string;
  event_note?: string;
  time?: string;
  title?: string;
  description?: string;
};

export function ProgressStepper({ events }: { events: StepEvent[] }) {
  if (!events || events.length === 0) return null;

  return (
    <div className="relative ml-2 mt-3 space-y-0 border-l-2 border-slate-200 pl-5">
      {events.map((evt, i) => {
        const time = evt.event_time || evt.time || "";
        const title = evt.event_type || evt.title || "";
        const desc = evt.event_note || evt.description || "";
        const isLast = i === events.length - 1;

        return (
          <div key={i} className={`relative pb-4 ${isLast ? "pb-0" : ""}`}>
            <span className="absolute -left-[25px] mt-1.5 flex h-3 w-3 items-center justify-center rounded-full border-2 border-cyan-500 bg-white" />
            <div className="text-xs text-slate-500">{time}</div>
            <div className="mt-0.5 text-sm font-medium text-slate-900">{title}</div>
            {desc ? <div className="mt-0.5 text-sm text-slate-600">{desc}</div> : null}
          </div>
        );
      })}
    </div>
  );
}
