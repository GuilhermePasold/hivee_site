"use client";

import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { useState, type ReactNode } from "react";

export const Card = ({
  className,
  children,
}: {
  className?: string;
  children?: ReactNode;
}) => {
  return (
    <div
      className={cn(
        "glass-solid h-[420px] w-[340px] overflow-hidden rounded-3xl",
        className,
      )}
    >
      {children}
    </div>
  );
};

interface StackedCardsInteractionProps {
  cards: ReactNode[];
  spreadDistance?: number;
  rotationAngle?: number;
  animationDelay?: number;
}

export const StackedCardsInteraction = ({
  cards,
  spreadDistance = 48,
  rotationAngle = 6,
  animationDelay = 0.08,
}: StackedCardsInteractionProps) => {
  const [isHovering, setIsHovering] = useState(false);
  const limited = cards.slice(0, 3);

  return (
    <div className="relative flex h-full w-full items-center justify-center">
      <div className="relative h-[420px] w-[340px]">
        {limited.map((card, index) => {
          const isFirst = index === 0;
          let xOffset = 0;
          let rotation = 0;
          if (limited.length > 1) {
            if (index === 1) {
              xOffset = -spreadDistance;
              rotation = -rotationAngle;
            } else if (index === 2) {
              xOffset = spreadDistance;
              rotation = rotationAngle;
            }
          }
          return (
            <motion.div
              key={index}
              className={cn("absolute", isFirst ? "z-10" : "z-0")}
              initial={{ x: 0, rotate: 0 }}
              animate={{
                x: isHovering ? xOffset : 0,
                rotate: isHovering ? rotation : 0,
                zIndex: isFirst ? 10 : 0,
              }}
              transition={{
                duration: 0.4,
                ease: [0.16, 1, 0.3, 1],
                delay: index * animationDelay,
                type: "spring",
                stiffness: 200,
                damping: 22,
              }}
              {...(isFirst && {
                onHoverStart: () => setIsHovering(true),
                onHoverEnd: () => setIsHovering(false),
              })}
            >
              <Card className={isFirst ? "cursor-pointer" : ""}>{card}</Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
