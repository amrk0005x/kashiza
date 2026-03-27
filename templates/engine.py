import os
import json
import shutil
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass
import re

@dataclass
class ProjectTemplate:
    id: str
    name: str
    description: str
    category: str
    files: Dict[str, str]
    variables: List[str]
    post_setup_commands: List[str]
    dependencies: Dict[str, List[str]]

class TemplateEngine:
    TEMPLATES = {
        'web_api': ProjectTemplate(
            id='web_api',
            name='REST API (FastAPI)',
            description='Production-ready FastAPI REST API with auth, DB, tests',
            category='backend',
            files={
                'main.py': '''from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="{{project_name}}", version="0.1.0")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Item(BaseModel):
    name: str
    description: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "Welcome to {{project_name}}"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.post("/items/")
def create_item(item: Item):
    return item

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
''',
                'requirements.txt': '''fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
sqlalchemy==2.0.23
alembic==1.12.1
pytest==7.4.3
httpx==0.25.2
''',
                'Dockerfile': '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
                'docker-compose.yml': '''version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/{{project_name}}
    depends_on:
      - db
  
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB={{project_name}}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
''',
                'tests/test_main.py': '''from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_create_item():
    response = client.post("/items/", json={"name": "Test", "description": "Test item"})
    assert response.status_code == 200
    assert response.json()["name"] == "Test"
''',
                '.env.example': '''DATABASE_URL=postgresql://user:pass@localhost:5432/{{project_name}}
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
''',
                'README.md': '''# {{project_name}}

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and configure

3. Run:
   ```bash
   uvicorn main:app --reload
   ```

## Docker

```bash
docker-compose up -d
```

## Tests

```bash
pytest
```
'''
            },
            variables=['project_name'],
            post_setup_commands=['mkdir -p tests', 'cp .env.example .env'],
            dependencies={'python': ['>=3.9'], 'docker': ['>=20.0']}
        ),
        
        'react_app': ProjectTemplate(
            id='react_app',
            name='React + TypeScript App',
            description='Modern React app with TypeScript, Vite, Tailwind',
            category='frontend',
            files={
                'package.json': '''{
  "name": "{{project_name}}",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@typescript-eslint/eslint-plugin": "^6.10.0",
    "@typescript-eslint/parser": "^6.10.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.53.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.4",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.2.2",
    "vite": "^5.0.0",
    "vitest": "^1.0.0"
  }
}
''',
                'index.html': '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{project_name}}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
''',
                'tailwind.config.js': '''/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
''',
                'postcss.config.js': '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
''',
                'tsconfig.json': '''{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
''',
                'src/main.tsx': '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
''',
                'src/App.tsx': '''import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </Router>
  )
}

export default App
''',
                'src/pages/Home.tsx': '''export default function Home() {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-lg">
        <h1 className="text-3xl font-bold text-gray-800">{{project_name}}</h1>
        <p className="mt-4 text-gray-600">Welcome to your new React app!</p>
      </div>
    </div>
  )
}
''',
                'src/index.css': '''@tailwind base;
@tailwind components;
@tailwind utilities;
''',
                'vite.config.ts': '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
''',
                'README.md': '''# {{project_name}}

## Setup

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Test

```bash
npm run test
```
'''
            },
            variables=['project_name'],
            post_setup_commands=['npm install'],
            dependencies={'node': ['>=18.0'], 'npm': ['>=9.0']}
        ),
        
        'python_cli': ProjectTemplate(
            id='python_cli',
            name='Python CLI Tool',
            description='CLI tool with Click, rich output, config management',
            category='cli',
            files={
                '{{project_name}}/__init__.py': '''__version__ = "0.1.0"
''',
                '{{project_name}}/cli.py': '''import click
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
@click.version_option(version=__version__)
def cli():
    """{{project_name}} CLI tool"""
    pass

@cli.command()
@click.argument('name')
def greet(name):
    """Greet someone"""
    console.print(f"[green]Hello, {name}![/green]")

@cli.command()
def status():
    """Show status"""
    table = Table(title="System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_row("API", "[green]Online[/green]")
    table.add_row("Database", "[green]Connected[/green]")
    console.print(table)

if __name__ == '__main__':
    cli()
''',
                '{{project_name}}/config.py': '''import os
from pathlib import Path

CONFIG_DIR = Path.home() / '.config' / '{{project_name}}'
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    API_URL = os.getenv('API_URL', 'https://api.example.com')
    API_KEY = os.getenv('API_KEY', '')
    
    @classmethod
    def load(cls):
        config_file = CONFIG_DIR / 'config.json'
        if config_file.exists():
            import json
            with open(config_file) as f:
                data = json.load(f)
                for key, value in data.items():
                    setattr(cls, key, value)
    
    @classmethod
    def save(cls):
        config_file = CONFIG_DIR / 'config.json'
        with open(config_file, 'w') as f:
            json.dump({k: v for k, v in cls.__dict__.items() if not k.startswith('_')}, f)
''',
                'setup.py': '''from setuptools import setup, find_packages

setup(
    name='{{project_name}}',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'click>=8.0.0',
        'rich>=13.0.0',
        'requests>=2.28.0',
    ],
    entry_points={
        'console_scripts': [
            '{{project_name}}={{project_name}}.cli:cli',
        ],
    },
)
''',
                'requirements.txt': '''click==8.1.7
rich==13.7.0
requests==2.31.0
pytest==7.4.3
''',
                'tests/test_cli.py': '''from click.testing import CliRunner
from {{project_name}}.cli import cli

def test_greet():
    runner = CliRunner()
    result = runner.invoke(cli, ['greet', 'World'])
    assert result.exit_code == 0
    assert 'Hello' in result.output
''',
                'README.md': '''# {{project_name}}

## Installation

```bash
pip install -e .
```

## Usage

```bash
{{project_name}} greet World
{{project_name}} status
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
'''
            },
            variables=['project_name'],
            post_setup_commands=['pip install -e .', 'mkdir -p tests'],
            dependencies={'python': ['>=3.8']}
        ),
        
        'ml_training': ProjectTemplate(
            id='ml_training',
            name='ML Training Pipeline',
            description='PyTorch training pipeline with W&B, configs, evaluation',
            category='ml',
            files={
                'train.py': '''import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import yaml
from pathlib import Path
import wandb
from tqdm import tqdm

from model import Model
from dataset import Dataset
from utils import get_optimizer, get_scheduler

def train(config):
    wandb.init(project=config['project_name'], config=config)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    model = Model(config['model']).to(device)
    dataset = Dataset(config['data'])
    dataloader = DataLoader(dataset, batch_size=config['batch_size'], shuffle=True)
    
    optimizer = get_optimizer(model, config['optimizer'])
    scheduler = get_scheduler(optimizer, config['scheduler'])
    criterion = nn.CrossEntropyLoss()
    
    for epoch in range(config['epochs']):
        model.train()
        total_loss = 0
        
        for batch in tqdm(dataloader, desc=f"Epoch {epoch}"):
            x, y = batch
            x, y = x.to(device), y.to(device)
            
            optimizer.zero_grad()
            output = model(x)
            loss = criterion(output, y)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(dataloader)
        wandb.log({'loss': avg_loss, 'epoch': epoch})
        
        if epoch % config['save_every'] == 0:
            torch.save(model.state_dict(), f"checkpoints/model_epoch_{epoch}.pt")
        
        scheduler.step()
    
    wandb.finish()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.yaml')
    args = parser.parse_args()
    
    with open(args.config) as f:
        config = yaml.safe_load(f)
    
    Path('checkpoints').mkdir(exist_ok=True)
    train(config)
''',
                'model.py': '''import torch
import torch.nn as nn

class Model(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(config['input_dim'], config['hidden_dim']),
            nn.ReLU(),
            nn.Dropout(config['dropout']),
            nn.Linear(config['hidden_dim'], config['output_dim'])
        )
    
    def forward(self, x):
        return self.layers(x)
''',
                'dataset.py': '''import torch
from torch.utils.data import Dataset

class Dataset(Dataset):
    def __init__(self, config):
        self.data = torch.randn(config['size'], config['input_dim'])
        self.labels = torch.randint(0, config['num_classes'], (config['size'],))
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]
''',
                'utils.py': '''import torch.optim as optim

def get_optimizer(model, config):
    if config['type'] == 'adam':
        return optim.Adam(model.parameters(), lr=config['lr'])
    elif config['type'] == 'sgd':
        return optim.SGD(model.parameters(), lr=config['lr'], momentum=config.get('momentum', 0.9))
    raise ValueError(f"Unknown optimizer: {config['type']}")

def get_scheduler(optimizer, config):
    if config['type'] == 'step':
        return optim.lr_scheduler.StepLR(optimizer, step_size=config['step_size'], gamma=config['gamma'])
    elif config['type'] == 'cosine':
        return optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config['t_max'])
    return None
''',
                'config.yaml': '''project_name: {{project_name}}
batch_size: 32
epochs: 10
save_every: 5

model:
  input_dim: 784
  hidden_dim: 256
  output_dim: 10
  dropout: 0.2

data:
  size: 10000
  input_dim: 784
  num_classes: 10

optimizer:
  type: adam
  lr: 0.001

scheduler:
  type: step
  step_size: 3
  gamma: 0.1
''',
                'requirements.txt': '''torch==2.1.1
wandb==0.16.0
pyyaml==6.0.1
tqdm==4.66.1
pytest==7.4.3
''',
                'README.md': '''# {{project_name}}

## Setup

```bash
pip install -r requirements.txt
wandb login
```

## Train

```bash
python train.py --config config.yaml
```

## Config

Edit `config.yaml` to adjust hyperparameters.
'''
            },
            variables=['project_name'],
            post_setup_commands=['mkdir -p checkpoints', 'wandb login'],
            dependencies={'python': ['>=3.9'], 'cuda': ['optional']}
        )
    }
    
    def __init__(self, templates_dir: str = "templates/custom"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._load_custom_templates()
    
    def _load_custom_templates(self):
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file) as f:
                    data = json.load(f)
                    template = ProjectTemplate(**data)
                    self.TEMPLATES[template.id] = template
            except:
                pass
    
    def list_templates(self, category: str = None) -> List[Dict]:
        templates = []
        for tid, t in self.TEMPLATES.items():
            if category and t.category != category:
                continue
            templates.append({
                'id': tid,
                'name': t.name,
                'description': t.description,
                'category': t.category
            })
        return templates
    
    def get_template(self, template_id: str) -> Optional[ProjectTemplate]:
        return self.TEMPLATES.get(template_id)
    
    def create_project(self, template_id: str, project_path: str, 
                       variables: Dict) -> Dict:
        template = self.TEMPLATES.get(template_id)
        if not template:
            return {'success': False, 'error': 'Template not found'}
        
        project_path = Path(project_path).expanduser()
        
        try:
            # Create directories
            for filepath in template.files.keys():
                full_path = project_path / filepath
                full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write files with variable substitution
            for filepath, content in template.files.items():
                full_path = project_path / self._substitute_variables(filepath, variables)
                processed_content = self._substitute_variables(content, variables)
                full_path.write_text(processed_content)
            
            # Run post-setup commands
            import subprocess
            for cmd in template.post_setup_commands:
                subprocess.run(cmd, shell=True, cwd=project_path, capture_output=True)
            
            return {
                'success': True,
                'path': str(project_path),
                'files_created': len(template.files),
                'template': template.name
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _substitute_variables(self, text: str, variables: Dict) -> str:
        result = text
        for key, value in variables.items():
            result = result.replace(f'{{{{{key}}}}}', str(value))
        return result
    
    def create_custom_template(self, name: str, description: str, 
                               category: str, source_path: str) -> str:
        source_path = Path(source_path).expanduser()
        
        files = {}
        for filepath in source_path.rglob('*'):
            if filepath.is_file():
                relative = filepath.relative_to(source_path)
                files[str(relative)] = filepath.read_text()
        
        template = ProjectTemplate(
            id=f"custom_{name.lower().replace(' ', '_')}",
            name=name,
            description=description,
            category=category,
            files=files,
            variables=['project_name'],
            post_setup_commands=[],
            dependencies={}
        )
        
        template_file = self.templates_dir / f"{template.id}.json"
        with open(template_file, 'w') as f:
            json.dump({
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'category': template.category,
                'files': template.files,
                'variables': template.variables,
                'post_setup_commands': template.post_setup_commands,
                'dependencies': template.dependencies
            }, f, indent=2)
        
        self.TEMPLATES[template.id] = template
        return template.id
