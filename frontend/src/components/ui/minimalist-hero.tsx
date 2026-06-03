import React from "react";
import { motion } from "framer-motion";
import { type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface MinimalistHeroProps {
  logo: React.ReactNode;
  navLinks: { label: string; href: string }[];
  mainText: string;
  ctaLabel: string;
  onCta: () => void;
  imageSrc: string;
  imageAlt: string;
  overlayText: { part1: string; part2: string };
  socialLinks: { icon: LucideIcon; href: string }[];
  locationText: string;
  phoneContent?: React.ReactNode;
  className?: string;
}

const NavLink = ({ href, children }: { href: string; children: React.ReactNode }) => (
  <a
    href={href}
    className="text-sm font-medium tracking-widest text-foreground/60 transition-colors hover:text-foreground"
  >
    {children}
  </a>
);

const SocialIcon = ({ href, icon: Icon }: { href: string; icon: LucideIcon }) => (
  <a href={href} target="_blank" rel="noopener noreferrer" className="text-foreground/60 transition-colors hover:text-foreground">
    <Icon className="h-5 w-5" />
  </a>
);

export const MinimalistHero = ({
  logo,
  navLinks,
  mainText,
  ctaLabel,
  onCta,
  imageSrc,
  imageAlt,
  overlayText,
  socialLinks,
  locationText,
  phoneContent,
  className,
}: MinimalistHeroProps) => {
  return (
    <div
      className={cn(
        "relative flex w-full flex-col items-center gap-8 overflow-hidden px-8 py-14 font-sans md:px-12",
        className,
      )}
    >
      <div className="relative grid w-full max-w-7xl grid-cols-1 items-center gap-8 md:grid-cols-3">
        {/* Left text */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="z-20 order-2 text-center md:order-1 md:text-left"
        >
          <p className="mx-auto max-w-xs text-base leading-relaxed text-foreground/80 md:mx-0">
            {mainText}
          </p>
          <button
            onClick={onCta}
            className="btn-gold mt-6 px-6 py-3 text-base"
          >
            {ctaLabel}
          </button>
        </motion.div>

        {/* Center: app product shot in a phone frame that opens in 3D + floats */}
        <div
          className="relative order-1 flex h-full items-center justify-center py-8 md:order-2"
          style={{ perspective: "1200px" }}
        >
          <div
            className="pointer-events-none absolute z-0 h-[340px] w-[340px] rounded-full md:h-[460px] md:w-[460px]"
            style={{ background: "radial-gradient(circle, rgba(234,179,8,0.30), transparent 70%)" }}
            aria-hidden="true"
          />
          <div className="animate-float relative z-10">
            <motion.div
              initial={{ opacity: 0, rotateY: -40, y: 60, scale: 0.9 }}
              whileInView={{ opacity: 1, rotateY: 0, y: 0, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1], delay: 0.15 }}
              style={{ transformStyle: "preserve-3d", transformPerspective: 1200 }}
              className="relative w-[290px] overflow-hidden rounded-[2.6rem] border-[6px] border-[#1b1b1f] bg-[#0c0a06] shadow-[0_50px_120px_-30px_rgba(0,0,0,0.95)] md:w-[320px]"
            >
              <div className="pointer-events-none absolute left-1/2 top-2 z-30 h-5 w-20 -translate-x-1/2 rounded-full bg-black" aria-hidden="true" />
              {phoneContent ? (
                <div className="h-[570px] overflow-hidden">{phoneContent}</div>
              ) : (
                <img
                  src={imageSrc}
                  alt={imageAlt}
                  className="w-full object-cover"
                  onError={(e) => {
                    const t = e.target as HTMLImageElement;
                    t.onerror = null;
                    t.src = "https://placehold.co/390x844/0c0a06/eab308?text=HIVEE";
                  }}
                />
              )}
            </motion.div>
          </div>
        </div>

        {/* Right big text */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="z-20 order-3 flex items-center justify-center text-center md:justify-start"
        >
          <h1 className="text-6xl font-extrabold tracking-tighter text-foreground md:text-7xl lg:text-8xl">
            {overlayText.part1}
            <br />
            <span className="text-gold">{overlayText.part2}</span>
          </h1>
        </motion.div>
      </div>
    </div>
  );
};
