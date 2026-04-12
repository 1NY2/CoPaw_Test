/**
 * Brand story: Why CoPaw? Name explanation in a quiet, emotional corner.
 */
import { motion } from "motion/react";
import { t, type Lang } from "../i18n";

interface BrandStoryProps {
  lang: Lang;
  delay?: number;
}

export function BrandStory({ lang, delay = 0 }: BrandStoryProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      style={{
        margin: "0 auto",
        maxWidth: "var(--container)",
        padding: "var(--space-6) var(--space-4)",
        textAlign: "center",
      }}
    >
      <div
        style={{
          maxWidth: "28rem",
          margin: "0 auto",
          padding: "var(--space-4)",
          borderTop: "1px solid var(--border)",
        }}
      >
        <h2
          style={{
            margin: "0 0 var(--space-3)",
            fontSize: "1rem",
            fontWeight: 600,
            color: "var(--text-muted)",
            letterSpacing: "0.02em",
          }}
        >
          {t(lang, "brandstory.title")}
        </h2>
        <p
          style={{
            margin: "0 0 var(--space-2)",
            fontSize: "0.9375rem",
            color: "var(--text)",
            lineHeight: 1.7,
          }}
        >
          {t(lang, "brandstory.para1")}
        </p>
        <p
          style={{
            margin: 0,
            fontSize: "0.9375rem",
            color: "var(--text-muted)",
            lineHeight: 1.7,
          }}
        >
          {t(lang, "brandstory.para2")}
        </p>
      </div>
    </motion.section>
  );
}
