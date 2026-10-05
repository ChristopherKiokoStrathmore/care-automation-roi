"use client";

import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";

import {
  CURRENCY_LABEL,
  DEFAULT_DRAFT,
  GITHUB_REPO,
  cloneDraft,
  draftsEqual,
  type AssumptionDraft,
} from "@/lib/assumptions";
import { fmtRate } from "@/lib/decimal-util";
import { committedHeadlineMatch, evaluate } from "@/lib/evaluate";

import { DemoView } from "./demo-studio";
import { WriteUp } from "./write-up";

type View = "demo" | "writeup";

function viewFromHash(): View {
  if (typeof window === "undefined") return "demo";
  return window.location.hash === "#write-up" ? "writeup" : "demo";
}

export function Calculator() {
  const [draft, setDraft] = useState<AssumptionDraft>(() => cloneDraft());
  const [selectedId, setSelectedId] = useState("bot_base");
  const [view, setView] = useState<View>("demo");
  const evaluation = useMemo(() => evaluate(draft), [draft]);
  const edited = !draftsEqual(draft, DEFAULT_DRAFT);
  const shares = evaluation.ok
    ? Object.fromEntries(Object.entries(evaluation.result.intentShares).map(([intent, share]) => [intent, fmtRate(share)]))
    : null;
  const headlinesMatch = evaluation.ok && committedHeadlineMatch(evaluation.result);

  useEffect(() => {
    const sync = () => setView(viewFromHash());
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  const skipScroll = useRef(true);

  useEffect(() => {
    if (skipScroll.current) {
      skipScroll.current = false;
      return;
    }
    document.getElementById(view === "writeup" ? "write-up" : "panel-demo")?.scrollIntoView({ block: "start" });
  }, [view]);

  const choose = (next: View) => {
    setView(next);
    const hash = next === "writeup" ? "#write-up" : "#demo";
    if (window.location.hash !== hash) {
      history.replaceState(null, "", hash);
    }
  };

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
    event.preventDefault();
    choose(view === "demo" ? "writeup" : "demo");
  };

  const reset = () => {
    setDraft(cloneDraft(DEFAULT_DRAFT));
    setSelectedId("bot_base");
  };

  return (
    <main id="demo">
      <header className="demo-intro wrap">
        <p className="kicker">Illustrative cost-benefit</p>
        <h1>Contact-centre automation ROI</h1>
        <p className="lede">
          Change containment, volume, wages, or build cost. Payback, year-1 ROI, the six scenarios, and the sensitivity tornado recompute from the same formulas as the Python model.
        </p>
      </header>

      <div className="app-nav wrap">
        <div className="tabs" role="tablist" aria-label="Site sections" onKeyDown={onKeyDown}>
          <button
            type="button"
            className="tab"
            role="tab"
            id="tab-demo"
            aria-controls="panel-demo"
            aria-selected={view === "demo"}
            tabIndex={view === "demo" ? 0 : -1}
            onClick={() => choose("demo")}
          >
            Demo
          </button>
          <button
            type="button"
            className="tab"
            role="tab"
            id="tab-writeup"
            aria-controls="write-up"
            aria-selected={view === "writeup"}
            tabIndex={view === "writeup" ? 0 : -1}
            onClick={() => choose("writeup")}
          >
            Write-up
          </button>
        </div>
        <button type="button" className="button" onClick={reset} disabled={!edited}>
          Reset to committed inputs
        </button>
      </div>

      {view === "demo" ? (
        <DemoView
          draft={draft}
          result={evaluation.ok ? evaluation.result : null}
          message={evaluation.ok ? null : evaluation.message}
          selectedId={selectedId}
          edited={edited}
          headlinesMatch={headlinesMatch}
          swing={draft.sensitivity_relative_swing}
          shares={shares}
          onDraft={setDraft}
          onSelect={setSelectedId}
          onReset={reset}
        />
      ) : (
        <WriteUp
          result={evaluation.ok ? evaluation.result : null}
          message={evaluation.ok ? null : evaluation.message}
          selectedId={selectedId}
          edited={edited}
          headlinesMatch={headlinesMatch}
          swing={draft.sensitivity_relative_swing}
          onSelect={setSelectedId}
          onShowDemo={() => choose("demo")}
        />
      )}

      <footer className="footer wrap">
        <p>Illustrative inputs. Currency is {CURRENCY_LABEL}.</p>
        <a href={GITHUB_REPO}>github.com/ChristopherKiokoStrathmore/care-automation-roi</a>
      </footer>
    </main>
  );
}
