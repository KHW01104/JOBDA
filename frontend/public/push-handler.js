self.addEventListener("push", (event) => {
  const payload = event.data ? event.data.json() : { title: "JOBDA", body: "새 알림이 있습니다." };
  event.waitUntil(self.registration.showNotification(payload.title, { body: payload.body, data: payload }));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data.job_id ? `/jobs/${event.notification.data.job_id}` : "/"));
});
