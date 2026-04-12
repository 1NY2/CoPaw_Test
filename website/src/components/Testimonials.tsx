import { useRef, useEffect, useState } from "react";
import { motion } from "motion/react";
import { ChevronRight } from "lucide-react";
import { t, type Lang } from "../i18n";
import {
  MOCK_TESTIMONIALS,
  REAL_TESTIMONIALS,
  type TestimonialItem,
} from "../data/testimonials";

const isDev = import.meta.env.DEV;

const CARD_GAP = 24;
const CARD_MIN_WIDTH = 280;
/** Pixels to move per frame for continuous scroll. */
const SCROLL_SPEED = 0.6;

interface TestimonialsProps {
  lang: Lang;
  delay?: number;
}

function TestimonialCard({
  item,
  lang,
  style,
}: {
  item: TestimonialItem;
  lang: Lang;
  style?: React.CSSProperties;
}) {
  const quote = lang === "zh" ? item.quoteZh : item.quoteEn;
  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        flexShrink: 0,
        width: "100%",
        minWidth: CARD_MIN_WIDTH,
        maxWidth: 360,
        display: "flex",
        gap: "var(--space-3)",
        padding: "var(--space-4)",
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "0.5rem",
        textAlign: "left",
        color: "inherit",
        textDecoration: "none",
        ...style,
      }}
    >
      <img
        src={item.avatar}
        alt=""
        width={48}
        height={48}
        style={{
          borderRadius: "50%",
          objectFit: "cover",
          flexShrink: 0,
        }}
      />
      <div style={{ minWidth: 0, flex: 1 }}>
        <p
          style={{
            margin: 0,
            fontSize: "0.9375rem",
            lineHeight: 1.6,
            color: "var(--text-muted)",
          }}
        >
          {quote}
        </p>
        <span
          style={{
            display: "inline-block",
            marginTop: "var(--space-2)",
            fontSize: "0.8125rem",
            fontWeight: 600,
            color: "var(--text)",
          }}
        >
          {item.username}
        </span>
      </div>
    </a>
  );
}

export function Testimonials({ lang, delay = 0 }: TestimonialsProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const offsetRef = useRef(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    let raf = 0;
    const tick = () => {
      raf = requestAnimationFrame(tick);
      if (paused) return;
      const el = trackRef.current;
      if (!el) return;
      const totalWidth = el.scrollWidth;
      const halfWidth = totalWidth / 2;
      offsetRef.current -= SCROLL_SPEED;
      if (offsetRef.current <= -halfWidth) {
        offsetRef.current += halfWidth;
      }
      el.style.transform = `translate3d(${offsetRef.current}px, 0, 0)`;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [paused]);

  const baseItems = isDev
    ? [...MOCK_TESTIMONIALS, ...REAL_TESTIMONIALS]
    : [...REAL_TESTIMONIALS];
  if (baseItems.length === 0) return null;

  const items = [...baseItems, ...baseItems];

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      style={{
        margin: "0 auto",
        maxWidth: "100%",
        padding: "var(--space-6) var(--space-4)",
      }}
    >
      <div
        style={{
          maxWidth: "var(--container)",
          margin: "0 auto",
          padding: "0 var(--space-4)",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            marginBottom: "var(--space-5)",
            textAlign: "center",
          }}
        >
          <h2
            style={{
              margin: "0 0 var(--space-1)",
              fontSize: "1.375rem",
              fontWeight: 600,
              color: "var(--text)",
            }}
          >
            {t(lang, "testimonials.title")}
          </h2>
          <span
            style={{
              fontSize: "0.9375rem",
              color: "var(--text-muted)",
            }}
          >
            {t(lang, "testimonials.viewAll")}
            <ChevronRight size={16} style={{ verticalAlign: "middle" }} />
          </span>
        </div>

        <div
          onMouseEnter={() => setPaused(true)}
          onMouseLeave={() => setPaused(false)}
          style={{
            overflow: "hidden",
            paddingBottom: "var(--space-2)",
            marginLeft: "calc(-1 * var(--space-4))",
            marginRight: "calc(-1 * var(--space-4))",
            paddingLeft: "var(--space-4)",
            paddingRight: "var(--space-4)",
          }}
          className="testimonials-carousel"
        >
          <div
            ref={trackRef}
            style={{
              display: "flex",
              gap: CARD_GAP,
              width: "max-content",
              willChange: "transform",
            }}
          >
            {items.map((item, i) => (
              <div key={`${item.username}-${i}`}>
                <TestimonialCard item={item} lang={lang} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.section>
  );
}
