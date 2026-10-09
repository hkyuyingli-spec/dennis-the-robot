"""Localized starter prompts and follow-up suggestions for NutriBot topics."""
from datetime import date

TOPICS = {
    "consultation": {
        "label": {"en": "Begin TCM Consultation", "zh": "开始中医咨询", "id": "Mulai Konsultasi TCM"},
        "starter": {
            "en": "Start a guided TCM wellness intake. Ask me one question at a time about my main symptoms and when they began, sleep, digestion, temperature or cold/heat preference, and emotions/stress. Explain that this is educational and not a diagnosis.",
            "zh": "请开始中医健康引导问询，每次只问我一个问题，了解主要症状及开始时间、睡眠、消化、冷热偏好，以及情绪和压力。说明这仅供教育参考，不作诊断。",
            "id": "Mulai wawancara kesehatan TCM terpandu. Ajukan satu pertanyaan setiap kali tentang gejala utama dan kapan mulai, tidur, pencernaan, preferensi dingin atau hangat, serta emosi dan stres. Jelaskan bahwa ini untuk edukasi, bukan diagnosis.",
        },
        "followups": {
            "en": ["What symptom details should I track?", "How can sleep and digestion affect this pattern?", "What signs mean I should seek medical care?"],
            "zh": ["我应该记录哪些症状细节？", "睡眠和消化会如何影响这种表现？", "出现哪些情况时应及时就医？"],
            "id": ["Gejala apa yang sebaiknya saya catat?", "Bagaimana tidur dan pencernaan memengaruhi pola ini?", "Tanda apa yang mengharuskan saya mencari bantuan medis?"],
        },
    },
    "herbs": {
        "label": {"en": "Herb Encyclopedia", "zh": "草药百科", "id": "Ensiklopedia Herbal"},
        "starter": {
            "en": "Introduce the TCM herb encyclopedia. Explain that you can look up a herb by common, Chinese, or pinyin name, summarize traditional properties and uses only when grounded in the knowledge base, and ask me which herb I want to explore.",
            "zh": "介绍中药百科。说明我可以用常见名称、中文名或拼音查询；只有在知识库有依据时才总结传统性味与用途，并询问我想了解哪味药材。",
            "id": "Perkenalkan ensiklopedia herbal TCM. Jelaskan bahwa saya dapat mencari herbal dengan nama umum, nama Mandarin, atau pinyin; rangkum sifat dan penggunaan tradisional hanya jika didukung basis pengetahuan, lalu tanyakan herbal yang ingin saya cari.",
        },
        "followups": {
            "en": ["What cautions apply to this herb?", "How is this traditionally prepared?", "Could it interact with a medicine?"],
            "zh": ["这种药材有哪些注意事项？", "传统上如何制备？", "它可能与药物相互作用吗？"],
            "id": ["Apa saja kehati-hatian untuk herbal ini?", "Bagaimana cara tradisional menyiapkannya?", "Apakah herbal ini dapat berinteraksi dengan obat?"],
        },
    },
    "constitution": {
        "label": {"en": "Body Constitution", "zh": "体质辨识", "id": "Konstitusi Tubuh"},
        "starter": {
            "en": "Begin an educational questionnaire about the nine traditional TCM constitution types. Ask one question at a time about energy, temperature preference, digestion, sleep, skin, and mood. Do not diagnose or assign a type from one answer.",
            "zh": "开始九种中医体质的教育性问卷。每次询问一个关于精力、冷热偏好、消化、睡眠、皮肤和情绪的问题。不要根据单一回答作出诊断或判定体质。",
            "id": "Mulai kuesioner edukasi tentang sembilan jenis konstitusi TCM. Tanyakan satu per satu tentang energi, preferensi suhu, pencernaan, tidur, kulit, dan suasana hati. Jangan mendiagnosis atau menetapkan tipe hanya dari satu jawaban.",
        },
        "followups": {
            "en": ["What are the nine constitution types?", "Which daily patterns are useful to observe?", "How reliable is a self-assessment?"],
            "zh": ["九种体质分别是什么？", "哪些日常表现值得观察？", "自我评估的可靠性如何？"],
            "id": ["Apa saja sembilan jenis konstitusi?", "Pola harian apa yang berguna untuk diamati?", "Seberapa andal penilaian mandiri?"],
        },
    },
    "seasonal": {
        "label": {"en": "Seasonal Health", "zh": "四季养生", "id": "Kesehatan Musiman"},
        "starter": {
            "en": "Give practical, low-risk seasonal wellness ideas for today's date {today}. Ask for my location if climate would change the advice. Distinguish traditional TCM concepts from established medical evidence.",
            "zh": "请根据今天的日期 {today} 提供实用、低风险的季节健康建议。如果气候会影响建议，请询问我的所在地。区分中医传统观点与已确立的医学证据。",
            "id": "Berikan saran kesehatan musiman yang praktis dan berisiko rendah berdasarkan tanggal hari ini {today}. Tanyakan lokasi saya jika iklim memengaruhi saran. Bedakan konsep tradisional TCM dari bukti medis yang mapan.",
        },
        "followups": {
            "en": ["What seasonal foods are practical here?", "How should I adapt this to my local climate?", "Which suggestions have good medical evidence?"],
            "zh": ["当地有哪些应季食物适合日常食用？", "如何根据当地气候调整建议？", "哪些建议有较好的医学证据？"],
            "id": ["Makanan musiman apa yang praktis di sini?", "Bagaimana menyesuaikan saran dengan iklim setempat?", "Saran mana yang memiliki bukti medis kuat?"],
        },
    },
    "skincare": {
        "label": {"en": "Skincare Rituals", "zh": "中医护肤", "id": "Ritual Perawatan Kulit"},
        "starter": {
            "en": "Suggest a gentle TCM-inspired skincare routine with basic evidence-aware skin care, patch testing, and clear advice to avoid unsafe topical herbs or ingestible remedies. Ask about skin type and concerns; do not diagnose skin disease.",
            "zh": "提供温和的中医灵感护肤流程，包含有基础证据支持的护肤、斑贴测试，并明确避免不安全的外用草药或口服疗法。询问肤质和困扰，不诊断皮肤病。",
            "id": "Sarankan rutinitas perawatan kulit terinspirasi TCM yang lembut, dengan perawatan dasar berbasis bukti, uji tempel, dan peringatan untuk menghindari herbal topikal atau obat minum yang tidak aman. Tanyakan jenis kulit dan keluhan; jangan mendiagnosis penyakit kulit.",
        },
        "followups": {
            "en": ["How do I patch test a product?", "What routine suits sensitive skin?", "When should a skin concern be checked by a clinician?"],
            "zh": ["如何进行护肤品斑贴测试？", "敏感肌适合什么基础流程？", "何时应请医生检查皮肤问题？"],
            "id": ["Bagaimana melakukan uji tempel produk?", "Rutinitas apa yang cocok untuk kulit sensitif?", "Kapan keluhan kulit perlu diperiksa tenaga medis?"],
        },
    },
    "nutrition": {
        "label": {"en": "Nutrition Advice", "zh": "饮食调养", "id": "Saran Nutrisi"},
        "starter": {
            "en": "Offer balanced food-therapy ideas inspired by TCM using ordinary foods, not supplements or restrictive diets. Ask about my goal, dietary pattern, allergies, and relevant conditions. Avoid medical claims and mention when dietitian or clinician input is needed.",
            "zh": "提供受中医启发、以普通食物为主的均衡食疗建议，不推荐补充剂或限制性饮食。询问我的目标、饮食习惯、过敏和相关健康状况。避免医疗功效宣称，并说明何时需要营养师或医生帮助。",
            "id": "Berikan ide terapi makanan seimbang yang terinspirasi TCM dengan makanan sehari-hari, bukan suplemen atau diet ketat. Tanyakan tujuan, pola makan, alergi, dan kondisi terkait. Hindari klaim medis dan sebutkan kapan perlu berkonsultasi dengan ahli gizi atau tenaga medis.",
        },
        "followups": {
            "en": ["Can you suggest a simple day of meals?", "How can I adapt this for my dietary restrictions?", "What food allergies or interactions matter?"],
            "zh": ["可以给我一个简单的一日饮食示例吗？", "如何根据饮食限制调整？", "需要注意哪些食物过敏或相互作用？"],
            "id": ["Bisakah berikan contoh menu sederhana untuk sehari?", "Bagaimana menyesuaikannya dengan pantangan makan saya?", "Alergi atau interaksi makanan apa yang perlu diperhatikan?"],
        },
    },
}

def build_topic_prompt(topic: str, lang: str, today: date | None = None) -> str:
    """Return a localized starter prompt for a known topic."""
    item = TOPICS[topic]
    lang = lang if lang in ("en", "zh", "id") else "en"
    return item["starter"][lang].format(today=(today or date.today()).isoformat())

def topic_label(topic: str, lang: str) -> str:
    return TOPICS[topic]["label"].get(lang, TOPICS[topic]["label"]["en"])

def topic_followups(topic: str, lang: str) -> list[str]:
    return TOPICS[topic]["followups"].get(lang, TOPICS[topic]["followups"]["en"])
