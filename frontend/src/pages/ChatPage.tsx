import { Navigate, useLocation } from "react-router-dom";

import { ChatWidget } from "@/components/ChatWidget";
import { useAuth } from "@/context/AuthContext";

export default function ChatPage() {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="min-h-screen bg-black pt-20" />;
  }

  if (!user) {
    return <Navigate to="/entrar" replace state={{ from: location.pathname + location.search }} />;
  }

  const telefone = `site_user_${user.id}`;

  return (
    <div className="min-h-screen bg-black pt-20">
      <ChatWidget telefone={telefone} />
    </div>
  );
}
