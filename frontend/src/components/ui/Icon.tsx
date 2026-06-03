import {
  Hammer, Lightning, Wrench, PaintRoller, Broom, Plant, Scissors,
  GraduationCap, Laptop, Camera, Confetti, PawPrint, Truck, Heartbeat,
  Fan, Briefcase, type Icon as PhosphorIcon,
} from "@phosphor-icons/react";

// Premium duotone icon set, one consistent family for the categories.
const MAP: Record<string, PhosphorIcon> = {
  Hammer,
  Zap: Lightning,
  Wrench,
  PaintRoller,
  Sparkles: Broom,
  Sprout: Plant,
  Scissors,
  GraduationCap,
  Laptop,
  Camera,
  PartyPopper: Confetti,
  PawPrint,
  Truck,
  HeartPulse: Heartbeat,
  AirVent: Fan,
};

export default function Icon({
  name,
  className,
  weight = "duotone",
}: {
  name: string;
  className?: string;
  weight?: "duotone" | "regular" | "bold" | "fill";
}) {
  const Cmp = MAP[name] ?? Briefcase;
  return <Cmp className={className} weight={weight} aria-hidden="true" />;
}
