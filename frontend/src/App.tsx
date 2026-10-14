import { useEffect, useRef, useState, type FormEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowDown, ArrowUp, Leaf, LoaderCircle, Plus } from "lucide-react";
import { sendChat, type ChatMessage, type Language } from "./api";

const copy: Record<Language, {
  title: string;
  subtitle: string;
  placeholder: string;
  greeting: string;
  suggestions: string[];
  disclaimer: string;
  newChat: string;
  language: string;
  retry: string;
  send: string;
  thinking: string;
}> = {
  en: {
    title: "NutriBot",
    subtitle: "A thoughtful space for everyday wellness",
    placeholder: "Ask about food, rest, movement, or wellbeing…",
    greeting: "What would you like to explore today?",
    suggestions: ["Easy ways to improve sleep", "Foods for steady energy", "What is Qi deficiency?"],
    disclaimer: "Educational information only — not medical advice.",
    newChat: "New chat",
    language: "Language",
    retry: "Try again",
    send: "Send message",
    thinking: "NutriBot is thinking…"
  },
  zh: {
    title: "NutriBot",
    subtitle: "探索日常健康的温和空间",
    placeholder: "询问饮食、休息、运动或身心健康…",
    greeting: "今天想了解什么？",
    suggestions: ["改善睡眠的简单方法", "有助于保持精力的食物", "什么是气虚？"],
    disclaimer: "仅供参考，不构成医疗建议。",
    newChat: "新对话",
    language: "语言",
    retry: "重试",
    send: "发送消息",
    thinking: "NutriBot 正在思考…"
  },
  id: {
    title: "NutriBot",
    subtitle: "Ruang nyaman untuk belajar tentang kesehatan sehari-hari",
    placeholder: "Tanyakan tentang makanan, istirahat, aktivitas, atau kebugaran…",
    greeting: "Apa yang ingin Anda pelajari hari ini?",
    suggestions: ["Cara sederhana untuk tidur lebih baik", "Makanan untuk energi stabil", "Apa itu defisiensi Qi?"],
    disclaimer: "Informasi edukatif saja — bukan nasihat medis.",
    newChat: "Obrolan baru",
    language: "Bahasa",
    retry: "Coba lagi",
    send: "Kirim pesan",
    thinking: "NutriBot sedang berpikir…"
  }
};

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [language, setLanguage] = useState<Language>("en");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const [showLatest, setShowLatest] = useState(false);
  const listRef = useRef<HTMLElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const text = copy[language];

  useEffect(() => {
    const list = listRef.current;
    if (!list) return;
    const distanceFromBottom =
      list.scrollHeight - list.scrollTop - list.clientHeight;
    if (distanceFromBottom < 180 || messages.length < 2) {
      list.scrollTo({ top: list.scrollHeight, behavior: "smooth" });
      setShowLatest(false);
    } else {
      setShowLatest(true);
    }
  }, [messages, isSending]);

  useEffect(() => () => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  function resizeComposer() {
    const field = textareaRef.current;
    if (!field) return;
    field.style.height = "auto";
    field.style.height = `${Math.min(field.scrollHeight, 180)}px`;
  }

  function startNewChat() {
    abortRef.current?.abort();
    abortRef.current = null;
    setMessages([]);
    setDraft("");
    setError("");
    setIsSending(false);
    requestAnimationFrame(resizeComposer);
    textareaRef.current?.focus();
  }

  async function submitMessage(event?: FormEvent, suggested?: string, retry = false) {
    event?.preventDefault();
    const content = (suggested ?? draft).trim();
    if (!content || isSending) return;

    const nextMessages = retry
      ? messages
      : [...messages, { role: "user" as const, content }];
    if (!retry) setMessages(nextMessages);
    setDraft("");
    setError("");
    setIsSending(true);
    requestAnimationFrame(resizeComposer);

    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const result = await sendChat(nextMessages.slice(-12), language, controller.signal);
      setMessages([...nextMessages, { role: "assistant", content: result.reply }]);
    } catch (caught) {
      if (controller.signal.aborted) return;
      setError(caught instanceof Error ? caught.message : "Something went wrong. Please try again.");
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null;
        setIsSending(false);
      }
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#" aria-label="NutriBot home" onClick={(event) => event.preventDefault()}>
          <span className="brand-mark"><Leaf size={19} strokeWidth={2.2} /></span>
          <span className="brand-name">{text.title}</span>
        </a>
        <div className="topbar-actions">
          <label className="language-picker">
            <span className="sr-only">{text.language}</span>
            <select
              value={language}
              onChange={(event) => setLanguage(event.target.value as Language)}
              aria-label={text.language}
            >
              <option value="en">EN</option>
              <option value="zh">中文</option>
              <option value="id">ID</option>
            </select>
          </label>
          <button className="new-chat-button" type="button" onClick={startNewChat} title={text.newChat}>
            <Plus size={17} />
            <span>{text.newChat}</span>
          </button>
        </div>
      </header>

      <section className="conversation" ref={listRef} aria-label="Conversation" aria-live="polite">
        {messages.length === 0 ? (
          <div className="welcome">
            <div className="welcome-icon"><Leaf size={25} strokeWidth={1.8} /></div>
            <p className="eyebrow">{text.subtitle}</p>
            <h1>{text.greeting}</h1>
            <div className="suggestions">
              {text.suggestions.map((suggestion) => (
                <button
                  type="button"
                  className="suggestion"
                  key={suggestion}
                  onClick={() => void submitMessage(undefined, suggestion)}
                >
                  {suggestion}
                  <ArrowUp size={15} aria-hidden="true" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="message-list">
            {messages.map((message, index) => (
              <article
                className={`message-row ${message.role}`}
                key={`${index}-${message.role}`}
                aria-label={message.role === "user" ? "Your message" : "NutriBot response"}
              >
                {message.role === "assistant" && (
                  <span className="assistant-mark"><Leaf size={15} aria-hidden="true" /></span>
                )}
                <div className="message-content">
                  {message.role === "assistant" ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                  ) : (
                    <p>{message.content}</p>
                  )}
                </div>
              </article>
            ))}
            {isSending && (
              <div className="thinking" role="status">
                <LoaderCircle className="spin" size={17} />
                <span>{text.thinking}</span>
              </div>
            )}
            {error && (
              <div className="error-banner" role="alert">
                <span>{error}</span>
                <button type="button" onClick={() => void submitMessage(undefined, messages.at(-1)?.content, true)}>
                  {text.retry}
                </button>
              </div>
            )}
          </div>
        )}
      </section>

      {showLatest && (
        <button
          className="latest-button"
          type="button"
          onClick={() => listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" })}
          aria-label="Scroll to latest message"
        >
          <ArrowDown size={17} />
        </button>
      )}

      <footer className="composer-area">
        <form className="composer" onSubmit={(event) => void submitMessage(event)}>
          <textarea
            ref={textareaRef}
            value={draft}
            onChange={(event) => {
              setDraft(event.target.value);
              resizeComposer();
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void submitMessage();
              }
            }}
            placeholder={text.placeholder}
            rows={1}
            maxLength={6000}
            aria-label={text.placeholder}
            enterKeyHint="send"
            autoComplete="off"
            disabled={isSending}
          />
          <button
            className="send-button"
            type="submit"
            disabled={!draft.trim() || isSending}
            aria-label={text.send}
          >
            {isSending ? <LoaderCircle className="spin" size={18} /> : <ArrowUp size={19} strokeWidth={2.5} />}
          </button>
        </form>
        <p className="disclaimer">{text.disclaimer}</p>
      </footer>
    </main>
  );
}
