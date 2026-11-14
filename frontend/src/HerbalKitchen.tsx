import { useState } from "react";
import { ArrowLeft, ArrowRight, Leaf } from "lucide-react";
import data from "./data/herbal_kitchen.json";
import strings from "./data/herbal_kitchen_strings.json";
import type { Language } from "./api";

const SHOW_DRAFTS = true;
const ACCEPTED_KEY = "nutribot-herbal-kitchen-welcome";

type NameSet = { id: string; zh: string; en: string; latin: string };
type Herb = {
  id: string; tier: "A" | "B"; status: string; names: NameSet; look: string;
  whereToBuy: string; preparation: string; amountPerServing: string;
  goodIn: string[]; substitutes: string; sources: string[]; checkedOn: string;
};
type Dish = { id: string; status: string; name: string; type: string; serves: string | number; minutes: string | number; steps: string[] };
type KitchenCopy = typeof strings.en;
type View = { kind: "list" } | { kind: "herb"; herbId: string } | { kind: "dish"; dishId: string };

const herbs = (data.herbs as Herb[]).filter((herb) => herb.status === "published" || SHOW_DRAFTS && herb.status === "draft");
const dishes = (data.dishes as Dish[]).filter((dish) => dish.status === "published" || SHOW_DRAFTS && dish.status === "draft");
const links = data.links;

function readAcceptance(): boolean {
  try { return localStorage.getItem(ACCEPTED_KEY) === "yes"; } catch { return false; }
}

export default function HerbalKitchen({ language }: { language: Language }) {
  const [view, setView] = useState<View>({ kind: "list" });
  const [accepted, setAccepted] = useState(readAcceptance);
  const copy: KitchenCopy = strings[language] ?? strings.en;
  const selectedHerb = view.kind === "herb" ? herbs.find((herb) => herb.id === view.herbId) : undefined;
  const selectedDish = view.kind === "dish" ? dishes.find((dish) => dish.id === view.dishId) : undefined;
  const label = (names: NameSet) => names[language] || names.en;

  function acceptWelcome() {
    try { localStorage.setItem(ACCEPTED_KEY, "yes"); } catch { /* The notice remains dismissible for this session. */ }
    setAccepted(true);
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

      {view.kind !== "list" && (
        <button className="secondary-button herbal-back herbal-tap-target" onClick={() => setView({ kind: "list" })} type="button">
          <ArrowLeft size={18} />{copy.back}
        </button>
      )}

      {view.kind === "list" && (
        <>
          <div className="screen-heading herbal-heading"><p className="eyebrow">{copy.tab}</p><h1>{copy.tab}</h1></div>
          <div className="herbal-card-list">
            {herbs.map((herb) => (
              <button className="herbal-card herbal-tap-target" key={herb.id} onClick={() => setView({ kind: "herb", herbId: herb.id })} type="button">
                <span className="herbal-card-title"><Leaf size={18} />{label(herb.names)}</span>
                {SHOW_DRAFTS && herb.status === "draft" && <span className="draft-badge">{copy.draftBadge}</span>}
                <span className="herbal-card-date">{copy.checkedOn}: {herb.checkedOn}</span>
              </button>
            ))}
          </div>
        </>
      )}

      {view.kind === "herb" && selectedHerb && (
        <>
          <div className="screen-heading herbal-heading"><h1>{label(selectedHerb.names)}</h1><p className="herbal-latin">{selectedHerb.names.latin}</p>
            {SHOW_DRAFTS && selectedHerb.status === "draft" && <span className="draft-badge">{copy.draftBadge}</span>}
            <p className="herbal-card-date">{copy.checkedOn}: {selectedHerb.checkedOn}</p>
          </div>
          <p className="herbal-caution">{copy.caution}</p>
          {selectedHerb.tier === "B" && <p className="herbal-notice">{copy.infoOnly}</p>}
          <dl className="herbal-details">
            <Detail label={copy.look} value={selectedHerb.look} />
            <Detail label={copy.whereToBuy} value={selectedHerb.whereToBuy} />
            <Detail label={copy.preparation} value={selectedHerb.preparation} />
            <Detail label={copy.amountPerServing} value={selectedHerb.amountPerServing} />
            <Detail label={copy.substitutes} value={selectedHerb.substitutes} />
            <Detail label={copy.sources} value={selectedHerb.sources.join(" · ")} />
          </dl>
          {selectedHerb.tier === "A" && (
            <>
              <h2 className="herbal-section-title">{copy.tab}</h2>
              <div className="herbal-card-list">
                {dishes.filter((dish) => links.some((link) => link.herbId === selectedHerb.id && link.dishId === dish.id)).map((dish) => (
                  <button className="herbal-card herbal-tap-target" key={dish.id} onClick={() => setView({ kind: "dish", dishId: dish.id })} type="button">
                    <span className="herbal-card-title">{dish.name}<ArrowRight size={18} /></span>
                    {SHOW_DRAFTS && dish.status === "draft" && <span className="draft-badge">{copy.draftBadge}</span>}
                  </button>
                ))}
                {selectedHerb.goodIn.length === 0 && <p className="herbal-muted">{copy.noDishes}</p>}
              </div>
            </>
          )}
        </>
      )}

      {view.kind === "dish" && selectedDish && (
        <>
          <div className="screen-heading herbal-heading"><h1>{selectedDish.name}</h1>
            {SHOW_DRAFTS && selectedDish.status === "draft" && <span className="draft-badge">{copy.draftBadge}</span>}
            <p className="herbal-card-date">{copy.checkedOn}: {herbs.find((herb) => links.some((link) => link.dishId === selectedDish.id && link.herbId === herb.id))?.checkedOn}</p>
          </div>
          <p className="herbal-caution">{copy.caution}</p>
          <p className="herbal-meta">{selectedDish.type} · {copy.serves}: {selectedDish.serves} · {copy.minutes}: {selectedDish.minutes}</p>
          <h2 className="herbal-section-title">{copy.ingredients}</h2>
          <div className="herbal-card-list">
            {links.filter((link) => link.dishId === selectedDish.id).map((link) => {
              const herb = herbs.find((item) => item.id === link.herbId);
              if (!herb || herb.tier === "B") return null;
              return <article className="herbal-info-card" key={link.herbId}><strong>{label(herb.names)}</strong><p>{link.amount}</p></article>;
            })}
          </div>
          <h2 className="herbal-section-title">{copy.steps}</h2>
          <ol className="herbal-steps">{selectedDish.steps.map((step, index) => <li key={`${index}-${step}`}>{step}</li>)}</ol>
        </>
      )}

      <footer className="herbal-footer">{copy.footer}</footer>
    </section>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="herbal-detail"><dt>{label}</dt><dd>{value}</dd></div>;
}
