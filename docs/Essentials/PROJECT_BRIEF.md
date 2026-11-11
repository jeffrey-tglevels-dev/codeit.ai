# Project Brief: Multi-Agent Coding System (codeit.ai)

## Problem
Building a quick, custom, good-quality application with a modular codebase takes time and skill.

## Solution
A multi-agent coding system that takes a simple request (for example "build a todo app") and delivers a working, tested application with a clean, layered codebase:
- a **source ZIP**, which includes a `Dockerfile` so tech-savvy users can build and deploy it themselves, and
- a **live local preview** of the app running in a Docker container.

## Goal
Learning multi-agent orchestration first, while keeping the design able to grow into a reliable tool (agents sit behind typed models, so any of them can later be replaced by templates or code).

## Target users
- **Long term:** non-technical users (primarily) and technical users who want something to get started with.
- **v1:** a single local operator using the dev console. There is no end-user product UI, login or hosting in v1.

## Success criteria
A simple working app with a frontend (HTML + CSS + JS) and a backend (FastAPI + SQLAlchemy 2.0 + SQLite), passing its generated tests, delivered as a ZIP plus a healthy preview URL.

## Platform
Web application: a FastAPI backend with a static HTML/JS dev console, run locally.

## Initial constraints
- Generated apps have **no authentication or role-based access** in v1 (recorded in `out_of_scope`).
- Agents are built on **CrewAI**; LLMs come from **OpenRouter**.
- Fixed generated-app stack; no packages beyond the sandbox base image.

See [`MVP_DEFINITION.md`](MVP_DEFINITION.md) for exact v1 scope and [`docs/architecture.md`](../architecture.md) for the design.
