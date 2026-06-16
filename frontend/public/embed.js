/*
 * RAG Chatbot embeddable widget.
 *
 * Usage on any website:
 *   <script src="https://your-widget-host/embed.js" data-base-url="https://your-widget-host" defer></script>
 *
 * Injects a floating bubble that opens the chat-only /widget view in an iframe.
 * The host site does not need to run Next.js.
 */
(function () {
  "use strict";

  var current = document.currentScript;
  var baseUrl = (current && current.getAttribute("data-base-url")) || deriveBaseUrl(current);
  var primary = (current && current.getAttribute("data-color")) || "#2563eb";

  if (document.getElementById("rag-chatbot-launcher")) return;

  var iframe = document.createElement("iframe");
  iframe.src = baseUrl.replace(/\/$/, "") + "/widget";
  iframe.title = "Chat assistant";
  iframe.setAttribute("aria-hidden", "true");
  setStyle(iframe, {
    position: "fixed",
    bottom: "96px",
    right: "24px",
    width: "390px",
    height: "600px",
    maxHeight: "calc(100vh - 130px)",
    maxWidth: "calc(100vw - 32px)",
    border: "none",
    borderRadius: "16px",
    boxShadow: "0 12px 40px rgba(0,0,0,0.18)",
    background: "#fff",
    zIndex: "2147483000",
    display: "none",
    opacity: "0",
    transition: "opacity 0.18s ease",
  });

  var button = document.createElement("button");
  button.id = "rag-chatbot-launcher";
  button.type = "button";
  button.setAttribute("aria-label", "Open chat assistant");
  button.innerHTML = chatIcon();
  setStyle(button, {
    position: "fixed",
    bottom: "24px",
    right: "24px",
    width: "56px",
    height: "56px",
    borderRadius: "9999px",
    border: "none",
    cursor: "pointer",
    background: primary,
    color: "#fff",
    boxShadow: "0 8px 24px rgba(0,0,0,0.22)",
    zIndex: "2147483001",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  });

  var open = false;
  button.addEventListener("click", function () {
    open = !open;
    if (open) {
      iframe.style.display = "block";
      iframe.setAttribute("aria-hidden", "false");
      requestAnimationFrame(function () {
        iframe.style.opacity = "1";
      });
      button.innerHTML = closeIcon();
    } else {
      iframe.style.opacity = "0";
      iframe.setAttribute("aria-hidden", "true");
      button.innerHTML = chatIcon();
      setTimeout(function () {
        if (!open) iframe.style.display = "none";
      }, 180);
    }
  });

  document.body.appendChild(iframe);
  document.body.appendChild(button);

  function deriveBaseUrl(script) {
    if (!script || !script.src) return "";
    try {
      var url = new URL(script.src);
      return url.origin;
    } catch (e) {
      return "";
    }
  }

  function setStyle(el, styles) {
    for (var key in styles) {
      if (Object.prototype.hasOwnProperty.call(styles, key)) {
        el.style[key] = styles[key];
      }
    }
  }

  function chatIcon() {
    return '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-8.5 8.5 8.5 8.5 0 0 1-3.6-.8L3 21l1.9-5.7A8.38 8.38 0 0 1 4 11.5 8.5 8.5 0 0 1 12.5 3 8.38 8.38 0 0 1 21 11.5z"/></svg>';
  }

  function closeIcon() {
    return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  }
})();
