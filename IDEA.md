# IDEA.md — Vivasayi Climate Guide

## One-line pitch
An AI assistant that fetches real weather forecasts and explains them to smallholder farmers in plain language, with a general preparedness checklist.

## Who it helps
Smallholder farmers in Tamil Nadu and similar regions who grow rain-dependent crops (rice, groundnut, cotton) and lack access to easy-to-understand weather guidance.

## The story
A farmer in Madurai plants groundnut and relies on monsoon rain. She can access weather apps, but the raw numbers — "38 °C max, 2 mm precipitation" — do not tell her whether to delay irrigation or watch for heat stress. Vivasayi Climate Guide translates that data into actionable language she can act on.

## The decision that must never be wrong
The weather data shown to the farmer must come from the real Open-Meteo API call, not from the model's memory or inference. The agent is constrained by its system prompt to call the tool first and base every claim on the tool's output.

## What will be measured
- Does the agent always call the weather tool? (tool-use recall)
- Does the response include the data source? (citation completeness)
- Does the response avoid inventing risk thresholds? (unsafe answer rate)
- Is the preparedness checklist present and reasonable? (completeness score)

## Languages
English (primary). Tamil translation is a stretch goal via Amazon Translate.

## Focus area
Climate resilience 🌍

## Scores (1–10)
| Quarter | Score | Rationale |
|---|---|---|
| Social impact | 8 | Addresses a real, measurable gap for a reachable user group |
| Technical execution | 7 | Real API + Strands agent; honest about limitations |
| Communication | 7 | Plain language, clear disclaimer, cites sources |
| Originality | 7 | Grounded in specific crop context and local geography |
| Buildable in days left | 9 | Minimal dependencies, no paid APIs required |

## Not this week
- Tamil UI translation
- SMS delivery via SNS
- Multi-crop comparison
- Historical climate trend analysis
