"use client";

export default function ApiDocsPage() {
  return (
    <div className="h-screen w-full">
      <iframe
        src="https://api.pierrestack.com/docs"
        className="h-full w-full border-0"
        title="API Documentation"
      />
    </div>
  );
}
