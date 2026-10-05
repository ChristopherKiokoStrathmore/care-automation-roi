# Care automation ROI demo

Next.js App Router frontend for the cost-benefit model in the parent repository. The page opens on the interactive demo: sliders and inputs recompute scenarios, payback, year-1 ROI, and the sensitivity tornado from the formulas in `care_roi/`. The write-up is the other tab.

Illustrative inputs. Currency is KES (illustrative).

Live site: [https://care-automation-roi.vercel.app](https://care-automation-roi.vercel.app)

## Run

```bash
npm install
npm run verify
npm run dev
```

`npm run verify` checks the default case against `../reports/` (base-case payback 8.47 months, year-1 ROI 0.4175, low-containment year-1 ROI -0.1571).

## Deploy

On Vercel, set the project **Root Directory** to `web`. The framework preset is Next.js. `npm run build` is the production build.
