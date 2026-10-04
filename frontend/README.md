# Frontend Application (React + Vite)

## Overview
This directory contains the future React + Vite demonstration and evaluation UI for the Proposition-Level ASAG research project.

## Architecture
- **Completely Independent**: The frontend contains zero NLP models or python dependencies.
- **API-Driven**: All grading and comparison actions interact with the Python backend API (`POST /api/grade`, `GET /api/models`).
- **Pages**:
  - `Home`: Project introduction and thesis research question overview.
  - `Grading`: Interactive short answer grading interface with model selector (V0–V5).
  - `Model Comparison`: Side-by-side evaluation comparison across all 6 model versions.
  - `Explanation Trace`: Visual audit graph showing proposition extraction, alignment, and score adjustments.
  - `Research Results`: Interactive charts and tables of the Mohler benchmark evaluation.

## Deployment (Vercel)
Configured for automatic deployment to Vercel via `vercel.json` and `vite.config.js`.
Build command: `npm run build`
Output directory: `dist`
