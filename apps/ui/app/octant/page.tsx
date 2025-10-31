"use client";

export default function OctantPage() {
  // Use the Next.js proxy route instead of direct connection
  return (
    <div className="h-screen w-full">
      <iframe
        src="/octant/"
        className="h-full w-full border-0"
        title="Octant - Kubernetes Dashboard"
      />
    </div>
  );
}
