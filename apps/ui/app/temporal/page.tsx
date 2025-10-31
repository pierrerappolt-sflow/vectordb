"use client";

export default function TemporalPage() {
  return (
    <div className="h-screen w-full">
      <iframe
        src="/api/temporal"
        className="h-full w-full border-0"
        title="Temporal UI"
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-top-navigation"
      />
    </div>
  );
}
