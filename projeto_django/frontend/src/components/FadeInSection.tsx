import React from 'react';

interface FadeInSectionProps {
  children: React.ReactNode;
  delay?: number;
}

export function FadeInSection({ children }: FadeInSectionProps) {
  return <div>{children}</div>;
}