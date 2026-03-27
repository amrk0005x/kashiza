import json
import os
import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import requests

@dataclass
class AgentPack:
    id: str
    name: str
    description: str
    author: str
    version: str
    price: float
    category: str
    tags: List[str]
    files: Dict[str, str]
    requirements: List[str]
    rating: float = 0.0
    downloads: int = 0
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class AgentMarket:
    def __init__(self, local_path: str = "~/.kashiza/market"):
        self.local_path = Path(local_path).expanduser()
        self.local_path.mkdir(parents=True, exist_ok=True)
        self.installed_path = self.local_path / "installed"
        self.installed_path.mkdir(exist_ok=True)
        
        self.packs: Dict[str, AgentPack] = {}
        self.registry_url = "https://api.kashiza-market.dev"
        
        self._load_installed()
        self._load_built_in()
    
    def _load_installed(self):
        for pack_file in self.installed_path.glob("*.json"):
            try:
                with open(pack_file) as f:
                    data = json.load(f)
                    pack = AgentPack(**data)
                    self.packs[pack.id] = pack
            except:
                pass
    
    def _load_built_in(self):
        # Built-in packs
        built_in = [
            AgentPack(
                id="web_developer_pro",
                name="Web Developer Pro",
                description="Full-stack web development pack with React, Node, Python expertise",
                author="Hermes Team",
                version="1.0.0",
                price=49.0,
                category="development",
                tags=["web", "react", "node", "python", "fullstack"],
                files={},
                requirements=["nodejs", "python"]
            ),
            AgentPack(
                id="data_scientist",
                name="Data Scientist Suite",
                description="ML pipelines, data analysis, visualization agents",
                author="Hermes Team",
                version="1.0.0",
                price=79.0,
                category="data",
                tags=["ml", "python", "pandas", "pytorch", "jupyter"],
                files={},
                requirements=["python", "cuda"]
            ),
            AgentPack(
                id="devops_master",
                name="DevOps Master",
                description="CI/CD, Docker, K8s, Terraform automation agents",
                author="Hermes Team",
                version="1.0.0",
                price=59.0,
                category="devops",
                tags=["docker", "kubernetes", "terraform", "aws", "cicd"],
                files={},
                requirements=["docker", "kubectl"]
            ),
            AgentPack(
                id="security_auditor",
                name="Security Auditor",
                description="Security scanning, vulnerability detection, compliance checks",
                author="Hermes Team",
                version="1.0.0",
                price=99.0,
                category="security",
                tags=["security", "audit", "penetration", "compliance"],
                files={},
                requirements=["python"]
            ),
            AgentPack(
                id="mobile_developer",
                name="Mobile Developer",
                description="iOS and Android development agents with Flutter/React Native",
                author="Hermes Team",
                version="1.0.0",
                price=69.0,
                category="mobile",
                tags=["flutter", "react-native", "ios", "android", "mobile"],
                files={},
                requirements=["flutter", "android-studio"]
            ),
            AgentPack(
                id="blockchain_builder",
                name="Blockchain Builder",
                description="Smart contracts, Web3, DeFi development agents",
                author="Hermes Team",
                version="1.0.0",
                price=129.0,
                category="blockchain",
                tags=["solidity", "ethereum", "web3", "defi", "smart-contracts"],
                files={},
                requirements=["nodejs", "hardhat"]
            ),
        ]
        
        for pack in built_in:
            if pack.id not in self.packs:
                self.packs[pack.id] = pack
    
    def search(self, query: str = None, category: str = None, 
               tags: List[str] = None, max_price: float = None) -> List[AgentPack]:
        results = []
        
        for pack in self.packs.values():
            if query and query.lower() not in pack.name.lower() and query.lower() not in pack.description.lower():
                continue
            if category and pack.category != category:
                continue
            if tags and not any(t in pack.tags for t in tags):
                continue
            if max_price is not None and pack.price > max_price:
                continue
            results.append(pack)
        
        return sorted(results, key=lambda x: (x.rating, x.downloads), reverse=True)
    
    def get_pack(self, pack_id: str) -> Optional[AgentPack]:
        return self.packs.get(pack_id)
    
    def install(self, pack_id: str) -> Dict:
        pack = self.packs.get(pack_id)
        if not pack:
            return {'success': False, 'error': 'Pack not found'}
        
        try:
            # Download if from remote
            if pack.files == {}:
                pack = self._download_pack(pack_id)
            
            # Save to installed
            pack_file = self.installed_path / f"{pack_id}.json"
            with open(pack_file, 'w') as f:
                json.dump(asdict(pack), f, indent=2)
            
            pack.downloads += 1
            return {'success': True, 'pack': pack}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _download_pack(self, pack_id: str) -> AgentPack:
        # Simulate download from registry
        # In production, this would fetch from the actual API
        pack = self.packs[pack_id]
        
        # Generate placeholder files
        pack.files = {
            'agents/__init__.py': '# Agent pack\n',
            'agents/coder.py': '# Coder agent\n',
            'config.yaml': f'name: {pack.name}\nversion: {pack.version}\n'
        }
        
        return pack
    
    def uninstall(self, pack_id: str) -> Dict:
        pack_file = self.installed_path / f"{pack_id}.json"
        if pack_file.exists():
            pack_file.unlink()
            return {'success': True}
        return {'success': False, 'error': 'Pack not installed'}
    
    def list_installed(self) -> List[AgentPack]:
        installed = []
        for pack_file in self.installed_path.glob("*.json"):
            try:
                with open(pack_file) as f:
                    data = json.load(f)
                    installed.append(AgentPack(**data))
            except:
                pass
        return installed
    
    def rate_pack(self, pack_id: str, rating: int, review: str = ""):
        pack = self.packs.get(pack_id)
        if pack:
            # Simple averaging
            pack.rating = (pack.rating * pack.downloads + rating) / (pack.downloads + 1)
            
            # Save review
            reviews_file = self.local_path / "reviews.json"
            reviews = []
            if reviews_file.exists():
                with open(reviews_file) as f:
                    reviews = json.load(f)
            
            reviews.append({
                'pack_id': pack_id,
                'rating': rating,
                'review': review,
                'date': datetime.now().isoformat()
            })
            
            with open(reviews_file, 'w') as f:
                json.dump(reviews, f, indent=2)
    
    def publish_pack(self, pack: AgentPack, api_key: str) -> Dict:
        # In production, upload to registry
        return {'success': True, 'message': 'Pack submitted for review'}
    
    def create_pack(self, name: str, description: str, category: str,
                    source_path: str, price: float = 0.0) -> str:
        source = Path(source_path).expanduser()
        
        files = {}
        for filepath in source.rglob('*'):
            if filepath.is_file():
                relative = filepath.relative_to(source)
                try:
                    files[str(relative)] = filepath.read_text()
                except:
                    files[str(relative)] = "# Binary file"
        
        pack_id = hashlib.md5(f"{name}{datetime.now()}".encode()).hexdigest()[:12]
        
        pack = AgentPack(
            id=pack_id,
            name=name,
            description=description,
            author="local",
            version="1.0.0",
            price=price,
            category=category,
            tags=[],
            files=files,
            requirements=[]
        )
        
        self.packs[pack_id] = pack
        return pack_id
    
    def get_categories(self) -> List[str]:
        categories = set()
        for pack in self.packs.values():
            categories.add(pack.category)
        return sorted(categories)

class PackInstaller:
    def __init__(self, market: AgentMarket):
        self.market = market
    
    def install_with_dependencies(self, pack_id: str) -> Dict:
        pack = self.market.get_pack(pack_id)
        if not pack:
            return {'success': False, 'error': 'Pack not found'}
        
        # Check requirements
        missing = self._check_requirements(pack.requirements)
        if missing:
            return {
                'success': False,
                'error': f'Missing requirements: {missing}',
                'install_commands': self._get_install_commands(missing)
            }
        
        # Install pack
        return self.market.install(pack_id)
    
    def _check_requirements(self, requirements: List[str]) -> List[str]:
        missing = []
        for req in requirements:
            if not self._is_installed(req):
                missing.append(req)
        return missing
    
    def _is_installed(self, requirement: str) -> bool:
        # Check if requirement is installed
        checks = {
            'python': 'python3 --version',
            'nodejs': 'node --version',
            'docker': 'docker --version',
            'kubectl': 'kubectl version --client',
            'flutter': 'flutter --version',
            'cuda': 'nvidia-smi',
        }
        
        if requirement in checks:
            return os.system(f"{checks[requirement]} > /dev/null 2>&1") == 0
        return True
    
    def _get_install_commands(self, missing: List[str]) -> Dict[str, str]:
        commands = {
            'python': 'sudo apt-get install python3 python3-pip',
            'nodejs': 'curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs',
            'docker': 'curl -fsSL https://get.docker.com | sh',
            'kubectl': 'curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl',
            'flutter': 'git clone https://github.com/flutter/flutter.git -b stable && export PATH="$PATH:`pwd`/flutter/bin"',
        }
        
        return {req: commands.get(req, f"# Install {req} manually") for req in missing}
