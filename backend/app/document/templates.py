# Ordered list of sections to export to the final Word document.
# Note: Cover Page and Table of Contents are added separately at the beginning.
STANDARD_SECTIONS = [
    "Executive Summary",
    "Client Requirements",
    "Project Objectives",
    "Scope of Work",
    "Functional Modules",
    "Technology Stack",
    "System Architecture",
    "Project Timeline",
    "Budget Estimation",
    "Risks",
    "Assumptions",
    "Conclusion"
]

# Case-insensitive synonym lists to match generated state keys to standard sections.
SECTION_SYNONYMS = {
    "Executive Summary": ["executive summary", "exec summary", "summary"],
    "Client Requirements": ["client requirements", "requirements", "client needs", "need assessment"],
    "Project Objectives": ["project objectives", "objectives", "goals", "project goals"],
    "Scope of Work": ["scope of work", "scope", "project scope"],
    "Functional Modules": ["functional modules", "modules", "features", "functional requirements", "system features"],
    "Technology Stack": ["technology stack", "tech stack", "technologies", "technology stack details"],
    "System Architecture": ["system architecture", "architecture", "system design", "technical architecture"],
    "Project Timeline": ["project timeline", "timeline", "schedule", "implementation timeline"],
    "Budget Estimation": ["budget estimation", "budget", "cost", "pricing", "financials", "cost estimation"],
    "Risks": ["risks", "risk", "risk assessment", "risk management", "mitigations"],
    "Assumptions": ["assumptions", "dependencies", "assumptions and dependencies"],
    "Conclusion": ["conclusion", "next steps", "concluding remarks"]
}
