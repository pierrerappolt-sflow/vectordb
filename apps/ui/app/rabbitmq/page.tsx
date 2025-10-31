"use client";

export default function RabbitMQPage() {
  return (
    <div className="h-screen w-full">
      <iframe
        src="/api/rabbitmq"
        className="h-full w-full border-0"
        title="RabbitMQ Management UI"
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-top-navigation"
      />
    </div>
  );
}
