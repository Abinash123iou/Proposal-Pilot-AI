Project Name:
ProposalPilot AI

Project Type:
AI-Powered Autonomous Proposal Generation Platform (Micro SaaS MVP)

Purpose:
A backend application that autonomously analyzes client requirements, creates an execution plan, generates professional business proposals, performs self-validation, and exports polished Microsoft Word (.docx) documents through a REST API.

Assessment Duration:
60-Minute Build Challenge (Built using a production-ready engineering approach)

Tech Stack
Backend
Python 3.12
FastAPI
Uvicorn
Pydantic
Loguru
python-dotenv

AI
Groq API (Free Tier)
LangGraph
LangChain (Utilities)
Document Generation
python-docx
Testing
Pytest
HTTPX
Architecture
API Layer
Controller Layer
Service Layer
Agent Layer
Tool Layer
Prompt Layer
Utility Layer
Configuration Layer
Exception Layer

AI Agent Workflow
User Request

↓

Request Validation

↓

Planner Agent

↓

Execution Agent

↓

Proposal Strategy Generator

↓

Reflection Agent

↓

Document Generator

↓

API Response
Functional Requirements
Core Features
Accept natural language business requests.
Analyze client requirements.
Generate an autonomous execution plan.
Create task/TODO list automatically.
Generate professional proposal content.
Estimate project scope.
Generate realistic project timeline.
Generate budget estimation.
Generate assumptions.
Generate project risks.
Perform proposal quality review.
Generate Microsoft Word (.docx) proposal.
Return structured API response.
Engineering Feature (Assignment Requirement)

Implement:

Reflection / Self-Check Agent

Responsibilities:

Validate proposal completeness
Detect missing sections
Verify consistency
Improve proposal quality before export
API Endpoints
Core
POST /agent
GET /health
Future Ready
POST /proposal/regenerate
GET /proposal/{proposal_id}
GET /agent/status
Coding Standards
Production-quality code
Clean Architecture
SOLID principles where applicable
Human-readable code
Clear naming conventions
Type hints throughout
Small focused classes and functions
Dependency injection where appropriate
Async/Await
Consistent API responses
Centralized configuration
Professional folder structure
Scalable architecture
Reusable services
Proper logging
Robust error handling
Comments Policy
Comment only where business logic is not obvious
Avoid redundant comments
Prefer self-explanatory code
Keep comments meaningful and concise
Expected Output

For every request, generate only:

Folder location
Code
Explanation
Required dependencies (if any)
Testing instructions
Suggested Git commit message

Important

Generate only the requested file or module.
Never generate the entire project at once.
Wait for the next instruction before proceeding.
Maintain consistency with the existing project architecture.
Do not modify unrelated modules.
Git Workflow Requirements
Every completed module must result in a Git commit.
Suggest a professional commit message after every completed task.
Follow Conventional Commits.

Allowed prefixes:

feat:
fix:
refactor:
docs:
test:
chore:

After each completed module:

git add .
git commit -m "<commit-message>"
git push origin main

Maintain a clean and professional commit history.

Ideal Commit History
chore: initialize ProposalPilot AI backend

feat: setup FastAPI application structure

feat: configure environment and application settings

feat: implement centralized logging

feat: integrate Gemini AI service

feat: implement planner agent

feat: implement execution agent

feat: implement reflection agent

feat: add proposal document generator

feat: implement agent orchestration service

feat: add proposal generation API

feat: implement request validation and exception handling

test: add API integration tests

docs: update README and API usage