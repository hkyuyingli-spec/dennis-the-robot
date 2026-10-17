import { useEffect, useRef, useState, type FormEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  BookOpen,
  Leaf,
  LoaderCircle,
  Plus,
  UserRound,
} from "lucide-react";
import { sendChat, type ChatMessage, type Language } from "./api";
import { ChatApiError } from "./apiErrors";
import logoUrl from "../../static/hero_logo.png";

type Goal = "stress" | "skin" | "energy" | "diet" | "sleep";
type AgeGroup = "18-25" | "26-35" | "36-50" | "50+";
type Gender = "male" | "female" | "prefer-not";
type TopicId =
  | "consultation"
  | "herbs"
  | "constitution"
  | "seasonal"
  | "skincare"
  | "nutrition";
type Page = "chat" | "topics" | "profile";

interface Profile {
  goal: Goal | "";
  ageGroup: AgeGroup | "";
  gender: Gender | "";
  completed: boolean;
}

const emptyProfile: Profile = {
  goal: "",
  ageGroup: "",
  gender: "",
  completed: false,
};

const goals: Record<Language, { value: Goal; label: string }[]> = {
  en: [
    { value: "stress", label: "💆 Stress Relief" },
    { value: "skin", label: "✨ Better Skin" },
    { value: "energy", label: "🔋 More Energy" },
    { value: "diet", label: "🍎 Better Diet" },
    { value: "sleep", label: "😴 Better Sleep" },
  ],
  zh: [
    { value: "stress", label: "💆 缓解压力" },
    { value: "skin", label: "✨ 改善皮肤" },
    { value: "energy", label: "🔋 增强精力" },
    { value: "diet", label: "🍎 改善饮食" },
    { value: "sleep", label: "😴 改善睡眠" },
  ],
  id: [
    { value: "stress", label: "💆 Meredakan Stres" },
    { value: "skin", label: "✨ Kulit Lebih Baik" },
    { value: "energy", label: "🔋 Lebih Bertenaga" },
    { value: "diet", label: "🍎 Pola Makan Lebih Baik" },
    { value: "sleep", label: "😴 Tidur Lebih Baik" },
  ],
};

const ageGroups: Record<Language, { value: AgeGroup; label: string }[]> = {
  en: ["18-25", "26-35", "36-50", "50+"].map((value) => ({ value: value as AgeGroup, label: value })),
  zh: ["18-25", "26-35", "36-50", "50+"].map((value) => ({ value: value as AgeGroup, label: value })),
  id: ["18-25", "26-35", "36-50", "50+"].map((value) => ({ value: value as AgeGroup, label: value })),
};

const genders: Record<Language, { value: Gender; label: string }[]> = {
  en: [
    { value: "male", label: "👨 Male" },
    { value: "female", label: "👩 Female" },
    { value: "prefer-not", label: "⭕ Prefer not to say" },
  ],
  zh: [
    { value: "male", label: "👨 男" },
    { value: "female", label: "👩 女" },
    { value: "prefer-not", label: "⭕ 不愿透露" },
  ],
  id: [
    { value: "male", label: "👨 Laki-laki" },
    { value: "female", label: "👩 Perempuan" },
    { value: "prefer-not", label: "⭕ Lebih suka tidak berkata" },
  ],
};

const text = {
  en: {
    title: "NutriBot V2",
    tagline: "Holistic Wellness Powered by AI",
    byline: "A proprietary wellness platform by NutriBot Co. Ltd.",
    welcomeTitle: "Welcome to NutriBot V2",
    welcomeSubtitle: "Help us personalise your wellness experience. Please answer 3 quick questions.",
    questionGoal: "1. What is your primary wellness goal today?",
    questionAge: "2. What is your age group?",
    questionGender: "3. What is your gender?",
    continue: "Continue",
    back: "Back",
    finish: "Save and continue",
    chat: "Chat",
    topics: "Wellness topics",
    profile: "Your profile",
    newChat: "New chat",
    language: "Language",
    greeting: "What would you like to explore today?",
    chatIntro: "Ask a question or choose a topic to begin.",
    placeholder: "How may I guide your wellness journey today?",
    suggestions: ["Easy ways to improve sleep", "Foods for steady energy", "What is Qi deficiency?"],
    disclaimer: "For education only; this is not medical advice. Consult a licensed practitioner, especially if pregnant, taking medication, or managing a medical condition.",
    thinking: "NutriBot is thinking…",
    send: "Send message",
    retry: "Try again",
    connectionError: "Could not connect to NutriBot. Check your internet connection and try again.",
    configurationError: "NutriBot is not configured correctly right now. Please try again later or contact support.",
    providerError: "NutriBot's AI service could not complete your request. Please try again shortly.",
    rateLimitError: "There have been too many requests. Please wait a moment and try again.",
    serverError: "NutriBot returned an unexpected server error. Please try again.",
    genericError: "NutriBot could not answer. Please try again.",
    topicsTitle: "Explore wellness topics",
    topicsSubtitle: "Choose a topic to start a guided conversation with NutriBot.",
    startTopic: "Start this topic",
    followups: "Suggested follow-up questions",
    storageNotice: "Some information could not be saved on this device. Your current screen will still work, but it may not be restored after closing the app.",
    privacyNote: "Your answers are saved only on this device. They are not sent to NutriBot or used to personalize AI replies.",
    profileTitle: "Personalisation answers",
    profileSubtitle: "You can change these answers at any time. They stay on this device and do not change AI replies.",
    saveProfile: "Save answers",
    profileSaved: "Your answers are saved on this device.",
    changeProfile: "Edit answers",
    restTopic: "A guided, educational TCM wellness intake, one question at a time.",
    herbsTopic: "Explore traditional herb information grounded in NutriBot's knowledge base.",
    constitutionTopic: "Learn about traditional constitution concepts without receiving a diagnosis.",
    seasonalTopic: "Discuss practical, low-risk seasonal wellness ideas.",
    skincareTopic: "Explore a gentle, evidence-aware skincare routine.",
    nutritionTopic: "Discuss balanced food ideas using everyday foods.",
  },
  zh: {
    title: "NutriBot V2",
    tagline: "AI 赋能的整体健康养生平台",
    byline: "NutriBot 有限公司专属健康平台",
    welcomeTitle: "欢迎来到 NutriBot V2",
    welcomeSubtitle: "帮助我们个性化您的健康体验。请回答 3 个简短问题。",
    questionGoal: "1. 您今天的主要健康目标是什么？",
    questionAge: "2. 您的年龄段是？",
    questionGender: "3. 您的性别？",
    continue: "继续",
    back: "返回",
    finish: "保存并继续",
    chat: "聊天",
    topics: "健康主题",
    profile: "个人资料",
    newChat: "新对话",
    language: "语言",
    greeting: "今天想了解什么？",
    chatIntro: "提出问题，或选择一个主题开始。",
    placeholder: "今天有什么我可以为您指导的健康问题吗？",
    suggestions: ["改善睡眠的简单方法", "有助于保持精力的食物", "什么是气虚？"],
    disclaimer: "仅供教育参考，不构成医疗建议。如您正在怀孕、服药或患有疾病，请咨询持牌医疗专业人员。",
    thinking: "NutriBot 正在思考…",
    send: "发送消息",
    retry: "重试",
    connectionError: "无法连接到 NutriBot。请检查网络连接后重试。",
    configurationError: "NutriBot 服务配置暂不可用。请稍后重试或联系支持人员。",
    providerError: "NutriBot 的 AI 服务暂时无法完成请求，请稍后重试。",
    rateLimitError: "请求次数过多，请稍等片刻后重试。",
    serverError: "NutriBot 服务器发生错误，请重试。",
    genericError: "NutriBot 无法回答，请重试。",
    topicsTitle: "探索健康主题",
    topicsSubtitle: "选择一个主题，与 NutriBot 开始引导式对话。",
    startTopic: "开始此主题",
    followups: "推荐的后续问题",
    storageNotice: "部分信息无法保存在此设备上。当前页面仍可使用，但关闭应用后可能无法恢复。",
    privacyNote: "您的答案仅保存在此设备上，不会发送给 NutriBot，也不会用于个性化 AI 回复。",
    profileTitle: "个性化问题答案",
    profileSubtitle: "您可以随时更改答案。答案仅保存在此设备上，不会改变 AI 回复。",
    saveProfile: "保存答案",
    profileSaved: "答案已保存在此设备上。",
    changeProfile: "编辑答案",
    restTopic: "逐步进行教育性质的中医健康问询，每次一个问题。",
    herbsTopic: "根据 NutriBot 知识库了解传统草药信息。",
    constitutionTopic: "了解传统体质概念，不进行诊断。",
    seasonalTopic: "讨论实用、低风险的季节健康建议。",
    skincareTopic: "探索温和且关注证据的护肤流程。",
    nutritionTopic: "讨论以日常食物为主的均衡饮食建议。",
  },
  id: {
    title: "NutriBot V2",
    tagline: "Kesehatan Holistik Didukung AI",
    byline: "Platform kesehatan eksklusif dari NutriBot Co. Ltd.",
    welcomeTitle: "Selamat datang di NutriBot V2",
    welcomeSubtitle: "Bantu kami menyesuaikan pengalaman kesehatan Anda. Silakan jawab 3 pertanyaan singkat.",
    questionGoal: "1. Apa tujuan kesehatan utama Anda hari ini?",
    questionAge: "2. Kelompok usia Anda?",
    questionGender: "3. Jenis kelamin Anda?",
    continue: "Lanjutkan",
    back: "Kembali",
    finish: "Simpan dan lanjutkan",
    chat: "Obrolan",
    topics: "Topik kesehatan",
    profile: "Profil Anda",
    newChat: "Obrolan baru",
    language: "Bahasa",
    greeting: "Apa yang ingin Anda pelajari hari ini?",
    chatIntro: "Ajukan pertanyaan atau pilih topik untuk memulai.",
    placeholder: "Bagaimana saya dapat membantu perjalanan kesehatan Anda hari ini?",
    suggestions: ["Cara sederhana untuk tidur lebih baik", "Makanan untuk energi stabil", "Apa itu defisiensi Qi?"],
    disclaimer: "Hanya untuk edukasi dan bukan nasihat medis. Konsultasikan dengan tenaga kesehatan berlisensi, terutama jika hamil, menggunakan obat, atau memiliki kondisi medis.",
    thinking: "NutriBot sedang berpikir…",
    send: "Kirim pesan",
    retry: "Coba lagi",
    connectionError: "Tidak dapat terhubung ke NutriBot. Periksa koneksi internet lalu coba lagi.",
    configurationError: "Konfigurasi layanan NutriBot belum tersedia. Coba lagi nanti atau hubungi dukungan.",
    providerError: "Layanan AI NutriBot tidak dapat menyelesaikan permintaan. Silakan coba lagi nanti.",
    rateLimitError: "Terlalu banyak permintaan. Tunggu sebentar lalu coba lagi.",
    serverError: "Server NutriBot mengalami kesalahan. Silakan coba lagi.",
    genericError: "NutriBot tidak dapat menjawab. Silakan coba lagi.",
    topicsTitle: "Jelajahi topik kesehatan",
    topicsSubtitle: "Pilih topik untuk memulai percakapan terpandu dengan NutriBot.",
    startTopic: "Mulai topik ini",
    followups: "Pertanyaan lanjutan yang disarankan",
    storageNotice: "Sebagian informasi tidak dapat disimpan di perangkat ini. Layar tetap dapat digunakan, tetapi mungkin tidak pulih setelah aplikasi ditutup.",
    privacyNote: "Jawaban Anda hanya disimpan di perangkat ini. Jawaban tidak dikirim ke NutriBot atau digunakan untuk menyesuaikan balasan AI.",
    profileTitle: "Jawaban personalisasi",
    profileSubtitle: "Anda dapat mengubah jawaban kapan saja. Jawaban hanya tersimpan di perangkat ini dan tidak mengubah balasan AI.",
    saveProfile: "Simpan jawaban",
    profileSaved: "Jawaban Anda tersimpan di perangkat ini.",
    changeProfile: "Ubah jawaban",
    restTopic: "Wawancara kesehatan TCM edukatif secara terpandu, satu pertanyaan setiap kali.",
    herbsTopic: "Jelajahi informasi herbal tradisional yang didukung basis pengetahuan NutriBot.",
    constitutionTopic: "Pelajari konsep konstitusi tradisional tanpa menerima diagnosis.",
    seasonalTopic: "Diskusikan ide kesehatan musiman yang praktis dan berisiko rendah.",
    skincareTopic: "Jelajahi rutinitas perawatan kulit yang lembut dan memperhatikan bukti.",
    nutritionTopic: "Diskusikan ide makanan seimbang dengan bahan sehari-hari.",
  },
} satisfies Record<Language, Record<string, string | string[]>>;

interface TopicFlow {
  label: Record<Language, string>;
  starter: Record<Language, string>;
  followups: Record<Language, string[]>;
  description: Record<Language, string>;
}

const topics: Record<TopicId, TopicFlow> = {
  consultation: {
    label: { en: "Begin TCM Consultation", zh: "开始中医咨询", id: "Mulai Konsultasi TCM" },
    starter: {
      en: "Start a guided TCM wellness intake. Ask me one question at a time about my main symptoms and when they began, sleep, digestion, temperature or cold/heat preference, and emotions/stress. Explain that this is educational and not a diagnosis.",
      zh: "请开始中医健康引导问询，每次只问我一个问题，了解主要症状及开始时间、睡眠、消化、冷热偏好，以及情绪和压力。说明这仅供教育参考，不作诊断。",
      id: "Mulai wawancara kesehatan TCM terpandu. Ajukan satu pertanyaan setiap kali tentang gejala utama dan kapan mulai, tidur, pencernaan, preferensi dingin atau hangat, serta emosi dan stres. Jelaskan bahwa ini untuk edukasi, bukan diagnosis.",
    },
    followups: {
      en: ["What symptom details should I track?", "How can sleep and digestion affect this pattern?", "What signs mean I should seek medical care?"],
      zh: ["我应该记录哪些症状细节？", "睡眠和消化会如何影响这种表现？", "出现哪些情况时应及时就医？"],
      id: ["Gejala apa yang sebaiknya saya catat?", "Bagaimana tidur dan pencernaan memengaruhi pola ini?", "Tanda apa yang mengharuskan saya mencari bantuan medis?"],
    },
    description: { en: text.en.restTopic, zh: text.zh.restTopic, id: text.id.restTopic },
  },
  herbs: {
    label: { en: "Herb Encyclopedia", zh: "草药百科", id: "Ensiklopedia Herbal" },
    starter: {
      en: "Introduce the TCM herb encyclopedia. Explain that you can look up a herb by common, Chinese, or pinyin name, summarize traditional properties and uses only when grounded in the knowledge base, and ask me which herb I want to explore.",
      zh: "介绍中药百科。说明我可以用常见名称、中文名或拼音查询；只有在知识库有依据时才总结传统性味与用途，并询问我想了解哪味药材。",
      id: "Perkenalkan ensiklopedia herbal TCM. Jelaskan bahwa saya dapat mencari herbal dengan nama umum, nama Mandarin, atau pinyin; rangkum sifat dan penggunaan tradisional hanya jika didukung basis pengetahuan, lalu tanyakan herbal yang ingin saya cari.",
    },
    followups: {
      en: ["What cautions apply to this herb?", "How is this traditionally prepared?", "Could it interact with a medicine?"],
      zh: ["这种药材有哪些注意事项？", "传统上如何制备？", "它可能与药物相互作用吗？"],
      id: ["Apa saja kehati-hatian untuk herbal ini?", "Bagaimana cara tradisional menyiapkannya?", "Apakah herbal ini dapat berinteraksi dengan obat?"],
    },
    description: { en: text.en.herbsTopic, zh: text.zh.herbsTopic, id: text.id.herbsTopic },
  },
  constitution: {
    label: { en: "Body Constitution", zh: "体质辨识", id: "Konstitusi Tubuh" },
    starter: {
      en: "Begin an educational questionnaire about the nine traditional TCM constitution types. Ask one question at a time about energy, temperature preference, digestion, sleep, skin, and mood. Do not diagnose or assign a type from one answer.",
      zh: "开始九种中医体质的教育性问卷。每次询问一个关于精力、冷热偏好、消化、睡眠、皮肤和情绪的问题。不要根据单一回答作出诊断或判定体质。",
      id: "Mulai kuesioner edukasi tentang sembilan jenis konstitusi TCM. Tanyakan satu per satu tentang energi, preferensi suhu, pencernaan, tidur, kulit, dan suasana hati. Jangan mendiagnosis atau menetapkan tipe hanya dari satu jawaban.",
    },
    followups: {
      en: ["What are the nine constitution types?", "Which daily patterns are useful to observe?", "How reliable is a self-assessment?"],
      zh: ["九种体质分别是什么？", "哪些日常表现值得观察？", "自我评估的可靠性如何？"],
      id: ["Apa saja sembilan jenis konstitusi?", "Pola harian apa yang berguna untuk diamati?", "Seberapa andal penilaian mandiri?"],
    },
    description: { en: text.en.constitutionTopic, zh: text.zh.constitutionTopic, id: text.id.constitutionTopic },
  },
  seasonal: {
    label: { en: "Seasonal Health", zh: "四季养生", id: "Kesehatan Musiman" },
    starter: {
      en: "Give practical, low-risk seasonal wellness ideas for today's date {today}. Ask for my location if climate would change the advice. Distinguish traditional TCM concepts from established medical evidence.",
      zh: "请根据今天的日期 {today} 提供实用、低风险的季节健康建议。如果气候会影响建议，请询问我的所在地。区分中医传统观点与已确立的医学证据。",
      id: "Berikan saran kesehatan musiman yang praktis dan berisiko rendah berdasarkan tanggal hari ini {today}. Tanyakan lokasi saya jika iklim memengaruhi saran. Bedakan konsep tradisional TCM dari bukti medis yang mapan.",
    },
    followups: {
      en: ["What seasonal foods are practical here?", "How should I adapt this to my local climate?", "Which suggestions have good medical evidence?"],
      zh: ["当地有哪些应季食物适合日常食用？", "如何根据当地气候调整建议？", "哪些建议有较好的医学证据？"],
      id: ["Makanan musiman apa yang praktis di sini?", "Bagaimana menyesuaikan saran dengan iklim setempat?", "Saran mana yang memiliki bukti medis kuat?"],
    },
    description: { en: text.en.seasonalTopic, zh: text.zh.seasonalTopic, id: text.id.seasonalTopic },
  },
  skincare: {
    label: { en: "Skincare Rituals", zh: "中医护肤", id: "Ritual Perawatan Kulit" },
    starter: {
      en: "Suggest a gentle TCM-inspired skincare routine with basic evidence-aware skin care, patch testing, and clear advice to avoid unsafe topical herbs or ingestible remedies. Ask about skin type and concerns; do not diagnose skin disease.",
      zh: "提供温和的中医灵感护肤流程，包含有基础证据支持的护肤、斑贴测试，并明确避免不安全的外用草药或口服疗法。询问肤质和困扰，不诊断皮肤病。",
      id: "Sarankan rutinitas perawatan kulit terinspirasi TCM yang lembut, dengan perawatan dasar berbasis bukti, uji tempel, dan peringatan untuk menghindari herbal topikal atau obat minum yang tidak aman. Tanyakan jenis kulit dan keluhan; jangan mendiagnosis penyakit kulit.",
    },
    followups: {
      en: ["How do I patch test a product?", "What routine suits sensitive skin?", "When should a skin concern be checked by a clinician?"],
      zh: ["如何进行护肤品斑贴测试？", "敏感肌适合什么基础流程？", "何时应请医生检查皮肤问题？"],
      id: ["Bagaimana melakukan uji tempel produk?", "Rutinitas apa yang cocok untuk kulit sensitif?", "Kapan keluhan kulit perlu diperiksa tenaga medis?"],
    },
    description: { en: text.en.skincareTopic, zh: text.zh.skincareTopic, id: text.id.skincareTopic },
  },
  nutrition: {
    label: { en: "Nutrition Advice", zh: "饮食调养", id: "Saran Nutrisi" },
    starter: {
      en: "Offer balanced food-therapy ideas inspired by TCM using ordinary foods, not supplements or restrictive diets. Ask about my goal, dietary pattern, allergies, and relevant conditions. Avoid medical claims and mention when dietitian or clinician input is needed.",
      zh: "提供受中医启发、以普通食物为主的均衡食疗建议，不推荐补充剂或限制性饮食。询问我的目标、饮食习惯、过敏和相关健康状况。避免医疗功效宣称，并说明何时需要营养师或医生帮助。",
      id: "Berikan ide terapi makanan seimbang yang terinspirasi TCM dengan makanan sehari-hari, bukan suplemen atau diet ketat. Tanyakan tujuan, pola makan, alergi, dan kondisi terkait. Hindari klaim medis dan sebutkan kapan perlu berkonsultasi dengan ahli gizi atau tenaga medis.",
    },
    followups: {
      en: ["Can you suggest a simple day of meals?", "How can I adapt this for my dietary restrictions?", "What food allergies or interactions matter?"],
      zh: ["可以给我一个简单的一日饮食示例吗？", "如何根据饮食限制调整？", "需要注意哪些食物过敏或相互作用？"],
      id: ["Bisakah berikan contoh menu sederhana untuk sehari?", "Bagaimana menyesuaikannya dengan pantangan makan saya?", "Alergi atau interaksi makanan apa yang perlu diperhatikan?"],
    },
    description: { en: text.en.nutritionTopic, zh: text.zh.nutritionTopic, id: text.id.nutritionTopic },
  },
};

const topicIds = Object.keys(topics) as TopicId[];
const goalValues = goals.en.map(({ value }) => value);
const ageValues = ageGroups.en.map(({ value }) => value);
const genderValues = genders.en.map(({ value }) => value);

function isLanguage(value: unknown): value is Language {
  return value === "en" || value === "zh" || value === "id";
}

function readLanguage(): Language {
  try {
    const saved = localStorage.getItem("nutribot-language");
    return isLanguage(saved) ? saved : "en";
  } catch {
    return "en";
  }
}

function readProfile(): Profile {
  try {
    const saved = localStorage.getItem("nutribot-profile");
    if (!saved) return emptyProfile;
    const value: unknown = JSON.parse(saved);
    if (!value || typeof value !== "object") return emptyProfile;
    const profile = value as Partial<Profile>;
    const validGoal = profile.goal === "" || goalValues.includes(profile.goal as Goal);
    const validAge = profile.ageGroup === "" || ageValues.includes(profile.ageGroup as AgeGroup);
    const validGender = profile.gender === "" || genderValues.includes(profile.gender as Gender);
    if (!validGoal || !validAge || !validGender) return emptyProfile;
    return {
      goal: profile.goal ?? "",
      ageGroup: profile.ageGroup ?? "",
      gender: profile.gender ?? "",
      completed:
        profile.completed === true &&
        Boolean(profile.goal && profile.ageGroup && profile.gender),
    };
  } catch {
    return emptyProfile;
  }
}

function readMessages(): ChatMessage[] {
  try {
    const saved = sessionStorage.getItem("nutribot-chat");
    if (!saved) return [];
    const value: unknown = JSON.parse(saved);
    if (!Array.isArray(value)) return [];
    return value
      .filter(
        (item): item is ChatMessage =>
          !!item &&
          typeof item === "object" &&
          (item.role === "user" || item.role === "assistant") &&
          typeof item.content === "string",
      )
      .slice(-100);
  } catch {
    return [];
  }
}

function readTopic(): TopicId | null {
  try {
    const saved = sessionStorage.getItem("nutribot-topic");
    return saved && topicIds.includes(saved as TopicId) ? (saved as TopicId) : null;
  } catch {
    return null;
  }
}

function localDate(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

function OptionGroup<T extends string>({
  title,
  options,
  value,
  onChange,
}: {
  title: string;
  options: { value: T; label: string }[];
  value: T | "";
  onChange: (value: T) => void;
}) {
  return (
    <fieldset className="question-group">
      <legend>{title}</legend>
      <div className="choice-grid">
        {options.map((option) => (
          <button
            aria-pressed={value === option.value}
            className={`choice-button${value === option.value ? " selected" : ""}`}
            key={option.value}
            onClick={() => onChange(option.value)}
            type="button"
          >
            {option.label}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>(readMessages);
  const [draft, setDraft] = useState("");
  const [language, setLanguage] = useState<Language>(readLanguage);
  const [profile, setProfile] = useState<Profile>(readProfile);
  const [profileDraft, setProfileDraft] = useState<Profile>(readProfile);
  const [onboardingStep, setOnboardingStep] = useState(0);
  const [page, setPage] = useState<Page>("chat");
  const [activeTopic, setActiveTopic] = useState<TopicId | null>(readTopic);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const [storageWarning, setStorageWarning] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);
  const [showLatest, setShowLatest] = useState(false);
  const listRef = useRef<HTMLElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const copy = text[language];

  useEffect(() => {
    try {
      localStorage.setItem("nutribot-language", language);
    } catch {
      setStorageWarning(true);
    }
  }, [language]);

  useEffect(() => {
    try {
      localStorage.setItem("nutribot-profile", JSON.stringify(profile));
    } catch {
      setStorageWarning(true);
    }
  }, [profile]);

  useEffect(() => {
    try {
      sessionStorage.setItem("nutribot-chat", JSON.stringify(messages.slice(-100)));
    } catch {
      setStorageWarning(true);
    }
  }, [messages]);

  useEffect(() => {
    try {
      if (activeTopic) sessionStorage.setItem("nutribot-topic", activeTopic);
      else sessionStorage.removeItem("nutribot-topic");
    } catch {
      setStorageWarning(true);
    }
  }, [activeTopic]);

  useEffect(() => {
    const list = listRef.current;
    if (!list) return;
    const distanceFromBottom = list.scrollHeight - list.scrollTop - list.clientHeight;
    if (distanceFromBottom < 180 || messages.length < 2) {
      list.scrollTo({ top: list.scrollHeight, behavior: "smooth" });
      setShowLatest(false);
    } else {
      setShowLatest(true);
    }
  }, [messages, isSending, page]);

  useEffect(
    () => () => {
      abortRef.current?.abort();
      abortRef.current = null;
    },
    [],
  );

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
    setActiveTopic(null);
    setDraft("");
    setError("");
    setIsSending(false);
    setPage("chat");
    requestAnimationFrame(resizeComposer);
    textareaRef.current?.focus();
  }

  async function submitMessage(
    event?: FormEvent,
    suggested?: string,
    retry = false,
    topicContext = activeTopic,
  ) {
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
      if (caught instanceof ChatApiError && caught.kind === "connection") {
        setError(copy.connectionError);
      } else if (caught instanceof ChatApiError && caught.kind === "rate_limit") {
        setError(copy.rateLimitError);
      } else if (caught instanceof ChatApiError && caught.kind === "backend_configuration") {
        setError(copy.configurationError);
      } else if (caught instanceof ChatApiError && caught.kind === "provider") {
        setError(copy.providerError);
      } else if (caught instanceof ChatApiError) {
        setError(copy.serverError);
      } else {
        setError(copy.genericError);
      }
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null;
        setIsSending(false);
      }
    }
    if (topicContext !== activeTopic) setActiveTopic(topicContext);
  }

  function startTopic(topic: TopicId) {
    if (isSending) return;
    setActiveTopic(topic);
    setPage("chat");
    const prompt = topics[topic].starter[language].replaceAll("{today}", localDate());
    void submitMessage(undefined, prompt, false, topic);
  }

  function finishOnboarding() {
    setProfile((current) => ({ ...current, completed: true }));
    setProfileDraft((current) => ({ ...current, completed: true }));
    setPage("chat");
  }

  function saveProfile() {
    setProfile({ ...profileDraft, completed: true });
    setProfileSaved(true);
  }

  const onboardingQuestion = onboardingStep === 0 ? (
    <OptionGroup<Goal>
      title={copy.questionGoal}
      options={goals[language]}
      value={profile.goal}
      onChange={(goal) => setProfile((current) => ({ ...current, goal }))}
    />
  ) : onboardingStep === 1 ? (
    <OptionGroup<AgeGroup>
      title={copy.questionAge}
      options={ageGroups[language]}
      value={profile.ageGroup}
      onChange={(ageGroup) => setProfile((current) => ({ ...current, ageGroup }))}
    />
  ) : (
    <OptionGroup<Gender>
      title={copy.questionGender}
      options={genders[language]}
      value={profile.gender}
      onChange={(gender) => setProfile((current) => ({ ...current, gender }))}
    />
  );
  const stepHasAnswer = onboardingStep === 0
    ? Boolean(profile.goal)
    : onboardingStep === 1
      ? Boolean(profile.ageGroup)
      : Boolean(profile.gender);

  if (!profile.completed) {
    return (
      <main className="app-shell onboarding-shell">
        <header className="onboarding-topbar">
          <img className="onboarding-logo-small" src={logoUrl} alt="" />
          <label className="language-picker">
            <span className="sr-only">{copy.language}</span>
            <select
              aria-label={copy.language}
              onChange={(event) => setLanguage(event.target.value as Language)}
              value={language}
            >
              <option value="en">English</option>
              <option value="zh">中文</option>
              <option value="id">Bahasa Indonesia</option>
            </select>
          </label>
        </header>
        <section className="onboarding-scroll">
          <div className="onboarding-card">
            <div className="brand-hero">
              <div className="hero-decoration hero-decoration-left" aria-hidden="true">健康</div>
              <div className="hero-decoration hero-decoration-right" aria-hidden="true">건강</div>
              <img className="hero-logo" src={logoUrl} alt="NutriBot logo" />
              <h1>{copy.title}</h1>
              <p className="hero-tagline">{copy.tagline}</p>
              <p className="hero-byline">{copy.byline}</p>
            </div>
            <div className="onboarding-content">
              <h2>{copy.welcomeTitle}</h2>
              <p className="section-subtitle">{copy.welcomeSubtitle}</p>
              <div className="step-indicator" aria-label={`${onboardingStep + 1} / 3`}>
                {[0, 1, 2].map((step) => (
                  <span className={step <= onboardingStep ? "active" : ""} key={step} />
                ))}
              </div>
              {onboardingQuestion}
              <div className="onboarding-actions">
                {onboardingStep > 0 && (
                  <button className="secondary-button" onClick={() => setOnboardingStep((step) => step - 1)} type="button">
                    <ArrowLeft size={17} />{copy.back}
                  </button>
                )}
                {onboardingStep < 2 ? (
                  <button
                    className="primary-button"
                    disabled={!stepHasAnswer}
                    onClick={() => setOnboardingStep((step) => step + 1)}
                    type="button"
                  >
                    {copy.continue}<ArrowRight size={17} />
                  </button>
                ) : (
                  <button className="primary-button" disabled={!stepHasAnswer} onClick={finishOnboarding} type="button">
                    {copy.finish}<ArrowRight size={17} />
                  </button>
                )}
              </div>
              <p className="privacy-note">{copy.privacyNote}</p>
              {storageWarning && <p className="storage-warning" role="status">{copy.storageNotice}</p>}
            </div>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <img className="brand-logo" src={logoUrl} alt="" />
          <span className="brand-copy">
            <span className="brand-name">{copy.title}</span>
            <span className="brand-tagline">{copy.tagline}</span>
          </span>
        </div>
        <div className="topbar-actions">
          <label className="language-picker">
            <span className="sr-only">{copy.language}</span>
            <select
              aria-label={copy.language}
              onChange={(event) => setLanguage(event.target.value as Language)}
              value={language}
            >
              <option value="en">EN</option>
              <option value="zh">中文</option>
              <option value="id">ID</option>
            </select>
          </label>
          <button className="new-chat-button" onClick={startNewChat} title={copy.newChat} type="button">
            <Plus size={17} />
            <span>{copy.newChat}</span>
          </button>
        </div>
      </header>

      <nav className="main-navigation" aria-label={copy.title}>
        <button className={page === "chat" ? "active" : ""} onClick={() => setPage("chat")} type="button">
          <Leaf size={17} />{copy.chat}
        </button>
        <button className={page === "topics" ? "active" : ""} onClick={() => setPage("topics")} type="button">
          <BookOpen size={17} />{copy.topics}
        </button>
        <button className={page === "profile" ? "active" : ""} onClick={() => { setProfileDraft(profile); setProfileSaved(false); setPage("profile"); }} type="button">
          <UserRound size={17} />{copy.profile}
        </button>
      </nav>

      {storageWarning && <p className="storage-warning app-storage-warning" role="status">{copy.storageNotice}</p>}

      {page === "topics" && (
        <section className="screen-scroll topics-screen">
          <div className="screen-heading">
            <p className="eyebrow">{copy.title}</p>
            <h1>{copy.topicsTitle}</h1>
            <p className="section-subtitle">{copy.topicsSubtitle}</p>
          </div>
          <div className="topic-grid">
            {topicIds.map((topicId) => (
              <article className="topic-card" key={topicId}>
                <div className="topic-card-heading"><Leaf size={18} /><h2>{topics[topicId].label[language]}</h2></div>
                <p>{topics[topicId].description[language]}</p>
                <button className="primary-button" disabled={isSending} onClick={() => startTopic(topicId)} type="button">
                  {copy.startTopic}<ArrowRight size={17} />
                </button>
              </article>
            ))}
          </div>
        </section>
      )}

      {page === "profile" && (
        <section className="screen-scroll profile-screen">
          <div className="screen-heading">
            <p className="eyebrow">{copy.title}</p>
            <h1>{copy.profileTitle}</h1>
            <p className="section-subtitle">{copy.profileSubtitle}</p>
          </div>
          <div className="profile-form">
            <OptionGroup title={copy.questionGoal} options={goals[language]} value={profileDraft.goal} onChange={(goal) => setProfileDraft((current) => ({ ...current, goal }))} />
            <OptionGroup title={copy.questionAge} options={ageGroups[language]} value={profileDraft.ageGroup} onChange={(ageGroup) => setProfileDraft((current) => ({ ...current, ageGroup }))} />
            <OptionGroup title={copy.questionGender} options={genders[language]} value={profileDraft.gender} onChange={(gender) => setProfileDraft((current) => ({ ...current, gender }))} />
            <button className="primary-button" disabled={!profileDraft.goal || !profileDraft.ageGroup || !profileDraft.gender} onClick={saveProfile} type="button">
              {copy.saveProfile}<ArrowRight size={17} />
            </button>
            {profileSaved && <p className="profile-saved" role="status">{copy.profileSaved}</p>}
          </div>
        </section>
      )}

      {page === "chat" && (
        <>
          <section className="conversation" ref={listRef} aria-label={copy.chat} aria-live="polite">
            {messages.length === 0 ? (
              <div className="welcome">
                <div className="welcome-icon"><Leaf size={25} strokeWidth={1.8} /></div>
                <p className="eyebrow">{copy.tagline}</p>
                <h1>{copy.greeting}</h1>
                <p className="welcome-intro">{copy.chatIntro}</p>
                <div className="suggestions">
                  {copy.suggestions.map((suggestion) => (
                    <button className="suggestion" key={suggestion} onClick={() => void submitMessage(undefined, suggestion)} type="button">
                      {suggestion}<ArrowUp size={15} aria-hidden="true" />
                    </button>
                  ))}
                  <button className="suggestion explore-suggestion" onClick={() => setPage("topics")} type="button">
                    {copy.topics}<ArrowRight size={15} aria-hidden="true" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="message-list">
                {activeTopic && (
                  <div className="active-topic">
                    <Leaf size={16} />{topics[activeTopic].label[language]}
                  </div>
                )}
                {messages.map((message, index) => (
                  <article
                    aria-label={message.role === "user" ? copy.chat : copy.title}
                    className={`message-row ${message.role}`}
                    key={`${index}-${message.role}`}
                  >
                    {message.role === "assistant" && <span className="assistant-mark"><Leaf size={15} aria-hidden="true" /></span>}
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
                    <LoaderCircle className="spin" size={17} /><span>{copy.thinking}</span>
                  </div>
                )}
                {error && (
                  <div className="error-banner" role="alert">
                    <span>{error}</span>
                    <button onClick={() => void submitMessage(undefined, messages.at(-1)?.content, true)} type="button">
                      {copy.retry}
                    </button>
                  </div>
                )}
                {!isSending && !error && activeTopic && messages.at(-1)?.role === "assistant" && (
                  <div className="followup-section">
                    <p>{copy.followups}</p>
                    <div className="followup-list">
                      {topics[activeTopic].followups[language].map((question) => (
                        <button className="followup-button" key={question} onClick={() => void submitMessage(undefined, question)} type="button">
                          {question}<ArrowUp size={14} aria-hidden="true" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>

          {showLatest && (
            <button
              aria-label={copy.greeting}
              className="latest-button"
              onClick={() => listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" })}
              type="button"
            >
              <ArrowDown size={17} />
            </button>
          )}

          <footer className="composer-area">
            <form className="composer" onSubmit={(event) => void submitMessage(event)}>
              <textarea
                aria-label={copy.placeholder}
                autoComplete="off"
                disabled={isSending}
                enterKeyHint="send"
                maxLength={6000}
                onChange={(event) => { setDraft(event.target.value); resizeComposer(); }}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    void submitMessage();
                  }
                }}
                placeholder={copy.placeholder}
                ref={textareaRef}
                rows={1}
                value={draft}
              />
              <button aria-label={copy.send} className="send-button" disabled={!draft.trim() || isSending} type="submit">
                {isSending ? <LoaderCircle className="spin" size={18} /> : <ArrowUp size={19} strokeWidth={2.5} />}
              </button>
            </form>
            <p className="disclaimer">{copy.disclaimer}</p>
          </footer>
        </>
      )}
    </main>
  );
}
