"use client";

export default function DatabasePage() {
  return (
    <div className="h-screen w-full">
      <iframe
        src="/api/database"
        className="h-full w-full border-0"
        title="Database UI (Adminer)"
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-top-navigation"
      />
    </div>
  );
}
