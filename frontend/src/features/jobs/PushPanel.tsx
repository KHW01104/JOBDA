import { useEffect, useState } from "react";

import { createPushSubscription, deletePushSubscription, getNotificationEvents, getPushSubscriptions, NotificationEvent, PushSubscription } from "../../api/client";

function toUint8Array(value: string) {
  const padding = "=".repeat((4 - value.length % 4) % 4);
  const binary = atob((value + padding).replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

function PushPanel() {
  const [subscriptions, setSubscriptions] = useState<PushSubscription[]>([]);
  const [events, setEvents] = useState<NotificationEvent[]>([]);
  const [message, setMessage] = useState("");
  const publicKey = import.meta.env.VITE_VAPID_PUBLIC_KEY as string | undefined;

  async function refresh() {
    const [nextSubscriptions, nextEvents] = await Promise.all([getPushSubscriptions(), getNotificationEvents()]);
    setSubscriptions(nextSubscriptions); setEvents(nextEvents);
  }

  useEffect(() => { refresh().catch(() => setMessage("알림 정보를 불러오지 못했습니다.")); }, []);

  async function subscribe() {
    if (!publicKey || !("serviceWorker" in navigator) || !("PushManager" in window)) return;
    const permission = await Notification.requestPermission();
    if (permission !== "granted") { setMessage("알림 권한이 필요합니다."); return; }
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: toUint8Array(publicKey) });
    const json = subscription.toJSON();
    await createPushSubscription({ endpoint: json.endpoint!, p256dh: json.keys!.p256dh!, auth: json.keys!.auth!, user_agent: navigator.userAgent });
    setMessage("Push 알림을 활성화했습니다."); await refresh();
  }

  return <section className="personalization-panel"><div className="panel-heading"><span className="section-kicker">ALERTS</span><h2>알림</h2></div>
    {!publicKey ? <p className="hint">VAPID 공개 키 설정 후 Push 알림을 활성화할 수 있습니다.</p> : <button onClick={() => subscribe().catch(() => setMessage("Push 알림을 활성화하지 못했습니다."))}>Push 알림 활성화</button>}
    {message && <p className="hint">{message}</p>}
    <ul>{subscriptions.map((item) => <li key={item.id}>등록된 기기<button className="icon-button" onClick={() => deletePushSubscription(item.id).then(refresh)}>해제</button></li>)}</ul>
    <ul>{events.map((event) => <li key={event.id}><strong>{event.title}</strong><span>{event.body}</span></li>)}</ul>
  </section>;
}

export default PushPanel;
