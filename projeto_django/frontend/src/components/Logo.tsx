import React from 'react';
import { Link } from 'react-router-dom';

export function Logo() {
  return (
    <Link to="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
      <h1 className="text-secondary text-2xl font-bold">HIVEE</h1>
    </Link>
  );
}