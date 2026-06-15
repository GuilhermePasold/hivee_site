import { useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import NotificationToaster from "@/components/NotificationToast";
import { ChatProvider } from "@/context/ChatContext";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
  }, [pathname]);
  return null;
}

export default function Layout() {
  return (
    <ChatProvider>
      {/* SVG refraction filter for real liquid glass (ref: suraj-xd/liquid-glass + Apple)
          Tuned for a subtle organic ripple — scale=18 keeps it refined on cards.
          Shadows come from CSS box-shadow, not from the SVG filter, so the
          element keeps its native border-radius and paint cycle. */}
      <svg aria-hidden="true" style={{ position: "absolute", width: 0, height: 0 }}>
        <filter id="glass-distortion" x="-10%" y="-10%" width="120%" height="120%" filterUnits="objectBoundingBox">
          <feTurbulence type="fractalNoise" baseFrequency="0.01 0.015" numOctaves="3" seed="42" result="noise" />
          {/* Halve noise alpha for a subtle, non-aggressive ripple */}
          <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.5 0" in="noise" result="softNoise" />
          <feDisplacementMap in="SourceGraphic" in2="softNoise" scale="18" xChannelSelector="R" yChannelSelector="G" />
        </filter>
      </svg>
      <div className="bg-mesh" aria-hidden="true" />
      <ScrollToTop />
      <Navbar />
      <main>
        <Outlet />
      </main>
      <Footer />
      <NotificationToaster />
    </ChatProvider>
  );
}
