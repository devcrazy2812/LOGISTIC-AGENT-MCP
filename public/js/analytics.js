/**
 * LogiSwarm AI - Privacy-Preserving Client-Side Telemetry & Analytics
 * Zero PII • Zero Third-Party Trackers • Respects Do-Not-Track (DNT)
 */
(function() {
  const isDntEnabled = navigator.doNotTrack === '1' || window.doNotTrack === '1';

  const Analytics = {
    sessionId: 'sess_' + Math.random().toString(36).substring(2, 9),
    startTime: Date.now(),

    track: function(eventName, properties = {}) {
      if (isDntEnabled) return;

      const payload = {
        event: eventName,
        sessionId: this.sessionId,
        url: window.location.pathname,
        referrer: document.referrer || null,
        durationSeconds: Math.round((Date.now() - this.startTime) / 1000),
        properties: properties,
        timestamp: new Date().toISOString()
      };

      try {
        if (navigator.sendBeacon) {
          navigator.sendBeacon('/api/analytics', JSON.stringify(payload));
        } else {
          fetch('/api/analytics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            keepalive: true
          }).catch(() => {});
        }
      } catch (e) {
        // Silently ignore to guarantee zero disruption to main thread
      }
    },

    init: function() {
      if (isDntEnabled) return;
      this.track('pageview', { title: document.title });

      // Track clicks on primary buttons
      document.addEventListener('click', (e) => {
        const target = e.target.closest('button, a');
        if (!target) return;

        const action = target.getAttribute('id') || target.getAttribute('data-action') || target.innerText.trim();
        if (action) {
          this.track('interaction_click', { element: action.substring(0, 50) });
        }
      }, { passive: true });
    }
  };

  window.LogiAnalytics = Analytics;
  document.addEventListener('DOMContentLoaded', () => Analytics.init());
})();
