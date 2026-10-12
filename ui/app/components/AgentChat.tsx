"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Bot,
  User,
  Sparkles,
  Terminal,
  ChevronDown,
  ChevronUp,
  Zap,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ArrowRight,
  Code2,
  FileText,
  Copy,
  Check,
  Cpu,
  Layers,
  Search,
  BookOpen,
  Eye,
  GitBranch
} from "lucide-react";

export interface AgentToolCall {
  tool: string;
  args?: Record<string, any>;
  resultSummary: string;
  durationMs: number;
  status: "success" | "warning" | "error";
  payload?: any;
}

export interface AgentSuggestedAction {
  label: string;
  prompt: string;
  style?: "primary" | "danger" | "emerald" | "default";
}

export interface CodeSnippetCard {
  file?: string;
  symbol?: string;
  language?: string;
  content?: string;
  totalLines?: number;
  displayedLines?: number;
}

export interface ReActStep {
  step: number;
  type: "thought" | "action" | "observation";
  title?: string;
  content?: string;
  tool?: string;
  args?: Record<string, any>;
  durationMs?: number;
  status?: string;
  summary?: string;
  toolCalls?: AgentToolCall[];
}

export interface ContextWindowStats {
  usedChars?: number;
  estimatedTokens?: number;
  maxBudgetTokens?: number;
  historyTurns?: number;
  ragChunksRetrieved?: number;
  reformulatedQuery?: string;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "agent";
  text: string;
  thought?: string;
  action?: string;
  toolCalls?: AgentToolCall[];
  suggestedActions?: AgentSuggestedAction[];
  timestamp: string;
  query?: string;
  reformulatedQuery?: string;
  contextWindow?: ContextWindowStats;
  reactSteps?: ReActStep[];
  codeCards?: CodeSnippetCard[];
}

interface AgentChatProps {
  messages: ChatMessage[];
  onSendMessage: (msg: string) => void;
  isLoading: boolean;
  isLiveActive?: boolean;
  datasetFileName?: string;
}

// Interactive Mermaid Diagram Renderer Component
const MermaidBlock: React.FC<{ chart: string; id: string }> = ({ chart, id }) => {
  const [svg, setSvg] = useState<string>("");
  const [showCode, setShowCode] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const renderChart = async () => {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "dark",
          securityLevel: "loose",
          fontFamily: "ui-monospace, monospace",
          themeVariables: {
            darkMode: true,
            background: "#080d1a",
            primaryColor: "#0284c7",
            primaryTextColor: "#f8fafc",
            primaryBorderColor: "#38bdf8",
            lineColor: "#38bdf8",
            secondaryColor: "#8b5cf6",
            tertiaryColor: "#1e293b",
          }
        });
        const cleanChart = chart.trim();
        const uniqueId = `mermaid-${id}-${Math.random().toString(36).substring(2, 7)}`;
        const { svg: renderedSvg } = await mermaid.render(uniqueId, cleanChart);
        if (isMounted) {
          setSvg(renderedSvg);
          setError(null);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || "Failed to render diagram");
        }
      }
    };
    renderChart();
    return () => { isMounted = false; };
  }, [chart, id]);

  const copyChart = () => {
    navigator.clipboard.writeText(chart);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ margin: "14px 0", borderRadius: "8px", background: "#0b1220", border: "1px solid rgba(56, 189, 248, 0.25)", overflow: "hidden", minWidth: 0, maxWidth: "100%" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 12px", background: "rgba(56, 189, 248, 0.08)", borderBottom: "1px solid rgba(255, 255, 255, 0.06)", fontSize: "11px", color: "#38bdf8" }}>
        <span style={{ display: "flex", alignItems: "center", gap: "6px", fontWeight: "600" }}>
          <GitBranch size={13} />
          <span>Interactive Flowchart / Architecture Diagram</span>
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <button onClick={() => setShowCode(!showCode)} style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: "10px", textDecoration: "underline" }}>
            {showCode ? "View Diagram" : "View Code"}
          </button>
          <button onClick={copyChart} style={{ background: "rgba(255, 255, 255, 0.06)", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "4px", padding: "2px 6px", color: copied ? "#10b981" : "#cbd5e1", fontSize: "10px", cursor: "pointer" }}>
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
      </div>
      {showCode || error ? (
        <pre style={{ margin: 0, padding: "12px 14px", fontFamily: "monospace", fontSize: "12px", color: "#cbd5e1", overflowX: "auto", maxWidth: "100%" }}>
          <code>{chart}</code>
        </pre>
      ) : svg ? (
        <div className="mermaid-svg-wrapper" style={{ padding: "14px 10px", display: "flex", justifyContent: "center", alignItems: "center", background: "#080d1a", overflowX: "auto", maxWidth: "100%" }} dangerouslySetInnerHTML={{ __html: svg }} />
      ) : (
        <div style={{ padding: "14px", textAlign: "center", color: "#94a3b8", fontSize: "11px" }}>Rendering diagram...</div>
      )}
    </div>
  );
};

// Markdown and Code Block Renderer Component
const FormattedMarkdown: React.FC<{ content: string }> = ({ content }) => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const copyToClipboard = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // Normalize markdown text: fix variable backtick `mermaid and ensure matching closing ```
  let normalized = (content || "")
    .replace(/`{1,6}mermaid[ \t]*\r?\n/gi, "```mermaid\n")
    .replace(/\n`{4,6}[ \t]*(?:\r?\n|$)/g, "\n```\n");
  if (normalized.includes("```mermaid") && (normalized.match(/```/g) || []).length % 2 !== 0) {
    normalized += "\n```";
  }

  // Split by code blocks ```lang ... ```
  const codeBlockRegex = /```([a-zA-Z0-9_\-\+]*)[ \t]*\r?\n([\s\S]*?)(?:```|$)/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;
  let blockIndex = 0;

  while ((match = codeBlockRegex.exec(normalized)) !== null) {
    if (match.index > lastIndex) {
      const textChunk = normalized.substring(lastIndex, match.index);
      parts.push(<TextSection key={`txt-${lastIndex}`} text={textChunk} />);
    }

    const lang = (match[1] || "text").toLowerCase();
    const code = match[2];
    const currentIndex = blockIndex;

    if (lang === "mermaid") {
      parts.push(
        <MermaidBlock key={`mm-${match.index}`} chart={code} id={`chart-${match.index}`} />
      );
    } else {
      parts.push(
        <div
          key={`code-${match.index}`}
          style={{
            margin: "12px 0",
            borderRadius: "8px",
            background: "#090d16",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            overflow: "hidden"
          }}
        >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "6px 12px",
            background: "rgba(255, 255, 255, 0.04)",
            borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
            fontSize: "11px",
            color: "#94a3b8"
          }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: "6px", fontFamily: "monospace" }}>
            <Code2 size={13} color="#38bdf8" />
            <span style={{ textTransform: "uppercase", fontWeight: "600" }}>{lang}</span>
          </span>
          <button
            onClick={() => copyToClipboard(code, currentIndex)}
            style={{
              background: "rgba(255, 255, 255, 0.06)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "4px",
              padding: "2px 8px",
              color: copiedIndex === currentIndex ? "#10b981" : "#cbd5e1",
              fontSize: "10px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "4px"
            }}
          >
            {copiedIndex === currentIndex ? <Check size={11} /> : <Copy size={11} />}
            <span>{copiedIndex === currentIndex ? "Copied!" : "Copy"}</span>
          </button>
        </div>
        <pre
          style={{
            padding: "12px 14px",
            margin: 0,
            overflowX: "auto",
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            fontSize: "12px",
            lineHeight: "1.5",
            color: "#e2e8f0"
          }}
        >
          <code>{code}</code>
        </pre>
      </div>
    );
    }

    lastIndex = match.index + match[0].length;
    blockIndex++;
  }

  if (lastIndex < content.length) {
    parts.push(<TextSection key={`txt-${lastIndex}`} text={content.substring(lastIndex)} />);
  }

  return <div style={{ lineHeight: "1.6" }}>{parts}</div>;
};

// Renders markdown text, headers, lists, tables, and links
const TextSection: React.FC<{ text: string }> = ({ text }) => {
  const lines = text.split("\n");
  const renderedElements: React.ReactNode[] = [];
  let inTable = false;
  let tableRows: string[][] = [];

  const flushTable = (key: string) => {
    if (tableRows.length === 0) return null;
    const headerRow = tableRows[0];
    const dataRows = tableRows.slice(1).filter(r => !r.every(c => c.match(/^[:\-\s]+$/)));

    const tableNode = (
      <div key={key} style={{ overflowX: "auto", margin: "10px 0" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "12px",
            border: "1px solid rgba(255, 255, 255, 0.1)"
          }}
        >
          <thead>
            <tr style={{ background: "rgba(255, 255, 255, 0.05)" }}>
              {headerRow.map((cell, idx) => (
                <th
                  key={idx}
                  style={{
                    padding: "6px 10px",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    textAlign: "left",
                    color: "var(--accent-cyan)",
                    fontWeight: "600"
                  }}
                >
                  {formatInlineText(cell.trim())}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dataRows.map((row, rIdx) => (
              <tr key={rIdx} style={{ background: rIdx % 2 === 0 ? "rgba(0,0,0,0.2)" : "transparent" }}>
                {row.map((cell, cIdx) => (
                  <td
                    key={cIdx}
                    style={{
                      padding: "6px 10px",
                      border: "1px solid rgba(255, 255, 255, 0.07)",
                      color: "#cbd5e1"
                    }}
                  >
                    {formatInlineText(cell.trim())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    tableRows = [];
    return tableNode;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Table line: | col1 | col2 |
    if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
      inTable = true;
      const cells = line.trim().slice(1, -1).split("|");
      tableRows.push(cells);
      continue;
    } else if (inTable) {
      inTable = false;
      const table = flushTable(`table-${i}`);
      if (table) renderedElements.push(table);
    }

    if (line.startsWith("### ")) {
      renderedElements.push(
        <h4 key={i} style={{ fontSize: "14px", fontWeight: "700", color: "#38bdf8", margin: "14px 0 6px 0" }}>
          {formatInlineText(line.replace("### ", ""))}
        </h4>
      );
    } else if (line.startsWith("## ")) {
      renderedElements.push(
        <h3 key={i} style={{ fontSize: "15px", fontWeight: "700", color: "#f8fafc", margin: "16px 0 8px 0" }}>
          {formatInlineText(line.replace("## ", ""))}
        </h3>
      );
    } else if (line.startsWith("# ")) {
      renderedElements.push(
        <h2 key={i} style={{ fontSize: "17px", fontWeight: "800", color: "#f8fafc", margin: "18px 0 10px 0" }}>
          {formatInlineText(line.replace("# ", ""))}
        </h2>
      );
    } else if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
      renderedElements.push(
        <li key={i} style={{ marginLeft: "18px", color: "#cbd5e1", fontSize: "13px", marginBottom: "4px" }}>
          {formatInlineText(line.trim().substring(2))}
        </li>
      );
    } else if (line.trim() === "---") {
      renderedElements.push(<hr key={i} style={{ border: "none", borderTop: "1px solid rgba(255, 255, 255, 0.1)", margin: "12px 0" }} />);
    } else if (line.trim().length > 0) {
      renderedElements.push(
        <p key={i} style={{ margin: "4px 0", color: "#cbd5e1", fontSize: "13px" }}>
          {formatInlineText(line)}
        </p>
      );
    }
  }

  if (inTable) {
    const table = flushTable(`table-end`);
    if (table) renderedElements.push(table);
  }

  return <>{renderedElements}</>;
};

// Inline parser for bold, code tags, and links
function formatInlineText(text: string): React.ReactNode {
  const elements: React.ReactNode[] = [];
  // Match links [text](url), code `code`, bold **text**
  const regex = /(\[.*?\]\(.*?\)|`.*?`|\*\*.*?\*\*)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      elements.push(text.substring(lastIndex, match.index));
    }

    const token = match[0];
    if (token.startsWith("[") && token.includes("](") && token.endsWith(")")) {
      const linkText = token.substring(1, token.indexOf("]("));
      const url = token.substring(token.indexOf("](") + 2, token.length - 1);
      elements.push(
        <a
          key={match.index}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "#38bdf8", textDecoration: "underline", fontWeight: "600" }}
        >
          {linkText}
        </a>
      );
    } else if (token.startsWith("`") && token.endsWith("`")) {
      elements.push(
        <code
          key={match.index}
          style={{
            background: "rgba(255, 255, 255, 0.08)",
            padding: "2px 5px",
            borderRadius: "4px",
            fontFamily: "monospace",
            fontSize: "12px",
            color: "#e0e7ff"
          }}
        >
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith("**") && token.endsWith("**")) {
      elements.push(
        <strong key={match.index} style={{ color: "#f8fafc", fontWeight: "700" }}>
          {token.slice(2, -2)}
        </strong>
      );
    }

    lastIndex = match.index + token.length;
  }

  if (lastIndex < text.length) {
    elements.push(text.substring(lastIndex));
  }

  return <>{elements}</>;
}

export const AgentChat: React.FC<AgentChatProps> = ({
  messages,
  onSendMessage,
  isLoading,
  isLiveActive = false,
  datasetFileName,
}) => {
  const [input, setInput] = useState("");
  const [expandedReActSteps, setExpandedReActSteps] = useState<Record<string, boolean>>({});
  const [expandedCodeCards, setExpandedCodeCards] = useState<Record<string, boolean>>({});
  const [copiedCodeId, setCopiedCodeId] = useState<string | null>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: "smooth"
      });
    }
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput("");
  };

  const handlePillClick = (prompt: string) => {
    if (isLoading) return;
    onSendMessage(prompt);
  };

  const toggleReActSteps = (id: string) => {
    setExpandedReActSteps(prev => ({ ...prev, [id]: prev[id] === false ? true : false }));
  };

  const toggleCodeCard = (key: string) => {
    setExpandedCodeCards(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const copyCodeContent = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCodeId(key);
    setTimeout(() => setCopiedCodeId(null), 2000);
  };

  const quickPills = [
    ...(isLiveActive
      ? [
          { label: "⚡ Deep Agentic Loop", prompt: `Analyse my uploaded CSV with the deep agentic loop, evaluate tradeoff consent, and prepare champion-challenger cloud workflow` },
          { label: "📈 Peak Sales Date?", prompt: `What was the highest daily sales date and volume in ${datasetFileName || "my uploaded CSV"}?` },
          { label: "📊 Dataset Statistical Profile", prompt: `Give me a full statistical Q&A summary of my active uploaded dataset ${datasetFileName || "custom CSV"}` },
        ]
      : []),
    { label: "🔍 Inspect Registry Code", prompt: "inspect src/models/registry.py" },
    { label: "⚡ Simulate Price Shock", prompt: "Simulate a price shock drift in Dairy and evaluate PSI" },
    { label: "📐 Explain Max Feature PSI", prompt: "explain max feature psi in simple terms" },
    { label: "🚀 Retrain Shadow Candidate", prompt: "Retrain shadow candidate on shifted data and promote if better" },
    { label: "⚔️ Run Model Battle Arena", prompt: "Run model battle arena tournament and compare LightGBM vs ETS vs Naive" },
    { label: "☸️ Dual-Layer Rollback Guide", prompt: "how does dual layer rollback work in kubernetes and python?" },
    { label: "🏛️ SOLID & Architecture", prompt: "explain the solid principles and lld architecture" },
    { label: "💼 Resume Talking Points", prompt: "what is the quantitative resume impact and talking points for an applied ai role" },
    { label: "⏪ Emergency Rollback", prompt: "Roll back active model to previous champion v1" },
  ];

  return (
    <div
      className="glass-panel"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        maxHeight: "100%",
        minHeight: 0,
        minWidth: 0,
        width: "100%",
        overflow: "hidden",
        boxSizing: "border-box"
      }}
    >
      
      {/* Coding Agent Header */}
      <div style={{
        padding: "12px 18px",
        borderBottom: "1px solid var(--border-subtle)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "rgba(10, 16, 29, 0.7)"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{
            width: "32px",
            height: "32px",
            borderRadius: "8px",
            background: "linear-gradient(135deg, #0284c7, #8b5cf6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 12px rgba(2, 132, 199, 0.4)"
          }}>
            <Code2 size={18} color="#fff" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontWeight: "700", fontSize: "14px", color: "var(--text-primary)" }}>
                Sentinel Coding & MLOps Agent
              </span>
              <span style={{
                fontSize: "10px",
                background: "rgba(56, 189, 248, 0.15)",
                color: "#38bdf8",
                padding: "2px 7px",
                borderRadius: "10px",
                fontWeight: "600",
                border: "1px solid rgba(56, 189, 248, 0.3)"
              }}>
                Conversational RAG • ReAct Loop
              </span>
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "6px" }}>
              <span className="live-badge" style={{ width: "6px", height: "6px", background: "#10b981", borderRadius: "50%", display: "inline-block" }} />
              <span>Full Repository Indexing • Budgeted Context Window • 14 MLOps Tools</span>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{
            fontSize: "11px",
            color: "var(--text-secondary)",
            background: "rgba(255, 255, 255, 0.05)",
            padding: "4px 9px",
            borderRadius: "6px",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            alignItems: "center",
            gap: "5px"
          }}>
            <Layers size={12} color="#38bdf8" />
            <span>FastAPI Port 8000</span>
          </div>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div
        ref={messagesContainerRef}
        style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          padding: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "18px",
          minWidth: 0,
          width: "100%"
        }}
      >
        {messages.map((m) => {
          const isUser = m.sender === "user";
          const isReActExpanded = expandedReActSteps[m.id] !== false; // Default expanded for visibility

          return (
            <div
              key={m.id}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: isUser ? "flex-end" : "flex-start",
                gap: "8px",
                width: "100%",
                maxWidth: "100%",
                minWidth: 0
              }}
            >
              {/* Sender & Timestamp Header */}
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "11px", color: "var(--text-muted)" }}>
                {isUser ? (
                  <>
                    <span>You</span>
                    <span>•</span>
                    <span>{m.timestamp}</span>
                    <User size={13} color="var(--accent-cyan)" />
                  </>
                ) : (
                  <>
                    <Bot size={13} color="var(--accent-cyan)" />
                    <span style={{ fontWeight: "600", color: "#38bdf8" }}>Sentinel Coding Agent</span>
                    <span>•</span>
                    <span>{m.timestamp}</span>
                    {m.action && (
                      <span style={{
                        fontSize: "9px",
                        fontWeight: "700",
                        padding: "1px 6px",
                        borderRadius: "3px",
                        background: "rgba(139, 92, 246, 0.2)",
                        color: "#a78bfa",
                        border: "1px solid rgba(139, 92, 246, 0.3)"
                      }}>
                        {m.action}
                      </span>
                    )}
                  </>
                )}
              </div>

              {/* Coding Agent Query Banner (Rendered on Agent response to show the query tackled) */}
              {!isUser && (m.query || m.reformulatedQuery || m.contextWindow) && (
                <div style={{
                  width: "100%",
                  background: "rgba(15, 23, 42, 0.75)",
                  border: "1px solid rgba(56, 189, 248, 0.2)",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px"
                }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "6px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "7px", fontSize: "12px", color: "#e2e8f0" }}>
                      <Search size={13} color="#38bdf8" />
                      <span style={{ color: "var(--text-muted)" }}>Target Query:</span>
                      <span style={{ fontWeight: "600", color: "#f8fafc" }}>&ldquo;{m.query || m.text.slice(0, 50)}&rdquo;</span>
                    </div>

                    {m.contextWindow && (
                      <div style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        fontSize: "11px",
                        color: "#94a3b8",
                        background: "rgba(0, 0, 0, 0.3)",
                        padding: "2px 8px",
                        borderRadius: "4px"
                      }}>
                        <Cpu size={12} color="#38bdf8" />
                        <span>
                          Context: <strong style={{ color: "#38bdf8" }}>{m.contextWindow.estimatedTokens || 1200}</strong> / 8,192 tok
                        </span>
                        <span>•</span>
                        <span>{m.contextWindow.ragChunksRetrieved || 3} RAG Chunks</span>
                      </div>
                    )}
                  </div>

                  {m.reformulatedQuery && m.reformulatedQuery !== m.query && (
                    <div style={{ fontSize: "11px", color: "var(--accent-cyan)", display: "flex", alignItems: "center", gap: "6px", paddingLeft: "20px" }}>
                      <span>↳ Conversational Context Expansion:</span>
                      <span style={{ fontStyle: "italic", color: "#7dd3fc" }}>&ldquo;{m.reformulatedQuery}&rdquo;</span>
                    </div>
                  )}
                </div>
              )}

              {/* Interactive ReAct Loop Step-by-Step Accordion */}
              {!isUser && ((m.reactSteps && m.reactSteps.length > 0) || (m.toolCalls && m.toolCalls.length > 0) || m.thought) && (
                <div style={{
                  width: "100%",
                  background: "rgba(8, 14, 26, 0.85)",
                  borderRadius: "8px",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  overflow: "hidden"
                }}>
                  <button
                    onClick={() => toggleReActSteps(m.id)}
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      background: "rgba(56, 189, 248, 0.05)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      color: "#38bdf8",
                      fontSize: "11px",
                      fontWeight: "600",
                      borderBottom: isReActExpanded ? "1px solid rgba(255, 255, 255, 0.06)" : "none",
                      cursor: "pointer"
                    }}
                  >
                    <span style={{ display: "flex", alignItems: "center", gap: "7px" }}>
                      <Terminal size={13} color="#38bdf8" />
                      <span>ReAct Execution Trace ({m.reactSteps?.length || (m.toolCalls?.length || 0) + 1} stages)</span>
                    </span>
                    <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{
                        padding: "1px 6px",
                        borderRadius: "4px",
                        background: "rgba(56, 189, 248, 0.15)",
                        color: "#38bdf8",
                        fontFamily: "monospace",
                        fontSize: "10px"
                      }}>
                        ⚡ Autonomous ReAct Active
                      </span>
                      {isReActExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                    </span>
                  </button>

                  {isReActExpanded && (
                    <div style={{ padding: "10px 12px", display: "flex", flexDirection: "column", gap: "8px" }}>
                      
                      {/* Step 1: Agent Reasoning / Thought */}
                      {m.thought && (
                        <div style={{
                          padding: "8px 10px",
                          borderRadius: "6px",
                          background: "rgba(139, 92, 246, 0.08)",
                          border: "1px solid rgba(139, 92, 246, 0.2)",
                          fontSize: "12px",
                          lineHeight: "1.4"
                        }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#a78bfa", fontWeight: "600", marginBottom: "4px", fontSize: "11px" }}>
                            <Cpu size={12} />
                            <span>Step 1: Thought & Strategy Formulation</span>
                          </div>
                          <div style={{ color: "#cbd5e1", fontFamily: "monospace", fontSize: "11px" }}>
                            {m.thought}
                          </div>
                        </div>
                      )}

                      {/* Step 2 & 3: Tool Dispatches and Observations */}
                      {m.toolCalls && m.toolCalls.map((tc, idx) => (
                        <div
                          key={idx}
                          style={{
                            padding: "8px 10px",
                            borderRadius: "6px",
                            background: "rgba(0, 0, 0, 0.4)",
                            border: "1px solid rgba(255, 255, 255, 0.05)",
                            display: "flex",
                            flexDirection: "column",
                            gap: "5px"
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                              {tc.status === "error" ? (
                                <XCircle size={13} color="var(--accent-rose)" />
                              ) : tc.status === "warning" ? (
                                <AlertTriangle size={13} color="var(--accent-amber)" />
                              ) : (
                                <CheckCircle2 size={13} color="var(--accent-emerald)" />
                              )}
                              <span style={{ fontFamily: "monospace", fontSize: "11px", color: "#e2e8f0", fontWeight: "600" }}>
                                {tc.tool}
                              </span>
                            </div>
                            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                              <span style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                                {tc.durationMs}ms
                              </span>
                              <span style={{
                                fontSize: "9px",
                                fontWeight: "700",
                                padding: "1px 5px",
                                borderRadius: "3px",
                                background: tc.status === "error" ? "rgba(244,63,94,0.2)" : tc.status === "warning" ? "rgba(245,158,11,0.2)" : "rgba(16,185,129,0.2)",
                                color: tc.status === "error" ? "var(--accent-rose)" : tc.status === "warning" ? "var(--accent-amber)" : "var(--accent-emerald)"
                              }}>
                                {tc.status.toUpperCase()}
                              </span>
                            </div>
                          </div>

                          <div style={{ fontSize: "11px", color: "var(--text-secondary)", paddingLeft: "19px", lineHeight: "1.4" }}>
                            ↳ <span style={{ color: "var(--text-primary)" }}>{tc.resultSummary}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* IDE Code Cards (Rendered when files or code snippets are retrieved) */}
              {!isUser && m.codeCards && m.codeCards.length > 0 && (
                <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: "10px" }}>
                  {m.codeCards.map((card, cIdx) => {
                    const cardKey = `${m.id}-code-${cIdx}`;
                    const isCardExpanded = expandedCodeCards[cardKey] !== false; // Default expanded
                    const isCopied = copiedCodeId === cardKey;

                    return (
                      <div
                        key={cardKey}
                        style={{
                          borderRadius: "8px",
                          background: "#080d1a",
                          border: "1px solid rgba(56, 189, 248, 0.25)",
                          overflow: "hidden"
                        }}
                      >
                        <div
                          style={{
                            padding: "8px 12px",
                            background: "rgba(56, 189, 248, 0.08)",
                            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between"
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <FileText size={14} color="#38bdf8" />
                            <span style={{ fontFamily: "monospace", fontSize: "12px", color: "#f8fafc", fontWeight: "600" }}>
                              {card.file || "code_snippet.py"}
                            </span>
                            {card.symbol && (
                              <span style={{ fontSize: "10px", color: "#a78bfa", background: "rgba(139, 92, 246, 0.2)", padding: "1px 6px", borderRadius: "3px" }}>
                                {card.symbol}
                              </span>
                            )}
                            <span style={{ fontSize: "10px", color: "#94a3b8" }}>
                              ({card.displayedLines || card.content?.split("\n").length || 0} lines)
                            </span>
                          </div>

                          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <button
                              onClick={() => copyCodeContent(card.content || "", cardKey)}
                              style={{
                                background: "rgba(255, 255, 255, 0.06)",
                                border: "1px solid rgba(255, 255, 255, 0.12)",
                                borderRadius: "4px",
                                padding: "3px 8px",
                                color: isCopied ? "#10b981" : "#cbd5e1",
                                fontSize: "11px",
                                cursor: "pointer",
                                display: "flex",
                                alignItems: "center",
                                gap: "4px"
                              }}
                            >
                              {isCopied ? <Check size={12} /> : <Copy size={12} />}
                              <span>{isCopied ? "Copied!" : "Copy Code"}</span>
                            </button>
                            <button
                              onClick={() => toggleCodeCard(cardKey)}
                              style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer" }}
                            >
                              {isCardExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            </button>
                          </div>
                        </div>

                        {isCardExpanded && (
                          <pre
                            style={{
                              margin: 0,
                              padding: "12px 16px",
                              fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                              fontSize: "12px",
                              lineHeight: "1.5",
                              color: "#e2e8f0",
                              overflowX: "auto",
                              maxHeight: "340px"
                            }}
                          >
                            <code>{card.content}</code>
                          </pre>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Main Message Bubble */}
              <div
                style={{
                  width: isUser ? "auto" : "100%",
                  maxWidth: isUser ? "85%" : "100%",
                  minWidth: 0,
                  padding: "14px 18px",
                  borderRadius: isUser ? "14px 14px 2px 14px" : "14px 14px 14px 2px",
                  background: isUser ? "linear-gradient(135deg, #0284c7, #2563eb)" : "rgba(15, 23, 42, 0.95)",
                  border: isUser ? "none" : "1px solid var(--border-subtle)",
                  fontSize: "13px",
                  lineHeight: "1.55",
                  color: "#f8fafc",
                  boxShadow: isUser ? "0 4px 12px rgba(37, 99, 235, 0.25)" : "none",
                  wordBreak: "break-word",
                  overflowWrap: "anywhere"
                }}
              >
                {isUser ? (
                  <span style={{ whiteSpace: "pre-wrap" }}>{m.text}</span>
                ) : (
                  <FormattedMarkdown content={m.text} />
                )}

                {/* Interactive Proactive Action Pills */}
                {!isUser && m.suggestedActions && m.suggestedActions.length > 0 && (
                  <div style={{ marginTop: "14px", paddingTop: "12px", borderTop: "1px solid rgba(255, 255, 255, 0.08)" }}>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "5px", marginBottom: "8px", fontWeight: "600" }}>
                      <Sparkles size={12} color="var(--accent-cyan)" />
                      <span>Proactive Closed-Loop Actions:</span>
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                      {m.suggestedActions.map((act, i) => (
                        <button
                          key={i}
                          onClick={() => handlePillClick(act.prompt)}
                          disabled={isLoading}
                          className={`agent-action-pill ${act.style || "default"}`}
                        >
                          <span>{act.label}</span>
                          <ArrowRight size={11} />
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "#38bdf8", fontSize: "12px", padding: "12px 16px", background: "rgba(56, 189, 248, 0.06)", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.25)", width: "fit-content" }}>
            <div className="pulsing-dot" style={{ background: "#38bdf8" }} />
            <span>Coding agent formulating ReAct plan, querying conversational RAG, and executing micro-tools...</span>
          </div>
        )}

        {/* Bottom padding spacer */}
        <div style={{ height: "4px" }} />
      </div>

      {/* Global Action Quick Pills */}
      <div style={{
        padding: "8px 14px",
        background: "rgba(0, 0, 0, 0.4)",
        borderTop: "1px solid var(--border-subtle)",
        display: "flex",
        gap: "6px",
        overflowX: "auto",
        whiteSpace: "nowrap"
      }}>
        {quickPills.map((p) => (
          <button
            key={p.label}
            onClick={() => handlePillClick(p.prompt)}
            disabled={isLoading}
            style={{
              fontSize: "11px",
              padding: "5px 12px",
              borderRadius: "14px",
              background: "rgba(255, 255, 255, 0.05)",
              color: "var(--text-secondary)",
              border: "1px solid var(--border-subtle)",
              cursor: "pointer",
              transition: "all 0.15s ease",
              flexShrink: 0
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(56, 189, 248, 0.15)";
              e.currentTarget.style.color = "#38bdf8";
              e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.4)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)";
              e.currentTarget.style.color = "var(--text-secondary)";
              e.currentTarget.style.borderColor = "var(--border-subtle)";
            }}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <form onSubmit={handleSubmit} style={{
        padding: "12px 16px",
        background: "rgba(10, 16, 29, 0.8)",
        borderTop: "1px solid var(--border-subtle)",
        display: "flex",
        gap: "10px"
      }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a technical question, inspect code, or command: 'inspect src/models/registry.py', 'how does rollback work?'..."
          disabled={isLoading}
          style={{
            flex: 1,
            background: "rgba(0, 0, 0, 0.4)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "8px",
            padding: "10px 14px",
            color: "#f8fafc",
            fontSize: "13px",
            outline: "none"
          }}
          onFocus={(e) => e.currentTarget.style.borderColor = "#38bdf8"}
          onBlur={(e) => e.currentTarget.style.borderColor = "var(--border-subtle)"}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          style={{
            background: input.trim() && !isLoading ? "linear-gradient(135deg, #0284c7, #2563eb)" : "rgba(255, 255, 255, 0.05)",
            border: "none",
            borderRadius: "8px",
            padding: "0 16px",
            color: input.trim() && !isLoading ? "#fff" : "var(--text-muted)",
            cursor: input.trim() && !isLoading ? "pointer" : "not-allowed",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.2s ease"
          }}
        >
          <Send size={15} />
        </button>
      </form>
    </div>
  );
};
