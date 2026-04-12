import { t, type Lang } from "../i18n";

const AGENTSCOPE_ORG = "https://github.com/agentscope-ai";
const AGENTSCOPE_REPO = "https://github.com/agentscope-ai/agentscope";
const AGENTSCOPE_RUNTIME =
  "https://github.com/agentscope-ai/agentscope-runtime";
const REME_REPO = "https://github.com/agentscope-ai/ReMe";
const OPENCLAW_URL = "https://openclaw.ai/";
const ANTHROPIC_SKILLS_URL =
  "https://github.com/anthropics/skills?tab=readme-ov-file";

export function Footer({ lang }: { lang: Lang }) {
  return (
    <footer
      style={{
        marginTop: "auto",
        padding: "var(--space-4) var(--space-4)",
        borderTop: "1px solid var(--border)",
        textAlign: "center",
        fontSize: "0.875rem",
        color: "var(--text-muted)",
      }}
    >
      <div style={{ marginBottom: "var(--space-2)" }}>{t(lang, "footer")}</div>
      <div style={{ fontSize: "0.8125rem", opacity: 0.9 }}>
        {t(lang, "footer.poweredBy.p1")}
        <a
          href={AGENTSCOPE_ORG}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "inherit", textDecoration: "underline" }}
        >
          {t(lang, "footer.poweredBy.team")}
        </a>
        {t(lang, "footer.poweredBy.p2")}
        <a
          href={AGENTSCOPE_REPO}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "inherit", textDecoration: "underline" }}
        >
          {t(lang, "footer.poweredBy.agentscope")}
        </a>
        {t(lang, "footer.poweredBy.p3")}
        <a
          href={AGENTSCOPE_RUNTIME}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "inherit", textDecoration: "underline" }}
        >
          {t(lang, "footer.poweredBy.runtime")}
        </a>
        {t(lang, "footer.poweredBy.p3b")}
        <a
          href={REME_REPO}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "inherit", textDecoration: "underline" }}
        >
          {t(lang, "footer.poweredBy.reme")}
        </a>
        {t(lang, "footer.poweredBy.p4")}
      </div>
      <div
        style={{
          marginTop: "var(--space-3)",
          fontSize: "0.8125rem",
          opacity: 0.85,
        }}
      >
        {t(lang, "footer.inspiredBy")}
        <a
          href={OPENCLAW_URL}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "inherit", textDecoration: "underline" }}
        >
          {t(lang, "footer.inspiredBy.name")}
        </a>
        {" · "}
        {t(lang, "footer.thanksSkills")}
        <a
          href={ANTHROPIC_SKILLS_URL}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "inherit", textDecoration: "underline" }}
        >
          {t(lang, "footer.thanksSkills.name")}
        </a>
        {t(lang, "footer.thanksSkills.suffix")}
      </div>
    </footer>
  );
}
