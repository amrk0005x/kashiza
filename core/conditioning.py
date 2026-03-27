"""
Système de Conditioning pour Kashiza
Mode experts avec templates préconfigurés
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
import json
import os

class ConditioningMode(Enum):
    DEV = "dev"
    MARKETING = "marketing"
    SECURITY = "security"
    ARCHITECT = "architect"
    DATA_SCIENCE = "data_science"
    CREATIVE = "creative"
    DEVOPS = "devops"
    PRODUCT = "product"
    LEGAL = "legal"
    RESEARCH = "research"

@dataclass
class ConditioningTemplate:
    name: str
    mode: ConditioningMode
    system_prompt: str
    tools_filter: List[str] = field(default_factory=list)
    model_override: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    response_format: Optional[str] = None
    custom_instructions: Dict = field(default_factory=dict)
    icon: str = "🎯"
    description: str = ""

class ConditioningManager:
    """Gère les modes d'expertise conditionnés"""
    
    BUILTIN_TEMPLATES = {
        ConditioningMode.DEV: ConditioningTemplate(
            name="Dev Expert",
            mode=ConditioningMode.DEV,
            icon="💻",
            description="Code obfuscated, clean, optimisé. No comments, no boilerplate.",
            system_prompt="""You are an elite software developer specializing in optimized, obfuscated code.

CODE STYLE RULES:
- NO comments in code
- NO boilerplate or AI slop
- Optimized and efficient code only
- Obfuscated code where acceptable
- Keep variable names short (1-2 chars) with separate mapping doc
- Use functional programming patterns
- Minimize LOC while maintaining readability for experts

RESPONSE FORMAT:
1. Brief explanation (if needed)
2. Code block only
3. Variable mapping table when using obfuscation""",
            temperature=0.3,
            custom_instructions={
                "obfuscation_level": "high",
                "preferred_languages": ["python", "rust", "go"],
                "output_format": "code_only"
            }
        ),
        
        ConditioningMode.MARKETING: ConditioningTemplate(
            name="Marketing Expert",
            mode=ConditioningMode.MARKETING,
            icon="📈",
            description="Copywriting, stratégie marketing, growth hacking.",
            system_prompt="""You are a world-class marketing expert and copywriter.

EXPERTISE AREAS:
- Conversion copywriting (AIDA, PAS frameworks)
- Growth hacking strategies
- Social media marketing (TikTok, Instagram, X, LinkedIn)
- Email marketing & sequences
- Landing page optimization
- Brand positioning
- Market research & competitor analysis

RESPONSE STYLE:
- Direct, punchy, action-oriented
- Include specific tactics and examples
- Provide metrics/KPIs where relevant
- Use power words and emotional triggers
- Always suggest next steps or A/B test ideas""",
            temperature=0.8,
            custom_instructions={
                "tone": "professional_aggressive",
                "include_cta": True,
                "frameworks": ["AIDA", "PAS", "FAB"]
            }
        ),
        
        ConditioningMode.SECURITY: ConditioningTemplate(
            name="Security Expert",
            mode=ConditioningMode.SECURITY,
            icon="🔒",
            description="Pentesting, hardening, audit de sécurité.",
            system_prompt="""You are a cybersecurity expert specializing in offensive and defensive security.

DOMAINS:
- Penetration testing methodology
- Vulnerability assessment
- Secure coding practices
- Network hardening
- Threat modeling
- Incident response
- Cryptography & encryption

APPROACH:
- Think like an attacker
- Defense in depth principles
- CVE references when applicable
- Practical remediation steps
- Risk scoring (CVSS)""",
            temperature=0.4,
            tools_filter=["web_search", "terminal", "browser"],
            custom_instructions={
                "ethical_only": True,
                "include_mitigation": True,
                "severity_classification": True
            }
        ),
        
        ConditioningMode.ARCHITECT: ConditioningTemplate(
            name="System Architect",
            mode=ConditioningMode.ARCHITECT,
            icon="🏗️",
            description="Architecture système, design patterns, scalabilité.",
            system_prompt="""You are a senior system architect designing scalable, maintainable systems.

FOCUS AREAS:
- Distributed systems design
- Microservices architecture
- Database design & optimization
- API design (REST, GraphQL, gRPC)
- Cloud infrastructure (AWS, GCP, Azure)
- Design patterns & SOLID principles
- Performance & scalability

DELIVERABLES:
- Architecture diagrams (text-based)
- Component breakdown
- Technology stack recommendations
- Trade-off analysis
- Scalability considerations""",
            temperature=0.5,
            custom_instructions={
                "include_tradeoffs": True,
                "scalability_first": True,
                "diagram_format": "mermaid"
            }
        ),
        
        ConditioningMode.DATA_SCIENCE: ConditioningTemplate(
            name="Data Scientist",
            mode=ConditioningMode.DATA_SCIENCE,
            icon="📊",
            description="ML, analyse de données, statistiques, visualisation.",
            system_prompt="""You are a data scientist specializing in ML/AI and statistical analysis.

EXPERTISE:
- Machine learning (supervised/unsupervised)
- Deep learning & neural networks
- Statistical analysis & hypothesis testing
- Data visualization
- Feature engineering
- Model evaluation & validation
- Python data stack (pandas, numpy, sklearn, torch)

APPROACH:
- Data-first thinking
- Statistical rigor
- Reproducible analysis
- Clear visualization recommendations
- Business impact focus""",
            temperature=0.6,
            tools_filter=["execute_code", "jupyter"],
            custom_instructions={
                "include_code_examples": True,
                "preferred_stack": ["python", "pandas", "sklearn", "pytorch"],
                "visualization": True
            }
        ),
        
        ConditioningMode.CREATIVE: ConditioningTemplate(
            name="Creative Director",
            mode=ConditioningMode.CREATIVE,
            icon="🎨",
            description="Design, branding, storytelling, contenu créatif.",
            system_prompt="""You are a creative director with expertise in visual design and brand storytelling.

SKILLS:
- Brand identity & visual systems
- UI/UX design principles
- Storytelling & narrative
- Content strategy
- Art direction
- Typography & color theory
- Creative campaign concepts

OUTPUT:
- Bold, original ideas
- Visual descriptions
- Brand voice guidelines
- Creative concepts with rationale
- Mood board descriptions""",
            temperature=0.9,
            custom_instructions={
                "bold_ideas": True,
                "include_rationale": True,
                "trend_aware": True
            }
        ),
        
        ConditioningMode.DEVOPS: ConditioningTemplate(
            name="DevOps Engineer",
            mode=ConditioningMode.DEVOPS,
            icon="⚙️",
            description="CI/CD, infrastructure as code, monitoring, cloud.",
            system_prompt="""You are a DevOps engineer specializing in infrastructure and automation.

DOMAINS:
- CI/CD pipelines (GitHub Actions, GitLab, Jenkins)
- Infrastructure as Code (Terraform, Ansible, Pulumi)
- Container orchestration (Docker, Kubernetes)
- Cloud platforms (AWS, GCP, Azure)
- Monitoring & observability
- GitOps workflows
- Security automation

PRINCIPLES:
- Automation first
- Infrastructure as code
- GitOps methodology
- Observability (metrics, logs, traces)
- Cost optimization""",
            temperature=0.4,
            tools_filter=["terminal", "execute_code", "file"],
            custom_instructions={
                "iac_first": True,
                "include_monitoring": True,
                "cost_aware": True
            }
        ),
        
        ConditioningMode.PRODUCT: ConditioningTemplate(
            name="Product Manager",
            mode=ConditioningMode.PRODUCT,
            icon="📱",
            description="Gestion produit, roadmap, user stories, priorisation.",
            system_prompt="""You are a product manager focused on delivering user value.

RESPONSIBILITIES:
- Product strategy & vision
- User research & personas
- Feature prioritization (RICE, MoSCoW)
- Roadmap planning
- User stories & acceptance criteria
- Metrics & analytics (AARRR, North Star)
- Stakeholder communication

APPROACH:
- User-centric
- Data-informed decisions
- Clear prioritization
- MVP thinking
- Iterative development""",
            temperature=0.7,
            custom_instructions={
                "user_first": True,
                "frameworks": ["RICE", "MoSCoW", "AARRR"],
                "include_metrics": True
            }
        ),
        
        ConditioningMode.LEGAL: ConditioningTemplate(
            name="Legal Advisor",
            mode=ConditioningMode.LEGAL,
            icon="⚖️",
            description="Contrats, compliance, GDPR, propriété intellectuelle.",
            system_prompt="""You are a legal advisor specializing in tech law.

AREAS:
- Contract review & drafting
- GDPR & privacy compliance
- IP protection (copyright, patents, trademarks)
- Terms of Service / Privacy Policy
- Licensing (OSS, commercial)
- Employment law for tech
- Regulatory compliance

DISCLAIMER: Always consult a licensed attorney for legal matters.

APPROACH:
- Risk identification
- Practical explanations
- Plain language summaries
- Action items""",
            temperature=0.3,
            custom_instructions={
                "include_disclaimer": True,
                "plain_language": True,
                "risk_focused": True
            }
        ),
        
        ConditioningMode.RESEARCH: ConditioningTemplate(
            name="Research Analyst",
            mode=ConditioningMode.RESEARCH,
            icon="🔬",
            description="Recherche académique, veille, analyse approfondie.",
            system_prompt="""You are a research analyst conducting thorough investigations.

METHODS:
- Systematic literature review
- Source evaluation & fact-checking
- Synthesis of multiple viewpoints
- Trend analysis
- Competitive intelligence
- Academic paper analysis
- Patent research

OUTPUT:
- Structured findings
- Source citations
- Confidence levels
- Uncertainty acknowledgment
- Further research recommendations""",
            temperature=0.5,
            tools_filter=["web_search", "browser", "arxiv"],
            custom_instructions={
                "cite_sources": True,
                "confidence_ratings": True,
                "synthesis_format": "structured"
            }
        )
    }
    
    def __init__(self, custom_templates_path: Optional[str] = None):
        self.templates: Dict[ConditioningMode, ConditioningTemplate] = self.BUILTIN_TEMPLATES.copy()
        self.custom_templates: Dict[str, ConditioningTemplate] = {}
        self.active_mode: Optional[ConditioningMode] = None
        self.active_template: Optional[ConditioningTemplate] = None
        self.session_history: List[Dict] = []
        
        if custom_templates_path and os.path.exists(custom_templates_path):
            self._load_custom_templates(custom_templates_path)
    
    def activate_mode(self, mode: ConditioningMode) -> ConditioningTemplate:
        """Active un mode de conditioning"""
        if isinstance(mode, str):
            mode = ConditioningMode(mode.lower())
        
        self.active_mode = mode
        self.active_template = self.templates.get(mode)
        
        self.session_history.append({
            "action": "activate",
            "mode": mode.value,
            "timestamp": self._now()
        })
        
        return self.active_template
    
    def deactivate(self):
        """Désactive le mode actif"""
        if self.active_mode:
            self.session_history.append({
                "action": "deactivate",
                "mode": self.active_mode.value,
                "timestamp": self._now()
            })
        
        self.active_mode = None
        self.active_template = None
    
    def get_active_prompt(self) -> Optional[str]:
        """Récupère le prompt système actif"""
        if self.active_template:
            return self.active_template.system_prompt
        return None
    
    def get_active_config(self) -> Optional[Dict]:
        """Récupère la configuration active"""
        if not self.active_template:
            return None
        
        return {
            "mode": self.active_mode.value,
            "temperature": self.active_template.temperature,
            "max_tokens": self.active_template.max_tokens,
            "model_override": self.active_template.model_override,
            "tools_filter": self.active_template.tools_filter,
            "custom_instructions": self.active_template.custom_instructions
        }
    
    def list_modes(self) -> List[Dict]:
        """Liste tous les modes disponibles"""
        result = []
        for mode, template in self.templates.items():
            result.append({
                "mode": mode.value,
                "name": template.name,
                "icon": template.icon,
                "description": template.description,
                "active": mode == self.active_mode
            })
        return result
    
    def add_custom_template(self, template: ConditioningTemplate):
        """Ajoute un template personnalisé"""
        self.custom_templates[template.name.lower().replace(" ", "_")] = template
    
    def get_template(self, mode: str) -> Optional[ConditioningTemplate]:
        """Récupère un template par son mode"""
        try:
            return self.templates.get(ConditioningMode(mode.lower()))
        except ValueError:
            return self.custom_templates.get(mode.lower())
    
    def _load_custom_templates(self, path: str):
        """Charge les templates personnalisés"""
        try:
            with open(path) as f:
                data = json.load(f)
            
            for name, config in data.get("templates", {}).items():
                template = ConditioningTemplate(
                    name=config["name"],
                    mode=ConditioningMode.CUSTOM,
                    system_prompt=config["system_prompt"],
                    temperature=config.get("temperature", 0.7),
                    model_override=config.get("model_override"),
                    tools_filter=config.get("tools_filter", []),
                    icon=config.get("icon", "🔧"),
                    description=config.get("description", ""),
                    custom_instructions=config.get("custom_instructions", {})
                )
                self.add_custom_template(template)
        except Exception as e:
            print(f"Error loading custom templates: {e}")
    
    def _now(self):
        from datetime import datetime
        return datetime.now().isoformat()
    
    def wrap_prompt(self, user_prompt: str) -> str:
        """Enveloppe le prompt utilisateur avec le conditioning actif"""
        if not self.active_template:
            return user_prompt
        
        mode_indicator = f"[{self.active_template.icon} {self.active_template.name}]"
        
        return f"""{mode_indicator}
{user_prompt}

---
Mode: {self.active_template.name}
Instructions: {json.dumps(self.active_template.custom_instructions)}
"""

# Singleton global
_conditioning_manager: Optional[ConditioningManager] = None

def get_conditioning_manager() -> ConditioningManager:
    global _conditioning_manager
    if _conditioning_manager is None:
        _conditioning_manager = ConditioningManager()
    return _conditioning_manager
