import { useState } from "react";
import { ArrowLeft, Leaf } from "lucide-react";
import data from "./data/herbal_kitchen.json";
import strings from "./data/herbal_kitchen_strings.json";
import type { Language } from "./api";
import { isHerbalKitchenRecordVisible } from "./HerbalKitchenConfig";

const ACCEPTED_KEY = "herbal_kitchen_welcome_accepted_v1";

type LanguageText = { en?: string; id?: string; zh?: string };
type Ingredient = { qty: number | null; unit: string | null; text: LanguageText; herbId?: string };
type Dish = {
  id: string;
  image?: string;
  status: string;
  name: LanguageText;
  type: "drink" | "soup" | "rice" | "main" | "side" | "dessert";
  serves: number;
  minutes: number;
  diet: string[];
  allergens: string[];
  intro: LanguageText;
  ingredients: Ingredient[];
  steps: LanguageText[];
  tips: LanguageText[];
  variations: LanguageText[];
  storage: LanguageText;
  cookingSafety?: LanguageText;
  sources: string[];
  checkedOn: string;
};
type Herb = {
  id: string;
  image?: string;
  tier: "A" | "B";
  status: string;
  names: LanguageText & { latin?: string };
  preparation: LanguageText;
  amountPerServing: LanguageText;
  caution: LanguageText;
  sources: string[];
};
type KitchenCopy = typeof strings.en;
type View = { kind: "list" } | { kind: "herb"; herbId: string };

function localize(field: LanguageText | undefined, lang: string): string {
  if (!field) return "";
  const selected = field[lang as keyof LanguageText];
  const hasChineseText = typeof selected === "string" && /[\u3400-\u9fff]/.test(selected);
  if (typeof selected === "string" && selected.trim() && !selected.includes("??") && (lang !== "zh" || hasChineseText)) return selected;
  return typeof field.en === "string" && !field.en.includes("??") ? field.en : "";
}

const imgSrc = (p?: string) =>
  p ? `${import.meta.env.BASE_URL}${p.replace(/^\//, "")}` : undefined;

function HerbAvatar({ image, alt }: { image?: string; alt: string }) {
  const [imageFailed, setImageFailed] = useState(false);
  return (
    <span
      aria-hidden={image && !imageFailed ? undefined : true}
      style={{ alignItems: "center", display: "inline-flex", flex: "0 0 40px", height: 40, justifyContent: "center", width: 40 }}
    >
      {image && !imageFailed ? (
        <img
          src={imgSrc(image)}
          alt={alt}
          loading="lazy"
          width={40}
          height={40}
          onError={() => setImageFailed(true)}
          style={{ width: 40, height: 40 }}
          className="rounded-full object-cover shrink-0"
        />
      ) : (
        <Leaf size={40} />
      )}
    </span>
  );
}

const herbs = (data.herbs as Herb[]).filter((herb) => isHerbalKitchenRecordVisible(herb.status));
const dishes = (data.dishes as Dish[]).filter((dish) => isHerbalKitchenRecordVisible(dish.status));

function readAcceptance(): boolean {
  try { return localStorage.getItem(ACCEPTED_KEY) === "yes"; } catch { return false; }
}

export default function HerbalKitchen({
  language,
  onAskAboutRecipe,
}: {
  language: Language;
  onAskAboutRecipe: (recipeName: string, herbName: string) => void;
}) {
  const [history, setHistory] = useState<View[]>([{ kind: "list" }]);
  const [accepted, setAccepted] = useState(readAcceptance);
  const [search, setSearch] = useState("");
  const copy: KitchenCopy = strings[language] ?? strings.en;
  const view = history[history.length - 1] ?? { kind: "list" as const };
  const selectedHerb = view.kind === "herb" ? herbs.find((herb) => herb.id === view.herbId) : undefined;
  const selectedRecipe = selectedHerb?.tier === "A"
    ? dishes.find((dish) => dish.ingredients.some((ingredient) => ingredient.herbId === selectedHerb.id))
    : undefined;
  const visibleHerbs = herbs.filter((herb) => {
    const query = search.trim().toLocaleLowerCase();
    return !query || [herb.names.en, herb.names.id, herb.names.zh, herb.names.latin ?? ""]
      .filter((name): name is string => typeof name === "string")
      .some((name) => name.toLocaleLowerCase().includes(query));
  });

  function navigate(herbId: string) {
    if (!herbs.some((herb) => herb.id === herbId)) return;
    setHistory((current) => [...current, { kind: "herb", herbId }]);
  }

  function goBack() {
    setHistory((current) => current.length > 1 ? current.slice(0, -1) : [{ kind: "list" }]);
  }

  function acceptWelcome() {
    try { localStorage.setItem(ACCEPTED_KEY, "yes"); } catch { /* Keep the notice dismissible for this session. */ }
    setAccepted(true);
  }

  function allergenName(code: string): string {
    const translated = copy.allergenNames[code as keyof typeof copy.allergenNames];
    return translated ?? code;
  }

  function askAboutSelectedRecipe() {
    if (!selectedRecipe || !selectedHerb) return;
    const recipeName = localize(selectedRecipe.name, language).trim();
    const herbName = localize(selectedHerb.names, language).trim();
    if (recipeName || herbName) onAskAboutRecipe(recipeName, herbName);
  }

  return (
    <section className="screen-scroll herbal-kitchen-screen" aria-label={copy.tab}>
      {!accepted && (
        <div className="herbal-welcome-backdrop" role="presentation">
          <section className="herbal-welcome" role="dialog" aria-modal="true" aria-labelledby="herbal-welcome-title">
            <h1 id="herbal-welcome-title">{copy.welcomeTitle}</h1>
            <p>{copy.welcomeBody}</p>
            <button className="primary-button herbal-tap-target" onClick={acceptWelcome} type="button">{copy.welcomeButton}</button>
          </section>
        </div>
      )}

      {view.kind === "herb" && (
        <button className="secondary-button herbal-back herbal-tap-target" onClick={goBack} type="button">
          <ArrowLeft size={18} />{copy.back}
        </button>
      )}

      {view.kind === "list" && (
        <>
          <div className="screen-heading herbal-heading"><p className="eyebrow">{copy.tab}</p><h1>{copy.tab}</h1></div>
          <input
            className="herbal-search"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={copy.searchPlaceholder}
            aria-label={copy.searchPlaceholder}
          />
          <div className="herbal-card-list">
            {visibleHerbs.map((herb) => (
              <button className="herbal-card herbal-tap-target" key={herb.id} onClick={() => navigate(herb.id)} type="button">
                <span className="herbal-card-title">
                  <span className="flex items-center gap-3 flex-1 min-w-0">
                    <HerbAvatar image={herb.image} alt={localize(herb.names, language)} />
                    <span className="min-w-0">{localize(herb.names, language)}</span>
                  </span>
                </span>
                {herb.status === "draft" && <span className="draft-badge">{copy.draftBadge}</span>}
              </button>
            ))}
            {visibleHerbs.length === 0 && <p className="herbal-muted">{copy.noSearchResults}</p>}
          </div>
        </>
      )}

      {view.kind === "herb" && selectedHerb && (
        <>
          <div className="screen-heading herbal-heading">
            <h1>{localize(selectedHerb.names, language)}</h1>
            {selectedHerb.status === "draft" && <span className="draft-badge">{copy.draftBadge}</span>}
          </div>
          <dl className="herbal-details">
            <Detail label={copy.englishName} value={localize({ en: selectedHerb.names.en }, "en")} />
            <Detail label={copy.indonesianName} value={localize({ id: selectedHerb.names.id, en: selectedHerb.names.en }, "id")} />
            <Detail label={copy.chineseName} value={localize({ zh: selectedHerb.names.zh, en: selectedHerb.names.en }, "zh")} />
            <Detail label={copy.latinName} value={selectedHerb.names.latin || "—"} />
            <Detail label={copy.preparation} value={localize(selectedHerb.preparation, language)} />
            <Detail label={copy.amountPerServing} value={localize(selectedHerb.amountPerServing, language)} />
          </dl>

          {selectedHerb.tier === "B" && <p className="herbal-notice">{copy.infoOnly}</p>}
          <h2 className="herbal-section-title">{copy.recipe}</h2>
          {selectedHerb.tier === "B" || !selectedRecipe ? (
            <p className="herbal-muted">{copy.noRecipeYet}</p>
          ) : (
            <>
              <h3 className="herbal-recipe-title">{localize(selectedRecipe.name, language)}</h3>
              {selectedRecipe.status === "draft" && <span className="draft-badge">{copy.draftBadge}</span>}
              <p className="herbal-meta">{copy.serves}: {selectedRecipe.serves} · {copy.minutes}: {selectedRecipe.minutes}</p>
              <h3 className="herbal-section-title">{copy.ingredients}</h3>
              <ul className="herbal-steps">
                {selectedRecipe.ingredients.map((ingredient, index) => (
                  <li key={`${index}-${ingredient.text.en}`}>{localize(ingredient.text, language)}</li>
                ))}
              </ul>
              <h3 className="herbal-section-title">{copy.steps}</h3>
              <ol className="herbal-steps">
                {selectedRecipe.steps.map((step, index) => (
                  <li key={`${index}-${step.en}`}>{localize(step, language)}</li>
                ))}
              </ol>
              <p className="herbal-allergens"><strong>{copy.allergens}:</strong> {selectedRecipe.allergens.length
                ? selectedRecipe.allergens.map(allergenName).join(", ")
                : copy.noKnownAllergens}</p>
              {selectedRecipe.cookingSafety && <p className="herbal-caution">{localize(selectedRecipe.cookingSafety, language)}</p>}
            </>
          )}
          {selectedRecipe && selectedHerb.tier === "A" && (
            <button className="secondary-button herbal-ask-ai" onClick={askAboutSelectedRecipe} type="button">
              {copy.askAI}
            </button>
          )}
          <p className="herbal-caution">{localize(selectedHerb.caution, language)}</p>
        </>
      )}

      <footer className="herbal-footer">{copy.footer}</footer>
    </section>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="herbal-detail"><dt>{label}</dt><dd>{value}</dd></div>;
}
