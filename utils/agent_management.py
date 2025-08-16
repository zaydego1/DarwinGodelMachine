# utils/agent_management.py
import os
import shutil
import json
from datetime import datetime


class ChessAgentManager:
    def __init__(self, base_dir="archive"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def create_new_agent(self, parent_id, generation, parallel_id):
        """Create new agent directory from parent"""
        timestamp = datetime.now().strftime("%H%M%S")
        new_agent_id = f"gen{generation}_agent{parallel_id}_{timestamp}"

        parent_dir = os.path.join(self.base_dir, parent_id)
        new_agent_dir = os.path.join(self.base_dir, new_agent_id)

        # Copy parent's codebase
        if os.path.exists(parent_dir):
            shutil.copytree(parent_dir, new_agent_dir)
        else:
            # Create from initial template
            self.create_initial_agent(new_agent_dir)

        # Update agent metadata
        self.update_agent_metadata(new_agent_id, parent_id, generation)

        return new_agent_id

    def create_initial_agent(self, agent_dir):
        """Create initial agent from template"""
        os.makedirs(agent_dir, exist_ok=True)

        # Copy base files
        base_files = [
            "chess_agent.py",
            "tools/",
            "requirements.txt"
        ]

        for file_path in base_files:
            if os.path.isdir(file_path):
                shutil.copytree(file_path, os.path.join(agent_dir, file_path))
            else:
                shutil.copy2(file_path, agent_dir)

    def update_agent_metadata(self, agent_id, parent_id, generation):
        """Update agent's metadata file"""
        metadata = {
            'agent_id': agent_id,
            'parent_id': parent_id,
            'generation': generation,
            'created_at': datetime.now().isoformat(),
            'performance': 0.0,
            'functioning_children_count': 0,
            'evaluation_history': []
        }

        metadata_path = os.path.join(self.base_dir, agent_id, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def update_performance(self, agent_id, performance_score, evaluation_details):
        """Update agent's performance score"""
        metadata_path = os.path.join(self.base_dir, agent_id, "metadata.json")

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        metadata['performance'] = performance_score
        metadata['evaluation_history'].append({
            'timestamp': datetime.now().isoformat(),
            'performance': performance_score,
            'details': evaluation_details
        })

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)